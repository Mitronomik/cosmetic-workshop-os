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
    for (const c of this.children) { if (c._matchSelector(sel)) return c; }
    for (const c of this.children) { const f = c.querySelector(sel); if (f) return f; }
    return null;
  }

  querySelectorAll(sel) {
    const r = [];
    this._querySelectorAll(sel, r);
    return r;
  }

  _querySelectorAll(sel, r) {
    for (const c of this.children) { if (c._matchSelector(sel)) r.push(c); c._querySelectorAll(sel, r); }
  }

  _matchSelector(sel) {
    if (sel === ':scope > .form-error-summary' || sel === '.form-error-summary')
      return (this.attrs['class'] ?? '').includes('form-error-summary');
    if (sel === '.field-error')
      return (this.attrs['class'] ?? '').includes('field-error');
    if (sel === '.form-field')
      return (this.attrs['class'] ?? '').includes('form-field');
    if (sel === 'button')
      return this.tag === 'button';
    if (sel === '[name]')
      return 'name' in this.attrs;
    // [name="x"] or [data-form="x"] or [id="x"]
    const m = sel.match(/^\[([a-z-]+)(?:=\"(.+?)\")?\]$/);
    if (m) {
      const [, a, v] = m;
      if (v !== undefined) {
        if (a === 'id') return this._id === v;
        return this.attrs[a] === v;
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
