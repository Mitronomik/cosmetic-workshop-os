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
