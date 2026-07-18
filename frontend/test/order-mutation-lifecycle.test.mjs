import test from 'node:test';
import assert from 'node:assert/strict';
import {
  clearOrderSourceValidation,
  emptyOrderValidationProvenance,
  orderPayloadFromDraft,
  orderReadCanRender,
} from '../dist-tests/order-mutation-lifecycle/order-mutation-lifecycle.js';
import { mutationDisabled, mutationReadonly, restoreMutationGuards } from '../dist-tests/order-mutation-lifecycle/mutation-lifecycle.js';

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function order(id, name = `Заказ ${id}`) {
  return { id, product_name: name, client_id: 1, recipe_version_id: 1, client_recipe_id: null };
}

function context(overrides = {}) {
  return { contextToken: 1, targetedValidationToken: 1, formMode: 'create', editedOrderId: null, selectedOrderId: null, showForm: true, ...overrides };
}

class OrderHarness {
  constructor() {
    this.state = { items: [], selectedOrder: null, showForm: false, formMode: 'create', editedOrderId: null, draft: {}, validation: { fieldErrors: {}, formErrors: [] }, warning: '', success: '', contextToken: 1, targetedValidationToken: 1, loading: false };
    this.createCalls = [];
    this.updateCalls = [];
    this.refreshCalls = [];
    this.active = false;
    this.token = 0;
  }
  snapshot() { return context({ contextToken: this.state.contextToken, targetedValidationToken: this.state.targetedValidationToken, formMode: this.state.formMode, editedOrderId: this.state.editedOrderId, selectedOrderId: this.state.selectedOrder?.id ?? null, showForm: this.state.showForm }); }
  canRender(snap) { return orderReadCanRender(snap, this.snapshot()); }
  openCreate(draft = {}) { if (this.active) return false; this.state.contextToken += 1; this.state.showForm = true; this.state.formMode = 'create'; this.state.editedOrderId = null; this.state.selectedOrder = null; this.state.draft = draft; return true; }
  openEdit(item, draft = {}) { if (this.active) return false; this.state.contextToken += 1; this.state.showForm = true; this.state.formMode = 'edit'; this.state.editedOrderId = item.id; this.state.selectedOrder = item; this.state.draft = draft; return true; }
  closeForm() { if (this.active) return false; this.state.contextToken += 1; this.state.showForm = false; return true; }
  submit(kind, draft, mutation, refresh) {
    if (this.active) return false;
    this.active = true;
    this.token += 1;
    const token = this.token;
    const submitContext = this.snapshot();
    const payload = orderPayloadFromDraft(draft);
    if (kind === 'create') this.createCalls.push(payload); else this.updateCalls.push(payload);
    mutation.then((saved) => {
      if (token !== this.token || !this.canRender(submitContext)) return;
      this.state.items = [saved, ...this.state.items.filter((item) => item.id !== saved.id)];
      this.state.selectedOrder = saved;
      this.state.showForm = false;
      this.state.success = kind === 'create' ? 'Заказ создан.' : 'Заказ сохранён.';
      this.active = false;
      this.state.contextToken += 1;
      const refreshContext = this.snapshot();
      this.refreshCalls.push(1);
      refresh.then((items) => {
        this.state.loading = false;
        this.state.items = items;
        this.state.warning = '';
      }).catch(() => {
        this.state.loading = false;
        this.state.warning = 'Заказ сохранён, но список не удалось обновить автоматически.';
      }).finally(() => {
        if (!this.canRender(refreshContext)) this.state.didStaleRender = false;
      });
    }).catch((error) => {
      if (token !== this.token) return;
      this.active = false;
      this.state.showForm = true;
      this.state.formMode = submitContext.formMode;
      this.state.editedOrderId = submitContext.editedOrderId;
      this.state.draft = draft;
      this.state.validation = error.validation;
      this.state.targetedValidationToken += 1;
    });
    return true;
  }
}

const baseDraft = { client_id: '1', source_type: 'recipe_version', recipe_version_id: '2', client_recipe_id: '', product_name: 'Крем', target_batch_size_value: '50', target_batch_size_unit: 'g', packaging_item_id: '', packaging_quantity: '', sale_price: '', ordered_at: '', planned_production_at: '', notes: '' };

test('duplicate create and edit submit once, package-without-item reaches backend, payload excludes lifecycle fields and no retry occurs', async () => {
  const createMutation = deferred();
  const refresh = deferred();
  const h = new OrderHarness();
  h.openCreate(baseDraft);
  assert.equal(h.submit('create', { ...baseDraft, packaging_quantity: '1' }, createMutation.promise, refresh.promise), true);
  assert.equal(h.submit('create', baseDraft, createMutation.promise, refresh.promise), false);
  assert.equal(h.createCalls.length, 1);
  assert.equal(h.createCalls[0].packaging_item_id, null);
  assert.equal(h.createCalls[0].packaging_quantity, '1');
  assert.equal('status' in h.createCalls[0], false);
  assert.equal('produced_at' in h.createCalls[0], false);
  assert.equal('delivered_at' in h.createCalls[0], false);
  createMutation.reject({ validation: { fieldErrors: { packaging_item_id: ['Тара: выберите тару.'] }, formErrors: [] } });
  await Promise.resolve(); await Promise.resolve();
  assert.equal(h.state.validation.fieldErrors.packaging_item_id[0], 'Тара: выберите тару.');
  assert.equal(h.createCalls.length, 1);

  const editMutation = deferred();
  const editRefresh = deferred();
  h.openEdit(order(7), baseDraft);
  assert.equal(h.submit('edit', baseDraft, editMutation.promise, editRefresh.promise), true);
  assert.equal(h.submit('edit', baseDraft, editMutation.promise, editRefresh.promise), false);
  assert.equal(h.updateCalls.length, 1);
});

test('rejections preserve form context, edited id, draft, focus-like selection model and stale callbacks cannot update newer contexts', async () => {
  const h = new OrderHarness();
  const mutation = deferred();
  h.openCreate({ ...baseDraft, product_name: 'Черновик', selectionStart: 2, selectionEnd: 6, activeName: 'product_name' });
  h.submit('create', h.state.draft, mutation.promise, deferred().promise);
  const formNode = { id: 'same-form' };
  h.state.formNode = formNode;
  mutation.reject({ validation: { fieldErrors: { product_name: ['Название продукта: обязательно.'] }, formErrors: [] } });
  await Promise.resolve();
  assert.equal(h.state.showForm, true);
  assert.equal(h.state.formMode, 'create');
  assert.equal(h.state.draft.product_name, 'Черновик');
  assert.equal(h.state.draft.selectionStart, 2);
  assert.equal(h.state.draft.selectionEnd, 6);
  assert.equal(h.state.formNode, formNode);

  const stale = deferred();
  h.active = false;
  h.openCreate(baseDraft);
  h.submit('create', baseDraft, stale.promise, deferred().promise);
  h.active = false;
  assert.equal(h.openEdit(order(9), { ...baseDraft, product_name: 'Позже' }), true);
  stale.resolve(order(3, 'Старый create'));
  await Promise.resolve();
  assert.equal(h.state.formMode, 'edit');
  assert.equal(h.state.editedOrderId, 9);
  assert.equal(h.state.selectedOrder.id, 9);

  const staleEdit = deferred();
  h.submit('edit', h.state.draft, staleEdit.promise, deferred().promise);
  h.active = false;
  h.openEdit(order(10), { ...baseDraft, product_name: 'Заказ B' });
  staleEdit.resolve(order(9, 'Старый edit A'));
  await Promise.resolve();
  assert.equal(h.state.editedOrderId, 10);
  assert.equal(h.state.selectedOrder.id, 10);
});

test('successful create and update are visible before refresh; refresh failure/success warning behavior is separate', async () => {
  const h = new OrderHarness();
  const createMutation = deferred();
  const createRefresh = deferred();
  h.openCreate(baseDraft);
  h.submit('create', baseDraft, createMutation.promise, createRefresh.promise);
  createMutation.resolve(order(11, 'Созданный'));
  await Promise.resolve();
  assert.equal(h.state.items[0].product_name, 'Созданный');
  assert.equal(h.state.showForm, false);
  assert.equal(h.state.success, 'Заказ создан.');
  createRefresh.reject(new Error('503'));
  await Promise.resolve(); await Promise.resolve();
  assert.equal(h.state.items[0].product_name, 'Созданный');
  assert.equal(h.state.success, 'Заказ создан.');
  assert.equal(h.state.warning, 'Заказ сохранён, но список не удалось обновить автоматически.');

  const updateMutation = deferred();
  const updateRefresh = deferred();
  h.openEdit(order(11, 'До'), baseDraft);
  h.submit('edit', baseDraft, updateMutation.promise, updateRefresh.promise);
  updateMutation.resolve(order(11, 'После'));
  await Promise.resolve();
  assert.equal(h.state.items[0].product_name, 'После');
  assert.equal(h.state.success, 'Заказ сохранён.');
  updateRefresh.resolve([order(11, 'После refresh')]);
  await Promise.resolve(); await Promise.resolve();
  assert.equal(h.state.warning, '');
  assert.equal(h.state.items[0].product_name, 'После refresh');
});

test('read context generation blocks stale list/detail/reference renders and remains independent of visible errors', () => {
  const original = context({ contextToken: 3, targetedValidationToken: 4, formMode: 'edit', editedOrderId: 1, selectedOrderId: 1, showForm: true });
  assert.equal(orderReadCanRender(original, { ...original }), true);
  assert.equal(orderReadCanRender(original, { ...original, contextToken: 4, formMode: 'create', editedOrderId: null }), false);
  assert.equal(orderReadCanRender(original, { ...original, selectedOrderId: 2 }), false);
  assert.equal(orderReadCanRender(original, { ...original, showForm: false }), false);
  const after422 = { ...original, targetedValidationToken: 5 };
  assert.equal(orderReadCanRender(original, after422), false);
  const afterOneFieldCleared = { ...after422 };
  assert.equal(orderReadCanRender(original, afterOneFieldCleared), false);
});

test('source and client changes clear only source-related validation provenance and preserve unrelated summary errors', () => {
  const validation = { fieldErrors: { source_type: ['Основа заказа: выберите основу.'], client_recipe_id: ['Индивидуальная формула: выберите.'], product_name: ['Название продукта: обязательно.'] }, formErrors: ['Версия рецепта: скрытая ошибка.', 'Индивидуальная формула: скрытая ошибка.', 'Общая ошибка остаётся.'] };
  const provenance = { formErrors: [{ origin: 'recipe_version_id', message: 'Версия рецепта: скрытая ошибка.' }, { origin: 'client_recipe_id', message: 'Индивидуальная формула: скрытая ошибка.' }] };
  const clearedSource = clearOrderSourceValidation(validation, provenance, ['recipe_source', 'recipe_version_id']);
  assert.equal(clearedSource.validation.fieldErrors.source_type, undefined);
  assert.equal(clearedSource.validation.formErrors.includes('Версия рецепта: скрытая ошибка.'), false);
  assert.equal(clearedSource.validation.formErrors.includes('Индивидуальная формула: скрытая ошибка.'), true);
  assert.equal(clearedSource.validation.formErrors.includes('Общая ошибка остаётся.'), true);
  assert.equal(clearedSource.validation.fieldErrors.client_recipe_id.length, 1);
  const clearedClient = clearOrderSourceValidation(clearedSource.validation, clearedSource.provenance, ['client_recipe_id']);
  assert.equal(clearedClient.validation.fieldErrors.client_recipe_id, undefined);
  assert.equal(clearedClient.validation.formErrors.includes('Индивидуальная формула: скрытая ошибка.'), false);
  const repeated = clearOrderSourceValidation(clearedClient.validation, clearedClient.provenance, ['client_recipe_id']);
  assert.deepEqual(repeated.validation.formErrors, ['Общая ошибка остаётся.']);
});

test('mutation guards preserve originally disabled and readonly controls', () => {
  const disabled = { disabled: true, readOnly: false, dataset: {}, querySelectorAll: () => [], setAttribute() {}, removeAttribute() {} };
  const readonly = { disabled: false, readOnly: true, dataset: {}, querySelectorAll: () => [], setAttribute() {}, removeAttribute() {} };
  const normalDisabled = { disabled: false, readOnly: false, dataset: {} };
  const normalReadonly = { disabled: false, readOnly: false, dataset: {} };
  globalThis.HTMLButtonElement = function HTMLButtonElement() {};
  globalThis.HTMLSelectElement = function HTMLSelectElement() {};
  globalThis.HTMLInputElement = function HTMLInputElement() {};
  globalThis.HTMLTextAreaElement = function HTMLTextAreaElement() {};
  Object.setPrototypeOf(disabled, globalThis.HTMLButtonElement.prototype);
  Object.setPrototypeOf(normalDisabled, globalThis.HTMLButtonElement.prototype);
  Object.setPrototypeOf(readonly, globalThis.HTMLInputElement.prototype);
  Object.setPrototypeOf(normalReadonly, globalThis.HTMLInputElement.prototype);
  mutationDisabled(disabled);
  mutationDisabled(normalDisabled);
  mutationReadonly(readonly);
  mutationReadonly(normalReadonly);
  const root = { querySelectorAll(selector) { if (selector.includes('mutation-readonly')) return [normalReadonly]; if (selector.includes('mutation-disabled')) return [normalDisabled]; return []; } };
  restoreMutationGuards(root);
  assert.equal(disabled.disabled, true);
  assert.equal(readonly.readOnly, true);
  assert.equal(normalDisabled.disabled, false);
  assert.equal(normalReadonly.readOnly, false);
});

test('pending submit blocks form closing and context-changing actions without loading deadlock', () => {
  const h = new OrderHarness();
  const mutation = deferred();
  h.openCreate(baseDraft);
  h.submit('create', baseDraft, mutation.promise, deferred().promise);
  assert.equal(h.openCreate(baseDraft), false);
  assert.equal(h.openEdit(order(2), baseDraft), false);
  assert.equal(h.closeForm(), false);
  mutation.reject({ validation: { fieldErrors: {}, formErrors: ['Проверьте заказ.'] } });
  return Promise.resolve().then(() => Promise.resolve()).then(() => {
    assert.equal(h.active, false);
    assert.equal(h.state.loading, false);
  });
});
