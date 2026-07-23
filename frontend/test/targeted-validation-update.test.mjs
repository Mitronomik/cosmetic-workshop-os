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

test('source guards cover packaging adjacent actions and owned stock detail context', () => {
  const disablePackaging = mainSourceFunction('disablePackagingItemSubmitControls');
  for (const action of ['filter-packaging-search', 'filter-packaging-category', 'filter-packaging-kind', 'filter-packaging-status', 'add-packaging-tag-filter', 'remove-packaging-tag-filter', 'clear-packaging-filter', 'reset-packaging-filters', 'packaging-catalog-category', 'packaging-catalog-tag', 'assign-packaging-category', 'toggle-packaging-tag', 'apply-packaging-assignment', 'reset-packaging-assignment', 'search-packaging-category', 'search-packaging-tags', 'toggle-packaging-tags', 'new-packaging-item', 'edit-packaging-item', 'deactivate-packaging-item', 'reload-packaging-items', 'hide-packaging-create-form', 'cancel-packaging-edit']) {
    assert.ok(disablePackaging.includes(action), `${action} is disabled by mutation guard`);
  }
  const lifecycleSource = readFileSync(new URL('../src/mutation-lifecycle.ts', import.meta.url), 'utf8');
  assert.ok(lifecycleSource.includes('data-mutation-disabled'));
  assert.ok(lifecycleSource.includes('data-mutation-readonly'));
  assert.ok(lifecycleSource.includes('packagingPageMutationActiveState'));
  const loadDetail = mainSourceFunction('loadSelectedStockMovementLot');
  assert.ok(loadDetail.includes('inventoryCatalogWorkspaceRuntime.read'));
  assert.ok(loadDetail.includes("operation: 'stock-lot-detail'"));
  assert.equal(loadDetail.includes("kind: 'reconciliation'"), false);
  assert.ok(loadDetail.includes('contextKey: `lot:${lotId}`'));
  assert.ok(loadDetail.includes('stockMovementsState.selectedLotId !== lotId'));
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
  assert.ok(templatePrefix.includes("formulaClientWorkspaceLifecycle.startMutation('recipes', 'recipe-template-create', 'template:new')"));

  const versionStart = source.indexOf('function submitRecipeVersionForm');
  const versionRequest = source.indexOf('createRecipeVersion(templateId', versionStart);
  const versionPrefix = source.slice(versionStart, versionRequest);
  assert.ok(versionPrefix.includes('disableRecipeVersionMutationControls(document)'));
  assert.equal(versionPrefix.includes('render()'), false);
  assert.ok(versionPrefix.includes('if (recipeTemplateSubmitting || !recipesState.selectedTemplate) return;'));
  assert.ok(versionPrefix.includes("formulaClientWorkspaceLifecycle.startMutation('recipes', 'recipe-version-create'"));

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


function clientFeedbackCardRuntime() {
  const stripTypes = (src) => src
    .replace(/: ClientFeedback/g, '')
    .replace(/: string \| null/g, '')
    .replace(/: string/g, '');
  const code = `
    function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char] ?? char)); }
    function clientFeedbackTypeLabel(value) { return ({ note: 'Заметка', reaction: 'Реакция', texture: 'Текстура', scent: 'Аромат', effect: 'Эффект', packaging: 'Упаковка', request: 'Просьба', other: 'Другое' })[value] ?? 'Другое'; }
    function clientFeedbackSentimentLabel(value) { return ({ positive: 'Положительный', neutral: 'Нейтральный', negative: 'Негативный', mixed: 'Смешанный' })[value] ?? 'Нейтральный'; }
    function clientCardRecipeTitle() { return 'Индивидуальный рецепт'; }
    ${stripTypes(mainSourceFunction('formatClientFeedbackDateOnly'))}
    ${stripTypes(mainSourceFunction('formatClientFeedbackDateTime'))}
    ${stripTypes(mainSourceFunction('clientFeedbackDisplayDate'))}
    ${stripTypes(mainSourceFunction('clientFeedbackCard'))}
    return { clientFeedbackCard, clientFeedbackDisplayDate };
  `;
  return new Function(code)();
}

function feedbackFixture(overrides = {}) {
  return {
    id: 1,
    client_id: 1,
    client_recipe_id: null,
    feedback_type: 'note',
    sentiment: 'neutral',
    rating: null,
    text: 'Клиенту понравилась текстура.',
    follow_up_needed: false,
    follow_up_note: '',
    occurred_at: null,
    created_at: '2026-07-17 14:45:02',
    ...overrides,
  };
}

test('client feedback card safely renders nullable occurrence dates and malformed values', () => {
  const { clientFeedbackCard } = clientFeedbackCardRuntime();
  const createdOnly = feedbackFixture();
  const createdExpected = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date('2026-07-17T14:45:02'));

  assert.doesNotThrow(() => clientFeedbackCard(createdOnly));
  const createdHtml = clientFeedbackCard(createdOnly);
  assert.ok(createdHtml.includes(createdExpected), 'created_at timestamp is used when occurred_at is null');
  assert.ok(createdHtml.includes('Клиенту понравилась текстура.'));
  assert.ok(mainSourceFunction('clientWishForm').includes('data-form="client-wish"'), 'Client Wish form remains renderable in source');
  assert.ok(mainSourceFunction('clientFeedbackForm').includes('data-form="client-feedback"'), 'Client Feedback form remains renderable in source');

  const explicit = feedbackFixture({ occurred_at: '2026-07-10' });
  const explicitExpected = new Intl.DateTimeFormat('ru-RU').format(new Date('2026-07-10T00:00:00'));
  const explicitHtml = clientFeedbackCard(explicit);
  assert.ok(explicitHtml.includes(explicitExpected), 'explicit occurred_at date is preferred');
  assert.equal(explicitHtml.includes(createdExpected), false, 'created_at fallback is not shown when occurrence date is present');

  const spaceSeparated = feedbackFixture({ created_at: '2026-07-18 15:00:00' });
  const spaceExpected = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date('2026-07-18T15:00:00'));
  assert.ok(clientFeedbackCard(spaceSeparated).includes(spaceExpected), 'space-separated created_at timestamp is normalized like PR #119');

  const malformed = feedbackFixture({ created_at: 'not-a-date' });
  const before = structuredClone(malformed);
  assert.doesNotThrow(() => clientFeedbackCard(malformed));
  assert.ok(clientFeedbackCard(malformed).includes('Дата не указана'));
  assert.deepEqual(malformed, before, 'rendering fallback does not mutate source feedback data');
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


test('client wish mutation guard disables feedback controls without losing prior disabled state', () => {
  reset();
  const wishForm = mkForm('client-wish');
  const title = addField(wishForm, 'title');
  const category = addField(wishForm, 'category', true);
  const wishSubmit = mockDoc.createElement('button');
  wishSubmit.setAttribute('type', 'submit');
  wishSubmit.textContent = 'Сохранить пожелание';
  wishForm.appendChild(wishSubmit);

  const feedbackForm = mkForm('client-feedback');
  const feedbackText = addField(feedbackForm, 'text');
  const feedbackType = addField(feedbackForm, 'feedback_type', true);
  const feedbackSubmit = mockDoc.createElement('button');
  feedbackSubmit.setAttribute('type', 'submit');
  feedbackForm.appendChild(feedbackSubmit);
  const alreadyDisabledFeedback = addField(feedbackForm, 'rating');
  alreadyDisabledFeedback.disabled = true;

  const openFeedback = mockDoc.createElement('button');
  openFeedback.setAttribute('data-action', 'toggle-client-feedback-form');
  const closeFeedback = mockDoc.createElement('button');
  closeFeedback.setAttribute('data-action', 'close-client-feedback-form');

  mockDoc.body.appendChild(wishForm);
  mockDoc.body.appendChild(feedbackForm);
  mockDoc.body.appendChild(openFeedback);
  mockDoc.body.appendChild(closeFeedback);

  title.focus();
  title.setSelectionRange(1, 3);
  lifecycle.disableClientWishCreateMutationControls(mockDoc.body);

  assert.equal(wishForm.getAttribute('aria-busy'), 'true');
  assert.equal(title.readOnly, true);
  assert.equal(category.disabled, true);
  assert.equal(wishSubmit.disabled, true);
  assert.equal(openFeedback.disabled, true);
  assert.equal(closeFeedback.disabled, true);
  assert.equal(feedbackText.disabled, true);
  assert.equal(feedbackType.disabled, true);
  assert.equal(feedbackSubmit.disabled, true);
  assert.equal(alreadyDisabledFeedback.disabled, true);
  assert.equal(alreadyDisabledFeedback.dataset.mutationDisabled, undefined, 'pre-existing disabled feedback control is not restored incorrectly');

  lifecycle.restoreClientWishMutationControls(mockDoc.body);

  assert.equal(wishForm.hasAttribute('aria-busy'), false);
  assert.equal(title.readOnly, false);
  assert.equal(category.disabled, false);
  assert.equal(wishSubmit.disabled, false);
  assert.equal(openFeedback.disabled, false);
  assert.equal(closeFeedback.disabled, false);
  assert.equal(feedbackText.disabled, false);
  assert.equal(feedbackType.disabled, false);
  assert.equal(feedbackSubmit.disabled, false);
  assert.equal(alreadyDisabledFeedback.disabled, true);
  assert.equal(mockDoc.activeElement, title);
  assert.equal(title.selectionStart, 1);
  assert.equal(title.selectionEnd, 3);
});


test('client card render context guard blocks stale feedback render after rejected Client Wish validation', () => {
  const captured = {
    capturedClientId: 1,
    currentClientId: 1,
    capturedCardContextToken: 10,
    currentCardContextToken: 10,
    capturedTargetedValidationToken: 20,
    currentTargetedValidationToken: 20,
    wishFormDomLocked: false,
  };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(captured), true, 'non-stale feedback response can render normally');

  const duringMutation = { ...captured, wishFormDomLocked: true };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(duringMutation), false, 'feedback response cannot render over a pending Client Wish mutation');

  const afterRejectedValidation = { ...captured, currentTargetedValidationToken: 21, wishFormDomLocked: false };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(afterRejectedValidation), false, 'older feedback response cannot render after targeted 422 validation advances the targeted-validation render token');

  const clientSwitch = { ...captured, currentClientId: 2, currentCardContextToken: 11 };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(clientSwitch), false, 'feedback from Client A cannot render into Client B');

  const futureRequest = { ...captured, capturedTargetedValidationToken: 21, currentTargetedValidationToken: 21 };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(futureRequest), true, 'new feedback request in the current safe context can render');
});


test('client wish form open and close do not stale targeted-validation render context', () => {
  const captured = {
    capturedClientId: 1,
    currentClientId: 1,
    capturedCardContextToken: 10,
    currentCardContextToken: 10,
    capturedTargetedValidationToken: 30,
    currentTargetedValidationToken: 30,
    wishFormDomLocked: false,
  };
  const openedFormMutationContext = 21;
  const closedFormMutationContext = 22;
  assert.equal(openedFormMutationContext > 20, true, 'ordinary form open may advance the mutation/form context');
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(captured), true, 'ordinary form open does not stale background render when targeted-validation token is unchanged');
  assert.equal(closedFormMutationContext > openedFormMutationContext, true, 'ordinary form close may advance the mutation/form context');
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(captured), true, 'ordinary form close does not stale background render when targeted-validation token is unchanged');

  const after422 = { ...captured, currentTargetedValidationToken: 31 };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(after422), false, 'authoritative targeted 422 validation still stales older background renders');
  const currentAfter422 = { ...after422, capturedTargetedValidationToken: 31 };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(currentAfter422), true, 'new current-context request after 422 can render when safe');
});

test('client card render context guard protects Client Recipes and Wishes callbacks after rejected Client Wish validation', () => {
  const captured = {
    capturedClientId: 1,
    currentClientId: 1,
    capturedCardContextToken: 10,
    currentCardContextToken: 10,
    capturedTargetedValidationToken: 20,
    currentTargetedValidationToken: 21,
    wishFormDomLocked: false,
  };
  const current = { ...captured, capturedTargetedValidationToken: 21 };
  const switched = { ...captured, currentClientId: 2, currentCardContextToken: 11 };

  const recipesState = { recipes: [], recipesStatus: 'loading', renders: 0 };
  const applyRecipesSuccess = (guardState) => {
    if (guardState.currentClientId !== guardState.capturedClientId || guardState.currentCardContextToken !== guardState.capturedCardContextToken) return;
    recipesState.recipes = ['recipe'];
    recipesState.recipesStatus = 'ready';
    if (lifecycle.clientCardRenderAllowedForCapturedContext(guardState)) recipesState.renders += 1;
  };
  applyRecipesSuccess(captured);
  assert.deepEqual(recipesState.recipes, ['recipe'], 'current-card stale-UI recipes response may update safe state');
  assert.equal(recipesState.recipesStatus, 'ready');
  assert.equal(recipesState.renders, 0, 'older recipes response cannot render over targeted validation');
  applyRecipesSuccess(current);
  assert.equal(recipesState.renders, 1, 'current-context recipes response renders normally');

  const recipesErrorState = { recipesStatus: 'loading', renders: 0 };
  const applyRecipesError = (guardState) => {
    if (guardState.currentClientId !== guardState.capturedClientId || guardState.currentCardContextToken !== guardState.capturedCardContextToken) return;
    recipesErrorState.recipesStatus = 'error';
    if (lifecycle.clientCardRenderAllowedForCapturedContext(guardState)) recipesErrorState.renders += 1;
  };
  applyRecipesError(captured);
  assert.equal(recipesErrorState.recipesStatus, 'error', 'current-card stale-UI recipes error may update status');
  assert.equal(recipesErrorState.renders, 0, 'older recipes error cannot render over targeted validation');

  const switchedState = { recipes: [], renders: 0 };
  const applySwitchedRecipes = (guardState) => {
    if (guardState.currentClientId !== guardState.capturedClientId || guardState.currentCardContextToken !== guardState.capturedCardContextToken) return;
    switchedState.recipes = ['stale'];
    if (lifecycle.clientCardRenderAllowedForCapturedContext(guardState)) switchedState.renders += 1;
  };
  applySwitchedRecipes(switched);
  assert.deepEqual(switchedState.recipes, [], 'Client A recipes response cannot update Client B');
  assert.equal(switchedState.renders, 0);

  const wishesState = { wishes: [], wishesStatus: 'loading', renders: 0, generation: 2, includeArchived: false };
  const applyWishesSuccess = (guardState, request = { generation: 2, includeArchived: false }) => {
    const requestCurrent = request.generation === wishesState.generation && request.includeArchived === wishesState.includeArchived;
    if (!requestCurrent || guardState.currentClientId !== guardState.capturedClientId || guardState.currentCardContextToken !== guardState.capturedCardContextToken) return;
    wishesState.wishes = ['wish'];
    wishesState.wishesStatus = 'ready';
    if (lifecycle.clientCardRenderAllowedForCapturedContext(guardState)) wishesState.renders += 1;
  };
  applyWishesSuccess(captured);
  assert.deepEqual(wishesState.wishes, ['wish'], 'current-generation stale-UI wishes response may update safe list state');
  assert.equal(wishesState.renders, 0, 'older wishes response cannot render over targeted validation');
  applyWishesSuccess(current);
  assert.equal(wishesState.renders, 1, 'current-context wishes response renders normally');
  applyWishesSuccess(current, { generation: 1, includeArchived: false });
  assert.equal(wishesState.renders, 1, 'stale wishes generation remains ignored');
});

test('client card source guards use card-level feedback validation contracts without obsolete token strings', () => {
  const obsoleteWishToken = ['client', 'Wish', 'Targeted', 'Validation', 'Token'].join('');
  const submit = mainSourceFunction('submitClientWishForm');
  assert.ok(submit.includes('clientPageMutationActive()'));
  assert.ok(submit.includes('clientWishCreateLifecycle.begin()'));
  assert.ok(submit.includes('clientCardTargetedValidationToken += 1;'));
  assert.equal(submit.includes(obsoleteWishToken), false);

  const refresh = mainSourceFunction('refreshClientWishes');
  assert.ok(refresh.includes('const targetedValidationToken = clientCardTargetedValidationToken;'));
  assert.ok(refresh.includes('clientWishListRequestLifecycle.begin()'));
  assert.ok(refresh.includes('clientCardCanRenderCapturedClientWishContext(clientId, cardContextToken, targetedValidationToken)'));
  assert.equal(refresh.includes(obsoleteWishToken), false);

  const load = mainSourceFunction('loadClientCardData');
  assert.ok(load.includes('const targetedValidationToken = clientCardTargetedValidationToken;'));
  assert.equal(load.includes(obsoleteWishToken), false);

  const feedbackRefresh = mainSourceFunction('refreshClientFeedback');
  assert.ok(feedbackRefresh.includes('const targetedValidationToken = clientCardTargetedValidationToken;'));
  assert.ok(feedbackRefresh.includes('clientFeedbackListRequestLifecycle.begin()'));
  assert.ok(feedbackRefresh.includes('clientFeedbackListRequestLifecycle.isCurrent(requestGeneration)'));
  assert.ok(feedbackRefresh.includes('if (!clientCardFormDomLocked()) syncClientCardDraftFormsFromDom();'));
  assert.equal(feedbackRefresh.includes(obsoleteWishToken), false);

  const renderGuard = mainSourceFunction('clientCardCanRenderCapturedClientWishContext');
  assert.ok(renderGuard.includes('currentTargetedValidationToken: clientCardTargetedValidationToken'));
  assert.ok(renderGuard.includes('clientCardDomLocked: clientCardFormDomLocked()'));
  assert.equal(renderGuard.includes(obsoleteWishToken), false);

  for (const name of ['submitClientForm', 'loadClients', 'openClientCreateForm', 'hideClientCreateForm', 'startEditClient', 'closeClientEdit', 'deactivateClient', 'updateClientFilterSearch', 'updateClientStatusFilter', 'resetClientFilters', 'clearClientFilter', 'toggleClientWishForm', 'closeClientWishForm', 'toggleArchivedClientWishes', 'changeClientWishStatus', 'archiveClientWishFromCard', 'toggleClientFeedbackForm', 'closeClientFeedbackForm', 'submitClientWishForm', 'submitClientFeedbackForm']) {
    const source = mainSourceFunction(name);
    assert.ok(
      source.includes('clientCardFormDomLocked()') || source.includes('clientPageMutationActive()'),
      `${name} has an event-level card/page DOM lock guard`,
    );
  }

  const pageMutation = mainSourceFunction('clientPageMutationActive');
  assert.ok(pageMutation.includes('clientDeactivatingId !== null'));
  assert.ok(pageMutation.includes('clientCardState.changingWishId !== null'));
  assert.ok(pageMutation.includes('clientCardState.archivingWishId !== null'));

  const deactivate = mainSourceFunction('deactivateClient');
  assert.ok(deactivate.includes("formulaClientWorkspaceLifecycle.startMutation('clients', 'client-deactivate'"));
  assert.ok(deactivate.includes('const token = ++clientSubmitToken;'));
  assert.ok(deactivate.includes('clientDeactivatingId = archivedClientId;'));
  assert.ok(deactivate.includes('disableClientDeactivationMutationControls(document, archivedClientId);'));
  assert.ok(deactivate.includes('clientSubmitToken !== token'));

  const feedbackSubmit = mainSourceFunction('submitClientFeedbackForm');
  assert.ok(feedbackSubmit.includes('clientFeedbackCreateLifecycle.begin()'));
  assert.ok(feedbackSubmit.includes('const submittedDraft: ClientFeedbackFormState = { ...clientCardState.feedbackForm };'));
  assert.ok(feedbackSubmit.includes('clientCardState.feedback = [created'));
  assert.ok(feedbackSubmit.includes('return refreshClientFeedback(false, true, false).catch'));
  assert.ok(feedbackSubmit.includes('clientCardTargetedValidationToken += 1;'));
  assert.ok(feedbackSubmit.includes('applyValidationToClientFeedbackForm(clientFeedbackValidation);'));
  assert.equal(feedbackSubmit.includes('render();\n  }).catch'), false);
});

function createFeedbackCreateHarness() {
  const lifecycleState = lifecycle.createRecipeMutationLifecycle();
  const post = deferred();
  const refresh = deferred();
  const state = { clientId: 1, context: 1, savingFeedback: false, savingWish: false, feedback: [], feedbackStatus: 'idle', showFeedbackForm: true, validation: 'clean', message: '', warning: '', error: '', posts: 0, renders: 0, cardToken: 0, draft: { text: 'draft', follow_up_needed: true }, cardActions: 0 };
  const cardLocked = () => state.savingFeedback || state.savingWish;
  const switchClient = (clientId) => { if (cardLocked()) return false; state.clientId = clientId; state.context += 1; state.cardActions += 1; return true; };
  const closeCard = () => { if (cardLocked()) return false; state.clientId = null; state.context += 1; state.cardActions += 1; return true; };
  const submitFeedback = () => {
    if (!state.clientId || cardLocked()) return false;
    const token = lifecycleState.begin();
    if (token === null) return false;
    const clientId = state.clientId;
    const context = state.context;
    const current = () => lifecycleState.isCurrent(token) && state.clientId === clientId && state.context === context;
    state.savingFeedback = true; state.error = ''; state.warning = ''; state.message = ''; state.posts += 1;
    post.promise.then((created) => {
      if (!current()) return;
      state.feedback = [created, ...state.feedback.filter((item) => item.id !== created.id)];
      state.feedbackStatus = 'ready'; state.showFeedbackForm = false; state.validation = 'clean'; state.savingFeedback = false; state.message = 'Отзыв клиента сохранён.'; state.renders += 1;
      return refresh.promise.then((items) => { if (!current()) return; state.feedback = items; state.feedbackStatus = 'ready'; lifecycleState.finish(token); }).catch(() => { if (!current()) return; state.warning = 'Отзыв сохранён, но список не удалось обновить автоматически.'; state.feedback = [created, ...state.feedback.filter((item) => item.id !== created.id)]; state.feedbackStatus = 'ready'; lifecycleState.finish(token); });
    }).catch(() => { if (!current()) return; state.savingFeedback = false; state.validation = 'backend'; state.cardToken += 1; lifecycleState.finish(token); });
    return true;
  };
  const submitWish = () => { if (!state.clientId || cardLocked()) return false; state.savingWish = true; return true; };
  return { state, post, refresh, submitFeedback, submitWish, switchClient, closeCard };
}

test('client feedback deferred lifecycle covers duplicate submit, blocking, stale callbacks, immediate success and refresh failure', async () => {
  const h = createFeedbackCreateHarness();
  assert.equal(h.submitFeedback(), true);
  assert.equal(h.submitFeedback(), false, 'duplicate feedback submit is blocked while POST is pending');
  assert.equal(h.state.posts, 1);
  assert.equal(h.submitWish(), false, 'pending feedback create blocks wish submit');
  assert.equal(h.switchClient(2), false, 'pending feedback create blocks client-card switch');
  assert.equal(h.closeCard(), false, 'pending feedback create blocks card close');
  h.post.resolve({ id: 7, text: 'created' }); await Promise.resolve();
  assert.deepEqual(h.state.feedback, [{ id: 7, text: 'created' }], 'POST result is visible before refresh finishes');
  assert.equal(h.state.message, 'Отзыв клиента сохранён.');
  h.refresh.reject(new Error('503')); await flush();
  assert.deepEqual(h.state.feedback, [{ id: 7, text: 'created' }]);
  assert.ok(h.state.warning.includes('список не удалось обновить'));
  assert.equal(h.state.posts, 1);

  const stale = createFeedbackCreateHarness();
  assert.equal(stale.submitFeedback(), true);
  stale.state.context += 1; stale.state.clientId = 2;
  stale.post.resolve({ id: 8, text: 'stale' }); await flush();
  assert.deepEqual(stale.state.feedback, [], 'Client A callback cannot update Client B');
});

test('client wish and feedback pending states mutually block submits', () => {
  const h = createFeedbackCreateHarness();
  h.state.savingWish = true;
  assert.equal(h.submitFeedback(), false, 'pending wish create blocks feedback submit');
  h.state.savingWish = false;
  assert.equal(h.submitFeedback(), true);
  assert.equal(h.submitWish(), false, 'pending feedback create blocks wish submit');
});

test('card-level targeted validation token controls delayed background renders', () => {
  const captured = { capturedClientId: 1, currentClientId: 1, capturedCardContextToken: 3, currentCardContextToken: 3, capturedTargetedValidationToken: 5, currentTargetedValidationToken: 5, clientCardDomLocked: false };
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(captured), true);
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext({ ...captured, clientCardDomLocked: true }), false, 'delayed GET during feedback POST cannot render');
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext({ ...captured, currentTargetedValidationToken: 6 }), false, 'delayed GET captured before feedback 422 cannot render');
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext({ ...captured, capturedTargetedValidationToken: 6, currentTargetedValidationToken: 6 }), true, 'current request captured after feedback 422 can render');
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext({ ...captured, currentClientId: 2, currentCardContextToken: 4 }), false, 'client switch invalidates old callback');
  assert.equal(lifecycle.clientCardRenderAllowedForCapturedContext(captured), true, 'ordinary form open/close does not stale valid background response');
});



test('client page mutation controls lock parent Clients form and toolbar for feedback and wish creates', () => {
  for (const mode of ['feedback', 'wish']) {
    reset();
    const clientForm = mkForm('client');
    const name = addField(clientForm, 'full_name');
    const notes = mockDoc.createElement('textarea'); notes.setAttribute('name', 'notes'); clientForm.appendChild(notes);
    const status = mockDoc.createElement('select'); status.setAttribute('name', 'status'); clientForm.appendChild(status);
    const preReadonly = addField(clientForm, 'pre_readonly'); preReadonly.readOnly = true;
    const preDisabled = mockDoc.createElement('button'); preDisabled.setAttribute('data-action', 'archive-client'); preDisabled.disabled = true;
    const submit = mockDoc.createElement('button'); submit.setAttribute('type', 'submit'); clientForm.appendChild(submit);
    const reload = mockDoc.createElement('button'); reload.setAttribute('data-action', 'reload-clients');
    const open = mockDoc.createElement('button'); open.setAttribute('data-action', 'open-client-create');
    const search = mockDoc.createElement('input'); search.setAttribute('data-action', 'filter-clients-search');
    const filter = mockDoc.createElement('select'); filter.setAttribute('data-action', 'filter-clients-status');
    const resetFilters = mockDoc.createElement('button'); resetFilters.setAttribute('data-action', 'reset-client-filters');
    mockDoc.body.appendChild(clientForm); mockDoc.body.appendChild(preDisabled); mockDoc.body.appendChild(reload); mockDoc.body.appendChild(open); mockDoc.body.appendChild(search); mockDoc.body.appendChild(filter); mockDoc.body.appendChild(resetFilters);

    if (mode === 'feedback') lifecycle.disableClientFeedbackCreateMutationControls(mockDoc.body);
    else lifecycle.disableClientWishCreateMutationControls(mockDoc.body);

    assert.equal(name.readOnly, true, `${mode}: client text input readonly`);
    assert.equal(notes.readOnly, true, `${mode}: client textarea readonly`);
    assert.equal(status.disabled, true, `${mode}: client select disabled`);
    assert.equal(submit.disabled, true, `${mode}: client form button disabled`);
    assert.equal(reload.disabled, true, `${mode}: reload disabled`);
    assert.equal(open.disabled, true, `${mode}: open create disabled`);
    assert.equal(search.disabled, true, `${mode}: search disabled`);
    assert.equal(filter.disabled, true, `${mode}: status filter disabled`);
    assert.equal(resetFilters.disabled, true, `${mode}: reset filters disabled`);

    if (mode === 'feedback') lifecycle.restoreClientFeedbackMutationControls(mockDoc.body);
    else lifecycle.restoreClientWishMutationControls(mockDoc.body);

    assert.equal(name.readOnly, false, `${mode}: helper restores client text input`);
    assert.equal(notes.readOnly, false, `${mode}: helper restores client textarea`);
    assert.equal(status.disabled, false, `${mode}: helper restores client select`);
    assert.equal(submit.disabled, false, `${mode}: helper restores client button`);
    assert.equal(reload.disabled, false, `${mode}: helper restores reload`);
    assert.equal(open.disabled, false, `${mode}: helper restores open create`);
    assert.equal(search.disabled, false, `${mode}: helper restores search`);
    assert.equal(filter.disabled, false, `${mode}: helper restores status filter`);
    assert.equal(resetFilters.disabled, false, `${mode}: helper restores reset`);
    assert.equal(preReadonly.readOnly, true, `${mode}: pre-readonly remains readonly`);
    assert.equal(preDisabled.disabled, true, `${mode}: pre-disabled archive remains disabled`);
  }
});

function createClientPageHarness() {
  const state = { clientSubmitting: false, savingWish: false, savingFeedback: false, clientsStatus: 'ready', items: ['old'], renders: 0, submits: 0, filters: { search: '', status: 'active' }, includeInactive: false, showCreate: false };
  const locked = () => state.savingWish || state.savingFeedback;
  const pageActive = () => state.clientSubmitting || locked();
  const render = () => { state.renders += 1; };
  const submitClientForm = () => { if (pageActive()) return false; state.submits += 1; state.clientSubmitting = true; return true; };
  const action = (fn) => { if (pageActive()) return false; fn(); return true; };
  const loadCompletion = (items) => { state.items = items; state.clientsStatus = 'ready'; if (!locked()) render(); };
  return { state, submitClientForm, openCreate: () => action(() => { state.showCreate = true; render(); }), search: (value) => action(() => { state.filters.search = value; render(); }), status: (value) => action(() => { state.filters.status = value; state.includeInactive = value !== 'active'; }), reset: () => action(() => { state.filters = { search: '', status: 'active' }; render(); }), reload: () => action(() => { state.clientsStatus = 'loading'; render(); }), loadCompletion };
}

test('client page mutation predicate blocks parent submit/filter/reload actions while feedback or wish POST is pending', () => {
  for (const mode of ['savingFeedback', 'savingWish']) {
    const h = createClientPageHarness();
    h.state[mode] = true;
    assert.equal(h.submitClientForm(), false, `${mode}: client form submit blocked`);
    assert.equal(h.openCreate(), false, `${mode}: open create blocked`);
    assert.equal(h.search('anna'), false, `${mode}: search blocked`);
    assert.equal(h.status('all'), false, `${mode}: status filter blocked`);
    assert.equal(h.reset(), false, `${mode}: reset blocked`);
    assert.equal(h.reload(), false, `${mode}: reload blocked`);
    assert.equal(h.state.renders, 0, `${mode}: blocked actions do not render over locked card`);
    h.state[mode] = false;
    assert.equal(h.submitClientForm(), true, `${mode}: normal submit works after unlock`);
  }
});

test('client list completion during wish or feedback POST updates safe state without replacing live card DOM', () => {
  for (const mode of ['savingFeedback', 'savingWish']) {
    const h = createClientPageHarness();
    h.state.clientsStatus = 'loading';
    h.state[mode] = true;
    h.loadCompletion(['new']);
    assert.deepEqual(h.state.items, ['new'], `${mode}: safe list state updates`);
    assert.equal(h.state.clientsStatus, 'ready', `${mode}: page does not stay loading`);
    assert.equal(h.state.renders, 0, `${mode}: no full render while card DOM is locked`);
    h.state[mode] = false;
    h.loadCompletion(['fresh']);
    assert.equal(h.state.renders, 1, `${mode}: current completion can render after unlock`);
  }
});


function createClientArchiveHarness() {
  const archiveLifecycle = lifecycle.createRecipeMutationLifecycle();
  const archive = deferred();
  const refresh = deferred();
  const state = { deactivatingId: null, clientSubmitting: false, savingWish: false, savingFeedback: false, changingWishId: null, archivingWishId: null, clients: [{ id: 1, active: true }, { id: 2, active: true }], currentFormId: 1, currentCardId: 1, renders: 0, archiveRequests: 0, message: '', error: '', warning: '', controlsRestored: 0, showCreate: false, filters: { search: '', status: 'active' } };
  const cardLocked = () => state.savingWish || state.savingFeedback;
  const pageActive = () => state.clientSubmitting || state.deactivatingId !== null || state.changingWishId !== null || state.archivingWishId !== null || cardLocked();
  const render = () => { state.renders += 1; };
  const restore = () => { state.controlsRestored += 1; };
  const startArchive = (id) => {
    if (pageActive()) return false;
    const token = archiveLifecycle.begin();
    if (token === null) return false;
    state.deactivatingId = id;
    state.archiveRequests += 1;
    const isCurrent = () => archiveLifecycle.isCurrent(token) && state.deactivatingId === id;
    archive.promise.then((archivedClient = { id, active: false }) => {
      if (!isCurrent()) return;
      state.clients = state.clients.map((client) => client.id === id ? { ...client, ...archivedClient, active: false } : client);
      state.message = 'Клиент архивирован.';
      state.error = '';
      state.warning = '';
      if (state.currentFormId === id) {
        state.currentFormId = null;
        state.currentCardId = null;
      }
      return refresh.promise.then((clients) => {
        if (!isCurrent()) return;
        state.clients = clients;
        state.message = 'Клиент архивирован.';
        state.error = '';
        state.warning = '';
      }).catch(() => {
        if (!isCurrent()) return;
        state.message = 'Клиент архивирован.';
        state.error = '';
        state.warning = 'Клиент архивирован, но список не удалось обновить автоматически.';
      });
    }, () => {
      if (!isCurrent()) return;
      state.message = '';
      state.error = 'Не удалось архивировать клиента. Попробуйте еще раз.';
      state.warning = '';
    }).finally(() => {
      if (!archiveLifecycle.finish(token) || state.deactivatingId !== id) return;
      state.deactivatingId = null;
      restore();
      render();
    });
    return true;
  };
  const submitFeedback = () => { if (pageActive()) return false; state.savingFeedback = true; return true; };
  const submitWish = () => { if (pageActive()) return false; state.savingWish = true; return true; };
  const submitClientForm = () => { if (pageActive()) return false; state.clientSubmitting = true; return true; };
  const action = (fn) => { if (pageActive()) return false; fn(); return true; };
  return {
    state, archive, refresh, archiveLifecycle,
    startArchive, submitFeedback, submitWish, submitClientForm,
    reload: () => action(render),
    search: () => action(() => { state.filters.search = 'anna'; render(); }),
    status: () => action(() => { state.filters.status = 'all'; render(); }),
    openCreate: () => action(() => { state.showCreate = true; render(); }),
    switchClient: (id) => action(() => { state.currentFormId = id; state.currentCardId = id; render(); }),
  };
}

test('client archive lifecycle separates archive success from list refresh success and blocks page actions', async () => {
  const h = createClientArchiveHarness();
  assert.equal(h.startArchive(1), true, 'ordinary archive starts');
  assert.equal(h.startArchive(1), false, 'duplicate archive is blocked');
  assert.equal(h.state.archiveRequests, 1, 'duplicate archive sends exactly one request');
  assert.equal(h.submitFeedback(), false, 'archive first blocks feedback submit');
  assert.equal(h.submitWish(), false, 'archive first blocks wish submit');
  assert.equal(h.submitClientForm(), false, 'archive first blocks client form submit');
  assert.equal(h.reload(), false, 'archive blocks reload');
  assert.equal(h.search(), false, 'archive blocks search');
  assert.equal(h.status(), false, 'archive blocks status filter');
  assert.equal(h.openCreate(), false, 'archive blocks create form');
  assert.equal(h.switchClient(2), false, 'archive blocks client switch');
  h.archive.resolve({ id: 1, active: false }); await Promise.resolve();
  assert.equal(h.state.currentCardId, null, 'archive success closes matching card before refresh');
  assert.deepEqual(h.state.clients, [{ id: 1, active: false }, { id: 2, active: true }], 'local state marks client archived before refresh');
  h.refresh.resolve([{ id: 1, active: false }, { id: 2, active: true }, { id: 3, active: true }]); await flush(); await flush();
  assert.equal(h.state.deactivatingId, null, 'archive releases page lock');
  assert.equal(h.state.controlsRestored, 1, 'archive restores controls once');
  assert.equal(h.state.currentFormId, null, 'successful archive closes matching edited card');
  assert.equal(h.state.currentCardId, null, 'successful archive clears matching client card');
  assert.equal(h.state.message, 'Клиент архивирован.');
  assert.equal(h.state.warning, '');
  assert.equal(h.state.error, '');
  assert.deepEqual(h.state.clients, [{ id: 1, active: false }, { id: 2, active: true }, { id: 3, active: true }], 'successful refresh replaces clients list');
  assert.equal(h.submitFeedback(), true, 'feedback submit is available after archive unlock');
});

test('client archive success with list refresh failure keeps archive success and warning separate', async () => {
  const h = createClientArchiveHarness();
  assert.equal(h.startArchive(1), true);
  h.archive.resolve({ id: 1, active: false }); await Promise.resolve();
  assert.equal(h.state.message, 'Клиент архивирован.');
  assert.equal(h.state.currentCardId, null, 'matching card closes immediately after archive success');
  assert.deepEqual(h.state.clients, [{ id: 1, active: false }, { id: 2, active: true }], 'archived local state is preserved before refresh');
  h.refresh.reject(new Error('503')); await flush(); await flush();
  assert.equal(h.state.deactivatingId, null, 'refresh failure releases archive lock');
  assert.equal(h.state.message, 'Клиент архивирован.');
  assert.equal(h.state.error, '', 'no false archive error after successful archive');
  assert.equal(h.state.warning, 'Клиент архивирован, но список не удалось обновить автоматически.');
  assert.equal(h.state.currentCardId, null, 'matching card remains closed after refresh failure');
  assert.deepEqual(h.state.clients, [{ id: 1, active: false }, { id: 2, active: true }], 'created archived state remains visible after refresh failure');
  assert.equal(h.state.archiveRequests, 1, 'refresh failure does not send another archive request');
});

test('client archive API failure releases lock without success state', async () => {
  const failed = createClientArchiveHarness();
  assert.equal(failed.startArchive(1), true);
  failed.archive.reject(new Error('409')); await flush(); await flush();
  assert.equal(failed.state.deactivatingId, null, 'failed archive releases lock');
  assert.equal(failed.state.currentCardId, 1, 'archive API failure preserves current card');
  assert.ok(failed.state.error.includes('Не удалось архивировать клиента'));
  assert.equal(failed.state.message, '', 'archive API failure does not show success');
  assert.equal(failed.state.warning, '', 'archive API failure does not show refresh warning');
  assert.deepEqual(failed.state.clients, [{ id: 1, active: true }, { id: 2, active: true }]);
  assert.equal(failed.state.archiveRequests, 1);
});

test('client archive failure releases lock and stale callback cannot update another client', async () => {
  const failed = createClientArchiveHarness();
  assert.equal(failed.startArchive(1), true);
  failed.archive.reject(new Error('503')); await flush(); await flush();
  assert.equal(failed.state.deactivatingId, null, 'failed archive releases lock');
  assert.equal(failed.state.currentCardId, 1, 'failed archive preserves current card');
  assert.ok(failed.state.error.includes('Не удалось архивировать клиента'));
  assert.equal(failed.state.controlsRestored, 1);

  const stale = createClientArchiveHarness();
  assert.equal(stale.startArchive(1), true);
  stale.archiveLifecycle.invalidate();
  stale.state.deactivatingId = null;
  stale.state.currentFormId = 2;
  stale.state.currentCardId = 2;
  stale.archive.resolve(); await Promise.resolve();
  stale.refresh.resolve([{ id: 1, active: false }]); await flush(); await flush();
  assert.equal(stale.state.currentCardId, 2, 'stale archive callback cannot update another client card');
  assert.deepEqual(stale.state.clients, [{ id: 1, active: true }, { id: 2, active: true }], 'stale archive callback does not replace clients state');
  assert.equal(stale.state.renders, 0, 'stale archive callback does not render');
});

test('client deactivation mutation controls restore readonly and disabled states safely', () => {
  reset();
  const clientForm = mkForm('client');
  const name = addField(clientForm, 'full_name');
  const preReadonly = addField(clientForm, 'pre_readonly'); preReadonly.readOnly = true;
  const submit = mockDoc.createElement('button'); submit.setAttribute('type', 'submit'); clientForm.appendChild(submit);
  const archiveButton = mockDoc.createElement('button'); archiveButton.setAttribute('data-action', 'archive-client'); archiveButton.setAttribute('data-id', '1');
  const preDisabled = mockDoc.createElement('button'); preDisabled.setAttribute('data-action', 'reload-clients'); preDisabled.disabled = true;
  const wishSubmit = mockDoc.createElement('button'); wishSubmit.setAttribute('data-action', 'toggle-client-wish-form');
  const feedbackSubmit = mockDoc.createElement('button'); feedbackSubmit.setAttribute('data-action', 'toggle-client-feedback-form');
  mockDoc.body.appendChild(clientForm); mockDoc.body.appendChild(archiveButton); mockDoc.body.appendChild(preDisabled); mockDoc.body.appendChild(wishSubmit); mockDoc.body.appendChild(feedbackSubmit);
  lifecycle.disableClientDeactivationMutationControls(mockDoc.body, 1);
  assert.equal(name.readOnly, true);
  assert.equal(submit.disabled, true);
  assert.equal(archiveButton.disabled, true);
  assert.equal(wishSubmit.disabled, true);
  assert.equal(feedbackSubmit.disabled, true);
  lifecycle.restoreMutationGuards(mockDoc.body);
  assert.equal(name.readOnly, false);
  assert.equal(submit.disabled, false);
  assert.equal(archiveButton.disabled, false);
  assert.equal(wishSubmit.disabled, false);
  assert.equal(feedbackSubmit.disabled, false);
  assert.equal(preReadonly.readOnly, true, 'pre-readonly remains unchanged');
  assert.equal(preDisabled.disabled, true, 'pre-disabled remains unchanged');
});

function createWishActionHarness() {
  const status = deferred();
  const archive = deferred();
  const state = { changingWishId: null, archivingWishId: null, savingFeedback: false, savingWish: false, clientSubmitting: false, deactivatingId: null, renders: 0, wishError: '', feedbackSubmits: 0, wishSubmits: 0, archiveRequests: 0, statusRequests: 0, clientArchiveRequests: 0, clientSubmits: 0 };
  const cardLocked = () => state.savingFeedback || state.savingWish;
  const pageActive = () => state.clientSubmitting || state.deactivatingId !== null || state.changingWishId !== null || state.archivingWishId !== null || cardLocked();
  const render = () => { state.renders += 1; };
  const startStatus = (wishId) => { if (pageActive()) return false; state.changingWishId = wishId; state.statusRequests += 1; render(); status.promise.catch(() => { state.changingWishId = null; state.wishError = 'Не удалось изменить статус пожелания. Обновите карточку клиента и попробуйте ещё раз.'; if (pageActive()) return; render(); }); return true; };
  const startWishArchive = (wishId) => { if (pageActive()) return false; state.archivingWishId = wishId; state.archiveRequests += 1; render(); archive.promise.catch(() => { state.archivingWishId = null; state.wishError = 'Не удалось архивировать пожелание. Попробуйте ещё раз.'; if (pageActive()) return; render(); }); return true; };
  const submitFeedback = () => { if (pageActive()) return false; state.feedbackSubmits += 1; state.savingFeedback = true; return true; };
  const submitWish = () => { if (pageActive()) return false; state.wishSubmits += 1; state.savingWish = true; return true; };
  const submitClientForm = () => { if (pageActive()) return false; state.clientSubmits += 1; state.clientSubmitting = true; return true; };
  const startClientArchive = () => { if (pageActive()) return false; state.clientArchiveRequests += 1; state.deactivatingId = 1; return true; };
  return { state, status, archive, startStatus, startWishArchive, submitFeedback, submitWish, submitClientForm, startClientArchive };
}

test('client wish status and archive pending states block feedback, wish, client form and archive actions', () => {
  const status = createWishActionHarness();
  assert.equal(status.startStatus(11), true, 'ordinary status mutation starts');
  assert.equal(status.startStatus(12), false, 'duplicate/overlapping status mutation is blocked');
  assert.equal(status.startWishArchive(11), false, 'status pending blocks wish archive');
  assert.equal(status.submitFeedback(), false, 'status pending blocks feedback submit');
  assert.equal(status.submitWish(), false, 'status pending blocks wish create');
  assert.equal(status.submitClientForm(), false, 'status pending blocks client form submit');
  assert.equal(status.startClientArchive(), false, 'status pending blocks client archive');
  assert.equal(status.state.statusRequests, 1);

  const archived = createWishActionHarness();
  assert.equal(archived.startWishArchive(22), true, 'ordinary wish archive starts');
  assert.equal(archived.startWishArchive(23), false, 'duplicate/overlapping archive is blocked');
  assert.equal(archived.startStatus(22), false, 'archive pending blocks status change');
  assert.equal(archived.submitFeedback(), false, 'archive pending blocks feedback submit');
  assert.equal(archived.submitWish(), false, 'archive pending blocks wish create');
  assert.equal(archived.submitClientForm(), false, 'archive pending blocks client form submit');
  assert.equal(archived.startClientArchive(), false, 'archive pending blocks client archive');
  assert.equal(archived.state.archiveRequests, 1);

  for (const mode of ['savingFeedback', 'savingWish', 'deactivatingId']) {
    const h = createWishActionHarness();
    h.state[mode] = mode === 'deactivatingId' ? 1 : true;
    assert.equal(h.startStatus(1), false, `${mode}: blocks wish status action`);
    assert.equal(h.startWishArchive(1), false, `${mode}: blocks wish archive action`);
  }
});

test('failed wish status or archive cannot render over live pending feedback form', async () => {
  const status = createWishActionHarness();
  assert.equal(status.startStatus(1), true);
  assert.equal(status.state.renders, 1, 'status start rendered once before feedback lock');
  status.state.savingFeedback = true;
  status.status.reject(new Error('503')); await flush();
  assert.equal(status.state.changingWishId, null);
  assert.ok(status.state.wishError.includes('Не удалось изменить статус пожелания'));
  assert.equal(status.state.renders, 1, 'status failure does not render over pending feedback form');

  const archived = createWishActionHarness();
  assert.equal(archived.startWishArchive(1), true);
  assert.equal(archived.state.renders, 1, 'archive start rendered once before feedback lock');
  archived.state.savingFeedback = true;
  archived.archive.reject(new Error('503')); await flush();
  assert.equal(archived.state.archivingWishId, null);
  assert.ok(archived.state.wishError.includes('Не удалось архивировать пожелание'));
  assert.equal(archived.state.renders, 1, 'archive failure does not render over pending feedback form');
});

test('client feedback mutation guard disables and restores follow-up checkbox correctly', () => {
  reset();
  const form = mkForm('client-feedback');
  const text = addField(form, 'text');
  const checkbox = addField(form, 'follow_up_needed');
  checkbox.type = 'checkbox';
  checkbox.checked = true;
  const preDisabledCheckbox = addField(form, 'pre_disabled_checkbox');
  preDisabledCheckbox.type = 'checkbox';
  preDisabledCheckbox.disabled = true;
  const submit = mockDoc.createElement('button');
  submit.setAttribute('type', 'submit');
  submit.textContent = 'Сохранить отзыв';
  form.appendChild(submit);
  mockDoc.body.appendChild(form);

  lifecycle.disableClientFeedbackCreateMutationControls(mockDoc.body);
  assert.equal(text.readOnly, true, 'text-like input is readonly during mutation');
  assert.equal(checkbox.disabled, true, 'checkbox is disabled during mutation');
  const attempted = !checkbox.checked;
  if (!checkbox.disabled) checkbox.checked = attempted;
  assert.equal(checkbox.checked, true, 'disabled checkbox cannot change during pending POST');
  assert.equal(preDisabledCheckbox.disabled, true);
  assert.equal(submit.disabled, true);

  lifecycle.restoreClientFeedbackMutationControls(mockDoc.body);
  assert.equal(text.readOnly, false);
  assert.equal(checkbox.disabled, false, 'helper restores checkbox it disabled');
  assert.equal(preDisabledCheckbox.disabled, true, 'pre-disabled checkbox remains disabled');
  assert.equal(submit.disabled, false);
  assert.equal(submit.textContent, 'Сохранить отзыв');
});

test('client feedback wrapper preserves form, controls, values, focus and selection', () => {
  reset();
  const form = mkForm('client-feedback');
  const controls = {};
  for (const f of ['feedback_type', 'sentiment', 'rating', 'occurred_at', 'client_recipe_id', 'text', 'follow_up_needed', 'follow_up_note']) {
    controls[f] = addField(form, f, ['feedback_type', 'sentiment', 'client_recipe_id'].includes(f));
  }
  controls.text.value = 'Очень плотный крем';
  controls.follow_up_needed.setAttribute('type', 'checkbox');
  controls.follow_up_needed.checked = true;
  mockDoc.body.appendChild(form);
  const originalForm = form;
  const originalText = controls.text;
  originalText.focus();
  originalText.setSelectionRange(6, 13);

  mod.applyValidationToClientFeedbackForm({
    fieldErrors: {
      text: ['Текст отзыва: запишите отзыв клиента.'],
      rating: ['Оценка: укажите целое число от 1 до 5.'],
      follow_up_note: ['Что учесть: слишком длинная заметка.'],
    },
    formErrors: ['Выбранный индивидуальный рецепт не относится к этому клиенту.'],
  });

  assert.equal(mockDoc.body.querySelector('[data-form="client-feedback"]'), originalForm);
  assert.equal(form.querySelector('[name="text"]'), originalText);
  assert.equal(mockDoc.activeElement, originalText);
  assert.equal(originalText.value, 'Очень плотный крем');
  assert.equal(controls.follow_up_needed.checked, true);
  assert.equal(originalText.selectionStart, 6);
  assert.equal(originalText.selectionEnd, 13);
  assert.equal(originalText.getAttribute('aria-invalid'), 'true');
  assert.equal(originalText.getAttribute('aria-describedby'), 'client-feedback-text-error');
  assert.ok(byId(form, 'client-feedback-text-error').textContent.includes('запишите отзыв'));
  assert.ok(byId(form, 'client-feedback-rating-error'));
  assert.ok(byId(form, 'client-feedback-follow_up_note-error'));
  assert.ok(form.querySelector('.form-error-summary').textContent.includes('не относится к этому клиенту'));

  mod.applyValidationToClientFeedbackForm({ fieldErrors: {}, formErrors: [] });
  assert.equal(mockDoc.body.querySelector('[data-form="client-feedback"]'), originalForm);
  assert.equal(form.querySelector('[name="text"]'), originalText);
  assert.equal(originalText.hasAttribute('aria-invalid'), false);
  assert.equal(originalText.hasAttribute('aria-describedby'), false);
  assert.equal(form.querySelectorAll('.field-error').length, 0);
  assert.equal(form.querySelector('.form-error-summary'), null);
  assert.equal(mockDoc.activeElement, originalText);
  assert.equal(originalText.selectionStart, 6);
  assert.equal(originalText.selectionEnd, 13);
});

test('applyValidationToOrderForm preserves order form DOM, values, focus, selection, ARIA and escaped text', async () => {
  reset();
  const form = mkForm('order');
  const fields = {};
  for (const name of ['product_name', 'target_batch_size_value', 'client_id', 'source_type', 'recipe_version_id', 'packaging_item_id', 'packaging_quantity', 'ordered_at', 'planned_production_at', 'notes']) {
    fields[name] = addField(form, name, ['client_id', 'source_type', 'recipe_version_id', 'packaging_item_id'].includes(name));
    fields[name].value = { product_name: 'Крем <день>', target_batch_size_value: '50,5', client_id: '12', source_type: 'recipe_version', recipe_version_id: '7', packaging_item_id: '3', packaging_quantity: '1', ordered_at: '2026-07-18', planned_production_at: '2026-07-19', notes: 'Не терять заметки' }[name];
  }
  mockDoc.body.appendChild(form);
  const product = fields.product_name;
  product.focus();
  product.setSelectionRange(2, 6);
  mod.applyValidationToOrderForm({ fieldErrors: { product_name: ['Название продукта: <b>не HTML</b>'], source_type: ['Основа заказа: выберите основу.'], recipe_version_id: ['Версия рецепта: выберите версию.'] }, formErrors: ['Общая <script>ошибка</script>'] });
  assert.equal(mockDoc.body.querySelector('[data-form="order"]'), form);
  assert.equal(form.querySelector('[name="product_name"]'), product);
  assert.equal(fields.product_name.value, 'Крем <день>');
  assert.equal(fields.target_batch_size_value.value, '50,5');
  assert.equal(fields.client_id.value, '12');
  assert.equal(fields.source_type.value, 'recipe_version');
  assert.equal(fields.recipe_version_id.value, '7');
  assert.equal(fields.packaging_item_id.value, '3');
  assert.equal(fields.packaging_quantity.value, '1');
  assert.equal(fields.ordered_at.value, '2026-07-18');
  assert.equal(fields.planned_production_at.value, '2026-07-19');
  assert.equal(fields.notes.value, 'Не терять заметки');
  assert.equal(mockDoc.activeElement, product);
  assert.equal(product.selectionStart, 2);
  assert.equal(product.selectionEnd, 6);
  assert.equal(product.getAttribute('aria-invalid'), 'true');
  assert.equal(product.getAttribute('aria-describedby'), 'order-product_name-error');
  assert.ok(byId(form, 'order-product_name-error').textContent.includes('<b>не HTML</b>'));
  assert.ok(byId(form, 'order-product_name-error'));
  mod.applyValidationToOrderForm({ fieldErrors: { product_name: ['Название продукта: повтор.'] }, formErrors: [] });
  assert.ok(byId(form, 'order-product_name-error'));
  assert.equal(form.querySelector('#order-recipe_version_id-error'), null);
  mod.applyValidationToOrderForm({ fieldErrors: {}, formErrors: [] });
  assert.equal(mockDoc.body.querySelector('[data-form="order"]'), form);
  assert.equal(product.hasAttribute('aria-invalid'), false);
  assert.equal(form.querySelectorAll('.field-error').length, 0);
});
