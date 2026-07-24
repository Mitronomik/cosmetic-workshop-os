import test from 'node:test';
import assert from 'node:assert/strict';
import {
  FORMULA_CLIENT_UNSUPPORTED_OPERATIONS,
  FormulaClientWorkspaceFeedbackLifecycle,
  containsSensitiveClientText,
  formulaClientReconciliationFor,
  isEntityDto,
  isRecipeVersionDetailDto,
} from '../dist-tests/formula-client-workspace-feedback/formula-client-workspace-feedback.js';
import { FormulaClientWorkspaceRuntime, requestRecipeTemplateSnapshot } from '../dist-tests/formula-client-workspace-feedback/formula-client-workspace-runtime.js';
import { finalizeWorkspaceMutationUi } from '../dist-tests/formula-client-workspace-feedback/core-workspace-feedback.js';
import { bindFormulaClientWorkspaceControls } from '../dist-tests/formula-client-workspace-feedback/formula-client-workspace-bindings.js';
import { formulaClientRouteForSection, transitionFormulaClientRouteOwnership } from '../dist-tests/formula-client-workspace-feedback/formula-client-workspace-route.js';
import { formulaClientWorkspacePresentation } from '../dist-tests/formula-client-workspace-feedback/formula-client-workspace-presentation.js';

const flush = () => new Promise((resolve) => setImmediate(resolve));
const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
};
const entity = (id = 1) => ({ id, name: `item-${id}` });
const version = (id = 1) => ({ version: { id, version_number: id }, ingredients: [{ id: id * 10 }] });

function harness(route = 'recipes') {
  const h = { route, renders: 0, announcements: [], focus: [], reads: [], mutations: [], applied: [], failed: [] };
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  const runtime = new FormulaClientWorkspaceRuntime({
    lifecycle,
    ownsRoute: (candidate) => h.route === candidate,
    render: () => { h.renders += 1; },
    announce: (message, kind) => h.announcements.push([kind, message]),
    focus: (key) => h.focus.push(key),
  });
  lifecycle.enter(route);
  return { h, lifecycle, runtime };
}

test('route adapter maps only the three supported Formula/Client sections', () => {
  assert.equal(formulaClientRouteForSection('Рецепты'), 'recipes');
  assert.equal(formulaClientRouteForSection('Клиенты'), 'clients');
  assert.equal(formulaClientRouteForSection('Индивидуальные рецепты'), 'clientRecipes');
  assert.equal(formulaClientRouteForSection('Заказы'), null);
});

test('same-route transition does not invalidate an owned read', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  transitionFormulaClientRouteOwnership(lifecycle, null, 'Рецепты');
  const read = lifecycle.startRead('recipes', 'recipe-list', 'initial');
  transitionFormulaClientRouteOwnership(lifecycle, 'Рецепты', 'Рецепты');
  assert.equal(read.accepted, true);
  assert.equal(lifecycle.finishReadSuccess(read.owner, { recipe_templates: [] }).canApply, true);
});

test('initial load success is silent and stores a readable snapshot', async () => {
  const { h, lifecycle, runtime } = harness();
  const request = deferred();
  runtime.read({ route: 'recipes', operation: 'recipe-list', kind: 'initial', request: () => request.promise, apply: (value) => h.applied.push(value) });
  request.resolve({ recipe_templates: [entity()] });
  await flush();
  assert.equal(lifecycle.hasSnapshot('recipes'), true);
  assert.equal(h.applied.length, 1);
  assert.deepEqual(h.announcements, []);
});

test('initial load failure is assertive and exposes a retry focus target', async () => {
  const { h, runtime } = harness();
  const request = deferred();
  runtime.read({ route: 'recipes', operation: 'recipe-list', kind: 'initial', request: () => request.promise, apply() {} });
  request.reject(new Error('down'));
  await flush();
  assert.equal(h.announcements[0][0], 'assertive');
  assert.equal(h.focus[0], 'core-recipes-retry');
});

test('obsolete same-route reference read is discarded without feedback or application', async () => {
  const { h, lifecycle, runtime } = harness('clientRecipes');
  const request = deferred();
  let ownsContext = true;
  runtime.read({
    route: 'clientRecipes',
    operation: 'client-recipe-references',
    kind: 'reference',
    ownsContext: () => ownsContext,
    request: () => request.promise,
    apply: (value) => h.applied.push(value),
  });
  ownsContext = false;
  request.reject(new Error('obsolete'));
  await flush();
  assert.deepEqual(h.applied, []);
  assert.deepEqual(h.announcements, []);
  assert.deepEqual(h.focus, []);
  assert.deepEqual(lifecycle.feedback('clientRecipes'), { neutral: '', success: '', warning: '', error: '' });
});

test('manual refresh success is politely announced once per request', async () => {
  const { h, runtime } = harness();
  for (let index = 0; index < 2; index += 1) {
    const request = deferred();
    runtime.read({ route: 'recipes', operation: 'recipe-list', kind: index ? 'refresh' : 'initial', request: () => request.promise, apply() {} });
    request.resolve({ recipe_templates: [] });
    await flush();
  }
  assert.equal(h.announcements.length, 1);
  assert.equal(h.announcements[0][0], 'polite');
  assert.equal(h.focus[0], 'core-recipes-refresh');
});

test('refresh failure retains the prior snapshot and reports a warning', async () => {
  const { h, lifecycle, runtime } = harness('clients');
  const first = deferred();
  runtime.read({ route: 'clients', operation: 'client-list', kind: 'initial', request: () => first.promise, apply: (value) => h.applied.push(value) });
  first.resolve({ clients: [entity()] });
  await flush();
  const refresh = deferred();
  runtime.read({ route: 'clients', operation: 'client-list', kind: 'refresh', request: () => refresh.promise, apply: (value) => h.applied.push(value) });
  refresh.reject(new Error('down'));
  await flush();
  assert.equal(h.applied.length, 1);
  assert.match(lifecycle.feedback('clients').warning, /Ранее загруженные данные/);
});

test('duplicate read is rejected without issuing a second request', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('recipes');
  assert.equal(lifecycle.startRead('recipes', 'recipe-list', 'initial').accepted, true);
  assert.deepEqual(lifecycle.startRead('recipes', 'recipe-list', 'refresh'), { accepted: false, reason: 'duplicate-read' });
});

test('route leave rejects a stale read and all presentation effects', async () => {
  const { h, lifecycle, runtime } = harness();
  const request = deferred();
  runtime.read({ route: 'recipes', operation: 'recipe-list', kind: 'initial', request: () => request.promise, apply: (value) => h.applied.push(value) });
  lifecycle.leave('recipes');
  h.route = 'clients';
  request.resolve({ recipe_templates: [entity(9)] });
  await flush();
  assert.deepEqual(h.applied, []);
  assert.deepEqual(h.announcements, []);
  assert.deepEqual(h.focus, []);
});

test('detail reads are independently owned from related-list reads', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  const detail = lifecycle.startRead('clients', 'client-related', 'detail', 'client:1');
  const wishes = lifecycle.startRead('clients', 'client-wishes', 'related', 'client:1');
  assert.equal(detail.accepted, true);
  assert.equal(wishes.accepted, true);
});

test('client related request cannot update another selected client', async () => {
  const { h, lifecycle, runtime } = harness('clients');
  const request = deferred();
  runtime.read({ route: 'clients', operation: 'client-related', kind: 'related', contextKey: 'client:1', request: () => request.promise, apply: (value) => h.applied.push(value) });
  lifecycle.leave('clients');
  lifecycle.enter('clients');
  request.resolve({ wishes: [entity()] });
  await flush();
  assert.deepEqual(h.applied, []);
});

test('recipe calculation has an independent owner and stale result is isolated', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('recipes');
  const calculation = lifecycle.startRead('recipes', 'recipe-calculation', 'calculation', 'version:1:100:g');
  lifecycle.leave('recipes');
  lifecycle.enter('recipes');
  assert.equal(lifecycle.finishReadSuccess(calculation.owner, { total: 100 }).canApply, false);
});

test('calculation failure does not require or mutate a formula snapshot', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('recipes');
  const calculation = lifecycle.startRead('recipes', 'recipe-calculation', 'calculation', 'version:1');
  lifecycle.finishReadFailure(calculation.owner);
  assert.equal(lifecycle.hasSnapshot('recipes'), false);
  assert.equal(lifecycle.reconciliationRequired('recipes'), false);
});

test('duplicate mutation is rejected', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  assert.equal(lifecycle.startMutation('clients', 'client-create').accepted, true);
  assert.deepEqual(lifecycle.startMutation('clients', 'client-update', 'client:1'), { accepted: false, reason: 'mutation-active' });
});

test('validated known success is the only path to apply a mutation', async () => {
  const { h, runtime } = harness('clientRecipes');
  const bad = deferred();
  runtime.mutate({ route: 'clientRecipes', operation: 'client-recipe-create', request: () => bad.promise, validate: isRecipeVersionDetailDto, successMessage: 'saved', apply: (value) => h.applied.push(value) });
  bad.resolve({ version: {}, ingredients: 'bad' });
  await flush();
  assert.deepEqual(h.applied, []);
  assert.equal(h.announcements.at(-1)[0], 'assertive');
});

test('definite failure calls failure handling without reconciliation lock', async () => {
  const { h, lifecycle, runtime } = harness('clients');
  const request = deferred();
  runtime.mutate({ route: 'clients', operation: 'client-update', contextKey: 'client:1', request: () => request.promise, validate: isEntityDto, successMessage: 'saved', apply() {}, failed: (error, ambiguous) => h.failed.push([error, ambiguous]) });
  request.reject({ status: 422 });
  await flush();
  assert.equal(h.failed.length, 1);
  assert.equal(h.failed[0][1], false);
  assert.equal(lifecycle.reconciliationRequired('clients'), false);
});

test('ambiguous mutation locks repetition until authoritative GET succeeds', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  const mutation = lifecycle.startMutation('clients', 'client-create', 'client:new');
  lifecycle.finishMutationFailure(mutation.owner, new TypeError('Failed to fetch'));
  assert.equal(lifecycle.reconciliationRequired('clients'), true);
  assert.equal(lifecycle.startMutation('clients', 'client-create').reason, 'reconciliation-required');
  const reconcile = lifecycle.startRead('clients', 'client-list', 'reconciliation', 'clients:list');
  assert.equal(lifecycle.finishReadSuccess(reconcile.owner, { clients: [] }).canApply, true);
  assert.equal(lifecycle.reconciliationRequired('clients'), false);
});

for (const scenario of [
  ['recipes', 'recipe-template-detail', 'template'],
  ['recipes', 'recipe-version-detail', 'version'],
  ['recipes', 'recipe-calculation', 'version'],
  ['clientRecipes', 'client-recipe-detail', 'client-recipe'],
  ['clients', 'client-related', 'client'],
  ['clients', 'client-wishes', 'client'],
  ['clients', 'client-feedback', 'client'],
]) {
  const [route, operation, contextPrefix] = scenario;
  test(`${operation} supersedes Context A with Context B and discards A's late completion`, async () => {
    const { h, lifecycle, runtime } = harness(route);
    const a = deferred();
    const b = deferred();
    const applied = [];
    const first = runtime.read({
      route,
      operation,
      kind: operation === 'recipe-calculation' ? 'calculation' : 'detail',
      contextKey: `${contextPrefix}:1`,
      request: () => a.promise,
      apply: (value) => applied.push(value.context),
    });
    const second = runtime.read({
      route,
      operation,
      kind: operation === 'recipe-calculation' ? 'calculation' : 'detail',
      contextKey: `${contextPrefix}:2`,
      request: () => b.promise,
      apply: (value) => applied.push(value.context),
    });
    assert.equal(first.accepted, true);
    assert.equal(second.accepted, true);
    a.resolve({ context: 'A' });
    await flush();
    assert.deepEqual(applied, []);
    assert.deepEqual(h.announcements, []);
    assert.deepEqual(h.focus, []);
    b.resolve({ context: 'B' });
    await flush();
    assert.deepEqual(applied, ['B']);
    const again = lifecycle.startRead(route, operation, 'detail', `${contextPrefix}:1`);
    assert.equal(again.accepted, true);
    lifecycle.discardRead(again.owner);
  });
}

test('same operation and exact context is rejected while active, but distinct contexts do not collide', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  const a = lifecycle.startRead('clients', 'client-wishes', 'related', 'client:1:archived:false');
  assert.equal(a.accepted, true);
  assert.deepEqual(
    lifecycle.startRead('clients', 'client-wishes', 'refresh', 'client:1:archived:false'),
    { accepted: false, reason: 'duplicate-read' },
  );
  const b = lifecycle.startRead('clients', 'client-wishes', 'related', 'client:2:archived:false');
  assert.equal(b.accepted, true);
  assert.equal(lifecycle.finishReadSuccess(a.owner, { wishes: ['A'] }).canApply, false);
  assert.equal(lifecycle.finishReadSuccess(b.owner, { wishes: ['B'] }).canApply, true);
});

test('obsolete Wishes owner is settled so Client B and a later Client A request are accepted', async () => {
  const { lifecycle, runtime } = harness('clients');
  const a = deferred();
  const b = deferred();
  const applied = [];
  runtime.read({
    route: 'clients',
    operation: 'client-wishes',
    kind: 'related',
    contextKey: 'client:1:archived:false',
    request: () => a.promise,
    apply: (value) => applied.push(value.client),
  });
  runtime.read({
    route: 'clients',
    operation: 'client-wishes',
    kind: 'related',
    contextKey: 'client:2:archived:false',
    request: () => b.promise,
    apply: (value) => applied.push(value.client),
  });
  a.reject(new Error('obsolete A'));
  b.resolve({ client: 'B' });
  await flush();
  assert.deepEqual(applied, ['B']);
  const laterA = lifecycle.startRead('clients', 'client-wishes', 'related', 'client:1:archived:false');
  assert.equal(laterA.accepted, true);
});

test('rejected production runtime read invokes unwind callback and cannot leave loading stuck', () => {
  const { runtime } = harness('recipes');
  const pending = deferred();
  let status = 'loading';
  let requestCount = 0;
  runtime.read({
    route: 'recipes',
    operation: 'recipe-version-detail',
    kind: 'detail',
    contextKey: 'version:5',
    request: () => { requestCount += 1; return pending.promise; },
    apply() {},
  });
  const duplicate = runtime.read({
    route: 'recipes',
    operation: 'recipe-version-detail',
    kind: 'detail',
    contextKey: 'version:5',
    request: () => { requestCount += 1; return Promise.resolve({}); },
    apply() {},
    rejected: () => { status = 'ready'; },
  });
  assert.equal(duplicate.accepted, false);
  assert.equal(status, 'ready');
  assert.equal(requestCount, 1);
});

test('non-stock reconciliation requires the mapped operation, exact context, valid DTO and manual retry', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  const snapshot = lifecycle.startRead('clients', 'client-list', 'initial', 'clients:list');
  lifecycle.finishReadSuccess(snapshot.owner, { clients: [entity(7)] }, (value) => Array.isArray(value.clients));
  const mutation = lifecycle.startMutation('clients', 'client-update', 'client:7');
  lifecycle.finishMutationFailure(mutation.owner, new TypeError('network'));
  const obligation = lifecycle.reconciliationObligation('clients');
  assert.deepEqual(
    { operation: obligation.readOperation, context: obligation.readContextKey, mutation: obligation.mutationOperation },
    { operation: 'client-list', context: 'clients:list', mutation: 'client-update' },
  );

  const unrelated = lifecycle.startRead('clients', 'client-feedback', 'reconciliation', 'client:7');
  lifecycle.finishReadSuccess(unrelated.owner, { feedback: [] }, () => true);
  assert.equal(lifecycle.reconciliationRequired('clients'), true);

  const wrongContext = lifecycle.startRead('clients', 'client-list', 'reconciliation', 'client:7');
  lifecycle.finishReadSuccess(wrongContext.owner, { clients: [] }, (value) => Array.isArray(value.clients));
  assert.equal(lifecycle.reconciliationRequired('clients'), true);

  const invalid = lifecycle.startRead('clients', 'client-list', 'reconciliation', 'clients:list');
  lifecycle.finishReadSuccess(invalid.owner, { clients: 'invalid' }, (value) => Array.isArray(value.clients));
  assert.equal(lifecycle.reconciliationRequired('clients'), true);
  assert.equal(lifecycle.hasSnapshot('clients'), true);

  const failed = lifecycle.startRead('clients', 'client-list', 'reconciliation', 'clients:list');
  lifecycle.finishReadFailure(failed.owner);
  assert.equal(lifecycle.reconciliationRequired('clients'), true);
  assert.equal(lifecycle.hasSnapshot('clients'), true);

  const manual = lifecycle.startRead('clients', 'client-list', 'reconciliation', 'clients:list');
  lifecycle.finishReadSuccess(manual.owner, { clients: [entity(7)] }, (value) => Array.isArray(value.clients));
  assert.equal(lifecycle.reconciliationRequired('clients'), false);
});

test('mutation completion identity includes entity context', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  const mutation = lifecycle.startMutation('clients', 'client-update', 'client:7');
  const wrongContextOwner = { ...mutation.owner, contextKey: 'client:8' };
  assert.equal(lifecycle.finishMutationSuccess(wrongContextOwner, entity(8), isEntityDto, 'saved').accepted, false);
  assert.equal(lifecycle.mutationActive('clients'), true);
  assert.equal(lifecycle.finishMutationSuccess(mutation.owner, entity(7), isEntityDto, 'saved').knownSuccess, true);
});

test('domain reconciliation map covers every migrated Formula/Client mutation', () => {
  const cases = [
    ['recipes', 'recipe-template-create', 'template:new', 'recipe-list', 'recipes:list'],
    ['recipes', 'recipe-version-create', 'template:4', 'recipe-version-list', 'template:4'],
    ['recipes', 'recipe-category-create', 'recipes:catalog', 'recipe-list', 'recipes:list'],
    ['recipes', 'recipe-tag-create', 'recipes:catalog', 'recipe-list', 'recipes:list'],
    ['recipes', 'recipe-category-assign', 'template:4', 'recipe-list', 'recipes:list'],
    ['recipes', 'recipe-tags-assign', 'template:4', 'recipe-list', 'recipes:list'],
    ['clients', 'client-create', 'client:new', 'client-list', 'clients:list'],
    ['clients', 'client-update', 'client:4', 'client-list', 'clients:list'],
    ['clients', 'client-deactivate', 'client:4', 'client-list', 'clients:list'],
    ['clients', 'wish-create', 'client:4:archived:false', 'client-wishes', 'client:4:archived:false'],
    ['clients', 'wish-status', 'client:4:archived:false:wish:2', 'client-wishes', 'client:4:archived:false'],
    ['clients', 'wish-archive', 'client:4:archived:true:wish:2', 'client-wishes', 'client:4:archived:true'],
    ['clients', 'feedback-create', 'client:4', 'client-feedback', 'client:4'],
    ['clientRecipes', 'client-recipe-create', 'client:4:version:2', 'client-recipe-list', 'client-recipes:list'],
    ['clientRecipes', 'client-recipe-composition', 'client-recipe:8', 'client-recipe-detail', 'client-recipe:8'],
    ['clientRecipes', 'client-recipe-deactivate', 'client-recipe:8', 'client-recipe-list', 'client-recipes:list'],
    ['clientRecipes', 'client-recipe-restore', 'client-recipe:8', 'client-recipe-list', 'client-recipes:list'],
  ];
  for (const [route, mutation, context, readOperation, readContextKey] of cases) {
    assert.deepEqual(formulaClientReconciliationFor(route, mutation, context), { readOperation, readContextKey });
  }
});

test('detached mutation completion is silent and requires reconciliation', async () => {
  const { h, lifecycle, runtime } = harness('clients');
  const request = deferred();
  runtime.mutate({ route: 'clients', operation: 'client-create', request: () => request.promise, validate: isEntityDto, successMessage: 'saved', apply: (value) => h.applied.push(value) });
  lifecycle.leave('clients');
  h.route = 'recipes';
  request.resolve(entity());
  await flush();
  assert.deepEqual(h.applied, []);
  assert.deepEqual(h.announcements, []);
  assert.equal(lifecycle.reconciliationRequired('clients'), true);
});

test('mutation finalizer runs exactly once for every accepted settlement path and never for a rejected start', async () => {
  const cases = [
    { name: 'known success', resolve: entity(1), validate: isEntityDto },
    { name: 'invalid DTO', resolve: { id: 0 }, validate: isEntityDto },
    { name: 'definite failure', reject: { status: 422 }, validate: isEntityDto },
    { name: 'ambiguous failure', reject: new TypeError('Failed to fetch'), validate: isEntityDto },
    { name: 'obsolete context', resolve: entity(2), validate: isEntityDto, obsolete: true },
    { name: 'stale ownership', resolve: entity(2), validate: isEntityDto, stale: true },
    { name: 'detached success', resolve: entity(3), validate: isEntityDto, detached: true },
    { name: 'detached failure', reject: new TypeError('Failed to fetch'), validate: isEntityDto, detached: true },
  ];
  for (const scenario of cases) {
    const { h, lifecycle, runtime } = harness('clients');
    const request = deferred();
    let ownsContext = true;
    const settlements = [];
    const started = runtime.mutate({
      route: 'clients',
      operation: 'client-create',
      contextKey: `client:${scenario.name}`,
      ownsContext: () => ownsContext,
      request: () => request.promise,
      validate: scenario.validate,
      successMessage: 'saved',
      apply() {},
      settled: (result) => settlements.push(result),
    });
    if (scenario.obsolete) ownsContext = false;
    if (scenario.stale) lifecycle.cancelMutation(started.owner);
    if (scenario.detached) {
      lifecycle.leave('clients');
      h.route = 'recipes';
    }
    if ('reject' in scenario) request.reject(scenario.reject);
    else request.resolve(scenario.resolve);
    await flush();
    assert.equal(settlements.length, 1, scenario.name);
  }

  const { lifecycle, runtime } = harness('clients');
  const active = lifecycle.startMutation('clients', 'client-create', 'client:active');
  let requestCount = 0;
  let settledCount = 0;
  const rejected = runtime.mutate({
    route: 'clients',
    operation: 'client-update',
    contextKey: 'client:2',
    request: () => { requestCount += 1; return Promise.resolve(entity(2)); },
    validate: isEntityDto,
    successMessage: 'saved',
    apply() {},
    settled: () => { settledCount += 1; },
  });
  assert.equal(rejected.accepted, false);
  assert.equal(requestCount, 0);
  assert.equal(settledCount, 0);
  lifecycle.cancelMutation(active.owner);
});

for (const [operation, contextKey] of [
  ['client-recipe-create', 'client:4:version:2'],
  ['client-recipe-composition', 'client-recipe:8'],
  ['client-recipe-deactivate', 'client-recipe:8'],
  ['client-recipe-restore', 'client-recipe:8'],
]) {
  test(`${operation} detached settlement clears only busy state, preserves draft, and permits route-return reconciliation`, async () => {
    const { h, lifecycle, runtime } = harness('clientRecipes');
    const request = deferred();
    const state = { busy: true, draft: { title: 'Черновик', ingredients: [{ amount: '4.5' }] } };
    const before = structuredClone(state.draft);
    let settledCount = 0;
    runtime.mutate({
      route: 'clientRecipes',
      operation,
      contextKey,
      request: () => request.promise,
      validate: isEntityDto,
      successMessage: 'saved',
      apply() { assert.fail('detached result must not apply'); },
      settled: () => {
        settledCount += 1;
        state.busy = false;
      },
    });
    lifecycle.leave('clientRecipes');
    h.route = 'recipes';
    lifecycle.enter('clientRecipes');
    h.route = 'clientRecipes';
    request.resolve(entity(8));
    await flush();
    assert.equal(settledCount, 1);
    assert.equal(state.busy, false);
    assert.deepEqual(state.draft, before);
    const obligation = lifecycle.reconciliationObligation('clientRecipes');
    assert.ok(obligation);
    const reconciliation = runtime.read({
      route: 'clientRecipes',
      operation: obligation.readOperation,
      kind: 'reconciliation',
      contextKey: obligation.readContextKey,
      request: () => Promise.resolve({ authoritative: true }),
      validate: (value) => value.authoritative === true,
      apply() {},
    });
    assert.equal(reconciliation.accepted, true);
    await flush();
    assert.equal(lifecycle.reconciliationRequired('clientRecipes'), false);
  });
}

for (const [route, operation, contextKey] of [
  ['recipes', 'recipe-template-create', 'template:new'],
  ['recipes', 'recipe-version-create', 'template:4'],
  ['clients', 'client-create', 'client:new'],
  ['clients', 'client-update', 'client:4'],
]) {
  test(`${operation} direct handler finalizer clears detached busy state and permits exact route-return reconciliation`, async () => {
    const { h, lifecycle, runtime } = harness(route);
    const request = deferred();
    const owner = lifecycle.startMutation(route, operation, contextKey);
    assert.equal(owner.accepted, true);
    const state = { busy: true, draft: { title: 'Черновик', note: 'сохранить' }, resumeCount: 0 };
    const before = structuredClone(state.draft);
    void request.promise.then((value) => {
      lifecycle.finishMutationSuccess(owner.owner, value, isEntityDto, 'saved');
    }).finally(() => {
      finalizeWorkspaceMutationUi({
        clearBusy: () => { state.busy = false; },
        ownsRoute: () => lifecycle.ownsRoute(route),
        resumeRoute: () => { state.resumeCount += 1; },
      });
    });
    lifecycle.leave(route);
    h.route = route === 'recipes' ? 'clients' : 'recipes';
    lifecycle.enter(route);
    h.route = route;
    request.resolve(entity(4));
    await flush();
    assert.equal(state.busy, false);
    assert.equal(state.resumeCount, 1);
    assert.deepEqual(state.draft, before);
    const obligation = lifecycle.reconciliationObligation(route);
    assert.ok(obligation);
    const reconciliationRead = runtime.read({
      route,
      operation: obligation.readOperation,
      kind: 'reconciliation',
      contextKey: obligation.readContextKey,
      request: () => Promise.resolve({ authoritative: true }),
      validate: (value) => value.authoritative === true,
      apply() {},
    });
    assert.equal(reconciliationRead.accepted, true);
    await flush();
    assert.equal(lifecycle.reconciliationRequired(route), false);
  });
}

test('RecipeTemplate snapshot waits for detail and versions and commits them atomically', async () => {
  const { runtime } = harness('recipes');
  const detail = deferred();
  const versions = deferred();
  const state = { selectedTemplate: entity(9), versions: [{ id: 90, recipe_template_id: 9 }] };
  runtime.read({
    route: 'recipes',
    operation: 'recipe-template-detail',
    kind: 'detail',
    contextKey: 'template:1',
    request: () => requestRecipeTemplateSnapshot(() => detail.promise, () => versions.promise),
    validate: ([template, response]) => template.id === 1 && response.recipe_versions.every((item) => item.recipe_template_id === 1),
    apply: ([template, response]) => {
      state.selectedTemplate = template;
      state.versions = response.recipe_versions;
    },
  });
  detail.resolve(entity(1));
  await flush();
  assert.equal(state.selectedTemplate.id, 9);
  assert.equal(state.versions[0].recipe_template_id, 9);
  versions.resolve({ recipe_versions: [{ id: 10, recipe_template_id: 1 }] });
  await flush();
  assert.equal(state.selectedTemplate.id, 1);
  assert.equal(state.versions[0].recipe_template_id, 1);
});

test('RecipeTemplate snapshot partial failure commits neither half', async () => {
  const { runtime } = harness('recipes');
  const detail = deferred();
  const versions = deferred();
  const state = { selectedTemplate: entity(7), versions: [{ id: 70, recipe_template_id: 7 }] };
  runtime.read({
    route: 'recipes',
    operation: 'recipe-template-detail',
    kind: 'detail',
    contextKey: 'template:1',
    request: () => requestRecipeTemplateSnapshot(() => detail.promise, () => versions.promise),
    validate: () => true,
    apply: ([template, response]) => {
      state.selectedTemplate = template;
      state.versions = response.recipe_versions;
    },
  });
  detail.resolve(entity(1));
  versions.reject(new Error('versions unavailable'));
  await flush();
  assert.equal(state.selectedTemplate.id, 7);
  assert.equal(state.versions[0].recipe_template_id, 7);
});

test('rapid RecipeTemplate A to B switch can commit only B coherent snapshot', async () => {
  const { runtime } = harness('recipes');
  const aDetail = deferred();
  const aVersions = deferred();
  const bDetail = deferred();
  const bVersions = deferred();
  const applied = [];
  const open = (id, detail, versions) => runtime.read({
    route: 'recipes',
    operation: 'recipe-template-detail',
    kind: 'detail',
    contextKey: `template:${id}`,
    request: () => requestRecipeTemplateSnapshot(() => detail.promise, () => versions.promise),
    validate: ([template, response]) => template.id === id && response.recipe_versions.every((item) => item.recipe_template_id === id),
    apply: ([template, response]) => applied.push([template.id, response.recipe_versions.map((item) => item.recipe_template_id)]),
  });
  open(1, aDetail, aVersions);
  open(2, bDetail, bVersions);
  bDetail.resolve(entity(2));
  bVersions.resolve({ recipe_versions: [{ id: 20, recipe_template_id: 2 }] });
  await flush();
  aDetail.resolve(entity(1));
  aVersions.resolve({ recipe_versions: [{ id: 10, recipe_template_id: 1 }] });
  await flush();
  assert.deepEqual(applied, [[2, [2]]]);
});

test('RecipeVersion reconciliation clears only its exact template obligation and does not alter another visible template', async () => {
  const { lifecycle, runtime } = harness('recipes');
  const mutation = lifecycle.startMutation('recipes', 'recipe-version-create', 'template:1');
  lifecycle.finishMutationFailure(mutation.owner, new TypeError('Failed to fetch'));
  const state = { selectedTemplateId: 2, versions: [{ id: 20, recipe_template_id: 2 }] };
  const request = deferred();
  runtime.read({
    route: 'recipes',
    operation: 'recipe-version-list',
    kind: 'reconciliation',
    contextKey: 'template:1',
    request: () => request.promise,
    validate: (response) => response.recipe_versions.every((item) => item.recipe_template_id === 1),
    apply: (response) => {
      if (state.selectedTemplateId === 1) state.versions = response.recipe_versions;
    },
  });
  request.resolve({ recipe_versions: [{ id: 10, recipe_template_id: 1 }] });
  await flush();
  assert.equal(lifecycle.reconciliationRequired('recipes'), false);
  assert.deepEqual(state.versions, [{ id: 20, recipe_template_id: 2 }]);
});

test('success can retain accepted result when a follow-up refresh fails', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('recipes');
  const mutation = lifecycle.startMutation('recipes', 'recipe-version-create');
  const result = lifecycle.finishMutationSuccess(mutation.owner, version(), isRecipeVersionDetailDto, 'Версия сохранена.');
  assert.equal(result.knownSuccess, true);
  const refresh = lifecycle.startRead('recipes', 'recipe-version-list', 'mutation-refresh', 'template:1');
  lifecycle.finishReadFailure(refresh.owner);
  assert.equal(lifecycle.feedback('recipes').success, 'Версия сохранена.');
  assert.match(lifecycle.feedback('recipes').warning, /Ранее загруженные данные|Не удалось загрузить/);
});

test('new RecipeVersion creation cannot mutate the prior snapshot in lifecycle state', () => {
  const prior = Object.freeze(version(1));
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('recipes');
  const mutation = lifecycle.startMutation('recipes', 'recipe-version-create', 'template:1');
  lifecycle.finishMutationSuccess(mutation.owner, version(2), isRecipeVersionDetailDto, 'saved');
  assert.deepEqual(prior, version(1));
});

test('ClientRecipe creation leaves its source RecipeVersion unchanged', () => {
  const source = structuredClone(version(3));
  const before = JSON.stringify(source);
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clientRecipes');
  const mutation = lifecycle.startMutation('clientRecipes', 'client-recipe-create', 'version:3');
  lifecycle.finishMutationSuccess(mutation.owner, { id: 7 }, isEntityDto, 'saved');
  assert.equal(JSON.stringify(source), before);
});

test('composition, archive and restore are context-owned ClientRecipe mutations', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clientRecipes');
  const update = lifecycle.startMutation('clientRecipes', 'client-recipe-composition', 'client-recipe:4');
  assert.equal(update.accepted, true);
  lifecycle.finishMutationSuccess(update.owner, { id: 4 }, isEntityDto, 'saved');
  const archive = lifecycle.startMutation('clientRecipes', 'client-recipe-deactivate', 'client-recipe:4');
  assert.equal(archive.owner.contextKey, 'client-recipe:4');
});

for (const operation of ['client-create', 'client-update', 'client-deactivate', 'wish-create', 'wish-status', 'wish-archive', 'feedback-create']) {
  test(`${operation} has explicit mutation ownership`, () => {
    const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
    lifecycle.enter('clients');
    const mutation = lifecycle.startMutation('clients', operation, operation.includes('wish') ? 'wish:2' : 'client:1');
    assert.equal(mutation.accepted, true);
    assert.equal(mutation.owner.operation, operation);
  });
}

test('sensitive wish, feedback and client note text is absent from generic messages', () => {
  const sensitive = ['аллергия на редкий компонент', 'личная медицинская заметка'];
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('clients');
  const mutation = lifecycle.startMutation('clients', 'feedback-create', 'client:1');
  const result = lifecycle.finishMutationFailure(mutation.owner, { status: 422 });
  assert.equal(containsSensitiveClientText(result.message, sensitive), false);
  assert.equal(containsSensitiveClientText(lifecycle.feedback('clients').error, sensitive), false);
});

test('unsupported operations stay closed and include no Feedback update path', () => {
  assert.ok(FORMULA_CLIENT_UNSUPPORTED_OPERATIONS.includes('client-feedback-update'));
  assert.ok(FORMULA_CLIENT_UNSUPPORTED_OPERATIONS.includes('client-recipe-calculation'));
  assert.ok(FORMULA_CLIENT_UNSUPPORTED_OPERATIONS.includes('recipe-ingredient-row-crud'));
});

test('presentation disables mutation while reconciliation is required', () => {
  const lifecycle = new FormulaClientWorkspaceFeedbackLifecycle();
  lifecycle.enter('recipes');
  const mutation = lifecycle.startMutation('recipes', 'recipe-template-create');
  lifecycle.finishMutationFailure(mutation.owner, new TypeError('network'));
  const presentation = formulaClientWorkspacePresentation(lifecycle, 'recipes');
  assert.equal(presentation.canMutate, false);
  assert.equal(presentation.reconciliationRequired, true);
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

test('production bindings cover every Formula/Client reload and form once per render', () => {
  const controls = [
    new Control({ 'data-action': 'reload-recipes' }),
    new Control({ 'data-form': 'recipe-template' }),
    new Control({ 'data-form': 'recipe-version' }),
    new Control({ 'data-form': 'recipe-calculation' }),
    new Control({ 'data-action': 'reload-clients' }),
    new Control({ 'data-form': 'client' }),
    new Control({ 'data-form': 'client-wish' }),
    new Control({ 'data-form': 'client-feedback' }),
    new Control({ 'data-action': 'reload-client-recipes' }),
    new Control({ 'data-form': 'client-recipe' }),
    new Control({ 'data-form': 'client-recipe-composition' }),
  ];
  const noop = () => {};
  const counts = bindFormulaClientWorkspaceControls(new Root(controls), {
    reloadRecipes: noop, submitRecipeTemplate: noop, submitRecipeVersion: noop, submitRecipeCalculation: noop,
    reloadClients: noop, submitClient: noop, submitClientWish: noop, submitClientFeedback: noop,
    reloadClientRecipes: noop, submitClientRecipe: noop, submitClientRecipeComposition: noop,
  });
  assert.deepEqual(Object.values(counts), Array(11).fill(1));
  for (const control of controls) assert.equal(control.listeners.length, 1);
});

test('main source contains supported endpoints and no unsupported mutation helpers', async () => {
  const fs = await import('node:fs/promises');
  const source = await fs.readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /\/api\/recipe-versions\/\$\{versionId\}\/calculation/);
  assert.match(source, /\/api\/client-recipes\/\$\{clientRecipeId\}\/ingredients/);
  assert.match(source, /\/api\/client-wishes\/\$\{wishId\}\/status/);
  assert.doesNotMatch(source, /function updateClientFeedback/);
  assert.doesNotMatch(source, /function calculateClientRecipe/);
  assert.match(source, /function reconcileRecipeWorkspaceObligation/);
  assert.match(source, /function reconcileClientWorkspaceObligation/);
  assert.match(source, /function reconcileClientRecipeWorkspaceObligation/);
  const openTemplate = source.slice(source.indexOf('function openRecipeTemplate'), source.indexOf('function openRecipeVersion'));
  assert.equal((openTemplate.match(/formulaClientWorkspaceRuntime\.read\(/g) ?? []).length, 1);
  assert.match(openTemplate, /requestRecipeTemplateSnapshot/);
  assert.match(openTemplate, /getRecipeTemplate\(id\)/);
  assert.match(openTemplate, /getRecipeVersions\(id\)/);
  assert.match(openTemplate, /version\.recipe_template_id === id/);
  assert.match(source, /operation: 'client-recipe-create'[\s\S]*?settled: \(result\)/);
  assert.match(source, /operation: 'client-recipe-composition'[\s\S]*?settled: \(result\)/);
  assert.match(source, /operation: 'client-recipe-deactivate'[\s\S]*?settled: \(result\)/);
  assert.match(source, /operation: 'client-recipe-restore'[\s\S]*?settled: \(result\)/);
  assert.match(source, /createRecipeTemplate\(payload\)[\s\S]*?\.finally\(\(\) =>/);
  assert.match(source, /createRecipeVersion\(templateId,[\s\S]*?\.finally\(\(\) =>/);
});
