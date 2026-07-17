import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// ── Minimal DOM mock ──────────────────────────────────────────────

let _activeElement = null;

function escapeCss(s) { return s.replace(/[!"#$%&'()*+,./:;<=>?@[\\\]^`{|}~]/g, '\\$&'); }

class MockNode {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attrs = {};
    this._parent = null;
    this._text = '';
  }

  get isConnected() {
    let n = this._parent;
    while (n) { if (n === mockDoc.body) return true; n = n._parent; }
    return this === mockDoc.body;
  }

  setAttribute(n, v) { this.attrs[n] = String(v); }
  getAttribute(n) { return this.attrs[n] ?? null; }
  removeAttribute(n) { delete this.attrs[n]; }
  hasAttribute(n) { return n in this.attrs; }

  get className() { return this.attrs['class'] ?? ''; }
  set className(v) { this.attrs['class'] = v; }
  get dataset() {
    const node = this;
    return new Proxy({}, {
      get(_, prop) { return node.attrs[`data-${String(prop).replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)}`]; },
      set(_, prop, value) { node.attrs[`data-${String(prop).replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)}`] = String(value); return true; },
      deleteProperty(_, prop) { delete node.attrs[`data-${String(prop).replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)}`]; return true; },
    });
  }

  get id() { return this._id ?? null; }
  set id(v) { this._id = v; }

  get textContent() {
    if (this.children.length === 0) return this._text;
    return this.children.map(c => c.textContent).join('');
  }
  set textContent(v) { this.children = []; this._text = String(v); }

  get firstChild() { return this.children[0] ?? null; }

  appendChild(c) {
    if (c._parent) c._parent.children = c._parent.children.filter(x => x !== c);
    c._parent = this;
    this.children.push(c);
  }

  insertBefore(c, ref) {
    if (c._parent) c._parent.children = c._parent.children.filter(x => x !== c);
    c._parent = this;
    const i = ref !== null ? this.children.indexOf(ref) : 0;
    if (i >= 0) this.children.splice(i, 0, c);
    else this.children.push(c);
  }

  replaceWith(n) {
    if (!this._parent) return;
    const i = this._parent.children.indexOf(this);
    if (i >= 0) { n._parent = this._parent; this._parent.children[i] = n; }
    this._parent = null;
  }

  remove() {
    if (!this._parent) return;
    this._parent.children = this._parent.children.filter(c => c !== this);
    this._parent = null;
  }

  closest(sel) {
    if (this._matchSelector(sel)) return this;
    return this._parent?.closest(sel) ?? null;
  }

  querySelector(sel) {
    return this.querySelectorAll(sel)[0] ?? null;
  }

  querySelectorAll(sel) {
    const r = [];
    for (const part of sel.split(',').map((x) => x.trim()).filter(Boolean)) this._querySelectorAll(part, r);
    return [...new Set(r)];
  }

  _querySelectorAll(sel, r) {
    for (const c of this.children) { if (c._matchSelector(sel)) r.push(c); c._querySelectorAll(sel, r); }
  }

  _matchSelector(sel) {
    if (sel === ':scope > .form-error-summary' || sel === '.form-error-summary')
      return (this.attrs['class'] ?? '').includes('form-error-summary');
    if (sel.includes(' ')) {
      const pieces = sel.split(/\s+/);
      const last = pieces.pop();
      if (!last || !this._matchSelector(last)) return false;
      let parent = this._parent;
      for (let i = pieces.length - 1; i >= 0; i -= 1) {
        while (parent && !parent._matchSelector(pieces[i])) parent = parent._parent;
        if (!parent) return false;
        parent = parent._parent;
      }
      return true;
    }
    if (sel === '.field-error')
      return (this.attrs['class'] ?? '').includes('field-error');
    if (sel === '.form-field')
      return (this.attrs['class'] ?? '').includes('form-field');
    if (['input', 'textarea', 'select', 'button'].includes(sel))
      return this.tag === sel;
    const tagAttr = sel.match(/^([a-z]+)\[([a-z-]+)="(.+?)"\]$/);
    if (tagAttr) {
      const [, tag, a, v] = tagAttr;
      return this.tag === tag && this.attrs[a] === v.replace(/\\/g, '');
    }
    if (sel === '[name]')
      return 'name' in this.attrs;
    // [name="x"] or [data-form="x"] or [id="x"]
    const m = sel.match(/^\[([a-z-]+)(?:=\"(.+?)\")?\]$/);
    if (m) {
      const [, a, v] = m;
      if (v !== undefined) {
        if (a === 'id') return this._id === v;
        return this.attrs[a] === v.replace(/\\/g, '');
      }
      if (a === 'id') return this._id !== null;
      return a in this.attrs;
    }
    return false;
  }

  focus() { _activeElement = this; }

  get value() { return this._value ?? ''; }
  set value(v) { this._value = String(v); }
}

class MockDocument {
  constructor() {
    this.body = new MockNode('body');
  }

  get activeElement() { return _activeElement; }

  createElement(tag) {
    if (tag === 'input') {
      const e = new MockNode('input');
      e._value = '';
      e._selStart = 0; e._selEnd = 0;
      Object.defineProperty(e, 'selectionStart', { get: () => e._selStart, configurable: true });
      Object.defineProperty(e, 'selectionEnd', { get: () => e._selEnd, configurable: true });
      e.setSelectionRange = function (s, end) { e._selStart = s; e._selEnd = end; };
      return e;
    }
    if (tag === 'select') return new MockNode('select');
    if (tag === 'button') return new MockNode('button');
    if (tag === 'div') return new MockNode('div');
    if (tag === 'label') return new MockNode('label');
    if (tag === 'strong') return new MockNode('strong');
    if (tag === 'ul') return new MockNode('ul');
    if (tag === 'li') return new MockNode('li');
    if (tag === 'p') return new MockNode('p');
    return new MockNode(tag);
  }

  getElementById(id) {
    return this.body.querySelector(`[id="${id}"]`);
  }

  querySelector(sel) {
    return this.body.querySelector(sel);
  }
}

const mockDoc = new MockDocument();
globalThis.document = mockDoc;
globalThis.HTMLInputElement = MockNode;
globalThis.HTMLTextAreaElement = MockNode;
globalThis.HTMLSelectElement = MockNode;
globalThis.HTMLButtonElement = MockNode;
globalThis.CSS = { escape: escapeCss };

const lifecycle = await import('../dist-tests/targeted-validation-update/mutation-lifecycle.js');
const mod = await import('../dist-tests/targeted-validation-update/targeted-validation-update.js');

function reset() {
  _activeElement = null;
  mockDoc.body.children = [];
}

function mkForm(dataForm) {
  const form = mockDoc.createElement('div');
  form.tag = 'form';
  form.attrs['data-form'] = dataForm;
  form.attrs['class'] = 'ingredient-form';
  form.setAttribute('novalidate', '');
  return form;
}

function addField(form, name, isSelect = false) {
  const field = mockDoc.createElement('div');
  field.attrs['class'] = 'form-field';
  const label = mockDoc.createElement('label');
  const el = isSelect ? mockDoc.createElement('select') : mockDoc.createElement('input');
  el.setAttribute('name', name);
  if (!isSelect) el.value = `value-${name}`;
  label.appendChild(el);
  field.appendChild(label);
  form.appendChild(field);
  return el;
}

function byId(form, id) {
  return form.querySelector(`[id="${id}"]`);
}

test('applies form summary and field errors without replacing nodes', () => {
  reset();

  const form = mkForm('client');
  const inputs = {};
  for (const f of ['full_name', 'phone', 'email', 'address']) {
    inputs[f] = addField(form, f);
  }
  mockDoc.body.appendChild(form);

  const orig = inputs['full_name'];
  orig.focus();
  orig.setSelectionRange(3, 7);

  mod.applyValidationToClientForm({
    fieldErrors: {
      full_name: ['ФИО клиента обязательно.'],
      email: ['Email: Некорректный email.'],
    },
    formErrors: ['Проверьте форму клиента.'],
  });

  // Focus / node identity
  assert.equal(mockDoc.activeElement, orig);
  assert.notEqual(mockDoc.activeElement, mockDoc.body);
  assert.equal(orig.isConnected, true);
  assert.equal(orig.value, 'value-full_name');

  // Selection unchanged
  assert.equal(orig.selectionStart, 3);
  assert.equal(orig.selectionEnd, 7);

  // Summary
  const summary = form.querySelector('.form-error-summary');
  assert.ok(summary);
  assert.ok(summary.textContent.includes('Проверьте форму клиента'));

  // Inline errors
  const fnErr = byId(form, 'client-full_name-error');
  assert.ok(fnErr);
  assert.ok(fnErr.textContent.includes('ФИО клиента обязательно'));

  const emErr = byId(form, 'client-email-error');
  assert.ok(emErr);
  assert.ok(emErr.textContent.includes('Некорректный email'));

  // ARIA
  assert.equal(orig.getAttribute('aria-invalid'), 'true');
  assert.equal(orig.getAttribute('aria-describedby'), 'client-full_name-error');
  assert.equal(inputs['email'].getAttribute('aria-invalid'), 'true');
  assert.equal(inputs['email'].getAttribute('aria-describedby'), 'client-email-error');

  // No stale errors on clean fields
  assert.equal(byId(form, 'client-phone-error'), null);
  assert.equal(byId(form, 'client-address-error'), null);
  assert.equal(inputs['phone'].getAttribute('aria-invalid'), null);
  assert.equal(inputs['address'].getAttribute('aria-invalid'), null);

  // Clear
  mod.applyValidationToClientForm({ fieldErrors: {}, formErrors: [] });
  assert.equal(byId(form, 'client-full_name-error'), null);
  assert.equal(byId(form, 'client-email-error'), null);
  assert.equal(form.querySelector('.form-error-summary'), null);
  assert.equal(orig.hasAttribute('aria-invalid'), false);
  assert.equal(inputs['email'].hasAttribute('aria-invalid'), false);
});

test('ingredient form scoping and focus preservation', () => {
  reset();

  const form = mkForm('ingredient');
  const inputs = {};
  for (const f of ['name', 'category', 'default_unit', 'density_g_per_ml']) {
    inputs[f] = addField(form, f, f === 'category' || f === 'default_unit');
  }
  mockDoc.body.appendChild(form);

  const orig = inputs['name'];
  orig.focus();
  orig.setSelectionRange(0, 5);

  mod.applyValidationToIngredientForm({
    fieldErrors: {
      name: ['Название компонента обязательно.'],
      density_g_per_ml: ['Плотность: Укажите положительное число.'],
    },
    formErrors: ['Проверьте форму компонента.'],
  });

  assert.equal(mockDoc.activeElement, orig);
  assert.equal(orig.isConnected, true);
  assert.equal(orig.selectionStart, 0);
  assert.equal(orig.selectionEnd, 5);

  assert.ok(byId(form, 'ingredient-name-error'));
  assert.equal(inputs['name'].getAttribute('aria-invalid'), 'true');
  assert.ok(byId(form, 'ingredient-density_g_per_ml-error'));
  assert.ok(form.querySelector('.form-error-summary'));

  mod.applyValidationToIngredientForm({ fieldErrors: {}, formErrors: [] });
  assert.equal(byId(form, 'ingredient-name-error'), null);
  assert.equal(byId(form, 'ingredient-density_g_per_ml-error'), null);
  assert.equal(form.querySelector('.form-error-summary'), null);
});

test('form summary includes nested path errors', () => {
  reset();

  const form = mkForm('client');
  addField(form, 'full_name');
  mockDoc.body.appendChild(form);

  const orig = form.querySelector('[name="full_name"]');
  orig.focus();

  mod.applyValidationToClientForm({
    fieldErrors: {},
    formErrors: ['Email: Проверьте email.', 'Название: Проверьте название.'],
  });

  assert.equal(mockDoc.activeElement, orig);

  const summary = form.querySelector('.form-error-summary');
  assert.ok(summary);
  assert.ok(summary.textContent.includes('Проверьте email.'));
  assert.ok(summary.textContent.includes('Проверьте название.'));
  assert.equal(byId(form, 'client-full_name-error'), null);
});

test('caret advances naturally after typed characters', () => {
  reset();

  const form = mkForm('client');
  addField(form, 'full_name');
  mockDoc.body.appendChild(form);

  const orig = form.querySelector('[name="full_name"]');
  orig.value = '';
  orig.focus();

  mod.applyValidationToClientForm({
    fieldErrors: { email: ['Email: Некорректный.'] },
    formErrors: [],
  });

  const chars = ['A', 'н', 'н', 'а'];
  for (const ch of chars) {
    const before = mockDoc.activeElement;
    orig.value += ch;
    orig.setSelectionRange(orig.value.length, orig.value.length);
    assert.equal(mockDoc.activeElement, orig, `activeElement after '${ch}'`);
    assert.equal(before, orig);
    assert.equal(orig.selectionStart, orig.value.length);
  }
});

test('ingredient lot wrapper applies inline errors, summary errors, escaping, and stable ARIA', () => {
  reset();

  const clientForm = mkForm('client');
  addField(clientForm, 'full_name');
  mockDoc.body.appendChild(clientForm);

  const ingredientForm = mkForm('ingredient');
  addField(ingredientForm, 'name');
  mockDoc.body.appendChild(ingredientForm);

  const lotForm = mkForm('ingredient-lot');
  const inputs = {};
  for (const f of ['ingredient_id', 'lot_code', 'supplier_name', 'purchased_at', 'expires_at', 'unit', 'unit_cost', 'total_cost', 'density_g_per_ml', 'notes']) {
    inputs[f] = addField(lotForm, f, f === 'ingredient_id' || f === 'unit');
  }
  mockDoc.body.appendChild(lotForm);

  const orig = inputs['density_g_per_ml'];
  orig.value = '0<script>alert(1)</script>';
  orig.focus();
  orig.setSelectionRange(1, 1);

  mod.applyValidationToIngredientLotForm({
    fieldErrors: {
      density_g_per_ml: ['Плотность, г/мл: <img src=x onerror=alert(1)> Укажите значение больше нуля.'],
      expires_at: ['Срок годности: Дата не может быть раньше даты покупки.'],
    },
    formErrors: ['metadata.unit_cost: Проверьте импортированные данные.', 'unknown_field: Проверьте форму.'],
  });

  assert.equal(mockDoc.activeElement, orig);
  assert.equal(orig.isConnected, true);
  assert.equal(orig.selectionStart, 1);
  assert.equal(orig.selectionEnd, 1);

  const densityError = byId(lotForm, 'ingredient-lot-density_g_per_ml-error');
  assert.ok(densityError);
  assert.ok(densityError.textContent.includes('<img src=x onerror=alert(1)>'));
  assert.equal(densityError.children[0].tag, 'p');
  assert.equal(densityError.children[0].children.length, 0, 'backend HTML stays text-only');
  assert.equal(orig.getAttribute('aria-invalid'), 'true');
  assert.equal(orig.getAttribute('aria-describedby'), 'ingredient-lot-density_g_per_ml-error');

  const summary = lotForm.querySelector('.form-error-summary');
  assert.ok(summary);
  assert.ok(summary.textContent.includes('metadata.unit_cost'));
  assert.ok(summary.textContent.includes('unknown_field'));
  assert.equal(byId(lotForm, 'ingredient-lot-unit_cost-error'), null, 'nested path is not guessed as a known field');

  assert.equal(clientForm.querySelector('.form-error-summary'), null);
  assert.equal(ingredientForm.querySelector('.form-error-summary'), null);

  mod.applyValidationToIngredientLotForm({
    fieldErrors: {
      expires_at: ['Срок годности: Дата не может быть раньше даты покупки.'],
    },
    formErrors: ['metadata.unit_cost: Проверьте импортированные данные.'],
  });

  assert.equal(byId(lotForm, 'ingredient-lot-density_g_per_ml-error'), null);
  assert.equal(orig.hasAttribute('aria-invalid'), false);
  assert.equal(orig.hasAttribute('aria-describedby'), false);
  assert.ok(byId(lotForm, 'ingredient-lot-expires_at-error'), 'unrelated field error remains');
  assert.equal(lotForm.querySelectorAll('.field-error').length, 1, 'repeated apply does not duplicate error elements');
  assert.equal(mockDoc.activeElement, orig);
  assert.equal(orig.selectionStart, 1);
});

test('empty ingredient lot validation clears DOM state without replacing focused input', () => {
  reset();

  const clientForm = mkForm('client');
  addField(clientForm, 'full_name');
  mockDoc.body.appendChild(clientForm);

  const ingredientForm = mkForm('ingredient');
  addField(ingredientForm, 'name');
  mockDoc.body.appendChild(ingredientForm);

  const lotForm = mkForm('ingredient-lot');
  const density = addField(lotForm, 'density_g_per_ml');
  addField(lotForm, 'expires_at');
  mockDoc.body.appendChild(lotForm);

  density.value = '0.5';
  density.focus();
  density.setSelectionRange(1, 3);
  const original = density;

  for (let i = 0; i < 2; i += 1) {
    mod.applyValidationToIngredientLotForm({
      fieldErrors: {
        density_g_per_ml: ['Плотность, г/мл: Укажите значение больше нуля.'],
        expires_at: ['Срок годности: Проверьте дату.'],
      },
      formErrors: ['metadata.unit_cost: Проверьте значение.'],
    });

    assert.equal(lotForm.querySelectorAll('.field-error').length, 2);
    assert.ok(lotForm.querySelector('.form-error-summary'));
    assert.equal(original.getAttribute('aria-invalid'), 'true');
    assert.equal(original.getAttribute('aria-describedby'), 'ingredient-lot-density_g_per_ml-error');

    mod.applyValidationToIngredientLotForm({ fieldErrors: {}, formErrors: [] });

    assert.equal(lotForm.querySelector('.form-error-summary'), null);
    assert.equal(lotForm.querySelectorAll('.field-error').length, 0);
    assert.equal(byId(lotForm, 'ingredient-lot-density_g_per_ml-error'), null);
    assert.equal(byId(lotForm, 'ingredient-lot-expires_at-error'), null);
    assert.equal(original.hasAttribute('aria-invalid'), false);
    assert.equal(original.hasAttribute('aria-describedby'), false);
    assert.equal(original.isConnected, true);
    assert.equal(lotForm.querySelector('[name="density_g_per_ml"]'), original);
    assert.equal(mockDoc.activeElement, original);
    assert.equal(original.selectionStart, 1);
    assert.equal(original.selectionEnd, 3);
  }

  assert.equal(clientForm.querySelector('.form-error-summary'), null);
  assert.equal(clientForm.querySelectorAll('.field-error').length, 0);
  assert.equal(ingredientForm.querySelector('.form-error-summary'), null);
  assert.equal(ingredientForm.querySelectorAll('.field-error').length, 0);
});

test('stock movement wrapper renders field and summary errors without replacing controls', () => {
  reset();
  const form = mkForm('stock-movement');
  const controls = {};
  for (const f of ['ingredient_lot_id', 'movement_type', 'quantity', 'unit', 'occurred_at', 'source', 'reason', 'note']) {
    controls[f] = addField(form, f, f === 'movement_type' || f === 'source');
  }
  mockDoc.body.appendChild(form);
  const qty = controls.quantity;
  qty.value = '0<script>alert(1)</script>';
  qty.focus();
  qty.setSelectionRange(1, 1);

  mod.applyValidationToStockMovementForm({
    fieldErrors: {
      quantity: ['Количество: <b>Введите количество больше нуля.</b>'],
      reason: ['Причина: Укажите причину ручной корректировки.'],
    },
    formErrors: ['items.0.quantity: Недостаточно остатка для такого списания.'],
  });

  assert.equal(mockDoc.activeElement, qty);
  assert.equal(form.querySelector('[name="quantity"]'), qty);
  assert.equal(qty.selectionStart, 1);
  const quantityError = byId(form, 'stock-movement-quantity-error');
  assert.ok(quantityError);
  assert.ok(quantityError.textContent.includes('<b>Введите количество больше нуля.</b>'));
  assert.equal(quantityError.children[0].children.length, 0, 'backend HTML remains text');
  assert.equal(qty.getAttribute('aria-invalid'), 'true');
  assert.equal(qty.getAttribute('aria-describedby'), 'stock-movement-quantity-error');
  assert.ok(form.querySelector('.form-error-summary').textContent.includes('items.0.quantity'));

  mod.applyValidationToStockMovementForm({ fieldErrors: { reason: ['Причина: Укажите причину.'] }, formErrors: [] });
  assert.equal(byId(form, 'stock-movement-quantity-error'), null);
  assert.equal(qty.hasAttribute('aria-invalid'), false);
  assert.ok(byId(form, 'stock-movement-reason-error'));
  assert.equal(form.querySelectorAll('.field-error').length, 1);
  assert.equal(mockDoc.activeElement, qty);
});

test('packaging item wrapper keeps edit input identity and clears stale validation', () => {
  reset();
  const form = mkForm('packaging-item');
  const controls = {};
  for (const f of ['name', 'kind', 'unit', 'capacity_value', 'capacity_unit', 'material', 'supplier_hint', 'unit_cost', 'notes']) {
    controls[f] = addField(form, f, f === 'kind' || f === 'unit' || f === 'capacity_unit');
  }
  mockDoc.body.appendChild(form);
  const name = controls.name;
  name.value = 'Баночка <script>alert(1)</script>';
  name.focus();
  name.setSelectionRange(2, 6);

  for (let i = 0; i < 2; i += 1) {
    mod.applyValidationToPackagingItemForm({
      fieldErrors: {
        name: ['Название: <img src=x onerror=alert(1)> Укажите название тары.'],
        unit_cost: ['Цена за единицу: Введите неотрицательное число.'],
      },
      formErrors: ['metadata.capacity.value: Проверьте объём.'],
    });
    assert.equal(form.querySelectorAll('.field-error').length, 2);
    assert.equal(form.querySelector('[name="name"]'), name);
    assert.equal(mockDoc.activeElement, name);
    assert.equal(name.selectionStart, 2);
    assert.equal(name.selectionEnd, 6);
    assert.equal(name.getAttribute('aria-invalid'), 'true');
    assert.equal(name.getAttribute('aria-describedby'), 'packaging-item-name-error');
    const err = byId(form, 'packaging-item-name-error');
    assert.ok(err.textContent.includes('<img src=x onerror=alert(1)>'));
    assert.equal(err.children[0].children.length, 0);
  }
  assert.equal(form.querySelectorAll('.field-error').length, 2, 'repeated apply does not duplicate errors');

  mod.applyValidationToPackagingItemForm({ fieldErrors: {}, formErrors: [] });
  assert.equal(form.querySelectorAll('.field-error').length, 0);
  assert.equal(form.querySelector('.form-error-summary'), null);
  assert.equal(name.hasAttribute('aria-invalid'), false);
  assert.equal(name.hasAttribute('aria-describedby'), false);
  assert.equal(form.querySelector('[name="name"]'), name);
  assert.equal(mockDoc.activeElement, name);
});


function mainSourceFunction(name) {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `${name} exists`);
  const next = source.indexOf('\nfunction ', start + 1);
  return source.slice(start, next === -1 ? undefined : next);
}

test('submit lifecycle source guard avoids global render at mutation start', () => {
  const stockSubmit = mainSourceFunction('submitStockMovementForm');
  const stockBeforeMutation = stockSubmit.slice(0, stockSubmit.indexOf('createStockMovement(payload)'));
  assert.ok(stockBeforeMutation.includes('applyValidationToStockMovementForm(stockMovementValidation)'));
  assert.ok(stockBeforeMutation.includes('disableStockMovementSubmitControls()'));
  assert.equal(stockBeforeMutation.includes('render()'), false, 'stock submit start must not replace focused controls');

  const packagingSubmit = mainSourceFunction('submitPackagingItemForm');
  const packagingBeforeMutation = packagingSubmit.slice(0, packagingSubmit.indexOf('const request ='));
  assert.ok(packagingBeforeMutation.includes('applyValidationToPackagingItemForm(packagingItemValidation)'));
  assert.ok(packagingBeforeMutation.includes('disablePackagingItemSubmitControls()'));
  assert.equal(packagingBeforeMutation.includes('render()'), false, 'packaging submit start must not replace focused controls');
});

test('packaging context source guard confirms validation clears only after discard confirmation', () => {
  for (const name of ['startEditPackagingItem', 'openPackagingCreateForm', 'cancelPackagingEdit']) {
    const body = mainSourceFunction(name);
    const confirmIndex = body.indexOf('confirmDiscardDirtyAssignment');
    const clearIndex = body.indexOf('packagingItemValidation = emptyFormValidationState()');
    const tokenIndex = body.indexOf('packagingItemSubmitToken += 1');
    assert.ok(confirmIndex > -1, `${name} asks before switching dirty context`);
    assert.ok(clearIndex > confirmIndex, `${name} clears validation only after confirmation`);
    assert.ok(tokenIndex > confirmIndex, `${name} invalidates stale responses only after confirmation`);
  }
});

test('stock movement selector source guard disables visual lot changes during mutation', () => {
  const selector = mainSourceFunction('stockLotSelector');
  assert.ok(selector.includes("data-action=\"select-stock-lot\" ${stockMovementSubmitting ? 'disabled' : ''}"));
  const disable = mainSourceFunction('disableStockMovementSubmitControls');
  assert.ok(disable.includes("[data-action=\"select-stock-lot\"]") && disable.includes("mutationDisabled"));
  const enable = mainSourceFunction('reenableStockMovementSubmitButtons');
  assert.ok(enable.includes("restoreMutationGuards(document)"));
});

test('runtime mutation guard markers preserve focused nodes and legitimate disabled state', () => {
  reset();
  const form = mkForm('packaging-item');
  const name = addField(form, 'name');
  const type = addField(form, 'kind', true);
  const alreadyDisabled = addField(form, 'unit', true);
  alreadyDisabled.disabled = true;
  const action = new MockNode('button');
  action.setAttribute('data-action', 'filter-packaging-search');
  mockDoc.body.appendChild(form);
  mockDoc.body.appendChild(action);
  name.focus();
  name.setSelectionRange(1, 3);

  form.querySelectorAll('[name]').forEach((el) => { if (el.tag === 'input') lifecycle.mutationReadonly(el); else lifecycle.mutationDisabled(el); });
  lifecycle.mutationDisabled(action);

  assert.equal(form.querySelector('[name="name"]'), name);
  assert.equal(mockDoc.activeElement, name);
  assert.equal(name.selectionStart, 1);
  assert.equal(name.readOnly, true);
  assert.equal(type.disabled, true);
  assert.equal(alreadyDisabled.disabled, true);
  assert.equal(alreadyDisabled.dataset.mutationDisabled, undefined, 'pre-existing disabled state is not marked');
  assert.equal(action.disabled, true);

  mod.applyValidationToPackagingItemForm({ fieldErrors: { name: ['Название: Укажите название.'] }, formErrors: [] });
  lifecycle.restoreMutationGuards(mockDoc.body);

  assert.equal(form.querySelector('[name="name"]'), name);
  assert.equal(name.readOnly, false);
  assert.equal(type.disabled, false);
  assert.equal(action.disabled, false);
  assert.equal(alreadyDisabled.disabled, true, 'legitimately disabled control remains disabled');
  assert.equal(mockDoc.activeElement, name);
  assert.equal(name.selectionStart, 1);
  assert.ok(byId(form, 'packaging-item-name-error'));
});

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

test('stock movement detail lifecycle rejects stale deferred responses before state commit', async () => {
  const detail = lifecycle.createStockMovementLotDetailLifecycle();
  const state = { selectedLotId: 1, balance: null, movements: [], detailStatus: 'idle', renders: 0 };
  const old = detail.begin(1);
  const oldRequest = deferred();
  detail.invalidate();
  const submitToken = 7;
  const fresh = detail.begin(1, submitToken);
  const freshRequest = deferred();

  const commit = (request, result, token = request.submitToken) => {
    if (!detail.isCurrent(request, state.selectedLotId, token)) return false;
    state.balance = result.balance;
    state.movements = result.movements;
    state.detailStatus = 'ready';
    state.renders += 1;
    return true;
  };

  const oldApplied = oldRequest.promise.then((result) => commit(old, result, null));
  const freshApplied = freshRequest.promise.then((result) => commit(fresh, result, submitToken));
  oldRequest.resolve({ balance: { quantity: 'stale' }, movements: ['old'] });
  assert.equal(await oldApplied, false);
  assert.equal(state.balance, null);
  assert.equal(state.renders, 0);
  freshRequest.resolve({ balance: { quantity: 'fresh' }, movements: ['new'] });
  assert.equal(await freshApplied, true);
  assert.deepEqual(state.balance, { quantity: 'fresh' });
  assert.deepEqual(state.movements, ['new']);
  assert.equal(state.detailStatus, 'ready');
  assert.equal(state.renders, 1);
});

test('packaging page mutation mutual exclusion helper blocks overlapping writes', () => {
  const state = { packagingItemSubmitting: false, catalogSaving: 'idle', catalogCreating: null, deactivatingId: null };
  const active = () => lifecycle.packagingPageMutationActiveState(state);
  let itemRequests = 0;
  let assignmentRequests = 0;
  let categoryRequests = 0;
  let deactivateRequests = 0;
  const submitItem = () => { if (active()) return false; state.packagingItemSubmitting = true; itemRequests += 1; return true; };
  const saveAssignment = () => { if (active()) return false; state.catalogSaving = 'saving'; assignmentRequests += 1; return true; };
  const createCategory = () => { if (active()) return false; state.catalogCreating = 'category'; categoryRequests += 1; return true; };
  const deactivate = () => { if (active()) return false; state.deactivatingId = 1; deactivateRequests += 1; return true; };

  assert.equal(saveAssignment(), true);
  assert.equal(submitItem(), false);
  assert.equal(itemRequests, 0);
  assert.equal(assignmentRequests, 1);
  state.catalogSaving = 'idle';
  assert.equal(createCategory(), true);
  assert.equal(submitItem(), false);
  assert.equal(categoryRequests, 1);
  state.catalogCreating = null;
  assert.equal(deactivate(), true);
  assert.equal(submitItem(), false);
  assert.equal(deactivateRequests, 1);
  state.deactivatingId = null;
  assert.equal(submitItem(), true);
  assert.equal(saveAssignment(), false);
  assert.equal(createCategory(), false);
  assert.equal(deactivate(), false);
  assert.equal(itemRequests, 1);
});



test('packaging submit lock remains active through deferred list refresh', async () => {
  const state = { packagingItemSubmitting: false, catalogSaving: 'idle', catalogCreating: null, deactivatingId: null };
  const active = () => lifecycle.packagingPageMutationActiveState(state);
  let itemRequests = 0;
  let assignmentRequests = 0;
  let categoryRequests = 0;
  let tagRequests = 0;
  let deactivateRequests = 0;
  let renders = 0;
  let items = ['old'];
  const mutation = deferred();
  const refresh = deferred();
  const submitItem = () => {
    if (active()) return false;
    state.packagingItemSubmitting = true;
    itemRequests += 1;
    mutation.promise.then(() => refresh.promise.then((response) => {
      items = response.items;
      state.packagingItemSubmitting = false;
      renders += 1;
    }));
    return true;
  };
  const saveAssignment = () => { if (active()) return false; assignmentRequests += 1; state.catalogSaving = 'saving'; return true; };
  const createCategory = () => { if (active()) return false; categoryRequests += 1; state.catalogCreating = 'category'; return true; };
  const createTag = () => { if (active()) return false; tagRequests += 1; state.catalogCreating = 'tag'; return true; };
  const deactivate = () => { if (active()) return false; deactivateRequests += 1; state.deactivatingId = 1; return true; };

  assert.equal(submitItem(), true);
  mutation.resolve({ id: 1 });
  await Promise.resolve();
  assert.equal(active(), true, 'lock remains active while refresh is pending');
  assert.equal(saveAssignment(), false);
  assert.equal(createCategory(), false);
  assert.equal(createTag(), false);
  assert.equal(deactivate(), false);
  assert.equal(submitItem(), false);
  assert.equal(itemRequests, 1);
  assert.equal(assignmentRequests + categoryRequests + tagRequests + deactivateRequests, 0);
  assert.equal(renders, 0, 'no unlocked intermediate render');

  refresh.resolve({ items: ['fresh'] });
  await mutation.promise;
  await Promise.resolve();
  await Promise.resolve();
  assert.deepEqual(items, ['fresh']);
  assert.equal(state.packagingItemSubmitting, false);
  assert.equal(active(), false);
  assert.equal(renders, 1);
});

test('packaging refresh failure preserves save success and releases lock once', async () => {
  const state = { packagingItemSubmitting: false, catalogSaving: 'idle', catalogCreating: null, deactivatingId: null };
  const active = () => lifecycle.packagingPageMutationActiveState(state);
  const refresh = deferred();
  let itemRequests = 0;
  let message = '';
  let warning = '';
  let error = '';
  let renders = 0;
  if (!active()) {
    state.packagingItemSubmitting = true;
    itemRequests += 1;
    message = 'Тара сохранена. Остатки не изменялись.';
    refresh.promise.catch(() => {
      warning = 'Тара сохранена, но список не обновился.';
      state.packagingItemSubmitting = false;
      renders += 1;
    });
  }
  refresh.reject(new Error('refresh failed'));
  await Promise.resolve();
  assert.equal(message.includes('сохранена'), true);
  assert.equal(warning.includes('список не обновился'), true);
  assert.equal(error, '');
  assert.equal(itemRequests, 1);
  assert.equal(state.packagingItemSubmitting, false);
  assert.equal(active(), false);
  assert.equal(renders, 1);
});

test('stale packaging refresh cannot overwrite newer lifecycle', async () => {
  let token = 1;
  let items = ['newer'];
  let message = 'Новая операция активна';
  let warning = '';
  let submitting = true;
  let renders = 0;
  const refreshA = deferred();
  const tokenA = token;
  token += 1;
  refreshA.promise.then((response) => {
    if (tokenA !== token) return;
    items = response.items;
    message = 'old';
    submitting = false;
    renders += 1;
  }).catch(() => {
    if (tokenA !== token) return;
    warning = 'old warning';
    submitting = false;
    renders += 1;
  });
  refreshA.resolve({ items: ['old'] });
  await Promise.resolve();
  assert.deepEqual(items, ['newer']);
  assert.equal(message, 'Новая операция активна');
  assert.equal(warning, '');
  assert.equal(submitting, true);
  assert.equal(renders, 0);
});

test('stock post-save refresh failure terminates loading state without retry', async () => {
  const detail = lifecycle.createStockMovementLotDetailLifecycle();
  const request = detail.begin(1, 3);
  const state = { selectedLotId: 1, detailStatus: 'loading', submitting: true, message: 'Движение создано.', warning: '', renders: 0, posts: 1 };
  const refresh = deferred();
  refresh.promise.catch(() => {
    if (!detail.isCurrent(request, state.selectedLotId, 3)) return;
    state.submitting = false;
    state.detailStatus = 'error';
    state.warning = 'Движение создано, но список не обновился.';
    state.renders += 1;
  });
  refresh.reject(new Error('detail refresh failed'));
  await Promise.resolve();
  assert.equal(state.message, 'Движение создано.');
  assert.equal(state.warning.includes('список не обновился'), true);
  assert.equal(state.submitting, false);
  assert.notEqual(state.detailStatus, 'loading');
  assert.equal(state.detailStatus, 'error');
  assert.equal(state.posts, 1);
  assert.equal(state.renders, 1);
});

test('stale stock post-save refresh failure does not mutate state', async () => {
  const detail = lifecycle.createStockMovementLotDetailLifecycle();
  const request = detail.begin(1, 4);
  const state = { selectedLotId: 1, detailStatus: 'ready', submitting: true, warning: '', renders: 0 };
  detail.invalidate();
  const refresh = deferred();
  refresh.promise.catch(() => {
    if (!detail.isCurrent(request, state.selectedLotId, 4)) return;
    state.submitting = false;
    state.detailStatus = 'error';
    state.warning = 'stale warning';
    state.renders += 1;
  });
  refresh.reject(new Error('stale'));
  await Promise.resolve();
  assert.equal(state.warning, '');
  assert.equal(state.detailStatus, 'ready');
  assert.equal(state.submitting, true);
  assert.equal(state.renders, 0);
});

test('source guards cover packaging adjacent actions and stock detail stale render token', () => {
  const disablePackaging = mainSourceFunction('disablePackagingItemSubmitControls');
  for (const action of ['filter-packaging-search', 'filter-packaging-category', 'filter-packaging-kind', 'filter-packaging-status', 'add-packaging-tag-filter', 'remove-packaging-tag-filter', 'clear-packaging-filter', 'reset-packaging-filters', 'packaging-catalog-category', 'packaging-catalog-tag', 'assign-packaging-category', 'toggle-packaging-tag', 'apply-packaging-assignment', 'reset-packaging-assignment', 'search-packaging-category', 'search-packaging-tags', 'toggle-packaging-tags', 'new-packaging-item', 'edit-packaging-item', 'deactivate-packaging-item', 'reload-packaging-items', 'hide-packaging-create-form', 'cancel-packaging-edit']) {
    assert.ok(disablePackaging.includes(action), `${action} is disabled by mutation guard`);
  }
  const lifecycleSource = readFileSync(new URL('../src/mutation-lifecycle.ts', import.meta.url), 'utf8');
  assert.ok(lifecycleSource.includes('data-mutation-disabled'));
  assert.ok(lifecycleSource.includes('data-mutation-readonly'));
  assert.ok(lifecycleSource.includes('packagingPageMutationActiveState'));
  const loadDetail = mainSourceFunction('loadSelectedStockMovementLot');
  assert.ok(loadDetail.includes('stockMovementLotDetailLifecycle.begin'));
  assert.ok(loadDetail.includes('stockMovementSubmitting'));
  assert.ok(mainSourceFunction('stockMovementLotDetailIsCurrent').includes('stockMovementsState.selectedLotId'));
  assert.ok(loadDetail.includes('if (!stockMovementSubmitting) render()'));
  const stockDisable = mainSourceFunction('disableStockMovementSubmitControls');
  assert.ok(stockDisable.includes('mutationDisabled(document.querySelector<HTMLSelectElement>(\'[data-action="select-stock-lot"]\'))'));
});

test('recipe wrappers map template and indexed version errors without replacing focused input', () => {
  reset();
  const templateForm = mkForm('recipe-template');
  const name = addField(templateForm, 'name');
  mockDoc.body.appendChild(templateForm);
  name.focus();
  name.setSelectionRange(1, 3);
  mod.applyValidationToRecipeTemplateForm({ fieldErrors: { name: ['Название рецепта обязательно.'] }, formErrors: ['Проверьте рецепт.'] });
  assert.equal(mockDoc.activeElement, name);
  assert.equal(name.selectionStart, 1);
  assert.equal(name.getAttribute('aria-invalid'), 'true');
  assert.equal(byId(templateForm, 'recipe-template-name-error').textContent, 'Название рецепта обязательно.');

  const versionForm = mkForm('recipe-version');
  const first = addField(versionForm, 'ingredients.0.amount_value');
  const second = addField(versionForm, 'ingredients.1.amount_unit', true);
  mockDoc.body.appendChild(versionForm);
  first.focus();
  first.setSelectionRange(0, 5);
  mod.applyValidationToRecipeVersionForm({ fieldErrors: { 'ingredients.0.amount_value': ['Строка 1: количество: больше нуля.'], 'ingredients.1.amount_unit': ['Строка 2: единица: выберите единицу.'] }, formErrors: ['Неизвестное поле осталось в сводке.'] });
  assert.equal(mockDoc.activeElement, first);
  assert.equal(first.selectionEnd, 5);
  assert.equal(first.getAttribute('aria-describedby'), 'recipe-version-ingredients.0.amount_value-error');
  assert.equal(second.getAttribute('aria-describedby'), 'recipe-version-ingredients.1.amount_unit-error');
  assert.equal(byId(versionForm, 'recipe-version-ingredients.0.amount_value-error').textContent, 'Строка 1: количество: больше нуля.');
  assert.equal(byId(versionForm, 'recipe-version-ingredients.1.amount_unit-error').textContent, 'Строка 2: единица: выберите единицу.');
});

test('recipe mutation guards lock live DOM controls without replacing focused nodes', () => {
  reset();
  const templateForm = mkForm('recipe-template');
  const templateName = addField(templateForm, 'name');
  const templateSubmit = mockDoc.createElement('button');
  templateSubmit.setAttribute('type', 'submit');
  templateSubmit.textContent = 'Создать рецепт';
  const templateBack = mockDoc.createElement('button');
  templateBack.setAttribute('data-action', 'hide-recipe-create');
  templateForm.appendChild(templateSubmit);
  templateForm.appendChild(templateBack);
  const reload = mockDoc.createElement('button');
  reload.setAttribute('data-action', 'reload-recipes');
  mockDoc.body.appendChild(templateForm);
  mockDoc.body.appendChild(reload);
  templateName.focus();
  templateName.setSelectionRange(2, 4);

  const preDisabled = mockDoc.createElement('button');
  preDisabled.disabled = true;
  templateForm.appendChild(preDisabled);
  lifecycle.disableRecipeTemplateMutationControls(mockDoc.body);
  assert.equal(templateForm.getAttribute('aria-busy'), 'true');
  assert.equal(mockDoc.activeElement, templateName);
  assert.equal(templateName.selectionStart, 2);
  assert.equal(templateName.readOnly, true);
  assert.equal(templateSubmit.disabled, true);
  assert.equal(templateSubmit.textContent, 'Создаём…');
  assert.equal(templateBack.disabled, true);
  assert.equal(reload.disabled, true);

  lifecycle.restoreRecipeMutationControls(mockDoc.body);
  assert.equal(templateName.readOnly, false);
  assert.equal(templateSubmit.disabled, false);
  assert.equal(templateSubmit.textContent, 'Создать рецепт');
  assert.equal(templateForm.getAttribute('aria-busy'), null);
  assert.equal(preDisabled.disabled, true);

  reset();
  const versionForm = mkForm('recipe-version');
  const amount = addField(versionForm, 'ingredients.1.amount_value');
  const unit = addField(versionForm, 'ingredients.1.amount_unit', true);
  const versionSubmit = mockDoc.createElement('button');
  versionSubmit.setAttribute('type', 'submit');
  versionSubmit.textContent = 'Сохранить версию рецепта';
  const addLine = mockDoc.createElement('button');
  addLine.setAttribute('data-action', 'add-recipe-line');
  const openVersion = mockDoc.createElement('button');
  openVersion.setAttribute('data-action', 'open-version');
  versionForm.appendChild(versionSubmit);
  versionForm.appendChild(addLine);
  mockDoc.body.appendChild(versionForm);
  mockDoc.body.appendChild(openVersion);
  amount.focus();
  amount.setSelectionRange(1, 5);

  amount.readOnly = true;
  lifecycle.disableRecipeVersionMutationControls(mockDoc.body);
  assert.equal(versionForm.getAttribute('aria-busy'), 'true');
  assert.equal(mockDoc.activeElement, amount);
  assert.equal(amount.selectionEnd, 5);
  assert.equal(amount.readOnly, true);
  assert.equal(unit.disabled, true);
  assert.equal(addLine.disabled, true);
  assert.equal(openVersion.disabled, true);
  assert.equal(versionSubmit.textContent, 'Сохраняем…');
  lifecycle.restoreRecipeMutationControls(mockDoc.body);
  assert.equal(versionForm.getAttribute('aria-busy'), null);
  assert.equal(amount.readOnly, true);
});

test('recipe source uses direct mutation guards and no render at submit start', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  const templateStart = source.indexOf('function submitRecipeTemplateForm');
  const templateRequest = source.indexOf('createRecipeTemplate(payload)', templateStart);
  const templatePrefix = source.slice(templateStart, templateRequest);
  assert.ok(templatePrefix.includes('disableRecipeTemplateMutationControls(document)'));
  assert.equal(templatePrefix.includes('render()'), false);
  assert.ok(templatePrefix.includes('if (recipeVersionSubmitting) return;'));
  assert.ok(templatePrefix.includes('recipeTemplateMutationLifecycle.begin()'));

  const versionStart = source.indexOf('function submitRecipeVersionForm');
  const versionRequest = source.indexOf('createRecipeVersion(templateId', versionStart);
  const versionPrefix = source.slice(versionStart, versionRequest);
  assert.ok(versionPrefix.includes('disableRecipeVersionMutationControls(document)'));
  assert.equal(versionPrefix.includes('render()'), false);
  assert.ok(versionPrefix.includes('if (recipeTemplateSubmitting || !recipesState.selectedTemplate) return;'));
  assert.ok(versionPrefix.includes('recipeVersionMutationLifecycle.begin()'));

  assert.ok(source.includes('restoreRecipeMutationControls(document);'));
  assert.ok(source.includes('recipesRefreshWarning = \'Рецепт создан, но список не обновился.'));
  assert.ok(source.includes('recipesRefreshWarning = \'Версия сохранена, но список или расчёт не обновились.'));
  assert.equal(/data-action=\"move-recipe-line/.test(source), false, 'ingredient-line reorder UI is not implemented in this route');
});


async function runSimulatedRecipeLifecycle({ failRefresh = false, stale = false } = {}) {
  const state = { posts: 0, message: '', warning: '', completed: 0, staleWrites: 0 };
  const lifecycleState = lifecycle.createRecipeMutationLifecycle();
  const post = deferred();
  const refresh = deferred();
  async function submit() {
    const token = lifecycleState.begin();
    if (token === null) return false;
    state.posts += 1;
    try {
      await post.promise;
      if (!lifecycleState.isCurrent(token)) { state.staleWrites += 1; return false; }
      state.message = 'Сохранено.';
      await refresh.promise;
      if (!lifecycleState.isCurrent(token)) { state.staleWrites += 1; return false; }
      lifecycleState.finish(token);
      state.completed += 1;
      return true;
    } catch (error) {
      if (!lifecycleState.isCurrent(token)) { state.staleWrites += 1; return false; }
      if (error && error.refresh) {
        state.warning = 'Сохранено, но список не обновился.';
        lifecycleState.finish(token);
        state.completed += 1;
        return true;
      }
      lifecycleState.finish(token);
      throw error;
    }
  }
  const first = submit();
  const second = submit();
  assert.equal(await second, false);
  assert.equal(state.posts, 1);
  assert.equal(lifecycleState.isActive(), true);
  post.resolve({ id: 1 });
  await Promise.resolve();
  assert.equal(lifecycleState.isActive(), true);
  if (stale) lifecycleState.invalidate();
  if (failRefresh) refresh.reject({ refresh: true });
  else refresh.resolve({ ok: true });
  await first;
  return { state, lifecycleState };
}

test('recipe template async lifecycle prevents duplicate POST and locks through refresh success', async () => {
  const { state, lifecycleState } = await runSimulatedRecipeLifecycle();
  assert.equal(state.posts, 1);
  assert.equal(state.completed, 1);
  assert.equal(state.message, 'Сохранено.');
  assert.equal(lifecycleState.isActive(), false);
});

test('recipe version async lifecycle preserves success warning on refresh failure without retry', async () => {
  const { state, lifecycleState } = await runSimulatedRecipeLifecycle({ failRefresh: true });
  assert.equal(state.posts, 1);
  assert.equal(state.completed, 1);
  assert.equal(state.warning, 'Сохранено, но список не обновился.');
  assert.equal(lifecycleState.isActive(), false);
});

test('recipe async lifecycle ignores stale refresh callbacks', async () => {
  const { state, lifecycleState } = await runSimulatedRecipeLifecycle({ stale: true });
  assert.equal(state.posts, 1);
  assert.equal(state.completed, 0);
  assert.equal(state.staleWrites, 1);
  assert.equal(lifecycleState.isActive(), false);
});

test('client recipe wrappers apply create and row-indexed composition errors without replacing focused controls', () => {
  reset();
  const create = mkForm('client-recipe');
  const title = addField(create, 'title');
  addField(create, 'client_id', true);
  mockDoc.body.appendChild(create);
  title.focus();
  title.setSelectionRange(2, 4);
  mod.applyValidationToClientRecipeCreateForm({ fieldErrors: { title: ['Название индивидуального рецепта: Укажите название.'] }, formErrors: ['Статус недопустим.'] });
  assert.equal(mockDoc.activeElement, title);
  assert.equal(title.selectionStart, 2);
  assert.ok(byId(create, 'client-recipe-title-error'));
  assert.ok(create.querySelector('.form-error-summary').textContent.includes('Статус недопустим'));

  const composition = mkForm('client-recipe-composition');
  const row1 = addField(composition, 'ingredients.0.amount_value');
  const row2 = addField(composition, 'ingredients.1.amount_value');
  mockDoc.body.appendChild(composition);
  row2.focus();
  row2.setSelectionRange(1, 1);
  mod.applyValidationToClientRecipeCompositionForm({ fieldErrors: { 'ingredients.1.amount_value': ['Строка 2: количество: больше нуля.'] }, formErrors: [] });
  assert.equal(mockDoc.activeElement, row2);
  assert.equal(composition.querySelector('[name="ingredients.1.amount_value"]'), row2);
  assert.equal(composition.querySelector('[name="ingredients.0.amount_value"]'), row1);
  assert.ok(byId(composition, 'client-recipe-composition-ingredients.1.amount_value-error'));
  assert.equal(byId(composition, 'client-recipe-composition-ingredients.0.amount_value-error'), null);
});

test('client recipe mutation guards set busy state and preserve pre-existing disabled or readonly states', () => {
  reset();
  const form = mkForm('client-recipe-composition');
  const amount = addField(form, 'ingredients.0.amount_value');
  const unit = addField(form, 'ingredients.0.amount_unit', true);
  const alreadyReadonly = addField(form, 'ingredients.0.notes');
  alreadyReadonly.readOnly = true;
  const alreadyDisabled = addField(form, 'ingredients.0.phase', true);
  alreadyDisabled.disabled = true;
  const submit = mockDoc.createElement('button');
  submit.setAttribute('type', 'submit');
  form.appendChild(submit);
  const action = mockDoc.createElement('button');
  action.setAttribute('data-action', 'remove-client-recipe-composition-line');
  mockDoc.body.appendChild(form);
  mockDoc.body.appendChild(action);
  amount.focus();
  amount.setSelectionRange(1, 3);

  lifecycle.disableClientRecipeCompositionMutationControls(mockDoc.body);
  assert.equal(form.getAttribute('aria-busy'), 'true');
  assert.equal(amount.readOnly, true);
  assert.equal(unit.disabled, true);
  assert.equal(action.disabled, true);
  assert.equal(submit.textContent, 'Сохраняем…');
  assert.equal(alreadyReadonly.dataset.mutationReadonly, undefined);
  assert.equal(alreadyDisabled.dataset.mutationDisabled, undefined);

  lifecycle.restoreClientRecipeMutationControls(mockDoc.body);
  assert.equal(form.getAttribute('aria-busy'), null);
  assert.equal(amount.readOnly, false);
  assert.equal(unit.disabled, false);
  assert.equal(action.disabled, false);
  assert.equal(alreadyReadonly.readOnly, true);
  assert.equal(alreadyDisabled.disabled, true);
  assert.equal(mockDoc.activeElement, amount);
  assert.equal(amount.selectionStart, 1);
});

test('client recipe source contains structural invalidation and authoritative composition update without refresh', () => {
  const removeBody = mainSourceFunction('removeClientRecipeCompositionLine');
  const moveBody = mainSourceFunction('moveClientRecipeCompositionLine');
  const resetBody = mainSourceFunction('resetClientRecipeCompositionEditor');
  assert.ok(removeBody.includes("clearIndexedCollectionValidation(clientRecipeCompositionValidation, 'ingredients')"));
  assert.ok(moveBody.includes("clearIndexedCollectionValidation(clientRecipeCompositionValidation, 'ingredients')"));
  assert.ok(resetBody.includes('clientRecipeCompositionValidation = emptyFormValidationState()'));
  const submitBody = mainSourceFunction('submitClientRecipeCompositionEditor');
  const beforePut = submitBody.slice(0, submitBody.indexOf('updateClientRecipeIngredients'));
  assert.ok(readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8').includes('applyValidationToClientRecipeCompositionForm(clientRecipeCompositionValidation)'));
  assert.ok(readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8').includes('disableClientRecipeCompositionMutationControls(document)'));
  assert.equal(beforePut.includes('render()'), false);
  assert.ok(submitBody.includes('clientRecipesState.selectedDetail = updated'));
  assert.equal(submitBody.includes('getClientRecipe('), false);
  assert.equal(submitBody.includes('getClientRecipes('), false);
});

test('client recipe position remains readonly and indexed validation anchors beside it', () => {
  reset();
  const form = mkForm('client-recipe-composition');
  const position = addField(form, 'ingredients.0.position');
  position.readOnly = true;
  const submit = mockDoc.createElement('button');
  submit.setAttribute('type', 'submit');
  form.appendChild(submit);
  mockDoc.body.appendChild(form);
  assert.equal(position.getAttribute('name'), 'ingredients.0.position');
  assert.equal(position.readOnly, true);
  mod.applyValidationToClientRecipeCompositionForm({ fieldErrors: { 'ingredients.0.position': ['Строка 1: позиция: проверьте порядок.'] }, formErrors: [] });
  assert.ok(byId(form, 'client-recipe-composition-ingredients.0.position-error'));
  lifecycle.disableClientRecipeCompositionMutationControls(mockDoc.body);
  lifecycle.restoreClientRecipeMutationControls(mockDoc.body);
  assert.equal(position.readOnly, true, 'position stays readonly because it was readonly before mutation guards');
  assert.equal(position.getAttribute('name'), 'ingredients.0.position');
});

test('locked row ingredient issue is not silent when a visible exact-name anchor exists', () => {
  reset();
  const form = mkForm('client-recipe-composition');
  const lockedIngredient = addField(form, 'ingredients.0.ingredient_id');
  lockedIngredient.disabled = true;
  mockDoc.body.appendChild(form);
  mod.applyValidationToClientRecipeCompositionForm({ fieldErrors: { 'ingredients.0.ingredient_id': ['Строка 1: компонент: архивный компонент.'] }, formErrors: [] });
  assert.ok(byId(form, 'client-recipe-composition-ingredients.0.ingredient_id-error'));
  assert.equal(lockedIngredient.getAttribute('aria-invalid'), 'true');
});

function createProductionLinkedCreateHarness() {
  const mutation = lifecycle.createRecipeMutationLifecycle();
  const post = deferred();
  const refresh = deferred();
  const state = { busy: false, loading: false, selectedDetail: null, items: [], message: '', error: '', refreshWarning: '', posts: 0, renders: 0, activeRequest: 0 };
  const submit = () => { const request = state.activeRequest + 1; return lifecycle.runClientRecipeCreateMutation({ lifecycle: mutation, blocked: () => false, create: () => { state.posts += 1; return post.promise; }, refresh: () => refresh.promise, onStart: () => { state.activeRequest = request; state.busy = true; state.loading = true; state.error = ''; state.refreshWarning = ''; }, onCreateSuccess: (detail) => { state.message = 'Индивидуальный рецепт создан.'; state.selectedDetail = detail; }, onRefreshSuccess: (items) => { state.items = items; state.busy = false; state.loading = false; }, onRefreshFailure: () => { state.refreshWarning = 'Индивидуальный рецепт создан, но список не обновился.'; state.busy = false; state.loading = false; }, onCreateFailure: () => { state.error = 'Не удалось создать индивидуальный рецепт.'; state.busy = false; state.loading = false; }, isContextCurrent: () => request === state.activeRequest, onFinish: () => { state.renders += 1; } }); };
  return { mutation, post, refresh, state, submit };
}
async function flush() { await Promise.resolve(); await Promise.resolve(); }

test('production-linked client recipe create lifecycle covers duplicate submit, refresh success, and unlock', async () => {
  const h = createProductionLinkedCreateHarness();
  assert.equal(h.submit(), true); assert.equal(h.submit(), false); assert.equal(h.state.posts, 1); assert.equal(h.state.renders, 0);
  h.post.resolve({ id: 1, title: 'created' }); await Promise.resolve();
  assert.equal(h.state.message, 'Индивидуальный рецепт создан.'); assert.deepEqual(h.state.selectedDetail, { id: 1, title: 'created' }); assert.equal(h.mutation.isActive(), true);
  h.refresh.resolve([{ id: 1 }]); await flush();
  assert.deepEqual(h.state.items, [{ id: 1 }]); assert.equal(h.state.busy, false); assert.equal(h.state.loading, false); assert.equal(h.mutation.isActive(), false); assert.equal(h.state.posts, 1);
});

test('production-linked client recipe create refresh failure preserves success without retry and clears on manual refresh', async () => {
  const h = createProductionLinkedCreateHarness();
  assert.equal(h.submit(), true); h.post.resolve({ id: 1, title: 'created' }); await Promise.resolve(); h.refresh.reject(new Error('503')); await flush();
  assert.equal(h.state.message, 'Индивидуальный рецепт создан.'); assert.deepEqual(h.state.selectedDetail, { id: 1, title: 'created' }); assert.ok(h.state.refreshWarning.includes('список не обновился')); assert.equal(h.state.error, ''); assert.equal(h.state.posts, 1); assert.equal(h.state.busy, false); assert.equal(h.state.loading, false); assert.equal(h.mutation.isActive(), false);
  const manualRefresh = (items) => { h.state.items = items; h.state.refreshWarning = ''; }; manualRefresh([{ id: 1 }]); assert.equal(h.state.refreshWarning, '');
});

test('production-linked client recipe create ignores stale create and refresh callbacks', async () => {
  const staleCreate = createProductionLinkedCreateHarness(); assert.equal(staleCreate.submit(), true); staleCreate.state.activeRequest += 1; staleCreate.post.resolve({ id: 1 }); await flush(); assert.equal(staleCreate.state.selectedDetail, null); assert.equal(staleCreate.state.renders, 0);
  const staleRefresh = createProductionLinkedCreateHarness(); assert.equal(staleRefresh.submit(), true); staleRefresh.post.resolve({ id: 1, title: 'created' }); await Promise.resolve(); staleRefresh.state.activeRequest += 1; staleRefresh.refresh.resolve([{ id: 1 }]); await flush(); assert.deepEqual(staleRefresh.state.selectedDetail, { id: 1, title: 'created' }); assert.deepEqual(staleRefresh.state.items, []); assert.equal(staleRefresh.state.renders, 0);
});

function createProductionLinkedCompositionHarness({ stale = false, switchContext = false, archiveActive = false } = {}) {
  const mutation = lifecycle.createRecipeMutationLifecycle(); const put = deferred(); const pageState = { createSubmitting: false, compositionSubmitting: false, archiveRestoreSubmittingId: archiveActive ? 7 : null }; const state = { busy: false, saving: false, selectedId: 1, selectedDetail: { id: 1, ingredients: ['old'] }, draft: ['current draft'], message: '', error: '', puts: 0, gets: 0, listRefreshes: 0, renders: 0, request: 0 };
  const submit = () => { if (lifecycle.clientRecipePageMutationActiveState(pageState)) return false; const request = state.request + 1; const contextId = state.selectedId; return lifecycle.runClientRecipeCompositionMutation({ lifecycle: mutation, blocked: () => lifecycle.clientRecipePageMutationActiveState(pageState), contextId, update: () => { state.puts += 1; return put.promise; }, onStart: () => { state.request = request; pageState.compositionSubmitting = true; state.busy = true; state.saving = true; }, onSuccess: (detail) => { state.selectedDetail = detail; state.draft = []; state.message = 'Состав индивидуального рецепта сохранён.'; state.busy = false; state.saving = false; }, onFailure: () => { state.error = 'Не удалось сохранить состав.'; state.busy = false; state.saving = false; }, isContextCurrent: (id) => state.request === request && state.selectedId === id, onFinish: () => { pageState.compositionSubmitting = false; state.renders += 1; } }); };
  const resolve = async () => { if (stale) state.request += 1; if (switchContext) { state.selectedId = 2; state.selectedDetail = { id: 2, ingredients: ['newer'] }; state.draft = ['newer draft']; } put.resolve({ id: 1, ingredients: ['authoritative'] }); await flush(); };
  return { state, pageState, mutation, put, submit, resolve };
}

test('production-linked client recipe composition applies authoritative PUT without refresh or retry', async () => {
  const h = createProductionLinkedCompositionHarness(); assert.equal(h.submit(), true); assert.equal(h.submit(), false); assert.equal(h.state.puts, 1); assert.equal(h.state.renders, 0); await h.resolve(); assert.deepEqual(h.state.selectedDetail, { id: 1, ingredients: ['authoritative'] }); assert.equal(h.state.gets, 0); assert.equal(h.state.listRefreshes, 0); assert.equal(h.state.puts, 1); assert.equal(h.state.busy, false); assert.equal(h.state.saving, false); assert.equal(h.mutation.isActive(), false);
});

test('production-linked client recipe composition ignores stale callbacks and preserves newer context or draft', async () => {
  const stale = createProductionLinkedCompositionHarness({ stale: true }); assert.equal(stale.submit(), true); await stale.resolve(); assert.deepEqual(stale.state.selectedDetail, { id: 1, ingredients: ['old'] }); assert.deepEqual(stale.state.draft, ['current draft']);
  const switched = createProductionLinkedCompositionHarness({ switchContext: true }); assert.equal(switched.submit(), true); await switched.resolve(); assert.deepEqual(switched.state.selectedDetail, { id: 2, ingredients: ['newer'] }); assert.deepEqual(switched.state.draft, ['newer draft']);
});

test('production-linked client recipe write state blocks archive/restore overlap', () => {
  assert.equal(createProductionLinkedCompositionHarness({ archiveActive: true }).submit(), false);
  const pageState = { createSubmitting: false, compositionSubmitting: true, archiveRestoreSubmittingId: null }; let archiveRequests = 0; const archive = (id) => { if (lifecycle.clientRecipePageMutationActiveState(pageState)) return false; pageState.archiveRestoreSubmittingId = id; archiveRequests += 1; return true; };
  assert.equal(archive(1), false); pageState.compositionSubmitting = false; pageState.archiveRestoreSubmittingId = 2; assert.equal(lifecycle.clientRecipePageMutationActiveState(pageState), true); assert.equal(createProductionLinkedCompositionHarness({ archiveActive: true }).submit(), false); pageState.archiveRestoreSubmittingId = null; assert.equal(archive(2), true); assert.equal(archive(2), false); assert.equal(archiveRequests, 1);
});

test('client recipe archive/restore guard disables conflicts without false create/save progress text', () => {
  reset(); const createForm = mkForm('client-recipe'); const createSubmit = mockDoc.createElement('button'); createSubmit.setAttribute('type', 'submit'); createSubmit.textContent = 'Создать индивидуальный рецепт'; createForm.appendChild(createSubmit); const compositionForm = mkForm('client-recipe-composition'); const compositionSubmit = mockDoc.createElement('button'); compositionSubmit.setAttribute('type', 'submit'); compositionSubmit.textContent = 'Сохранить состав'; compositionForm.appendChild(compositionSubmit); const preDisabled = mockDoc.createElement('button'); preDisabled.setAttribute('data-action', 'archive-client-recipe'); preDisabled.disabled = true; const restore = mockDoc.createElement('button'); restore.setAttribute('data-action', 'restore-client-recipe'); const move = mockDoc.createElement('button'); move.setAttribute('data-action', 'move-client-recipe-composition-line'); mockDoc.body.appendChild(createForm); mockDoc.body.appendChild(compositionForm); mockDoc.body.appendChild(preDisabled); mockDoc.body.appendChild(restore); mockDoc.body.appendChild(move);
  lifecycle.disableClientRecipeArchiveRestoreMutationControls(mockDoc.body); assert.equal(createSubmit.disabled, true); assert.equal(compositionSubmit.disabled, true); assert.equal(restore.disabled, true); assert.equal(move.disabled, true); assert.equal(createSubmit.textContent, 'Создать индивидуальный рецепт'); assert.equal(compositionSubmit.textContent, 'Сохранить состав'); lifecycle.restoreClientRecipeMutationControls(mockDoc.body); assert.equal(createSubmit.disabled, false); assert.equal(compositionSubmit.disabled, false); assert.equal(restore.disabled, false); assert.equal(move.disabled, false); assert.equal(preDisabled.disabled, true);
});

test('production-linked request generations use deferred promises for stale client recipe references', async () => {
  const createRefs = lifecycle.createRequestGenerationLifecycle(); const versions = lifecycle.createRequestGenerationLifecycle(); const compositionRefs = lifecycle.createRequestGenerationLifecycle(); const state = { showCreate: true, activeMutation: false, depsApplied: false, selectedTemplate: 'A', versions: [], versionsStatus: 'loading', selectedRecipeId: 1, editorOpened: false };
  const deps = deferred(); const depsToken = createRefs.begin(); deps.promise.then(() => { if (createRefs.isCurrent(depsToken) && state.showCreate && !state.activeMutation) state.depsApplied = true; }); state.activeMutation = true; deps.resolve('refs'); await flush(); assert.equal(state.depsApplied, false);
  const tokenA = versions.begin(); const requestA = deferred(); state.selectedTemplate = 'B'; const tokenB = versions.begin(); const requestB = deferred(); requestB.promise.then((items) => { if (versions.isCurrent(tokenB) && state.selectedTemplate === 'B') { state.versions = items; state.versionsStatus = 'ready'; } }); requestA.promise.then((items) => { if (versions.isCurrent(tokenA) && state.selectedTemplate === 'A') state.versions = items; }); requestB.resolve(['B1']); await flush(); requestA.resolve(['A1']); await flush(); assert.deepEqual(state.versions, ['B1']); assert.equal(state.versionsStatus, 'ready');
  const repeatOpenToken = versions.begin(); const repeatOpen = deferred(); state.selectedTemplate = 'B'; state.versionsStatus = 'loading'; const openCreateAgainSameContext = () => {}; openCreateAgainSameContext(); repeatOpen.promise.then((items) => { if (versions.isCurrent(repeatOpenToken) && state.selectedTemplate === 'B') { state.versions = items; state.versionsStatus = 'ready'; } }); repeatOpen.resolve(['B2']); await flush(); assert.deepEqual(state.versions, ['B2']); assert.equal(state.versionsStatus, 'ready');
  const compToken = compositionRefs.begin(); const comp = deferred(); comp.promise.then(() => { if (compositionRefs.isCurrent(compToken) && state.selectedRecipeId === 1) state.editorOpened = true; }); state.selectedRecipeId = 2; comp.resolve('ingredients'); await flush(); assert.equal(state.editorOpened, false);
});

test('client wish wrapper maps approved fields and preserves focused draft controls', () => {
  reset();
  const form = mkForm('client-wish');
  const controls = {};
  for (const f of ['title', 'description', 'category', 'priority', 'client_recipe_id']) {
    controls[f] = addField(form, f, ['category', 'priority', 'client_recipe_id'].includes(f));
  }
  mockDoc.body.appendChild(form);
  const title = controls.title;
  title.value = 'Лёгкая текстура <script>alert(1)</script>';
  title.focus();
  title.setSelectionRange(2, 8);

  mod.applyValidationToClientWishForm({
    fieldErrors: {
      title: ['Кратко о пожелании: <img src=x onerror=alert(1)> Укажите заголовок.'],
      category: ['Категория: Выберите категорию.'],
      priority: ['Важность: Выберите важность.'],
      client_recipe_id: ['Индивидуальный рецепт: Рецепт не относится к клиенту.'],
    },
    formErrors: ['metadata.title: Остаётся в сводке.', 'client_id: Клиент не найден.'],
  });

  assert.equal(mockDoc.activeElement, title);
  assert.equal(form.querySelector('[name="title"]'), title);
  assert.equal(title.value, 'Лёгкая текстура <script>alert(1)</script>');
  assert.equal(title.selectionStart, 2);
  assert.equal(title.selectionEnd, 8);
  assert.equal(title.getAttribute('aria-invalid'), 'true');
  assert.equal(title.getAttribute('aria-describedby'), 'client-wish-title-error');
  assert.ok(byId(form, 'client-wish-title-error').textContent.includes('<img src=x onerror=alert(1)>'));
  assert.ok(byId(form, 'client-wish-category-error'));
  assert.ok(byId(form, 'client-wish-priority-error'));
  assert.ok(byId(form, 'client-wish-client_recipe_id-error'));
  assert.ok(form.querySelector('.form-error-summary').textContent.includes('metadata.title'));

  mod.applyValidationToClientWishForm({ fieldErrors: { priority: ['Важность: Выберите важность.'] }, formErrors: ['client_id: Клиент не найден.'] });
  assert.equal(byId(form, 'client-wish-title-error'), null);
  assert.equal(title.hasAttribute('aria-invalid'), false);
  assert.ok(byId(form, 'client-wish-priority-error'));
  assert.equal(form.querySelector('[name="title"]'), title);
  assert.equal(mockDoc.activeElement, title);
});

test('client wish source guards cover lifecycle source wiring without replacing browser smoke', () => {
  const submit = mainSourceFunction('submitClientWishForm');
  assert.ok(submit.includes('clientCardState.savingWish'));
  assert.ok(submit.includes('clientWishCreateLifecycle.begin()'));
  assert.ok(submit.includes('token === null'));
  assert.ok(submit.includes('contextToken !== clientWishContextToken'));
  assert.ok(submit.includes('createClientWish(clientId, payload)'));
  assert.ok(submit.includes('clientCardState.wishes = [created'));
  assert.ok(submit.includes('clientCardState.showWishForm = false'));
  assert.ok(submit.includes('normalizeBackendValidation(apiValidationPayload(error), clientWishFieldLabels'));
  assert.ok(submit.includes('wishRefreshWarning'));
  const successRenderIndex = submit.indexOf('announcePolite(clientCardState.wishMessage);\n    render();\n    return fetchClientWishes');
  assert.notEqual(successRenderIndex, -1, 'successful create renders before the follow-up wishes refresh starts');
  const rejectedStart = submit.indexOf('clientWishValidation = normalizeBackendValidation(apiValidationPayload(error), clientWishFieldLabels');
  const rejectedEnd = submit.indexOf('}).finally', rejectedStart);
  const rejectedPath = submit.slice(rejectedStart, rejectedEnd);
  assert.ok(rejectedPath.includes('applyValidationToClientWishForm(clientWishValidation);'));
  assert.ok(rejectedPath.includes('restoreClientWishMutationControls(document);'));
  assert.equal(rejectedPath.includes('render();'), false, 'rejected create path must not globally render after targeted validation');
  const finalizer = submit.slice(submit.indexOf('}).finally'));
  assert.equal(finalizer.includes('restoreClientWishMutationControls(document);\n      render();'), true, 'finalizer keeps stale/non-rejected fallback render only');
  assert.ok(finalizer.includes('if (createRejected) return;'));
  assert.equal(submit.includes('createClientFeedback'), false);

  const form = mainSourceFunction('clientWishForm');
  assert.ok(form.includes('novalidate'));
  assert.ok(form.includes('validationSummary(clientWishValidation'));
  assert.ok(form.includes('clientWishFieldAttrs'));

  const feedback = mainSourceFunction('submitClientFeedbackForm');
  assert.equal(feedback.includes('clientWishValidation'), false, 'Client Feedback remains outside A3.5 validation migration');
});
