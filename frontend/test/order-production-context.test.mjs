import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  batchTaxRateSnapshotsAreValid,
  isTaxRateContextStaleFailure,
  productionConfirmRequestBody,
  readinessTaxRateContextIsValid,
  taxRateContextFromReadiness,
  TAX_RATE_CONTEXT_STALE_CODE,
} from '../dist-tests/order-production-context/order-production-context.js';
import {
  canOpenOrderProductionConfirmation,
  createOrderMutationController,
  extractProductionApiFailure,
  productionBatchDtoIsValid,
  productionConfirmationFailurePresentation,
  productionReadinessDtoIsValid,
} from '../dist-tests/order-production-context/order-mutation-lifecycle.js';

const CONFIGURED = { tax_rate_percent: '6.00', tax_rate_effective_at: '2026-07-27T19:44:53Z' };
const NO_RATE = { tax_rate_percent: null, tax_rate_effective_at: null };

function readiness(orderId = 7, overrides = {}) {
  return {
    order_id: orderId,
    can_produce: true,
    status: 'ready',
    blocking_issues: [],
    warnings: [],
    ingredients: [],
    packaging: [],
    estimated_cost: '110.00',
    estimated_tax: '12.00',
    estimated_margin: '78.00',
    ...CONFIGURED,
    generated_at: '2026-07-24T10:00:00Z',
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
    component_cost: '100.00',
    packaging_cost: '10.00',
    other_cost: '0.00',
    total_cost: '110.00',
    sale_price: '200.00',
    tax: '12.00',
    margin: '78.00',
    margin_percent: '39.00',
    tax_rate_percent_snapshot: '6.00',
    tax_rate_effective_at_snapshot: '2026-07-27T19:44:53Z',
    produced_at: '2026-07-24T10:00:00Z',
    notes: '',
    created_at: '2026-07-24T10:00:00Z',
    ingredients: [],
    packaging: [],
    ...overrides,
  };
}

function staleFailure() {
  return extractProductionApiFailure(Object.assign(new Error('API request failed'), {
    status: 409,
    payload: { detail: { code: TAX_RATE_CONTEXT_STALE_CODE, message: 'Налоговая ставка изменилась. Обновите готовность и подтвердите производство ещё раз.', next_action: 'Запустите проверку готовности заново.' } },
  }));
}

const activeOrder = { id: 7, is_active: true, status: 'ready_to_produce', updated_at: '2026-07-24T10:00:00Z' };

// --------------------------------------------------------------------------
// Readiness context ownership
// --------------------------------------------------------------------------

test('an accepted readiness result stores the exact configured context pair', () => {
  const stored = taxRateContextFromReadiness(readiness());

  assert.deepEqual(stored, {
    expected_tax_rate_percent: '6.00',
    expected_tax_rate_effective_at: '2026-07-27T19:44:53Z',
  });
});

test('the configured context is sent back byte for byte, never reparsed or reformatted', () => {
  const body = productionConfirmRequestBody('  заметка  ', taxRateContextFromReadiness(readiness()));

  assert.deepEqual(body, {
    confirm: true,
    notes: 'заметка',
    expected_tax_rate_percent: '6.00',
    expected_tax_rate_effective_at: '2026-07-27T19:44:53Z',
  });
  assert.equal(typeof body.expected_tax_rate_percent, 'string');
  assert.equal(typeof body.expected_tax_rate_effective_at, 'string');
});

test('a valid no-rate readiness result sends explicit null/null', () => {
  const body = productionConfirmRequestBody(undefined, taxRateContextFromReadiness(readiness(7, NO_RATE)));

  assert.equal(body.expected_tax_rate_percent, null);
  assert.equal(body.expected_tax_rate_effective_at, null);
  assert.equal(body.notes, null);
  assert.ok('expected_tax_rate_percent' in body && 'expected_tax_rate_effective_at' in body);
});

test('missing readiness context fields never fabricate a null/null pair', () => {
  const withoutContext = readiness();
  delete withoutContext.tax_rate_percent;
  delete withoutContext.tax_rate_effective_at;

  assert.equal(taxRateContextFromReadiness(withoutContext), null);
  assert.equal(readinessTaxRateContextIsValid(withoutContext), false);
  assert.equal(productionReadinessDtoIsValid(withoutContext, 7), false);
  assert.equal(canOpenOrderProductionConfirmation(false, activeOrder, withoutContext), false);
});

test('an invalid or half-populated readiness context blocks confirmation', () => {
  for (const overrides of [
    { tax_rate_percent: '6.00', tax_rate_effective_at: null },
    { tax_rate_percent: null, tax_rate_effective_at: '2026-07-27T19:44:53Z' },
    { tax_rate_percent: '6', tax_rate_effective_at: '2026-07-27T19:44:53Z' },
    { tax_rate_percent: '6.0', tax_rate_effective_at: '2026-07-27T19:44:53Z' },
    { tax_rate_percent: 6, tax_rate_effective_at: '2026-07-27T19:44:53Z' },
    { tax_rate_percent: '6.00', tax_rate_effective_at: '2026-07-27 19:44:53' },
    { tax_rate_percent: '6.00', tax_rate_effective_at: '2026-07-27T19:44:53.000Z' },
    { tax_rate_percent: '6.00', tax_rate_effective_at: '2026-07-27T19:44:53+03:00' },
    { tax_rate_percent: '6.00', tax_rate_effective_at: '2026-07-27T19:44:53' },
  ]) {
    const value = readiness(7, overrides);
    assert.equal(taxRateContextFromReadiness(value), null, JSON.stringify(overrides));
    assert.equal(canOpenOrderProductionConfirmation(false, activeOrder, value), false, JSON.stringify(overrides));
  }
});

test('a valid no-rate readiness result is still confirmable', () => {
  assert.equal(canOpenOrderProductionConfirmation(false, activeOrder, readiness(7, NO_RATE)), true);
  assert.equal(productionReadinessDtoIsValid(readiness(7, NO_RATE), 7), true);
});

// --------------------------------------------------------------------------
// Stale conflict recovery
// --------------------------------------------------------------------------

test('a stale 409 is a known no-write conflict that invalidates the old readiness', () => {
  const presentation = productionConfirmationFailurePresentation(staleFailure());

  assert.equal(presentation.kind, 'business_conflict');
  assert.equal(presentation.invalidateReadiness, true);
  assert.equal(presentation.closeConfirmation, true);
  assert.match(presentation.message, /Налоговая ставка изменилась/);
  assert.match(presentation.message, /не выполнено/);
  assert.ok(presentation.nextAction.length > 0);
});

test('a stale 409 never becomes an uncertain-outcome reconciliation obligation', () => {
  const presentation = productionConfirmationFailurePresentation(staleFailure());
  const uncertain = presentation.kind === 'network_uncertain' || presentation.kind === 'unexpected';

  assert.equal(uncertain, false);

  const controller = createOrderMutationController();
  if (uncertain) {
    const request = controller.beginRequest('production', controller.snapshot({ formMode: 'create', editedOrderId: null, selectedOrderId: 7, showForm: false }), { requestedOrderId: 7 });
    controller.requireProductionReconciliation(request, 7);
  }
  assert.equal(controller.hasProductionReconciliation(), false);
  assert.equal(controller.productionReconciliationRequired(7), false);
});

test('a stale 409 requires a fresh readiness check before another confirmation', () => {
  const cache = { 7: readiness() };
  const presentation = productionConfirmationFailurePresentation(staleFailure());

  if (presentation.invalidateReadiness) delete cache[7];

  assert.equal(cache[7], undefined);
  assert.equal(canOpenOrderProductionConfirmation(false, activeOrder, cache[7]), false);
  cache[7] = readiness(7, { tax_rate_percent: '7.00', tax_rate_effective_at: '2026-07-28T08:00:00Z' });
  assert.equal(canOpenOrderProductionConfirmation(false, activeOrder, cache[7]), true);
  assert.deepEqual(taxRateContextFromReadiness(cache[7]), {
    expected_tax_rate_percent: '7.00',
    expected_tax_rate_effective_at: '2026-07-28T08:00:00Z',
  });
});

test('a stale 409 is never retried automatically', () => {
  const presentation = productionConfirmationFailurePresentation(staleFailure());
  let productionPostCount = 0;
  const cache = {};

  // The only path back to a POST is an explicit fresh readiness result.
  if (canOpenOrderProductionConfirmation(false, activeOrder, cache[7])) productionPostCount += 1;

  assert.equal(presentation.kind, 'business_conflict');
  assert.equal(productionPostCount, 0);
});

test('a stale callback from an obsolete route generation cannot render or invalidate a newer Order', () => {
  const controller = createOrderMutationController();
  const workspace = { formMode: 'create', editedOrderId: null, selectedOrderId: 7, showForm: false };
  const request = controller.beginRequest('production', controller.snapshot(workspace), { requestedOrderId: 7 });

  controller.leaveRoute();
  controller.enterRoute();
  const newerWorkspace = { formMode: 'create', editedOrderId: null, selectedOrderId: 8, showForm: false };
  const cache = { 8: readiness(8) };

  const settlement = controller.settleRequest(request);
  const canPresent = controller.canApplyRequest(request, controller.snapshot(newerWorkspace));
  if (canPresent) delete cache[8];

  assert.equal(settlement.detached, true);
  assert.equal(canPresent, false);
  assert.ok(cache[8], 'the newer Order readiness must survive an obsolete stale callback');
  assert.equal(controller.hasProductionReconciliation(), false);
});

test('a detached known conflict does not render on the wrong route', () => {
  const controller = createOrderMutationController();
  const request = controller.beginRequest('production', controller.snapshot({ formMode: 'create', editedOrderId: null, selectedOrderId: 7, showForm: false }), { requestedOrderId: 7 });
  controller.leaveRoute();

  const settlement = controller.settleRequest(request);

  assert.equal(settlement.accepted, true);
  assert.equal(settlement.canPresent, false);
  assert.equal(settlement.detached, true);
  assert.equal(controller.shouldAnnounce(request, 'assertive'), false);
});

test('an unknown or network outcome still uses the existing reconciliation path', () => {
  const network = productionConfirmationFailurePresentation(extractProductionApiFailure(new TypeError('Failed to fetch')));
  const unexpected = productionConfirmationFailurePresentation(extractProductionApiFailure(Object.assign(new Error('API request failed'), {
    status: 500,
    payload: { detail: { code: 'production_unexpected_failure', message: 'Неожиданная ошибка локального приложения.' } },
  })));

  assert.equal(network.kind, 'network_uncertain');
  assert.equal(unexpected.kind, 'unexpected');
  for (const presentation of [network, unexpected]) {
    assert.equal(presentation.requireRefreshBeforeRetry, true);
    assert.equal(presentation.invalidateReadiness, true);
  }
});

test('duplicate confirmation remains blocked while one production owns the write', () => {
  const controller = createOrderMutationController();
  const state = { owner: null, loadingOrderId: null, postCount: 0 };
  const operations = () => [{ owner: state.owner, loadingOrderId: state.loadingOrderId }];
  const confirm = () => {
    if (!canOpenOrderProductionConfirmation(false, activeOrder, readiness())) return;
    if (state.owner) return;
    const request = controller.beginRequest('production', controller.snapshot({ formMode: 'create', editedOrderId: null, selectedOrderId: 7, showForm: false }), { requestedOrderId: 7 });
    state.owner = { kind: 'production', generation: request.generation, orderId: 7 };
    state.loadingOrderId = 7;
    state.postCount += 1;
  };

  confirm();
  confirm();
  confirm();

  assert.equal(state.postCount, 1);
  assert.equal(operations()[0].loadingOrderId, 7);
});

// --------------------------------------------------------------------------
// Response DTO boundaries
// --------------------------------------------------------------------------

test('the confirmation and detail DTO accepts both snapshot fields', () => {
  assert.equal(productionBatchDtoIsValid(batch(7), 7), true);
  assert.equal(batchTaxRateSnapshotsAreValid(batch(7)), true);
});

test('the batch detail DTO accepts null snapshots and rejects malformed ones', () => {
  assert.equal(productionBatchDtoIsValid(batch(7, { tax_rate_percent_snapshot: null, tax_rate_effective_at_snapshot: null, tax: null, margin: null, margin_percent: null }), 7), true);
  assert.equal(productionBatchDtoIsValid(batch(7, { tax_rate_percent_snapshot: '6.00', tax_rate_effective_at_snapshot: null }), 7), false);
  assert.equal(productionBatchDtoIsValid(batch(7, { tax_rate_percent_snapshot: null, tax_rate_effective_at_snapshot: '2026-07-27T19:44:53Z' }), 7), false);
  assert.equal(productionBatchDtoIsValid(batch(7, { tax_rate_percent_snapshot: 6 }), 7), false);
  assert.equal(productionBatchDtoIsValid(batch(7, { tax_rate_percent_snapshot: '6' }), 7), false);
  assert.equal(productionBatchDtoIsValid(batch(7, { tax_rate_effective_at_snapshot: '2026-07-27 19:44:53' }), 7), false);
});

test('a pre-C2-II batch DTO without the snapshot keys is still accepted', () => {
  const historical = batch(7);
  delete historical.tax_rate_percent_snapshot;
  delete historical.tax_rate_effective_at_snapshot;

  assert.equal(productionBatchDtoIsValid(historical, 7), true);
});

test('the stale-failure classifier matches only the exact code and status', () => {
  assert.equal(isTaxRateContextStaleFailure({ status: 409, code: TAX_RATE_CONTEXT_STALE_CODE }), true);
  assert.equal(isTaxRateContextStaleFailure({ status: 409, code: 'production_conflict' }), false);
  assert.equal(isTaxRateContextStaleFailure({ status: 422, code: TAX_RATE_CONTEXT_STALE_CODE }), false);
  assert.equal(isTaxRateContextStaleFailure(null), false);
  assert.equal(isTaxRateContextStaleFailure(undefined), false);
});

// --------------------------------------------------------------------------
// Ownership boundaries
// --------------------------------------------------------------------------

test('the context module performs no financial arithmetic and adds no financial UI', () => {
  const source = readFileSync(new URL('../src/order-production-context.ts', import.meta.url), 'utf8');
  const code = source.replace(/\/\*\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

  for (const forbidden of [/\bNumber\s*\(/, /parseFloat/, /parseInt/, /\btoFixed\b/, /[^/*]\s[-+*/]\s*(tax|margin|rate)/i]) {
    assert.equal(forbidden.test(code), false, `unexpected arithmetic: ${forbidden}`);
  }
  for (const forbidden of ['innerHTML', '<div', '<section', '<p>', 'Недоступно', 'Маржа', 'Налог:']) {
    assert.equal(code.includes(forbidden), false, `unexpected presentation: ${forbidden}`);
  }
});

test('main.ts stays at or below its 6399-line ceiling and adds no arithmetic', () => {
  const source = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');

  // Match `wc -l`: count newlines, so a trailing newline is not an extra line.
  const lineCount = source.split('\n').length - (source.endsWith('\n') ? 1 : 0);

  assert.ok(lineCount <= 6399, `main.ts must not grow beyond 6399 lines, saw ${lineCount}`);
  assert.equal(/expected_tax_rate_percent\s*[:=]\s*(?!context)/.test(source), false, 'main.ts must not construct the tax context itself');
  assert.equal(source.includes('tax_rate_percent_snapshot'), false, 'C2-II adds no snapshot presentation to main.ts');
});
