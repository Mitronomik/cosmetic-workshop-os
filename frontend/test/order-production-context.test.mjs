import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  batchTaxRateSnapshotsAreValid,
  isCanonicalTaxRatePercent,
  isCanonicalTaxRateTimestamp,
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
    sale_price: '200.00',
    estimated_cost: '110.00',
    estimated_tax: '12.00',
    estimated_margin: '78.00',
    estimated_margin_percent: '39.00',
    financial_estimate_status: 'available',
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
// Canonical boundary validator
// --------------------------------------------------------------------------

const ACCEPTED_PERCENTS = ['0.00', '6.00', '99.99', '100.00', '0.01', '50.50'];
const REJECTED_PERCENTS = [
  '06.00', '100.01', '999.99', '-1.00', '6.0', '6.005', '6', '6,00', '6e0',
  '', ' 6.00 ', '+6.00', '.00', '6.', '0100.00', 'abc', '1000.00',
];
const ACCEPTED_TIMESTAMPS = ['2026-07-27T19:44:53Z', '2024-02-29T00:00:00Z', '2026-01-01T00:00:00Z', '2026-12-31T23:59:59Z'];
const REJECTED_TIMESTAMPS = [
  '2026-02-30T00:00:00Z', '2026-13-01T00:00:00Z', '2026-00-01T00:00:00Z', '2026-07-00T00:00:00Z',
  '2026-07-32T00:00:00Z', '2026-07-27T24:00:00Z', '2026-07-27T19:60:00Z', '2026-07-27T19:44:60Z',
  '2025-02-29T00:00:00Z', '2026-07-27T19:44:53+03:00', '2026-07-27T19:44:53-05:00',
  '2026-07-27T19:44:53.000Z', '2026-07-27T19:44:53', '2026-07-27 19:44:53', '2026-07-27T19:44:53z',
  '2026-07-27', '', 'не время',
];

test('the canonical percentage validator accepts only exact in-range backend values', () => {
  for (const value of ACCEPTED_PERCENTS) {
    assert.equal(isCanonicalTaxRatePercent(value), true, `should accept ${value}`);
  }
  for (const value of REJECTED_PERCENTS) {
    assert.equal(isCanonicalTaxRatePercent(value), false, `should reject ${JSON.stringify(value)}`);
  }
  for (const value of [6, 6.0, true, null, undefined, {}, ['6.00']]) {
    assert.equal(isCanonicalTaxRatePercent(value), false, `should reject non-string ${JSON.stringify(value)}`);
  }
});

test('the canonical timestamp validator rejects impossible calendar and clock values', () => {
  for (const value of ACCEPTED_TIMESTAMPS) {
    assert.equal(isCanonicalTaxRateTimestamp(value), true, `should accept ${value}`);
  }
  for (const value of REJECTED_TIMESTAMPS) {
    assert.equal(isCanonicalTaxRateTimestamp(value), false, `should reject ${JSON.stringify(value)}`);
  }
  for (const value of [20260727, true, null, undefined, {}, ['2026-07-27T19:44:53Z']]) {
    assert.equal(isCanonicalTaxRateTimestamp(value), false, `should reject non-string ${JSON.stringify(value)}`);
  }
});

test('readiness context and batch snapshots share the same canonical validator', () => {
  for (const value of REJECTED_PERCENTS.slice(0, 8)) {
    assert.equal(readinessTaxRateContextIsValid(readiness(7, { tax_rate_percent: value })), false, `readiness ${value}`);
    assert.equal(batchTaxRateSnapshotsAreValid(batch(7, { tax_rate_percent_snapshot: value })), false, `batch ${value}`);
  }
  for (const value of REJECTED_TIMESTAMPS.slice(0, 12)) {
    assert.equal(readinessTaxRateContextIsValid(readiness(7, { tax_rate_effective_at: value })), false, `readiness ${value}`);
    assert.equal(batchTaxRateSnapshotsAreValid(batch(7, { tax_rate_effective_at_snapshot: value })), false, `batch ${value}`);
  }
  assert.equal(readinessTaxRateContextIsValid(readiness(7, { tax_rate_percent: '100.00' })), true);
  assert.equal(batchTaxRateSnapshotsAreValid(batch(7, { tax_rate_percent_snapshot: '100.00' })), true);
  assert.equal(readinessTaxRateContextIsValid(readiness(7, { tax_rate_percent: '99.99' })), true);
  assert.equal(batchTaxRateSnapshotsAreValid(batch(7, { tax_rate_percent_snapshot: '0.00' })), true);
});

test('the boundary validator adds no financial arithmetic', () => {
  const source = readFileSync(new URL('../src/order-production-context.ts', import.meta.url), 'utf8');
  const code = source.replace(/\/\*\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

  assert.equal(/parseFloat|parseInt|toFixed/.test(code), false, 'no float parsing or formatting');
  // `Number(...)` is used only for integer digit-group range checks, never on a
  // money value and never on the fractional part of a rate.
  const numberCalls = code.match(/Number\([^)]*\)/g) || [];
  assert.deepEqual([...new Set(numberCalls)].sort(), ['Number(whole)']);
});

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

// C2-III-A tightened this: a missing key is an outdated response, not a backend
// statement that no rate was snapshotted. Old database rows stay compatible
// because the backend always returns both keys, with explicit null values.
test('a batch DTO missing a snapshot key is untrusted, while explicit null/null is accepted', () => {
  for (const missing of ['tax_rate_percent_snapshot', 'tax_rate_effective_at_snapshot']) {
    const outdated = batch(7);
    delete outdated[missing];
    assert.equal(batchTaxRateSnapshotsAreValid(outdated), false, `missing ${missing}`);
    assert.equal(productionBatchDtoIsValid(outdated, 7), false, `missing ${missing}`);
  }

  const bothMissing = batch(7);
  delete bothMissing.tax_rate_percent_snapshot;
  delete bothMissing.tax_rate_effective_at_snapshot;
  assert.equal(productionBatchDtoIsValid(bothMissing, 7), false);

  const historical = batch(7, { tax_rate_percent_snapshot: null, tax_rate_effective_at_snapshot: null });
  assert.equal(batchTaxRateSnapshotsAreValid(historical), true);
  assert.equal(productionBatchDtoIsValid(historical, 7), true);
});

test('a readiness DTO missing an additive financial key is not a trusted current result', () => {
  for (const key of ['sale_price', 'estimated_cost', 'estimated_tax', 'estimated_margin', 'estimated_margin_percent', 'financial_estimate_status']) {
    const outdated = readiness(7);
    delete outdated[key];
    assert.equal(productionReadinessDtoIsValid(outdated, 7), false, `missing ${key}`);
  }

  for (const status of ['available', 'partial', 'unavailable']) {
    assert.equal(productionReadinessDtoIsValid(readiness(7, { financial_estimate_status: status }), 7), true, status);
  }
  for (const status of ['AVAILABLE', 'ready', '', null, 0, true]) {
    assert.equal(productionReadinessDtoIsValid(readiness(7, { financial_estimate_status: status }), 7), false, JSON.stringify(status));
  }
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

  for (const forbidden of [/parseFloat/, /parseInt/, /\btoFixed\b/, /[^/*]\s[-+*/]\s*(tax|margin|rate)/i]) {
    assert.equal(forbidden.test(code), false, `unexpected arithmetic: ${forbidden}`);
  }
  // `Number(...)` is permitted only for the integer digit-group range check in
  // the boundary validator — never on a money value, a fractional part, or a
  // rate being applied. Pinned exactly so a real calculation cannot slip in.
  assert.deepEqual([...new Set(code.match(/Number\([^)]*\)/g) || [])].sort(), ['Number(whole)']);
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
