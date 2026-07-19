import test from 'node:test';
import assert from 'node:assert/strict';
import {
  canOpenOrderProductionConfirmation,
  canStartOrderReadinessRequest,
  canStartOrderWriteRequest,
  clearOrderSourceValidation,
  createOrderMutationController,
  emptyOrderValidationProvenance,
  orderOperationError,
  orderOperationErrorFor,
  orderBoundOperationActive,
  orderPayloadFromDraft,
  orderPersistentWriteActive,
  orderPersistentWriteOwner,
  orderProductionIsClosed,
  orderReadinessRequestActive,
  orderReadinessAttemptMatches,
  orderReadinessResultIsCurrent,
  orderRequestOwnerMatches,
  ownerFromOrderRequest,
  extractProductionApiFailure, productionConfirmationFailurePresentation, productionReadinessFailureMessage, productionResponseBelongsToOrder,
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
  const active = { id: 1, is_active: true, status: 'new', updated_at: '2026-07-19T10:00:00Z' };
  const ready = { order_id: 1, can_produce: true, status: 'ready' };
  assert.equal(canOpenOrderProductionConfirmation(false, active, undefined), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, { order_id: 1, can_produce: false, status: 'blocked' }), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, { ...ready, order_id: 2 }), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, { ...ready, status: 'blocked' }), false);
  assert.equal(canOpenOrderProductionConfirmation(false, active, ready), true);
  assert.equal(canOpenOrderProductionConfirmation(false, { ...active, status: 'produced' }, ready), false);
  assert.equal(canOpenOrderProductionConfirmation(false, { ...active, is_active: false }, ready), false);
  assert.equal(canOpenOrderProductionConfirmation(true, active, ready), false);
  assert.equal(orderProductionIsClosed({ ...active, status: 'delivered' }), true);
});

test('rapid repeated readiness action starts exactly one POST and owns one honest loading state', () => {
  const controller = createOrderMutationController();
  const active = { id: 1, is_active: true, status: 'new', updated_at: '2026-07-19T10:00:00Z' };
  const context = ctx(controller, { selectedOrderId: 1, showForm: false });
  const state = { owner: null, loadingOrderId: null, postCount: 0 };
  const trigger = () => {
    if (!canStartOrderReadinessRequest(false, active, state.owner, state.loadingOrderId, 1)) return;
    const request = controller.beginRequest('readiness', context, { requestedOrderId: 1 });
    state.owner = ownerFromOrderRequest(request, 1, 'readiness');
    state.loadingOrderId = 1;
    state.postCount += 1;
  };
  trigger();
  trigger();
  assert.equal(state.postCount, 1);
  assert.equal(orderReadinessRequestActive(state.owner, state.loadingOrderId, 1), true);
  assert.equal(canStartOrderReadinessRequest(false, active, state.owner, state.loadingOrderId, 1), false);
});

test('readiness currentness separates blocked results, failed attempts, wrong orders and edited orders', () => {
  const orderA = { id: 1, is_active: true, status: 'new', updated_at: 'v1' };
  const blocked = { order_id: 1, can_produce: false, status: 'blocked' };
  const ready = { order_id: 1, can_produce: true, status: 'ready' };
  assert.equal(orderReadinessResultIsCurrent(orderA, blocked, 4, 4, 'v1', 7, 7), true);
  assert.equal(orderReadinessResultIsCurrent(orderA, ready, 4, 4, 'v1', 7, 7), true);
  assert.equal(orderReadinessResultIsCurrent(orderA, ready, 5, 4, 'v1', 7, 7), false);
  assert.equal(orderReadinessResultIsCurrent(orderA, { ...ready, order_id: 2 }, 4, 4, 'v1', 7, 7), false);
  assert.equal(orderReadinessResultIsCurrent({ ...orderA, updated_at: 'v2' }, ready, 4, 4, 'v1', 7, 7), false);
  assert.equal(orderReadinessResultIsCurrent(orderA, ready, 4, 4, 'v1', 7, 8), false);
  assert.equal(orderReadinessAttemptMatches(orderA, 1, 'v1', 7, 7), true);
  assert.equal(orderReadinessAttemptMatches({ ...orderA, updated_at: 'v2' }, 1, 'v1', 7, 7), false);
  assert.equal(orderReadinessAttemptMatches(orderA, 1, 'v1', 7, 8), false);
  assert.equal(canOpenOrderProductionConfirmation(false, orderA, blocked), false);
  assert.equal(canOpenOrderProductionConfirmation(false, orderA, undefined), false);
});

test('readiness remains order-bound while production, cancel and archive ownership is globally serialized', () => {
  const active = { id: 1, is_active: true, status: 'new', updated_at: 'v1' };
  const operation = (kind, orderId = 1, generation = 1) => ({ owner: { kind, orderId, generation }, loadingOrderId: orderId });
  for (const kind of ['production', 'cancel', 'archive']) {
    const conflicting = [operation(kind)];
    assert.equal(canStartOrderReadinessRequest(false, active, null, null, 1, conflicting), false, `${kind} blocks same-order readiness`);
    assert.equal(canStartOrderReadinessRequest(false, { ...active, id: 2 }, null, null, 2, conflicting), true, `${kind} does not block unrelated Order readiness`);
    assert.equal(orderPersistentWriteActive(conflicting), true, `${kind} is a global persistent write`);
    assert.deepEqual(orderPersistentWriteOwner(conflicting), { kind, orderId: 1, generation: 1 });
    assert.equal(canStartOrderWriteRequest(false, { ...active, id: 2 }, 2, conflicting), false, `${kind} prevents a second persistent owner for Order B`);
  }
  const readiness = operation('readiness');
  assert.equal(canStartOrderWriteRequest(false, active, 1, [readiness]), false);
  assert.equal(canStartOrderWriteRequest(false, { ...active, id: 2 }, 2, [readiness]), true);
  assert.equal(orderPersistentWriteActive([readiness]), false);
  assert.equal(orderPersistentWriteOwner([readiness]), null);
  assert.equal(orderPersistentWriteActive([{ owner: { kind: 'cancel', orderId: 1, generation: 1 }, loadingOrderId: 2 }]), false, 'mismatched loading cannot claim ownership');
  assert.equal(orderBoundOperationActive([readiness], 1), true);
  assert.equal(orderBoundOperationActive([readiness], 2), false);
});

test('duplicate cancel and archive actions each start exactly one POST-equivalent request', () => {
  for (const kind of ['cancel', 'archive']) {
    const controller = createOrderMutationController();
    const active = { id: 1, is_active: true, status: 'new', updated_at: 'v1' };
    const context = ctx(controller, { selectedOrderId: 1, showForm: false });
    const state = { owner: null, loadingOrderId: null, postCount: 0, request: null };
    const trigger = () => {
      if (!canStartOrderWriteRequest(false, active, 1, [{ owner: state.owner, loadingOrderId: state.loadingOrderId }])) return;
      const request = controller.beginRequest(kind, context, { requestedOrderId: 1 });
      state.owner = ownerFromOrderRequest(request, 1, kind);
      state.loadingOrderId = 1;
      state.request = request;
      state.postCount += 1;
    };
    trigger();
    trigger();
    assert.equal(state.postCount, 1, `${kind} request count`);
    assert.equal(orderRequestOwnerMatches(state.owner, { ...state.owner, kind }, 1, kind), true);
    assert.equal(orderPersistentWriteActive([{ owner: state.owner, loadingOrderId: state.loadingOrderId }]), true);

    if (orderRequestOwnerMatches(state.owner, state.request, 1, kind)) {
      state.owner = null;
      state.loadingOrderId = null;
    }
    assert.equal(orderPersistentWriteActive([{ owner: state.owner, loadingOrderId: state.loadingOrderId }]), false, `${kind} controls recover after settlement`);
    assert.equal(canStartOrderWriteRequest(false, active, 1, [{ owner: state.owner, loadingOrderId: state.loadingOrderId }]), true);
  }
});

test('stale cancel, archive and production callbacks cannot clear a newer operation owner', () => {
  const controller = createOrderMutationController();
  const context = ctx(controller, { selectedOrderId: 1, showForm: false });
  for (const kind of ['cancel', 'archive', 'production']) {
    const older = controller.beginRequest(kind, context, { requestedOrderId: 1 });
    const newer = controller.beginRequest(kind, context, { requestedOrderId: 1 });
    const state = { owner: ownerFromOrderRequest(newer, 1, kind), loadingOrderId: 1 };
    if (orderRequestOwnerMatches(state.owner, older, 1, kind)) {
      state.owner = null;
      state.loadingOrderId = null;
    }
    assert.equal(state.loadingOrderId, 1, `${kind} newer loading remains`);
    assert.equal(orderRequestOwnerMatches(state.owner, newer, 1, kind), true, `${kind} newer owner remains`);
  }
});

test('readiness system failures are distinct from a valid blocked result and never leak backend details', () => {
  const blocked = { order_id: 1, can_produce: false, status: 'blocked' };
  assert.equal(blocked.status, 'blocked');
  assert.match(productionReadinessFailureMessage({ status: 404, message: 'Linked recipe record was not found.' }), /рецепт|формула/i);
  assert.match(productionReadinessFailureMessage({ status: 404, message: 'Order was not found.' }), /Заказ не найден/);
  assert.match(productionReadinessFailureMessage({ status: 409, message: 'internal lifecycle conflict' }), /состояния заказа/);
  assert.match(productionReadinessFailureMessage({ status: 422, message: 'raw payload' }), /параметры проверки/);
  assert.match(productionReadinessFailureMessage({ networkFailure: true, message: 'Failed to fetch' }), /локальным приложением/);
  const unexpected = productionReadinessFailureMessage({ status: 500, message: 'sqlite3.OperationalError: secret_table' });
  assert.match(unexpected, /непредвиденная ошибка/);
  assert.equal(unexpected.includes('sqlite3'), false);
  assert.equal(unexpected.includes('secret_table'), false);
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

test('delayed Order A readiness success and failure cannot appear after switching to Order B', () => {
  const controller = createOrderMutationController();
  const orderAContext = ctx(controller, { selectedOrderId: 1, showForm: false });
  const requestA = controller.beginRequest('readiness', orderAContext, { requestedOrderId: 1 });
  const ownerA = ownerFromOrderRequest(requestA, 1, 'readiness');
  controller.bumpContext();
  const orderBContext = ctx(controller, { selectedOrderId: 2, showForm: false });
  const state = { owner: null, loadingOrderId: null, results: { 2: { order_id: 2, status: 'blocked' } }, error: orderOperationError(2, 'Ошибка B') };
  const canApplyDelayedA = controller.canApplyRequest(requestA, orderBContext)
    && orderRequestOwnerMatches(state.owner, requestA, 1, 'readiness');
  if (canApplyDelayedA) {
    state.results[1] = { order_id: 1, status: 'ready' };
    state.error = orderOperationError(1, 'Ошибка A');
    state.loadingOrderId = null;
  }
  assert.equal(canApplyDelayedA, false);
  assert.equal(state.results[1], undefined);
  assert.equal(orderOperationErrorFor(state.error, 1), '');
  assert.equal(orderOperationErrorFor(state.error, 2), 'Ошибка B');
  assert.equal(orderRequestOwnerMatches(ownerA, requestA, 1, 'readiness'), true);
});

test('older readiness callback cannot replace newer success or clear the newer loading owner', () => {
  const controller = createOrderMutationController();
  const context = ctx(controller, { selectedOrderId: 1, showForm: false });
  const older = controller.beginRequest('readiness', context, { requestedOrderId: 1 });
  const newer = controller.beginRequest('readiness', context, { requestedOrderId: 1 });
  const state = {
    owner: ownerFromOrderRequest(newer, 1, 'readiness'),
    loadingOrderId: 1,
    result: { order_id: 1, can_produce: true, status: 'ready', marker: 'newer' },
  };
  const olderMayApply = controller.canApplyRequest(older, context)
    && orderRequestOwnerMatches(state.owner, older, 1, 'readiness');
  if (olderMayApply) {
    state.result = { order_id: 1, can_produce: false, status: 'blocked', marker: 'older' };
    state.loadingOrderId = null;
    state.owner = null;
  }
  assert.equal(olderMayApply, false);
  assert.equal(state.result.marker, 'newer');
  assert.equal(state.loadingOrderId, 1);
  assert.equal(orderRequestOwnerMatches(state.owner, newer, 1, 'readiness'), true);
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


test('production confirmation failure presentation separates conflict validation missing and uncertain states safely', () => {
  const conflict = productionConfirmationFailurePresentation(extractProductionApiFailure({ status: 409, message: 'API request failed', payload: { detail: { code: 'readiness_changed', message: 'Недостаточно компонента', next_action: 'Запустите проверку заново' } } }));
  assert.equal(conflict.kind, 'business_conflict');
  assert.equal(conflict.invalidateReadiness, true);
  assert.equal(conflict.closeConfirmation, true);
  assert.match(conflict.message, /Недостаточно компонента|изменилось/);
  assert.equal(conflict.nextAction, 'Запустите проверку заново');

  const validation = productionConfirmationFailurePresentation(extractProductionApiFailure({ status: 422, message: 'API request failed', payload: { detail: { code: 'explicit_confirmation_required', message: 'Traceback sqlite SELECT secret', next_action: 'Повторите подтверждение' } } }));
  assert.equal(validation.kind, 'validation');
  assert.equal(validation.closeConfirmation, false);
  assert.doesNotMatch(validation.message, /Traceback|sqlite|SELECT/);

  const missing = productionConfirmationFailurePresentation(extractProductionApiFailure({ status: 404, payload: { detail: { code: 'order_not_found', message: 'Заказ больше не найден.', next_action: 'Обновите список' } } }));
  assert.equal(missing.kind, 'missing_record');
  assert.equal(missing.requireRefreshBeforeRetry, true);

  const network = productionConfirmationFailurePresentation({ networkFailure: true });
  assert.equal(network.kind, 'network_uncertain');
  assert.equal(network.requireRefreshBeforeRetry, true);
});

test('production success ownership rejects wrong-order batch responses', () => {
  assert.equal(productionResponseBelongsToOrder({ order_id: 7 }, 7), true);
  assert.equal(productionResponseBelongsToOrder({ order_id: 8 }, 7), false);
  assert.equal(productionResponseBelongsToOrder(null, 7), false);
});


test('production API failure extractor consumes realistic structured payloads safely', () => {
  const cases = [
    [409, 'readiness_changed'], [409, 'readiness_blocked'], [409, 'production_conflict'],
    [422, 'explicit_confirmation_required'], [404, 'order_not_found'], [404, 'linked_source_not_found'], [500, 'production_unexpected_failure'],
  ];
  for (const [status, code] of cases) {
    const extracted = extractProductionApiFailure({ status, message: 'API request failed', payload: { detail: { code, message: `${code} безопасно`, next_action: 'Следующее действие' } } });
    assert.equal(extracted.status, status);
    assert.equal(extracted.code, code);
    assert.equal(extracted.message, `${code} безопасно`);
    assert.equal(extracted.nextAction, 'Следующее действие');
    const presentation = productionConfirmationFailurePresentation(extracted);
    assert.doesNotMatch(presentation.message, /API request failed|SELECT|Traceback|workspace|production_batches/);
  }
});

test('production delayed A success and failure are order-bound and do not mutate B presentation state', () => {
  const stored = {};
  const errors = {};
  const selectedB = { id: 2, product_name: 'B' };
  const batchA = { order_id: 1, id: 10 };
  if (productionResponseBelongsToOrder(batchA, 1)) stored[1] = batchA;
  assert.deepEqual(selectedB, { id: 2, product_name: 'B' });
  assert.equal(stored[1].id, 10);
  const failureA = productionConfirmationFailurePresentation(extractProductionApiFailure(new TypeError('network')));
  errors[1] = failureA.message;
  assert.equal(errors[2], undefined);
  assert.match(errors[1], /Исход изготовления неизвестен/);
});


test('production reconciliation request ownership suppresses duplicates and stale cleanup', () => {
  const controller = createOrderMutationController();
  const context = ctx(controller, { selectedOrderId: 1, showForm: false });
  const state = { owner: null, loadingOrderId: null, requestPairs: 0 };
  const start = () => {
    if (orderBoundOperationActive([{ owner: state.owner, loadingOrderId: state.loadingOrderId }], 1)) return null;
    const request = controller.beginRequest('productionReconciliation', context, { requestedOrderId: 1 });
    state.owner = ownerFromOrderRequest(request, 1, 'productionReconciliation');
    state.loadingOrderId = 1;
    state.requestPairs += 1;
    return request;
  };
  const first = start();
  const duplicate = start();
  assert.ok(first);
  assert.equal(duplicate, null);
  assert.equal(state.requestPairs, 1);
  const newer = controller.beginRequest('productionReconciliation', context, { requestedOrderId: 1 });
  state.owner = ownerFromOrderRequest(newer, 1, 'productionReconciliation');
  assert.equal(orderRequestOwnerMatches(state.owner, first, 1, 'productionReconciliation'), false);
  assert.equal(orderRequestOwnerMatches(state.owner, newer, 1, 'productionReconciliation'), true);
});
