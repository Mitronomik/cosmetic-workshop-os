import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  createOrderMutationController,
  orderDtoIsValid,
  ordersDtoIsValid,
  orderReferenceDataIsValid,
  productionBatchDtoIsValid,
  productionReadinessDtoIsValid,
  productionReconciliationIsCoherent,
} from '../dist-tests/order-production-feedback/order-mutation-lifecycle.js';

function workspace(overrides = {}) {
  return { formMode: 'create', editedOrderId: null, selectedOrderId: null, showForm: false, ...overrides };
}

function context(controller, overrides = {}) {
  return controller.snapshot(workspace(overrides));
}

function order(id = 7, overrides = {}) {
  return {
    id,
    client_id: 2,
    recipe_version_id: 3,
    client_recipe_id: null,
    product_name: 'Крем',
    target_batch_size_value: '50.000',
    target_batch_size_unit: 'g',
    packaging_item_id: null,
    packaging_quantity: null,
    status: 'produced',
    sale_price: '1200.00',
    ordered_at: null,
    planned_production_at: null,
    produced_at: '2026-07-24T10:00:00Z',
    delivered_at: null,
    notes: '',
    is_active: true,
    created_at: '2026-07-24T09:00:00Z',
    updated_at: '2026-07-24T10:00:00Z',
    ...overrides,
  };
}

function batch(orderId = 7, overrides = {}) {
  return {
    id: 11,
    order_id: orderId,
    product_name: 'Крем',
    client_id: 2,
    client_name: 'Анна',
    recipe_version_id: 3,
    client_recipe_id: null,
    final_batch_value: '50.000',
    final_batch_unit: 'g',
    component_cost: '200.00',
    packaging_cost: null,
    other_cost: '0.00',
    total_cost: '200.00',
    sale_price: '1200.00',
    tax: null,
    margin: null,
    margin_percent: null,
    produced_at: '2026-07-24T10:00:00Z',
    notes: '',
    created_at: '2026-07-24T10:00:00Z',
    ingredients: [{
      id: 31,
      production_batch_id: 11,
      ingredient_id: 4,
      ingredient_lot_id: 9,
      ingredient_name_snapshot: 'Вода',
      lot_code_snapshot: 'W-1',
      required_quantity: '50.000',
      consumed_quantity: '50.000',
      unit: 'g',
      unit_cost_snapshot: null,
      total_cost_snapshot: null,
      expiration_date_snapshot: null,
      created_at: '2026-07-24T10:00:00Z',
    }],
    packaging: [],
    ...overrides,
  };
}

test('route enter and leave own presentation and returning cannot reactivate an old request', () => {
  const controller = createOrderMutationController({ routeActive: false });
  assert.equal(controller.ownsRoute(), false);
  controller.enterRoute();
  const request = controller.beginRequest('detail', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  assert.equal(controller.canApplyRequest(request, context(controller, { selectedOrderId: 7 })), true);
  controller.leaveRoute();
  assert.equal(controller.canApplyRequest(request, context(controller, { selectedOrderId: 7 })), false);
  controller.enterRoute();
  assert.equal(controller.canApplyRequest(request, context(controller, { selectedOrderId: 7 })), false);
});

test('accepted request settles exactly once while a rejected inactive submit has no settlement', () => {
  const controller = createOrderMutationController({ routeActive: false });
  assert.equal(controller.beginSubmit(context(controller)), null);
  controller.enterRoute();
  const submit = controller.beginSubmit(context(controller));
  assert.ok(submit);
  assert.equal(controller.finishSubmit(submit), true);
  assert.equal(controller.finishSubmit(submit), false);
  const request = controller.beginRequest('cancel', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  assert.deepEqual(controller.settleRequest(request), { accepted: true, canPresent: true, detached: false });
  assert.equal(controller.settleRequest(request).accepted, false);
});

test('detached persistent completion settles controls without presentation authority', () => {
  const controller = createOrderMutationController();
  const request = controller.beginRequest('production', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  controller.leaveRoute();
  assert.deepEqual(controller.settleRequest(request), { accepted: true, canPresent: false, detached: true });
});

test('newer owner cannot be cleared by an older request settlement', () => {
  const controller = createOrderMutationController();
  const first = controller.beginRequest('detail', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  const second = controller.beginRequest('detail', context(controller, { selectedOrderId: 8 }), { requestedOrderId: 8 });
  assert.deepEqual(controller.settleRequest(first), { accepted: true, canPresent: false, detached: false });
  assert.equal(controller.settleRequest(second).accepted, true);
});

test('shared feedback keeps mutation success and refresh warning separate without an error', () => {
  const controller = createOrderMutationController();
  controller.setSuccessFeedback('Заказ сохранён.');
  controller.setWarningFeedback('Список не удалось обновить.', true);
  assert.deepEqual(controller.feedback(), {
    neutral: '',
    success: 'Заказ сохранён.',
    warning: 'Список не удалось обновить.',
    error: '',
  });
  controller.setErrorFeedback('Заказ не сохранён.');
  assert.deepEqual(controller.feedback(), {
    neutral: '',
    success: '',
    warning: '',
    error: 'Заказ не сохранён.',
  });
});

test('request-owned announcements and focus reject detachment, obsolete context and newer focus owners', () => {
  const controller = createOrderMutationController();
  const request = controller.beginRequest('cancel', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  assert.equal(controller.shouldAnnounce(request, 'polite'), true);
  assert.equal(controller.shouldAnnounce(request, 'polite'), false);
  const firstFocus = controller.beginFocus(context(controller, { selectedOrderId: 7 }), 'order-detail');
  const newerFocus = controller.beginFocus(context(controller, { selectedOrderId: 7 }), 'production:failure');
  assert.ok(firstFocus);
  assert.ok(newerFocus);
  assert.equal(controller.canApplyFocus(firstFocus, context(controller, { selectedOrderId: 7 })), false);
  assert.equal(controller.canApplyFocus(newerFocus, context(controller, { selectedOrderId: 7 })), true);
  controller.bumpContext();
  assert.equal(controller.canApplyFocus(newerFocus, context(controller, { selectedOrderId: 7 })), false);
  const detachedFocus = controller.beginFocus(context(controller, { selectedOrderId: 7 }), 'order-detail');
  assert.ok(detachedFocus);
  controller.leaveRoute();
  assert.equal(controller.shouldAnnounce(request, 'assertive'), false);
  assert.equal(controller.canApplyFocus(detachedFocus, context(controller, { selectedOrderId: 7 })), false);
});

test('Order DTO boundary rejects wrong identity, unknown status and incomplete objects', () => {
  assert.equal(orderDtoIsValid(order(7), 7), true);
  assert.equal(orderDtoIsValid(order(8), 7), false);
  assert.equal(orderDtoIsValid(order(7, { status: 'mystery' }), 7), false);
  assert.equal(orderDtoIsValid({ id: 7 }, 7), false);
  assert.equal(ordersDtoIsValid({ orders: [order(7), order(8)] }), true);
  assert.equal(ordersDtoIsValid({ orders: [order(7), { id: 8 }] }), false);
});

test('reference snapshot boundary requires every complete list and positive identities', () => {
  const snapshot = {
    clients: [{ id: 1 }],
    templates: [{ id: 2 }],
    versions: [{ id: 3 }],
    clientRecipes: [{ id: 4 }],
    packagingItems: [{ id: 5 }],
  };
  assert.equal(orderReferenceDataIsValid(snapshot), true);
  assert.equal(orderReferenceDataIsValid({ ...snapshot, versions: undefined }), false);
  assert.equal(orderReferenceDataIsValid({ ...snapshot, packagingItems: [{ id: -1 }] }), false);
});

test('readiness DTO boundary keeps ready, warning and blocked valid but rejects another Order', () => {
  for (const status of ['ready', 'warning', 'blocked']) {
    const value = {
      order_id: 7,
      can_produce: status !== 'blocked',
      status,
      blocking_issues: [],
      warnings: [],
      ingredients: [],
      packaging: [],
      estimated_cost: null,
      estimated_tax: null,
      estimated_margin: null,
      generated_at: '2026-07-24T10:00:00Z',
    };
    assert.equal(productionReadinessDtoIsValid(value, 7), true);
    assert.equal(productionReadinessDtoIsValid({ ...value, order_id: 8 }, 7), false);
    assert.equal(productionReadinessDtoIsValid({ ...value, ingredients: [{ ingredient_id: 4 }] }, 7), false);
  }
});

test('ProductionBatch boundary requires exact Order and internally matching snapshot rows', () => {
  assert.equal(productionBatchDtoIsValid(batch(7), 7), true);
  assert.equal(productionBatchDtoIsValid(batch(8), 7), false);
  assert.equal(productionBatchDtoIsValid(batch(7, {
    ingredients: [{ ...batch(7).ingredients[0], production_batch_id: 99 }],
  }), 7), false);
  assert.equal(productionBatchDtoIsValid(batch(7, { total_cost: 200 }), 7), false);
});

test('production uncertainty creates one exact obligation and automatic reconciliation is consumed once', () => {
  const controller = createOrderMutationController();
  const request = controller.beginRequest('production', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  const first = controller.requireProductionReconciliation(request, 7);
  const second = controller.requireProductionReconciliation(request, 7);
  assert.equal(first.epoch, second.epoch);
  assert.equal(controller.productionReconciliationRequired(7), true);
  assert.equal(controller.productionReconciliationRequired(8), false);
  assert.equal(controller.consumeAutomaticProductionReconciliation()?.orderId, 7);
  assert.equal(controller.consumeAutomaticProductionReconciliation(), null);
});

test('reconciliation targets only the original Order and partial, wrong or invalid facts cannot unlock', () => {
  const controller = createOrderMutationController();
  const production = controller.beginRequest('production', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  controller.requireProductionReconciliation(production, 7);
  assert.equal(controller.canStartProductionReconciliation(8), false);
  const reconciliation = controller.beginRequest('productionReconciliation', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  assert.equal(controller.completeProductionReconciliation(reconciliation, order(7), null), false);
  assert.equal(controller.completeProductionReconciliation(reconciliation, null, batch(7)), false);
  assert.equal(controller.completeProductionReconciliation(reconciliation, order(7), batch(8)), false);
  assert.equal(controller.completeProductionReconciliation(reconciliation, order(7, { status: 'new' }), batch(7)), false);
  assert.equal(controller.productionReconciliationRequired(7), true);
});

test('only exact produced Order plus exact ProductionBatch clears the obligation', () => {
  const controller = createOrderMutationController();
  const production = controller.beginRequest('production', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  controller.requireProductionReconciliation(production, 7);
  const reconciliation = controller.beginRequest('productionReconciliation', context(controller, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  assert.equal(productionReconciliationIsCoherent(order(7), batch(7), 7), true);
  assert.equal(controller.completeProductionReconciliation(reconciliation, order(7), batch(7)), true);
  assert.equal(controller.productionReconciliationRequired(), false);
});

test('stale and detached reconciliation cannot clear exact production uncertainty', () => {
  const stale = createOrderMutationController();
  const production = stale.beginRequest('production', context(stale, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  stale.requireProductionReconciliation(production, 7);
  const older = stale.beginRequest('productionReconciliation', context(stale, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  stale.beginRequest('productionReconciliation', context(stale, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  assert.equal(stale.completeProductionReconciliation(older, order(7), batch(7)), false);

  const detached = createOrderMutationController();
  const detachedProduction = detached.beginRequest('production', context(detached, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  detached.requireProductionReconciliation(detachedProduction, 7);
  const reconciliation = detached.beginRequest('productionReconciliation', context(detached, { selectedOrderId: 7 }), { requestedOrderId: 7 });
  detached.leaveRoute();
  assert.equal(detached.completeProductionReconciliation(reconciliation, order(7), batch(7)), false);
  assert.equal(detached.productionReconciliationRequired(7), true);
});

test('production source composes route ownership, exact settlement and controller feedback', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /orderMutationController\.transitionRoute\(previousSection === 'Заказы', nextSection === 'Заказы'\)/);
  assert.match(source, /detachOrderRouteState\(\)/);
  assert.match(source, /orderMutationController\.settleRequest\(snapshot\)/);
  assert.match(source, /orderMutationController\.feedback\(\)/);
  assert.match(source, /orderMutationController\.beginFocus\(currentOrderContext\(\),target\)/);
  assert.match(source, /orderMutationController\.canApplyFocus\(ticket,currentOrderContext\(\)\)/);
});

test('production source validates exact DTOs and keeps reference snapshots atomic', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /orderDtoIsValid\(saved/);
  assert.match(source, /productionReadinessDtoIsValid\(result,id\)/);
  assert.match(source, /productionBatchDtoIsValid\(batch,id\)/);
  assert.match(source, /productionReconciliationIsCoherent\(updated,confirmedBatch,id\)/);
  assert.doesNotMatch(source, /getRecipeVersions\(t\.id\)\.catch\(\(\)=>\(\{recipe_versions:\[\]\}\)\)/);
});

test('production source sends one production POST path and reconciliation uses exact GET composition only', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  const confirmationBody = source.slice(source.indexOf('function confirmProduction'), source.indexOf('function apiErrorCode'));
  assert.equal((confirmationBody.match(/produceOrder\(id,/g) || []).length, 1);
  const reconciliationBody = source.slice(source.indexOf('function reconcileProductionOutcome'), source.indexOf('function editOrder'));
  assert.match(reconciliationBody, /Promise\.all\(\[getOrder\(id\), getProductionBatchByOrder\(id\)\]\)/);
  assert.doesNotMatch(reconciliationBody, /produceOrder\(/);
  assert.doesNotMatch(reconciliationBody, /getOrders\(/);
  assert.doesNotMatch(reconciliationBody, /getProductionBatches\(/);
  assert.doesNotMatch(reconciliationBody, /Promise\.allSettled/);
});

test('production source preserves mutation success when exact refresh fails and uses non-assertive warning', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /setWarningFeedback\(ordersState\.productionRefreshWarningByOrderId\[id\],true\)/);
  assert.match(source, /shouldAnnounce\(refresh,'polite'\)/);
  assert.doesNotMatch(source, /announceAssertive\(ordersState\.productionRefreshWarningByOrderId\[id\]\)/);
});

test('production source blocks unsafe actions while exact reconciliation remains required', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /productionReconciliationRequired\(id\)/);
  assert.match(source, /canStartProductionReconciliation\(id\)/);
  assert.match(source, /consumeAutomaticProductionReconciliation\(\)/);
  assert.match(source, /reconcileProductionOutcome\(obligation\.orderId, true\)/);
});
