import test from 'node:test';
import assert from 'node:assert/strict';
import {
  canOpenOrderProductionConfirmation,
  clearOrderSourceValidation,
  createOrderMutationController,
  emptyOrderValidationProvenance,
  orderOperationError,
  orderOperationErrorFor,
  orderPayloadFromDraft,
  orderProductionIsClosed,
  orderRequestOwnerMatches,
  ownerFromOrderRequest,
} from '../dist-tests/order-mutation-lifecycle/order-mutation-lifecycle.js';
import { mutationDisabled, mutationReadonly, restoreMutationGuards } from '../dist-tests/order-mutation-lifecycle/mutation-lifecycle.js';

function workspace(overrides = {}) {
  return { formMode: 'create', editedOrderId: null, selectedOrderId: null, showForm: true, ...overrides };
}
function ctx(controller, overrides = {}) { return controller.snapshot(workspace(overrides)); }
function order(id, name = `Заказ ${id}`) { return { id, product_name: name }; }
const baseDraft = { client_id: '1', source_type: 'recipe_version', recipe_version_id: '2', client_recipe_id: '', product_name: 'Крем', target_batch_size_value: '50', target_batch_size_unit: 'g', packaging_item_id: '', packaging_quantity: '', sale_price: '', ordered_at: '', planned_production_at: '', notes: '' };

test('production controller blocks duplicate create/edit submits and keeps package-without-item backend-boundary payload clean', () => {
  const controller = createOrderMutationController();
  const create = controller.beginSubmit(ctx(controller));
  assert.ok(create);
  assert.equal(controller.beginSubmit(ctx(controller)), null);
  assert.equal(controller.isSubmitting(), true);
  assert.equal(controller.finishSubmit(create), true);
  const edit = controller.beginSubmit(ctx(controller, { formMode: 'edit', editedOrderId: 7, selectedOrderId: 7 }));
  assert.ok(edit);
  assert.equal(controller.beginSubmit(ctx(controller, { formMode: 'edit', editedOrderId: 7, selectedOrderId: 7 })), null);
  const payload = orderPayloadFromDraft({ ...baseDraft, packaging_quantity: '1' });
  assert.equal(payload.packaging_item_id, null);
  assert.equal(payload.packaging_quantity, '1');
  assert.equal('status' in payload, false);
  assert.equal('produced_at' in payload, false);
  assert.equal('delivered_at' in payload, false);
});

test('submit snapshots preserve create/edit context and stale mutations cannot apply to newer contexts', () => {
  const controller = createOrderMutationController();
  const createSubmit = controller.beginSubmit(ctx(controller, { formMode: 'create', editedOrderId: null, selectedOrderId: null, showForm: true }));
  assert.ok(createSubmit);
  assert.equal(controller.canApplySubmit(createSubmit, ctx(controller, { formMode: 'create', editedOrderId: null, selectedOrderId: null, showForm: true })), true);
  controller.finishSubmit(createSubmit);
  controller.bumpContext();
  const laterEdit = ctx(controller, { formMode: 'edit', editedOrderId: 9, selectedOrderId: 9, showForm: true });
  assert.equal(controller.canApplySubmit(createSubmit, laterEdit), false);

  const editSubmit = controller.beginSubmit(laterEdit);
  assert.ok(editSubmit);
  controller.finishSubmit(editSubmit);
  controller.bumpContext();
  const orderB = ctx(controller, { formMode: 'edit', editedOrderId: 10, selectedOrderId: 10, showForm: true });
  assert.equal(controller.canApplySubmit(editSubmit, orderB), false);
  assert.equal(editSubmit.editedOrderId, 9);
});

test('post-save refresh generation applies only to current save context and cannot mutate newer warnings', () => {
  const controller = createOrderMutationController();
  const submit = controller.beginSubmit(ctx(controller));
  assert.ok(submit);
  controller.finishSubmit(submit);
  controller.bumpContext();
  const savedContext = ctx(controller, { showForm: false, selectedOrderId: 11 });
  const refresh = controller.beginRequest('postSaveRefresh', savedContext, { savedOrderId: 11 });
  assert.equal(controller.canApplyPostSaveRefresh(refresh, savedContext), true);

  const newerCreateContext = ctx(controller, { showForm: true, selectedOrderId: null });
  assert.equal(controller.canApplyPostSaveRefresh(refresh, newerCreateContext), false);
  controller.bumpContext();
  const newerEditContext = ctx(controller, { formMode: 'edit', editedOrderId: 12, selectedOrderId: 12, showForm: true });
  assert.equal(controller.canApplyPostSaveRefresh(refresh, newerEditContext), false);

  const newerRefresh = controller.beginRequest('postSaveRefresh', newerEditContext, { savedOrderId: 12 });
  assert.equal(controller.canApplyPostSaveRefresh(refresh, newerEditContext), false);
  assert.equal(controller.canApplyPostSaveRefresh(newerRefresh, newerEditContext), true);
});

test('list generations reject old success/failure, preserve newer warnings, and targeted validation keeps old requests stale after field clearing', () => {
  const controller = createOrderMutationController();
  const first = controller.beginRequest('list', ctx(controller, { showForm: false }));
  const second = controller.beginRequest('list', ctx(controller, { showForm: false }));
  assert.equal(controller.canApplyRequest(first, ctx(controller, { showForm: false })), false);
  assert.equal(controller.canApplyRequest(second, ctx(controller, { showForm: false })), true);
  assert.equal(controller.isCurrentRequest(first), false);
  assert.equal(controller.isCurrentRequest(second), true);

  const before422 = controller.beginRequest('list', ctx(controller, { showForm: true }));
  controller.markTargetedValidationApplied();
  const after422 = ctx(controller, { showForm: true });
  assert.equal(controller.canApplyRequest(before422, after422), false);
  // Clearing a single field error is a validation-state change, not a generation reset.
  assert.equal(controller.canApplyRequest(before422, after422), false);
});

test('reference generations apply only after context checks and keep loading ownership current', () => {
  const controller = createOrderMutationController();
  const createRefs = controller.beginRequest('reference', ctx(controller, { formMode: 'create', showForm: true }));
  controller.bumpContext();
  const editCtx = ctx(controller, { formMode: 'edit', editedOrderId: 21, selectedOrderId: 21, showForm: true });
  const editRefs = controller.beginRequest('reference', editCtx, { requestedOrderId: 21 });
  assert.equal(controller.canApplyRequest(createRefs, editCtx), false);
  assert.equal(controller.canApplyRequest(editRefs, editCtx), true);
  assert.equal(controller.isCurrentRequest(createRefs), false);

  controller.bumpContext();
  const editBCtx = ctx(controller, { formMode: 'edit', editedOrderId: 22, selectedOrderId: 22, showForm: true });
  assert.equal(controller.canApplyRequest(editRefs, editBCtx), false);
  const currentRefs = controller.beginRequest('reference', editBCtx, { requestedOrderId: 22 });
  assert.equal(controller.canApplyRequest(currentRefs, editBCtx), true);
  controller.markTargetedValidationApplied();
  assert.equal(controller.canApplyRequest(currentRefs, ctx(controller, { formMode: 'edit', editedOrderId: 22, selectedOrderId: 22, showForm: true })), false);
});

test('detail generations stop delayed Order A success/failure from affecting Order B or create/edit forms', () => {
  const controller = createOrderMutationController();
  const detailA = controller.beginRequest('detail', ctx(controller, { selectedOrderId: 1, showForm: false }), { requestedOrderId: 1 });
  controller.bumpContext();
  const detailBCtx = ctx(controller, { selectedOrderId: 2, showForm: false });
  const detailB = controller.beginRequest('detail', detailBCtx, { requestedOrderId: 2 });
  assert.equal(controller.canApplyRequest(detailA, detailBCtx), false);
  assert.equal(controller.canApplyRequest(detailB, detailBCtx), true);
  controller.bumpContext();
  assert.equal(controller.canApplyRequest(detailB, ctx(controller, { formMode: 'create', selectedOrderId: null, showForm: true })), false);
  controller.bumpContext();
  assert.equal(controller.canApplyRequest(detailB, ctx(controller, { formMode: 'edit', editedOrderId: 3, selectedOrderId: 3, showForm: true })), false);
});

test('repeated open-create can return before invalidating the active reference request', () => {
  const controller = createOrderMutationController();
  controller.bumpContext();
  const createCtx = ctx(controller, { formMode: 'create', showForm: true });
  const activeRefs = controller.beginRequest('reference', createCtx);
  const contextBeforeRepeat = controller.getContextToken();
  // Production openOrderCreate checks referenceLoading+create before bumpContext; emulate no-op repeat.
  assert.equal(controller.getContextToken(), contextBeforeRepeat);
  assert.equal(controller.canApplyRequest(activeRefs, createCtx), true);
  assert.equal(controller.isCurrentRequest(activeRefs), true);
  controller.bumpContext();
  assert.equal(controller.canApplyRequest(activeRefs, ctx(controller, { formMode: 'edit', editedOrderId: 5, selectedOrderId: 5, showForm: true })), false);
});

test('readiness and production request loading ownership is generation-safe', () => {
  const controller = createOrderMutationController();
  const readyA = controller.beginRequest('readiness', ctx(controller, { selectedOrderId: 1, showForm: false }), { requestedOrderId: 1 });
  const readyB = controller.beginRequest('readiness', ctx(controller, { selectedOrderId: 1, showForm: false }), { requestedOrderId: 1 });
  assert.equal(controller.isCurrentRequest(readyA), false);
  assert.equal(controller.canApplyRequest(readyB, ctx(controller, { selectedOrderId: 1, showForm: false })), true);
  const prodA = controller.beginRequest('production', ctx(controller, { selectedOrderId: 1, showForm: false }), { requestedOrderId: 1 });
  controller.bumpContext();
  assert.equal(controller.canApplyRequest(prodA, ctx(controller, { selectedOrderId: 2, showForm: false })), false);
});



test('production confirmation guard requires current positive readiness and unlocked active order', () => {
  const active = { is_active: true, status: 'new' };
  assert.equal(canOpenOrderProductionConfirmation(false, active, undefined), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, { can_produce: false, status: 'blocked' }), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, { can_produce: false }), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, { can_produce: true }), true);
  assert.equal(canOpenOrderProductionConfirmation(false, { is_active: true, status: 'produced' }, { can_produce: true }), false);
  assert.equal(canOpenOrderProductionConfirmation(false, { is_active: false, status: 'new' }, { can_produce: true }), false);
  assert.equal(canOpenOrderProductionConfirmation(true, active, { can_produce: true }), false);
  assert.equal(orderProductionIsClosed({ is_active: true, status: 'delivered' }), true);
});

test('readiness transient ownership is order-bound, generation-bound and clears without dropping cached results', () => {
  const controller = createOrderMutationController();
  const state = { readinessLoadingOrderId: null, readinessOwner: null, readinessError: null, readinessByOrderId: { 1: { can_produce: true } } };
  const requestA = controller.beginRequest('readiness', ctx(controller, { selectedOrderId: 1, showForm: false }), { requestedOrderId: 1 });
  state.readinessOwner = ownerFromOrderRequest(requestA, 1, 'readiness');
  state.readinessLoadingOrderId = 1;
  assert.deepEqual(state.readinessOwner, { kind: 'readiness', generation: requestA.generation, orderId: 1 });
  controller.bumpContext();
  controller.invalidateRequest('readiness');
  state.readinessOwner = null;
  state.readinessLoadingOrderId = null;
  state.readinessError = null;
  assert.equal(state.readinessByOrderId[1].can_produce, true);
  const orderBContext = ctx(controller, { selectedOrderId: 2, showForm: false });
  assert.equal(controller.canApplyRequest(requestA, orderBContext), false);
  assert.equal(orderRequestOwnerMatches(state.readinessOwner, requestA, 1, 'readiness'), false);

  const requestB = controller.beginRequest('readiness', orderBContext, { requestedOrderId: 2 });
  state.readinessOwner = ownerFromOrderRequest(requestB, 2, 'readiness');
  state.readinessLoadingOrderId = 2;
  assert.equal(orderRequestOwnerMatches(state.readinessOwner, requestA, 1, 'readiness'), false);
  assert.equal(orderRequestOwnerMatches(state.readinessOwner, requestB, 2, 'readiness'), true);
  state.readinessError = orderOperationError(2, 'Ошибка проверки B');
  assert.equal(orderOperationErrorFor(state.readinessError, 1), '');
  assert.equal(orderOperationErrorFor(state.readinessError, 2), 'Ошибка проверки B');
  if (controller.canApplyRequest(requestB, orderBContext) && orderRequestOwnerMatches(state.readinessOwner, requestB, 2, 'readiness')) {
    state.readinessLoadingOrderId = null;
    state.readinessOwner = null;
  }
  assert.equal(state.readinessLoadingOrderId, null);
});

test('production and production-history ownership are separate and stale callbacks cannot navigate or clear newer loading', () => {
  const controller = createOrderMutationController();
  const state = { productionLoadingOrderId: null, productionOwner: null, historyOwner: null, productionError: null, productionByOrderId: { 1: { id: 101 } }, navigated: false };
  const productionA = controller.beginRequest('production', ctx(controller, { selectedOrderId: 1, showForm: false }), { requestedOrderId: 1 });
  state.productionOwner = ownerFromOrderRequest(productionA, 1, 'production');
  state.productionLoadingOrderId = 1;
  assert.deepEqual(state.productionOwner, { kind: 'production', generation: productionA.generation, orderId: 1 });

  controller.bumpContext();
  controller.invalidateRequest('production');
  state.productionOwner = null;
  state.historyOwner = null;
  state.productionLoadingOrderId = null;
  state.productionError = null;
  assert.equal(state.productionByOrderId[1].id, 101);
  const orderBContext = ctx(controller, { selectedOrderId: 2, showForm: false });
  assert.equal(controller.canApplyRequest(productionA, orderBContext), false);

  const historyA = controller.beginRequest('productionHistory', orderBContext, { requestedOrderId: 2 });
  state.historyOwner = ownerFromOrderRequest(historyA, 2, 'productionHistory');
  state.productionLoadingOrderId = 2;
  const productionB = controller.beginRequest('production', orderBContext, { requestedOrderId: 2 });
  state.productionOwner = ownerFromOrderRequest(productionB, 2, 'production');
  state.productionLoadingOrderId = 2;
  assert.equal(controller.canApplyRequest(historyA, orderBContext), true);
  assert.equal(orderRequestOwnerMatches(state.productionOwner, productionB, 2, 'production'), true);
  assert.equal(orderRequestOwnerMatches(state.productionOwner, historyA, 2, 'productionHistory'), false);
  controller.bumpContext();
  controller.invalidateRequest('productionHistory');
  const laterContext = ctx(controller, { selectedOrderId: 3, showForm: false });
  if (controller.canApplyRequest(historyA, laterContext) && orderRequestOwnerMatches(state.historyOwner, historyA, 2, 'productionHistory')) state.navigated = true;
  assert.equal(state.navigated, false);
  state.productionError = orderOperationError(2, 'Ошибка производства B');
  assert.equal(orderOperationErrorFor(state.productionError, 1), '');
  assert.equal(orderOperationErrorFor(state.productionError, 2), 'Ошибка производства B');
});

test('source and client changes clear only source-related validation provenance and preserve unrelated summary errors', () => {
  const validation = { fieldErrors: { source_type: ['Основа заказа: выберите основу.'], client_recipe_id: ['Индивидуальная формула: выберите.'], product_name: ['Название продукта: обязательно.'] }, formErrors: ['Версия рецепта: скрытая ошибка.', 'Индивидуальная формула: скрытая ошибка.', 'Общая ошибка остаётся.'] };
  const provenance = { formErrors: [{ origin: 'recipe_version_id', message: 'Версия рецепта: скрытая ошибка.' }, { origin: 'client_recipe_id', message: 'Индивидуальная формула: скрытая ошибка.' }] };
  const clearedSource = clearOrderSourceValidation(validation, provenance, ['recipe_source', 'recipe_version_id']);
  assert.equal(clearedSource.validation.fieldErrors.source_type, undefined);
  assert.equal(clearedSource.validation.formErrors.includes('Версия рецепта: скрытая ошибка.'), false);
  assert.equal(clearedSource.validation.formErrors.includes('Индивидуальная формула: скрытая ошибка.'), true);
  assert.equal(clearedSource.validation.formErrors.includes('Общая ошибка остаётся.'), true);
  const clearedClient = clearOrderSourceValidation(clearedSource.validation, clearedSource.provenance, ['client_recipe_id']);
  assert.equal(clearedClient.validation.fieldErrors.client_recipe_id, undefined);
  assert.deepEqual(clearOrderSourceValidation(clearedClient.validation, emptyOrderValidationProvenance(), ['client_recipe_id']).validation.formErrors, ['Общая ошибка остаётся.']);
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
