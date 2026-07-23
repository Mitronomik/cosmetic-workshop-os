import test from 'node:test';
import assert from 'node:assert/strict';
import {
  INVENTORY_CATALOG_UNSUPPORTED_OPERATIONS,
  InventoryCatalogWorkspaceFeedbackLifecycle,
  inventoryCatalogReconciliationFor,
  isInventoryEntityDto,
  isStockMovementDto,
  isStockReconciliationDto,
  isStockReconciliationForLot,
} from '../dist-tests/inventory-catalog-workspace-feedback/inventory-catalog-workspace-feedback.js';
import { InventoryCatalogWorkspaceRuntime } from '../dist-tests/inventory-catalog-workspace-feedback/inventory-catalog-workspace-runtime.js';
import { bindInventoryCatalogWorkspaceControls } from '../dist-tests/inventory-catalog-workspace-feedback/inventory-catalog-workspace-bindings.js';
import { inventoryCatalogRouteForSection, transitionInventoryCatalogRouteOwnership } from '../dist-tests/inventory-catalog-workspace-feedback/inventory-catalog-workspace-route.js';
import { inventoryCatalogWorkspacePresentation } from '../dist-tests/inventory-catalog-workspace-feedback/inventory-catalog-workspace-presentation.js';

const flush = () => new Promise((resolve) => setImmediate(resolve));
const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
};
const entity = (id = 1) => ({ id, name: `item-${id}` });
const movement = (id = 1, lotId = 4) => ({ id, ingredient_lot_id: lotId, movement_type: 'receipt', quantity: '10.0000', unit: 'g' });
const reconciliation = (lotId = 4) => ({ movements: [movement(1, lotId)], balance: { ingredient_lot_id: lotId, remaining_quantity: '10.0000', unit: 'g' } });

function harness(route = 'inventory') {
  const h = { route, renders: 0, announcements: [], focus: [], applied: [], created: [], failures: [], postCount: 0, getCount: 0 };
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  const runtime = new InventoryCatalogWorkspaceRuntime({
    lifecycle,
    ownsRoute: (candidate) => h.route === candidate,
    render: () => { h.renders += 1; },
    announce: (message, kind) => h.announcements.push([kind, message]),
    focus: (key) => h.focus.push(key),
  });
  lifecycle.enter(route);
  return { h, lifecycle, runtime };
}

test('route adapter maps only Inventory/Catalog sections', () => {
  assert.equal(inventoryCatalogRouteForSection('Склад'), 'inventory');
  assert.equal(inventoryCatalogRouteForSection('Компоненты'), 'ingredients');
  assert.equal(inventoryCatalogRouteForSection('Партии'), 'ingredientLots');
  assert.equal(inventoryCatalogRouteForSection('Движения сырья'), 'stockMovements');
  assert.equal(inventoryCatalogRouteForSection('Тара'), 'packaging');
  assert.equal(inventoryCatalogRouteForSection('Заказы'), null);
});

test('same-route transition preserves current ownership', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  transitionInventoryCatalogRouteOwnership(lifecycle, null, 'Склад');
  const read = lifecycle.startRead('inventory', 'inventory-overview', 'initial');
  transitionInventoryCatalogRouteOwnership(lifecycle, 'Склад', 'Склад');
  assert.equal(lifecycle.finishReadSuccess(read.owner, { overview: {} }).canApply, true);
});

test('Inventory overview initial load stores composed snapshot', async () => {
  const { h, lifecycle, runtime } = harness();
  const request = deferred();
  runtime.read({ route: 'inventory', operation: 'inventory-overview', kind: 'initial', request: () => request.promise, validate: (value) => Boolean(value.overview && value.ingredientLots && value.packaging), apply: (value) => h.applied.push(value) });
  request.resolve({ overview: {}, ingredientLots: [], packaging: [] });
  await flush();
  assert.equal(lifecycle.hasSnapshot('inventory'), true);
  assert.equal(h.applied.length, 1);
  assert.deepEqual(h.announcements, []);
});

test('Inventory initial failure has retry focus', async () => {
  const { h, runtime } = harness();
  const request = deferred();
  runtime.read({ route: 'inventory', operation: 'inventory-overview', kind: 'initial', request: () => request.promise, apply() {} });
  request.reject(new Error('down'));
  await flush();
  assert.equal(h.announcements[0][0], 'assertive');
  assert.equal(h.focus[0], 'core-inventory-retry');
});

test('obsolete same-route inventory reference read is discarded silently', async () => {
  const { h, lifecycle, runtime } = harness('ingredients');
  const request = deferred();
  let ownsContext = true;
  runtime.read({
    route: 'ingredients',
    operation: 'ingredient-references',
    kind: 'reference',
    ownsContext: () => ownsContext,
    request: () => request.promise,
    apply: (value) => h.applied.push(value),
  });
  ownsContext = false;
  request.resolve({ ingredients: [entity()] });
  await flush();
  assert.deepEqual(h.applied, []);
  assert.deepEqual(h.announcements, []);
  assert.deepEqual(h.focus, []);
  assert.deepEqual(lifecycle.feedback('ingredients'), { neutral: '', success: '', warning: '', error: '' });
});

test('Inventory refresh failure retains readable snapshot', async () => {
  const { h, lifecycle, runtime } = harness();
  const first = deferred();
  runtime.read({ route: 'inventory', operation: 'inventory-overview', kind: 'initial', request: () => first.promise, apply: (value) => h.applied.push(value) });
  first.resolve({ overview: { total: 1 } });
  await flush();
  const refresh = deferred();
  runtime.read({ route: 'inventory', operation: 'inventory-overview', kind: 'refresh', request: () => refresh.promise, apply: (value) => h.applied.push(value) });
  refresh.reject(new Error('down'));
  await flush();
  assert.equal(h.applied.length, 1);
  assert.match(lifecycle.feedback('inventory').warning, /Ранее загруженные данные/);
});

test('manual Inventory refresh success is politely announced', async () => {
  const { h, runtime } = harness();
  const first = deferred();
  runtime.read({ route: 'inventory', operation: 'inventory-overview', kind: 'initial', request: () => first.promise, apply() {} });
  first.resolve({});
  await flush();
  const refresh = deferred();
  runtime.read({ route: 'inventory', operation: 'inventory-overview', kind: 'refresh', request: () => refresh.promise, apply() {} });
  refresh.resolve({});
  await flush();
  assert.equal(h.announcements.length, 1);
  assert.equal(h.announcements[0][0], 'polite');
});

test('duplicate inventory read is rejected', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('inventory');
  assert.equal(lifecycle.startRead('inventory', 'inventory-overview', 'initial').accepted, true);
  assert.equal(lifecycle.startRead('inventory', 'inventory-overview', 'refresh').reason, 'duplicate-read');
});

test('ingredient list and reference data have separate owners', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('ingredients');
  assert.equal(lifecycle.startRead('ingredients', 'ingredient-list', 'initial').accepted, true);
  assert.equal(lifecycle.startRead('ingredients', 'ingredient-references', 'reference').accepted, true);
});

test('stale ingredient reference data is rejected after route change', async () => {
  const { h, lifecycle, runtime } = harness('ingredients');
  const request = deferred();
  runtime.read({ route: 'ingredients', operation: 'ingredient-references', kind: 'reference', request: () => request.promise, apply: (value) => h.applied.push(value) });
  lifecycle.leave('ingredients');
  h.route = 'packaging';
  request.resolve({ categories: [entity()] });
  await flush();
  assert.deepEqual(h.applied, []);
});

for (const operation of ['ingredient-create', 'ingredient-update', 'ingredient-deactivate', 'ingredient-category-create', 'ingredient-tag-create', 'ingredient-assignment']) {
  test(`${operation} has explicit entity/catalog ownership`, () => {
    const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
    lifecycle.enter('ingredients');
    const result = lifecycle.startMutation('ingredients', operation, 'ingredient:2');
    assert.equal(result.accepted, true);
    assert.equal(result.owner.contextKey, 'ingredient:2');
  });
}

test('Ingredient definite failure permits the preserved draft to remain editable', async () => {
  const { h, lifecycle, runtime } = harness('ingredients');
  const request = deferred();
  runtime.mutate({ route: 'ingredients', operation: 'ingredient-create', request: () => request.promise, validate: isInventoryEntityDto, successMessage: 'saved', apply() {}, failed: (error, ambiguous) => h.failures.push([error, ambiguous]) });
  request.reject({ status: 422 });
  await flush();
  assert.equal(h.failures[0][1], false);
  assert.equal(lifecycle.reconciliationRequired('ingredients'), false);
});

for (const operation of ['lot-create', 'lot-update', 'lot-deactivate']) {
  test(`${operation} is owned by the selected lot context`, () => {
    const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
    lifecycle.enter('ingredientLots');
    const result = lifecycle.startMutation('ingredientLots', operation, 'lot:8');
    assert.equal(result.accepted, true);
    assert.equal(result.owner.contextKey, 'lot:8');
  });
}

test('stale lot reference data is rejected', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('ingredientLots');
  const read = lifecycle.startRead('ingredientLots', 'lot-references', 'reference', 'form:create');
  lifecycle.leave('ingredientLots');
  lifecycle.enter('ingredientLots');
  assert.equal(lifecycle.finishReadSuccess(read.owner, { ingredients: [entity()] }).canApply, false);
});

test('stale lot movement and balance reads cannot update another selected lot', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('stockMovements');
  const movements = lifecycle.startRead('stockMovements', 'stock-movements', 'detail', 'lot:1');
  const balance = lifecycle.startRead('stockMovements', 'stock-balance', 'detail', 'lot:1');
  lifecycle.leave('stockMovements');
  lifecycle.enter('stockMovements');
  assert.equal(lifecycle.finishReadSuccess(movements.owner, { movements: [] }).canApply, false);
  assert.equal(lifecycle.finishReadSuccess(balance.owner, { ingredient_lot_id: 1 }).canApply, false);
});

for (const scenario of [
  ['ingredientLots', 'lot-references', 'lot'],
  ['stockMovements', 'stock-lot-detail', 'lot'],
  ['ingredients', 'ingredient-references', 'ingredient'],
  ['packaging', 'packaging-references', 'packaging'],
]) {
  const [route, operation, prefix] = scenario;
  test(`${operation} supersedes Context A with Context B and releases stale ownership`, async () => {
    const { h, lifecycle, runtime } = harness(route);
    const a = deferred();
    const b = deferred();
    const applied = [];
    runtime.read({
      route,
      operation,
      kind: 'detail',
      contextKey: `${prefix}:1`,
      request: () => a.promise,
      apply: (value) => applied.push(value.context),
    });
    const second = runtime.read({
      route,
      operation,
      kind: 'detail',
      contextKey: `${prefix}:2`,
      request: () => b.promise,
      apply: (value) => applied.push(value.context),
    });
    assert.equal(second.accepted, true);
    a.resolve({ context: 'A' });
    await flush();
    assert.deepEqual(applied, []);
    assert.deepEqual(h.announcements, []);
    assert.deepEqual(h.focus, []);
    b.resolve({ context: 'B' });
    await flush();
    assert.deepEqual(applied, ['B']);
    const laterA = lifecycle.startRead(route, operation, 'detail', `${prefix}:1`);
    assert.equal(laterA.accepted, true);
  });
}

test('non-stock Inventory reconciliation ignores unrelated and wrong-context reads', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('ingredients');
  const mutation = lifecycle.startMutation('ingredients', 'ingredient-update', 'ingredient:4');
  lifecycle.finishMutationFailure(mutation.owner, new TypeError('network'));
  const obligation = lifecycle.reconciliationObligation('ingredients');
  assert.deepEqual(
    { operation: obligation.readOperation, context: obligation.readContextKey },
    { operation: 'ingredient-list', context: 'ingredients:list' },
  );
  const unrelated = lifecycle.startRead('ingredients', 'ingredient-references', 'reconciliation', 'ingredients:list');
  lifecycle.finishReadSuccess(unrelated.owner, { ingredients: [] }, () => true);
  assert.equal(lifecycle.reconciliationRequired('ingredients'), true);
  const wrong = lifecycle.startRead('ingredients', 'ingredient-list', 'reconciliation', 'ingredient:4');
  lifecycle.finishReadSuccess(wrong.owner, { ingredients: [] }, (value) => Array.isArray(value.ingredients));
  assert.equal(lifecycle.reconciliationRequired('ingredients'), true);
  const exact = lifecycle.startRead('ingredients', 'ingredient-list', 'reconciliation', 'ingredients:list');
  lifecycle.finishReadSuccess(exact.owner, { ingredients: [] }, (value) => Array.isArray(value.ingredients));
  assert.equal(lifecycle.reconciliationRequired('ingredients'), false);
});

test('domain reconciliation map covers every migrated Inventory/Catalog mutation', () => {
  const cases = [
    ...['ingredient-create', 'ingredient-update', 'ingredient-deactivate', 'ingredient-category-create', 'ingredient-tag-create', 'ingredient-assignment']
      .map((mutation) => ['ingredients', mutation, 'ingredient:4', 'ingredient-list', 'ingredients:list']),
    ...['lot-create', 'lot-update', 'lot-deactivate']
      .map((mutation) => ['ingredientLots', mutation, 'lot:4', 'lot-list', 'lots:list']),
    ...['packaging-create', 'packaging-update', 'packaging-deactivate', 'packaging-category-create', 'packaging-tag-create', 'packaging-assignment']
      .map((mutation) => ['packaging', mutation, 'packaging:4', 'packaging-list', 'packaging:list']),
    ['stockMovements', 'stock-movement-create', 'lot:4', 'stock-reconciliation', 'lot:4'],
  ];
  for (const [route, mutation, context, readOperation, readContextKey] of cases) {
    assert.deepEqual(inventoryCatalogReconciliationFor(route, mutation, context), { readOperation, readContextKey });
  }
});

for (const operation of ['packaging-create', 'packaging-update', 'packaging-deactivate', 'packaging-category-create', 'packaging-tag-create', 'packaging-assignment']) {
  test(`${operation} has explicit item/catalog ownership`, () => {
    const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
    lifecycle.enter('packaging');
    const result = lifecycle.startMutation('packaging', operation, 'packaging:5');
    assert.equal(result.accepted, true);
  });
}

test('Packaging presentation preserves filter-capable snapshot after refresh failure', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('packaging');
  const initial = lifecycle.startRead('packaging', 'packaging-list', 'initial');
  lifecycle.finishReadSuccess(initial.owner, { packaging_items: [entity()] });
  const refresh = lifecycle.startRead('packaging', 'packaging-list', 'refresh');
  lifecycle.finishReadFailure(refresh.owner);
  const view = inventoryCatalogWorkspacePresentation(lifecycle, 'packaging');
  assert.equal(view.hasSnapshot, true);
  assert.match(view.feedback.warning, /Ранее загруженные данные/);
});

test('StockMovement DTO validation rejects incomplete results', () => {
  assert.equal(isStockMovementDto(movement()), true);
  assert.equal(isStockMovementDto({ id: 1, ingredient_lot_id: 4 }), false);
  assert.equal(isStockReconciliationDto(reconciliation()), true);
  assert.equal(isStockReconciliationDto({ movements: [], balance: null }), false);
  assert.equal(isStockReconciliationForLot(reconciliation(4), 4), true);
  assert.equal(isStockReconciliationForLot(reconciliation(5), 4), false);
});

test('StockMovement creation issues exactly one POST and applies validated DTO', async () => {
  const { h, runtime } = harness('stockMovements');
  const post = deferred();
  const get = deferred();
  runtime.createStockMovement({
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return get.promise; },
    applyCreated: (value) => h.created.push(value),
    applyReconciliation: (value) => h.applied.push(value),
  });
  post.resolve(movement());
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(h.created.length, 1);
  assert.equal(h.getCount, 1);
  get.resolve(reconciliation());
  await flush();
  assert.equal(h.applied.length, 1);
});

test('ambiguous StockMovement result locks repeat and reconciles with GET only', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const get = deferred();
  const options = {
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return get.promise; },
    applyCreated() {},
    applyReconciliation: (value) => h.applied.push(value),
  };
  runtime.createStockMovement(options);
  post.reject(new TypeError('Failed to fetch'));
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(h.getCount, 1);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
  assert.equal(runtime.createStockMovement(options).reason, 'reconciliation-required');
  assert.equal(h.postCount, 1);
  get.resolve(reconciliation());
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), false);
});

test('StockMovement obligation ignores references, lot list and wrong-lot reconciliation', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const automatic = deferred();
  const options = {
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return automatic.promise; },
    applyCreated() {},
    applyReconciliation: (value) => h.applied.push(value),
  };
  runtime.createStockMovement(options);
  post.reject(new TypeError('Failed to fetch'));
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(runtime.stockMovementObligationLotId(), 4);

  const references = lifecycle.startRead('stockMovements', 'stock-references', 'reference', 'stock:references');
  lifecycle.finishReadSuccess(references.owner, { lots: [], ingredients: [] }, () => true);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);

  const lots = lifecycle.startRead('stockMovements', 'stock-lot-detail', 'detail', 'lots:list');
  lifecycle.finishReadSuccess(lots.owner, { lots: [] }, () => true);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);

  const wrongLot = deferred();
  runtime.read({
    route: 'stockMovements',
    operation: 'stock-lot-detail',
    kind: 'detail',
    contextKey: 'lot:5',
    request: () => { h.getCount += 1; return wrongLot.promise; },
    validate: (value) => isStockReconciliationForLot(value, 5),
    apply: (value) => h.applied.push(value),
  });
  wrongLot.resolve(reconciliation(5));
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);

  automatic.resolve(reconciliation(4));
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), false);
  assert.equal(h.postCount, 1);
  assert.equal(h.getCount, 2);
});

test('invalid original-lot history or balance cannot clear the StockMovement obligation', async () => {
  const { lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const automatic = deferred();
  runtime.createStockMovement({
    lotId: 4,
    create: () => post.promise,
    reconcile: () => automatic.promise,
    applyCreated() {},
    applyReconciliation() {},
  });
  post.reject(new TypeError('network'));
  await flush();
  automatic.resolve({
    movements: [movement(1, 5)],
    balance: { ingredient_lot_id: 4, remaining_quantity: '10.0000', unit: 'g' },
  });
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
  const manual = deferred();
  runtime.reconcileStockMovement(4, () => manual.promise, () => {});
  manual.resolve(reconciliation(4));
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), false);
});

test('failed authoritative StockMovement reconciliation never loops', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const get = deferred();
  runtime.createStockMovement({
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return get.promise; },
    applyCreated() {},
    applyReconciliation() {},
  });
  post.reject(new TypeError('network'));
  await flush();
  get.reject(new Error('GET down'));
  await flush();
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(h.getCount, 1);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
});

test('manual StockMovement reconciliation remains possible after GET failure', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const firstGet = deferred();
  runtime.createStockMovement({
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return firstGet.promise; },
    applyCreated() {},
    applyReconciliation() {},
  });
  post.reject(new TypeError('network'));
  await flush();
  firstGet.reject(new Error('down'));
  await flush();
  const manual = deferred();
  runtime.reconcileStockMovement(4, () => { h.getCount += 1; return manual.promise; }, (value) => h.applied.push(value));
  assert.equal(h.getCount, 2);
  manual.resolve(reconciliation());
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), false);
  assert.equal(h.postCount, 1);
});

test('invalid StockMovement DTO never enters presentation and keeps safety lock', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const get = deferred();
  runtime.createStockMovement({
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return get.promise; },
    applyCreated: (value) => h.created.push(value),
    applyReconciliation() {},
  });
  post.resolve({ id: 1 });
  await flush();
  assert.deepEqual(h.created, []);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
  assert.equal(h.getCount, 1);
  get.resolve(reconciliation());
  await flush();
});

test('StockMovement success plus failed refresh retains accepted success and warning', async () => {
  const { lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const get = deferred();
  runtime.createStockMovement({ lotId: 4, create: () => post.promise, reconcile: () => get.promise, applyCreated() {}, applyReconciliation() {} });
  post.resolve(movement());
  await flush();
  get.reject(new Error('down'));
  await flush();
  assert.match(lifecycle.feedback('stockMovements').success, /Движение создано/);
  assert.match(lifecycle.feedback('stockMovements').warning, /Ранее загруженные данные/);
});

test('detached StockMovement completion is silent and POST is never repeated', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  runtime.createStockMovement({ lotId: 4, create: () => { h.postCount += 1; return post.promise; }, reconcile: () => Promise.resolve(reconciliation()), applyCreated: (value) => h.created.push(value), applyReconciliation() {} });
  lifecycle.leave('stockMovements');
  h.route = 'ingredients';
  post.resolve(movement());
  await flush();
  assert.equal(h.postCount, 1);
  assert.deepEqual(h.created, []);
  assert.deepEqual(h.announcements, []);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
});

test('detached StockMovement waits for settlement, queues one original-lot GET, does not loop, and supports manual retry', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const automatic = deferred();
  const applied = [];
  runtime.createStockMovement({
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return automatic.promise; },
    applyCreated: (value) => h.created.push(value),
    applyReconciliation: (value) => applied.push(value),
  });
  lifecycle.leave('stockMovements');
  h.route = 'ingredients';
  lifecycle.enter('ingredients');
  lifecycle.leave('ingredients');
  h.route = 'stockMovements';
  lifecycle.enter('stockMovements');

  const references = deferred();
  runtime.read({
    route: 'stockMovements',
    operation: 'stock-references',
    kind: 'reference',
    contextKey: 'stock:references',
    request: () => references.promise,
    apply() {},
  });
  references.resolve({ lots: [], ingredients: [] });
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
  assert.equal(h.getCount, 0);
  assert.equal(runtime.startQueuedStockReconciliation(4, () => { h.getCount += 1; return automatic.promise; }, (value) => applied.push(value)), null);

  post.reject(new TypeError('detached network result'));
  await flush();
  assert.equal(h.getCount, 1);
  assert.equal(runtime.startQueuedStockReconciliation(4, () => { h.getCount += 1; return Promise.resolve(reconciliation(4)); }, () => {}), null);
  automatic.reject(new Error('GET down'));
  await flush();
  await flush();
  assert.equal(h.getCount, 1);
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);

  const manual = deferred();
  runtime.reconcileStockMovement(4, () => { h.getCount += 1; return manual.promise; }, (value) => applied.push(value));
  manual.resolve(reconciliation(4));
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), false);
  assert.equal(h.postCount, 1);
  assert.equal(h.getCount, 2);
});

test('Lot B selection cannot clear Lot A obligation and recovery targets Lot A', async () => {
  const { h, lifecycle, runtime } = harness('stockMovements');
  const post = deferred();
  const automatic = deferred();
  const options = {
    lotId: 4,
    create: () => { h.postCount += 1; return post.promise; },
    reconcile: () => { h.getCount += 1; return automatic.promise; },
    applyCreated() {},
    applyReconciliation() {},
  };
  runtime.createStockMovement(options);
  post.reject(new TypeError('network'));
  await flush();
  const lotB = deferred();
  runtime.read({
    route: 'stockMovements',
    operation: 'stock-lot-detail',
    kind: 'detail',
    contextKey: 'lot:5',
    request: () => { h.getCount += 1; return lotB.promise; },
    validate: (value) => isStockReconciliationForLot(value, 5),
    apply() {},
  });
  lotB.resolve(reconciliation(5));
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), true);
  assert.equal(runtime.stockMovementObligationLotId(), 4);
  assert.equal(runtime.createStockMovement({ ...options, lotId: 5 }).reason, 'reconciliation-required');
  automatic.resolve(reconciliation(4));
  await flush();
  assert.equal(lifecycle.reconciliationRequired('stockMovements'), false);
  assert.equal(h.postCount, 1);
});

test('unsupported inventory mutations remain explicitly closed', () => {
  assert.ok(INVENTORY_CATALOG_UNSUPPORTED_OPERATIONS.includes('stock-movement-update'));
  assert.ok(INVENTORY_CATALOG_UNSUPPORTED_OPERATIONS.includes('stock-movement-delete'));
  assert.ok(INVENTORY_CATALOG_UNSUPPORTED_OPERATIONS.includes('packaging-stock-movement'));
});

test('Inventory overview is genuinely read-only in presentation', () => {
  const lifecycle = new InventoryCatalogWorkspaceFeedbackLifecycle();
  lifecycle.enter('inventory');
  assert.equal(inventoryCatalogWorkspacePresentation(lifecycle, 'inventory').canMutate, false);
});

class Control {
  constructor(attrs) { this.attrs = attrs; this.listeners = []; }
  addEventListener(type, callback) { this.listeners.push([type, callback]); }
}
class Root {
  constructor(controls) { this.controls = controls; }
  querySelectorAll(selector) {
    const [, key, value] = selector.match(/^\[([^=]+)="([^"]+)"\]$/) ?? [];
    if (!key) throw new SyntaxError(selector);
    return this.controls.filter((control) => control.attrs[key] === value);
  }
}

test('production bindings cover every Inventory/Catalog refresh and form once', () => {
  const controls = [
    new Control({ 'data-action': 'reload-inventory' }),
    new Control({ 'data-action': 'reload-ingredients' }),
    new Control({ 'data-form': 'ingredient' }),
    new Control({ 'data-action': 'reload-ingredient-lots' }),
    new Control({ 'data-form': 'ingredient-lot' }),
    new Control({ 'data-action': 'reload-stock-movements' }),
    new Control({ 'data-action': 'reconcile-stock-movement' }),
    new Control({ 'data-form': 'stock-movement' }),
    new Control({ 'data-action': 'reload-packaging-items' }),
    new Control({ 'data-form': 'packaging-item' }),
  ];
  const noop = () => {};
  const counts = bindInventoryCatalogWorkspaceControls(new Root(controls), {
    reloadInventory: noop, reloadIngredients: noop, submitIngredient: noop, reloadLots: noop, submitLot: noop,
    reloadStock: noop, reconcileStock: noop, submitStockMovement: noop, reloadPackaging: noop, submitPackaging: noop,
  });
  assert.deepEqual(Object.values(counts), Array(10).fill(1));
  for (const control of controls) assert.equal(control.listeners.length, 1);
});

test('main source has GET-only lot reconciliation and no Packaging movement helper', async () => {
  const fs = await import('node:fs/promises');
  const source = await fs.readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /getStockMovementsByLot/);
  assert.match(source, /getIngredientLotBalance/);
  assert.match(source, /data-reconciliation-context="\$\{obligatedLotId \? `lot:\$\{obligatedLotId\}` : ''\}"/);
  assert.match(source, /stockMovementObligationLotId\(\) \?\? stockMovementsState\.selectedLotId/);
  assert.match(source, /operation: 'stock-references',\n\s+kind: retained \? 'refresh' : 'initial'/);
  assert.doesNotMatch(source, /createPackagingStockMovement/);
  assert.doesNotMatch(source, /updateStockMovement/);
  assert.doesNotMatch(source, /deleteStockMovement/);
});
