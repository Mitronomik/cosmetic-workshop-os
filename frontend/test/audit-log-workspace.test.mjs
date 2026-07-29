import test from 'node:test';
import assert from 'node:assert/strict';
import {
  EMPTY_AUDIT_LOG_FILTERS,
  FORBIDDEN_ITEM_KEYS,
  appendAuditLogPage,
  auditLogAllRowsLoaded,
  auditLogItemDtoIsValid,
  auditLogListDtoIsValid,
  auditLogRequestUrl,
  auditLogValidationIssue,
  canonicalUtcFromLocalInput,
} from '../dist-tests/audit-log-workspace/audit-log-contract.js';
import {
  AUDIT_LOG_ALL_LOADED,
  AUDIT_LOG_CLEAR_FILTERS_LABEL,
  AUDIT_LOG_EMPTY_TITLE,
  AUDIT_LOG_FILTERED_EMPTY_TITLE,
  AUDIT_LOG_INITIAL_FAILURE,
  AUDIT_LOG_LOAD_MORE_FAILURE,
  AUDIT_LOG_LOAD_MORE_LABEL,
  AUDIT_LOG_REFRESH_FAILURE,
  AUDIT_LOG_TITLE,
  auditLogPresentation,
  auditLogWorkspaceMarkup,
  formatAuditLogTimestamp,
} from '../dist-tests/audit-log-workspace/audit-log-presentation.js';
import { AuditLogWorkspaceRuntime } from '../dist-tests/audit-log-workspace/audit-log-workspace.js';
import { bindAuditLogWorkspaceControls } from '../dist-tests/audit-log-workspace/audit-log-bindings.js';
import { sectionForLocation } from '../dist-tests/audit-log-workspace/app-navigation-routes.js';

// --------------------------------------------------------------------------
// Minimal read-only view over rendered markup
// --------------------------------------------------------------------------

const voidTags = new Set(['br', 'hr', 'img', 'input', 'link', 'meta']);

class ViewNode {
  constructor(tag = '', attrs = {}, text = '') { this.tag = tag; this.attrs = attrs; this.children = []; this.text = text; }
  append(node) { this.children.push(node); }
  get textContent() { return this.tag === '#text' ? this.text : this.children.map((child) => child.textContent).join(''); }
  getAttribute(name) { return this.attrs[name] ?? null; }
  hasAttribute(name) { return Object.hasOwn(this.attrs, name); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  querySelectorAll(selector) {
    const found = [];
    const visit = (node) => { for (const child of node.children) { if (child.matches(selector)) found.push(child); visit(child); } };
    visit(this);
    return found;
  }
  matches(selector) {
    if (this.tag === '#text') return false;
    const match = selector.match(/^([a-z0-9-]+)?(?:\.([a-z0-9_-]+))?(?:\[([a-z0-9-]+)(?:="([^"]*)")?\])?$/i);
    if (!match) throw new Error(`Unsupported test selector: ${selector}`);
    const [, tag, className, attribute, value] = match;
    if (tag && this.tag !== tag.toLowerCase()) return false;
    if (className && !(this.attrs.class ?? '').split(/\s+/).includes(className)) return false;
    if (attribute && !this.hasAttribute(attribute)) return false;
    return value === undefined || this.attrs[attribute] === value;
  }
}

function decodeEntities(value) {
  return value.replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&quot;', '"').replaceAll('&#39;', "'").replaceAll('&amp;', '&');
}

function renderView(markup) {
  const root = new ViewNode('root');
  const stack = [root];
  for (const token of markup.match(/<[^>]+>|[^<]+/g) ?? []) {
    if (token.startsWith('</')) { stack.pop(); continue; }
    if (token.startsWith('<')) {
      const open = token.match(/^<([a-z0-9-]+)([^>]*)>/i);
      if (!open) continue;
      const tag = open[1].toLowerCase();
      const attrs = {};
      for (const attribute of open[2].matchAll(/([a-z0-9-]+)(?:="([^"]*)")?/gi)) attrs[attribute[1]] = decodeEntities(attribute[2] ?? '');
      const node = new ViewNode(tag, attrs);
      stack.at(-1).append(node);
      if (!voidTags.has(tag) && !token.endsWith('/>')) stack.push(node);
      continue;
    }
    stack.at(-1).append(new ViewNode('#text', {}, decodeEntities(token)));
  }
  return root;
}

const renderFeedback = (tone, message) => `<div data-feedback-tone="${tone}"><p>${message}</p></div>`;

// --------------------------------------------------------------------------
// Fixtures
// --------------------------------------------------------------------------

const flush = () => new Promise((resolve) => setImmediate(resolve));

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function item(overrides = {}) {
  return {
    id: 1,
    created_at: '2026-07-01T10:00:00Z',
    action: 'client.created',
    action_label: 'Клиент создан',
    entity_type: 'client',
    entity_label: 'Клиент',
    display_summary: 'Клиент создан: Анна Иванова',
    actor_type: 'system',
    actor_label: 'Система',
    ...overrides,
  };
}

const FILTER_OPTIONS = {
  actions: [
    { value: 'client.created', label: 'Клиент создан' },
    { value: 'client_wish.created', label: 'Пожелание клиента добавлено' },
  ],
  entity_types: [{ value: 'client', label: 'Клиент' }],
  actor_types: [
    { value: 'system', label: 'Система' },
    { value: 'user', label: 'Пользователь' },
  ],
};

function page(items, total = items.length, options = FILTER_OPTIONS) {
  return { items, total, limit: 50, offset: 0, filter_options: options };
}

function harness() {
  const state = { active: true, renders: 0, polite: [], assertive: [], urls: [], reads: [] };
  const runtime = new AuditLogWorkspaceRuntime({
    read: (url) => { state.urls.push(url); const d = deferred(); state.reads.push(d); return d.promise; },
    ownsRoute: () => state.active,
    render: () => { state.renders += 1; },
    announce: (message, kind) => state[kind === 'assertive' ? 'assertive' : 'polite'].push(message),
  });
  runtime.enter();
  return { state, runtime };
}

async function loaded(payload = page([item()])) {
  const { state, runtime } = harness();
  runtime.load();
  state.reads.at(-1).resolve(payload);
  await flush();
  return { state, runtime };
}

function view(runtime) {
  return auditLogPresentation(runtime.state);
}

function markupView(runtime) {
  return renderView(auditLogWorkspaceMarkup(view(runtime), renderFeedback));
}

// --------------------------------------------------------------------------
// Response validation
// --------------------------------------------------------------------------

test('a complete response with the exact nine item fields is accepted', () => {
  assert.equal(auditLogListDtoIsValid(page([item()])), true);
  assert.equal(auditLogItemDtoIsValid(item()), true);
  assert.equal(auditLogItemDtoIsValid(item({ entity_type: null })), true);
});

test('an item carrying any forbidden field is rejected outright', () => {
  for (const key of FORBIDDEN_ITEM_KEYS) {
    const poisoned = { ...item(), [key]: 'Client created: Анна Иванова' };
    assert.equal(auditLogItemDtoIsValid(poisoned), false, key);
    assert.equal(auditLogListDtoIsValid(page([poisoned])), false, key);
  }
});

test('a response missing a required field is rejected', () => {
  for (const key of ['items', 'total', 'limit', 'offset', 'filter_options']) {
    const payload = page([item()]);
    delete payload[key];
    assert.equal(auditLogListDtoIsValid(payload), false, key);
  }
  for (const key of Object.keys(item())) {
    const broken = item();
    delete broken[key];
    assert.equal(auditLogItemDtoIsValid(broken), false, key);
  }
});

test('a non-canonical timestamp or a non-integer counter is rejected', () => {
  assert.equal(auditLogItemDtoIsValid(item({ created_at: '2026-07-01 10:00:00' })), false);
  assert.equal(auditLogItemDtoIsValid(item({ created_at: '2026-07-01T10:00:00' })), false);
  assert.equal(auditLogItemDtoIsValid(item({ id: 1.5 })), false);
  assert.equal(auditLogListDtoIsValid({ ...page([item()]), total: -1 }), false);
});

test('a page claiming more rows than the total is rejected', () => {
  assert.equal(auditLogListDtoIsValid({ ...page([item(), item({ id: 2 })]), total: 1 }), false);
});

test('malformed filter options are rejected', () => {
  assert.equal(auditLogListDtoIsValid(page([item()], 1, { actions: [], entity_types: [] })), false);
  assert.equal(auditLogListDtoIsValid(page([item()], 1, { actions: [{ value: 'a' }], entity_types: [], actor_types: [] })), false);
});

// --------------------------------------------------------------------------
// Request building
// --------------------------------------------------------------------------

test('the request uses only the authorized parameter names', () => {
  const url = auditLogRequestUrl({ ...EMPTY_AUDIT_LOG_FILTERS, action: 'client.created', entityType: 'client', actorType: 'user' }, { limit: 50, offset: 0 });
  const parameters = new URLSearchParams(url.split('?')[1]);
  assert.deepEqual([...parameters.keys()].sort(), ['action', 'actor_type', 'entity_type', 'limit', 'offset']);
  assert.equal(parameters.get('action'), 'client.created');
  assert.equal(parameters.get('entity_type'), 'client');
  assert.equal(parameters.get('actor_type'), 'user');
});

test('no source filter and no free-text search parameter is ever sent', () => {
  const url = auditLogRequestUrl({ ...EMPTY_AUDIT_LOG_FILTERS, action: 'client.created' }, { limit: 50, offset: 0 });
  for (const forbidden of ['source', 'source_label', 'search', 'q', 'entity_id', 'metadata']) {
    assert.equal(url.includes(forbidden), false, forbidden);
  }
});

test('blank filters are omitted rather than sent empty', () => {
  const url = auditLogRequestUrl(EMPTY_AUDIT_LOG_FILTERS, { limit: 50, offset: 0 });
  assert.equal(url, '/api/audit-logs?limit=50&offset=0');
});

test('a local date is converted to the canonical backend UTC instant', () => {
  const converted = canonicalUtcFromLocalInput('2026-07-01T10:30');
  assert.match(converted, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
  const expected = new Date(2026, 6, 1, 10, 30, 0, 0).toISOString().replace(/\.\d{3}Z$/, 'Z');
  assert.equal(converted, expected);
});

test('an incomplete or impossible local date produces no parameter', () => {
  for (const value of ['', '2026-07', '2026-07-01', '01.07.2026 10:30', '2026-02-30T10:00']) {
    assert.equal(canonicalUtcFromLocalInput(value), null, value);
  }
  assert.equal(auditLogRequestUrl({ ...EMPTY_AUDIT_LOG_FILTERS, createdFrom: '2026-07' }, { limit: 50, offset: 0 }).includes('created_from'), false);
});

// --------------------------------------------------------------------------
// Structured backend rejections
// --------------------------------------------------------------------------

test('the structured 422 envelope is read, and anything else is not', () => {
  const issue = auditLogValidationIssue({
    status: 422,
    payload: { detail: { code: 'invalid_date', message: 'Конец периода должен быть позже его начала.', field: 'created_before', value: '2026-07-01T00:00:00Z', next_action: 'Выберите дату окончания позже даты начала.' } },
  });
  assert.equal(issue.code, 'invalid_date');
  assert.equal(issue.field, 'created_before');
  assert.equal(auditLogValidationIssue({ status: 500, payload: { detail: 'boom' } }), null);
  assert.equal(auditLogValidationIssue(new Error('network')), null);
  assert.equal(auditLogValidationIssue({ status: 422, payload: { detail: [{ loc: ['query', 'limit'], type: 'int_parsing' }] } }), null);
});

// --------------------------------------------------------------------------
// Route resolution
// --------------------------------------------------------------------------

test('the nested audit-log route resolves directly and is distinct from /settings', () => {
  assert.equal(sectionForLocation('/settings/audit-log'), 'Журнал действий');
  assert.equal(sectionForLocation('/settings/audit-log/'), 'Журнал действий');
  assert.equal(sectionForLocation('/settings'), 'Настройки');
  assert.equal(sectionForLocation('/settings/unknown'), 'Главная');
  assert.equal(sectionForLocation('/'), 'Главная');
  assert.equal(sectionForLocation('/reports'), 'Отчеты');
  assert.equal(sectionForLocation('/', '#help'), 'Помощь');
});

// --------------------------------------------------------------------------
// Read lifecycle
// --------------------------------------------------------------------------

test('the initial read requests the first page and shows a loading state', () => {
  const { state, runtime } = harness();
  runtime.load();
  assert.equal(state.urls.at(-1), '/api/audit-logs?limit=50&offset=0');
  assert.equal(view(runtime).listState, 'loading');
  assert.equal(view(runtime).busy, true);
});

test('a successful initial read renders the rows the backend sent', async () => {
  const { runtime } = await loaded(page([item(), item({ id: 2, display_summary: 'Компонент создан: Масло ши' })], 2));
  const presentation = view(runtime);
  assert.equal(presentation.listState, 'rows');
  assert.equal(presentation.rows.length, 2);
  assert.equal(presentation.rows[0].displaySummary, 'Клиент создан: Анна Иванова');
  assert.equal(presentation.allLoaded, true);
});

test('an empty database and a filtered-empty result are different states', async () => {
  const { runtime } = await loaded(page([], 0, { actions: [], entity_types: [], actor_types: [] }));
  assert.equal(view(runtime).listState, 'empty');

  const filtered = await loaded(page([]));
  filtered.runtime.setFilter('action', 'client.created');
  filtered.runtime.applyFilters();
  filtered.state.reads.at(-1).resolve(page([]));
  await flush();
  assert.equal(view(filtered.runtime).listState, 'filtered-empty');
});

test('an initial failure shows the retry path and no rows', async () => {
  const { state, runtime } = harness();
  runtime.load();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  const presentation = view(runtime);
  assert.equal(presentation.listState, 'error');
  assert.equal(presentation.initialError, AUDIT_LOG_INITIAL_FAILURE);
  assert.equal(state.assertive.at(-1), AUDIT_LOG_INITIAL_FAILURE);
});

test('retry after an initial failure succeeds', async () => {
  const { state, runtime } = harness();
  runtime.load();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  assert.equal(runtime.retry().accepted, true);
  state.reads.at(-1).resolve(page([item()]));
  await flush();
  assert.equal(view(runtime).listState, 'rows');
  assert.equal(view(runtime).initialError, '');
});

test('a refresh failure retains the previously accepted rows', async () => {
  const { state, runtime } = await loaded(page([item()]));
  runtime.refresh();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  const presentation = view(runtime);
  assert.equal(presentation.listState, 'rows');
  assert.equal(presentation.rows.length, 1);
  assert.equal(presentation.refreshError, AUDIT_LOG_REFRESH_FAILURE);
});

test('a successful refresh replaces the list and announces politely', async () => {
  const { state, runtime } = await loaded(page([item()]));
  runtime.refresh();
  state.reads.at(-1).resolve(page([item({ id: 9, display_summary: 'Заказ создан: Дневной крем' })]));
  await flush();
  assert.equal(view(runtime).rows.length, 1);
  assert.equal(view(runtime).rows[0].displaySummary, 'Заказ создан: Дневной крем');
  assert.equal(state.polite.at(-1), 'Журнал действий обновлён.');
});

test('a response failing validation takes the read-failure path', async () => {
  const { state, runtime } = await loaded(page([item()]));
  runtime.refresh();
  state.reads.at(-1).resolve(page([{ ...item(), summary: 'Client created: Анна Иванова' }]));
  await flush();
  assert.equal(view(runtime).rows.length, 1);
  assert.notEqual(view(runtime).refreshError, '');
});

// --------------------------------------------------------------------------
// Pagination
// --------------------------------------------------------------------------

test('load more requests the offset of the accepted row count and appends', async () => {
  const { state, runtime } = await loaded(page([item(), item({ id: 2 })], 4));
  assert.equal(view(runtime).canLoadMore, true);
  runtime.loadMore();
  assert.equal(state.urls.at(-1), '/api/audit-logs?limit=50&offset=2');
  state.reads.at(-1).resolve({ ...page([item({ id: 3 }), item({ id: 4 })], 4), offset: 2 });
  await flush();
  assert.deepEqual(view(runtime).rows.map((row) => row.id), [1, 2, 3, 4]);
  assert.equal(view(runtime).allLoaded, true);
  assert.equal(view(runtime).canLoadMore, false);
});

test('an overlapping page cannot produce a duplicate row identity', () => {
  const appended = appendAuditLogPage([item(), item({ id: 2 })], [item({ id: 2 }), item({ id: 3 })]);
  assert.deepEqual(appended.map((row) => row.id), [1, 2, 3]);
});

test('a load-more failure retains existing rows and allows retry', async () => {
  const { state, runtime } = await loaded(page([item()], 3));
  runtime.loadMore();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  assert.equal(view(runtime).rows.length, 1);
  assert.equal(view(runtime).loadMoreError, AUDIT_LOG_LOAD_MORE_FAILURE);
  assert.equal(view(runtime).canLoadMore, true);
  assert.equal(runtime.loadMore().accepted, true);
});

test('load more is refused once every matching row is loaded', async () => {
  const { runtime } = await loaded(page([item()], 1));
  assert.deepEqual(runtime.loadMore(), { accepted: false, reason: 'all-loaded' });
  assert.equal(auditLogAllRowsLoaded(1, 1), true);
  assert.equal(auditLogAllRowsLoaded(1, 2), false);
});

test('a duplicate load-more request is blocked while one is in flight', async () => {
  const { state, runtime } = await loaded(page([item()], 5));
  assert.equal(runtime.loadMore().accepted, true);
  assert.deepEqual(runtime.loadMore(), { accepted: false, reason: 'busy' });
  assert.equal(state.reads.length, 2);
});

test('a duplicate refresh is blocked while one is in flight', async () => {
  const { state, runtime } = await loaded();
  assert.equal(runtime.refresh().accepted, true);
  assert.deepEqual(runtime.refresh(), { accepted: false, reason: 'busy' });
  assert.equal(state.reads.length, 2);
});

// --------------------------------------------------------------------------
// Filters and stale responses
// --------------------------------------------------------------------------

test('changing a filter resets the offset and starts a new authoritative request', async () => {
  const { state, runtime } = await loaded(page([item(), item({ id: 2 })], 9));
  runtime.loadMore();
  state.reads.at(-1).resolve({ ...page([item({ id: 3 })], 9), offset: 2 });
  await flush();
  assert.equal(view(runtime).rows.length, 3);

  runtime.setFilter('actorType', 'user');
  runtime.applyFilters();
  assert.equal(state.urls.at(-1), '/api/audit-logs?actor_type=user&limit=50&offset=0');
  state.reads.at(-1).resolve(page([item({ id: 7, actor_label: 'Пользователь' })], 1));
  await flush();
  assert.deepEqual(view(runtime).rows.map((row) => row.id), [7]);
});

test('a stale filter response cannot overwrite a newer result', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('action', 'client.created');
  runtime.applyFilters();
  const stale = state.reads.at(-1);
  runtime.setFilter('action', 'client_wish.created');
  runtime.applyFilters();
  const current = state.reads.at(-1);

  current.resolve(page([item({ id: 5, display_summary: 'Пожелание клиента добавлено' })], 1));
  await flush();
  stale.resolve(page([item({ id: 99, display_summary: 'Клиент создан: Анна Иванова' })], 1));
  await flush();

  assert.deepEqual(view(runtime).rows.map((row) => row.id), [5]);
});

test('a stale failure cannot clear a newer accepted list', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.applyFilters();
  const stale = state.reads.at(-1);
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 4 })], 1));
  await flush();
  stale.reject(new Error('offline'));
  await flush();
  assert.deepEqual(view(runtime).rows.map((row) => row.id), [4]);
  assert.equal(view(runtime).refreshError, '');
});

test('clearing filters resets every control and reloads', async () => {
  const { state, runtime } = await loaded();
  runtime.setFilter('action', 'client.created');
  runtime.setFilter('createdFrom', '2026-07-01T10:00');
  assert.equal(view(runtime).filtersActive, true);
  runtime.clearFilters();
  assert.deepEqual(runtime.state.filters, EMPTY_AUDIT_LOG_FILTERS);
  assert.equal(state.urls.at(-1), '/api/audit-logs?limit=50&offset=0');
});

test('a structured date-range rejection is attached to the end-date control', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('createdFrom', '2026-07-05T00:00');
  runtime.setFilter('createdBefore', '2026-07-01T00:00');
  runtime.applyFilters();
  state.reads.at(-1).reject({
    status: 422,
    payload: { detail: { code: 'invalid_date', message: 'Конец периода должен быть позже его начала.', field: 'created_before', value: '2026-07-01T00:00:00Z', next_action: 'Выберите дату окончания позже даты начала.' } },
  });
  await flush();
  const presentation = view(runtime);
  assert.equal(presentation.fieldErrors.createdFrom, '');
  assert.match(presentation.fieldErrors.createdBefore, /Конец периода должен быть позже его начала\./);
  assert.match(presentation.fieldErrors.createdBefore, /Выберите дату окончания позже даты начала\./);
  assert.equal(presentation.rows.length, 1);
  assert.equal(presentation.refreshError, '');
});

test('a pagination rejection is reported without touching a date control', async () => {
  const { state, runtime } = harness();
  runtime.load();
  state.reads.at(-1).reject({ status: 422, payload: { detail: { code: 'pagination_out_of_range', message: 'Количество записей вне допустимого диапазона.', field: 'limit', value: '0', next_action: 'Укажите количество записей от 1 до 200.' } } });
  await flush();
  assert.equal(view(runtime).fieldErrors.createdBefore, '');
  assert.equal(view(runtime).initialError, 'Количество записей вне допустимого диапазона.');
});

// --------------------------------------------------------------------------
// Rendered markup
// --------------------------------------------------------------------------

test('the workspace renders the stable page and list contracts', async () => {
  const { runtime } = await loaded(page([item()], 5));
  const root = markupView(runtime);
  assert.ok(root.querySelector('[data-page="audit-log"]'));
  assert.ok(root.querySelector('[data-audit-log-list]'));
  assert.ok(root.querySelector('[data-audit-log-filters]'));
  assert.equal(root.querySelector('[data-audit-log-row]').getAttribute('data-audit-log-id'), '1');
  for (const filter of ['action', 'entity-type', 'actor-type', 'created-from', 'created-before']) {
    assert.ok(root.querySelector(`[data-audit-log-filter="${filter}"]`), filter);
  }
  for (const action of ['refresh-audit-log', 'clear-audit-log-filters', 'load-more-audit-log']) {
    assert.ok(root.querySelector(`[data-action="${action}"]`), action);
  }
});

test('the workspace renders the backend labels and summary verbatim', async () => {
  const { runtime } = await loaded(page([item()], 1));
  const root = markupView(runtime);
  assert.equal(root.querySelector('[data-audit-log-summary]').textContent, 'Клиент создан: Анна Иванова');
  assert.equal(root.querySelector('[data-audit-log-action]').textContent, 'Клиент создан');
  assert.equal(root.querySelector('[data-audit-log-entity]').textContent, 'Клиент');
  assert.equal(root.querySelector('[data-audit-log-actor]').textContent, 'Система');
  assert.equal(root.textContent.includes(AUDIT_LOG_TITLE), true);
});

test('no raw code, raw summary, metadata or internal id is ever visible', async () => {
  const { runtime } = await loaded(page([
    item({ id: 42, action: 'ingredient_lot.created', action_label: 'Партия компонента создана', entity_type: 'ingredient_lot', entity_label: 'Партия компонента', display_summary: 'Создана партия компонента' }),
  ], 1));
  const root = markupView(runtime);
  const visible = root.textContent;
  for (const forbidden of ['ingredient_lot.created', 'ingredient_lot', 'client.created', 'Ingredient lot created', 'metadata_json', 'entity_id', 'audit_logs', '#12', 'SELECT', 'source_label']) {
    assert.equal(visible.includes(forbidden), false, forbidden);
  }
  // The row id survives only as DOM identity, never as visible text.
  assert.equal(root.querySelector('[data-audit-log-row]').getAttribute('data-audit-log-id'), '42');
  assert.equal(visible.includes('42'), false);
});

test('raw codes are used as select values while only labels are displayed', async () => {
  const { runtime } = await loaded(page([item()], 1));
  const root = markupView(runtime);
  const options = root.querySelector('[data-audit-log-filter="action"]').querySelectorAll('option');
  assert.deepEqual(options.map((option) => option.getAttribute('value')), ['', 'client.created', 'client_wish.created']);
  assert.deepEqual(options.map((option) => option.textContent), ['Любое', 'Клиент создан', 'Пожелание клиента добавлено']);
});

test('each list state renders its own stable marker', async () => {
  const empty = await loaded(page([], 0, { actions: [], entity_types: [], actor_types: [] }));
  assert.ok(markupView(empty.runtime).querySelector('[data-state="audit-log-empty"]'));
  assert.equal(markupView(empty.runtime).textContent.includes(AUDIT_LOG_EMPTY_TITLE), true);

  const filtered = await loaded(page([]));
  filtered.runtime.setFilter('action', 'client.created');
  filtered.runtime.applyFilters();
  filtered.state.reads.at(-1).resolve(page([]));
  await flush();
  const filteredRoot = markupView(filtered.runtime);
  assert.ok(filteredRoot.querySelector('[data-state="audit-log-filtered-empty"]'));
  assert.equal(filteredRoot.textContent.includes(AUDIT_LOG_FILTERED_EMPTY_TITLE), true);
  assert.ok(filteredRoot.querySelector('[data-action="clear-audit-log-filters"]'));

  const failed = harness();
  failed.runtime.load();
  failed.state.reads.at(-1).reject(new Error('offline'));
  await flush();
  const failedRoot = markupView(failed.runtime);
  assert.ok(failedRoot.querySelector('[data-state="audit-log-error"]'));
  assert.ok(failedRoot.querySelector('[data-action="retry-audit-log"]'));
});

test('the load-more control is bounded by the backend total', async () => {
  const partial = await loaded(page([item()], 5));
  const partialRoot = markupView(partial.runtime);
  assert.equal(partialRoot.querySelector('[data-action="load-more-audit-log"]').hasAttribute('disabled'), false);
  assert.equal(partialRoot.textContent.includes(AUDIT_LOG_LOAD_MORE_LABEL), true);

  const complete = await loaded(page([item()], 1));
  const completeRoot = markupView(complete.runtime);
  assert.equal(completeRoot.querySelector('[data-action="load-more-audit-log"]'), null);
  assert.ok(completeRoot.querySelector('[data-state="audit-log-all-loaded"]'));
  assert.equal(completeRoot.textContent.includes(AUDIT_LOG_ALL_LOADED), true);
});

test('accessible names, labels and busy state are present', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.refresh();
  const root = markupView(runtime);
  assert.equal(root.querySelector('[data-form="audit-log-filters"]').getAttribute('aria-busy'), 'true');
  assert.equal(root.querySelector('[data-audit-log-list]').getAttribute('aria-busy'), 'true');
  assert.ok(root.querySelector('fieldset'));
  assert.ok(root.querySelector('legend'));
  for (const id of ['audit-log-created-from', 'audit-log-created-before', 'audit-log-action', 'audit-log-entity-type', 'audit-log-actor-type']) {
    const label = root.querySelectorAll('label').find((node) => node.getAttribute('for') === id);
    assert.ok(label && label.textContent.trim(), id);
  }
  for (const control of root.querySelectorAll('[data-audit-log-filter]')) {
    assert.equal(control.hasAttribute('disabled'), true);
  }
  for (const button of root.querySelectorAll('button')) {
    assert.ok(button.textContent.trim(), 'every button needs an accessible name');
  }
  state.active = true;
});

test('an invalid date control is marked and described by its own error', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.applyFilters();
  state.reads.at(-1).reject({ status: 422, payload: { detail: { code: 'invalid_date', message: 'Конец периода должен быть позже его начала.', field: 'created_before', value: 'x', next_action: 'Выберите дату окончания позже даты начала.' } } });
  await flush();
  const root = markupView(runtime);
  const control = root.querySelector('[data-audit-log-filter="created-before"]');
  assert.equal(control.getAttribute('aria-invalid'), 'true');
  assert.equal(control.getAttribute('aria-describedby'), 'audit-log-created-before-error');
  const error = root.querySelector('[data-audit-log-field-error="created-before"]');
  assert.equal(error.getAttribute('role'), 'alert');
  assert.equal(error.hasAttribute('hidden'), false);
  assert.equal(root.querySelector('[data-audit-log-field-error="created-from"]').hasAttribute('hidden'), true);
});

test('long summaries and labels are rendered as escaped plain text', () => {
  const markup = auditLogWorkspaceMarkup(
    auditLogPresentation({
      status: 'ready', activeKind: null, items: [item({ display_summary: 'Клиент создан: <script>alert("x")</script>' })],
      total: 1, filterOptions: FILTER_OPTIONS, filters: { ...EMPTY_AUDIT_LOG_FILTERS }, appliedFilters: { ...EMPTY_AUDIT_LOG_FILTERS },
      loaded: true, initialError: '', refreshError: '', loadMoreError: '', fieldErrors: { createdFrom: '', createdBefore: '' },
    }),
    renderFeedback,
  );
  assert.equal(markup.includes('<script>'), false);
  assert.equal(markup.includes('&lt;script&gt;'), true);
});

test('an unreadable timestamp degrades to a dash rather than raw text', () => {
  assert.equal(formatAuditLogTimestamp('not-a-date'), '—');
  assert.notEqual(formatAuditLogTimestamp('2026-07-01T10:00:00Z'), '2026-07-01T10:00:00Z');
});

// --------------------------------------------------------------------------
// Bindings
// --------------------------------------------------------------------------

class Control {
  constructor(attrs) { this.attrs = attrs; this.listeners = {}; this.value = ''; this.dataset = { auditLogFilter: attrs['data-audit-log-filter'] }; }
  addEventListener(type, handler) { (this.listeners[type] ??= []).push(handler); }
  fire(type, event = { preventDefault() {} }) { for (const handler of this.listeners[type] ?? []) handler(event); }
}

class StrictRoot {
  constructor(controls) { this.controls = controls; }
  matches(control, selector) {
    const withValue = [...selector.matchAll(/\[([^=\]]+)="([^"]+)"\]/g)].map(([, key, value]) => [key, value]);
    const bare = [...selector.matchAll(/\[([a-z-]+)\]/g)].map(([, key]) => key);
    if (withValue.length) return withValue.every(([key, value]) => control.attrs[key] === value);
    return bare.length > 0 && bare.every((key) => key in control.attrs);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  querySelectorAll(selector) { return this.controls.filter((control) => this.matches(control, selector)); }
}

test('every stable control is wired to its own runtime action exactly once', () => {
  const refresh = new Control({ 'data-action': 'refresh-audit-log' });
  const retry = new Control({ 'data-action': 'retry-audit-log' });
  const loadMore = new Control({ 'data-action': 'load-more-audit-log' });
  const clear = new Control({ 'data-action': 'clear-audit-log-filters' });
  const clearInEmptyState = new Control({ 'data-action': 'clear-audit-log-filters' });
  const form = new Control({ 'data-form': 'audit-log-filters' });
  const actionFilter = new Control({ 'data-audit-log-filter': 'action' });
  const endDate = new Control({ 'data-audit-log-filter': 'created-before' });
  const unrelated = new Control({ 'data-action': 'refresh-reports' });

  const calls = [];
  bindAuditLogWorkspaceControls(new StrictRoot([refresh, retry, loadMore, clear, clearInEmptyState, form, actionFilter, endDate, unrelated]), {
    refresh: () => calls.push('refresh'),
    retry: () => calls.push('retry'),
    loadMore: () => calls.push('load-more'),
    clearFilters: () => calls.push('clear'),
    applyFilters: () => calls.push('apply'),
    setFilter: (name, value) => calls.push(`set:${name}=${value}`),
  });

  refresh.fire('click');
  retry.fire('click');
  loadMore.fire('click');
  clear.fire('click');
  clearInEmptyState.fire('click');
  actionFilter.value = 'client.created';
  actionFilter.fire('change');
  endDate.value = '2026-07-01T10:00';
  endDate.fire('change');
  unrelated.fire('click');

  assert.deepEqual(calls, ['refresh', 'retry', 'load-more', 'clear', 'clear', 'set:action=client.created', 'set:createdBefore=2026-07-01T10:00']);
});

test('submitting the filter form applies filters and prevents navigation', () => {
  const form = new Control({ 'data-form': 'audit-log-filters' });
  const calls = [];
  let prevented = false;
  bindAuditLogWorkspaceControls(new StrictRoot([form]), {
    refresh: () => {}, retry: () => {}, loadMore: () => {}, clearFilters: () => {},
    applyFilters: () => calls.push('apply'), setFilter: () => {},
  });
  form.fire('submit', { preventDefault() { prevented = true; } });
  assert.deepEqual(calls, ['apply']);
  assert.equal(prevented, true);
});
