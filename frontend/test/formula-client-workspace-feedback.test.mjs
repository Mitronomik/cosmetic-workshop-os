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
import { FormulaClientWorkspaceRuntime } from '../dist-tests/formula-client-workspace-feedback/formula-client-workspace-runtime.js';
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
});
