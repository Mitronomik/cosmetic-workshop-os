import test from 'node:test';
import assert from 'node:assert/strict';
import {
  EMPTY_AUDIT_LOG_FILTERS,
  FORBIDDEN_ITEM_KEYS,
  appendAuditLogPage,
  auditLogAllRowsLoaded,
  auditLogFiltersEqual,
  auditLogItemDtoIsValid,
  auditLogListDtoIsValid,
  auditLogRequestPlan,
  auditLogValidationIssue,
} from '../dist-tests/audit-log-workspace/audit-log-contract.js';
import {
  AMBIGUOUS_LOCAL_TIME_MESSAGE,
  INVALID_LOCAL_TIME_MESSAGE,
  NONEXISTENT_LOCAL_TIME_MESSAGE,
  convertLocalInputToUtc,
} from '../dist-tests/audit-log-workspace/audit-log-local-time.js';
import {
  AUDIT_LOG_ALL_LOADED,
  AUDIT_LOG_EMPTY_TITLE,
  AUDIT_LOG_FILTERED_EMPTY_TITLE,
  AUDIT_LOG_FILTERS_PENDING,
  AUDIT_LOG_INITIAL_FAILURE,
  AUDIT_LOG_LOAD_MORE_FAILURE,
  AUDIT_LOG_LOAD_MORE_LABEL,
  AUDIT_LOG_REFRESH_FAILURE,
  AUDIT_LOG_FILTER_FAILURE,
  AUDIT_LOG_TITLE,
  auditLogPresentation,
  auditLogWorkspaceMarkup,
  formatAuditLogTimestamp,
} from '../dist-tests/audit-log-workspace/audit-log-presentation.js';
import { AuditLogWorkspaceRuntime } from '../dist-tests/audit-log-workspace/audit-log-workspace.js';
import { bindAuditLogWorkspaceControls } from '../dist-tests/audit-log-workspace/audit-log-bindings.js';
import { renderAuditLogWithFocus, syncAuditLogFilterState } from '../dist-tests/audit-log-workspace/audit-log-dom.js';
import { sectionForLocation } from '../dist-tests/audit-log-workspace/app-navigation-routes.js';

// --------------------------------------------------------------------------
// Minimal read-only view over rendered markup
//
// Extended into a small mutable fake DOM so the targeted-update and focus
// modules can be exercised against the *real* rendered markup rather than a
// hand-built fixture that could drift from it.
// --------------------------------------------------------------------------

const voidTags = new Set(['br', 'hr', 'img', 'input', 'link', 'meta']);

/** The single fake document the focus module reads `activeElement` from. */
const fakeDocument = { activeElement: null };

class ViewNode {
  constructor(tag = '', attrs = {}, text = '') {
    this.tag = tag;
    this.attrs = attrs;
    this.children = [];
    this.text = text;
    this.parent = null;
  }
  get tagName() { return this.tag.toUpperCase(); }
  get disabled() { return Object.hasOwn(this.attrs, 'disabled'); }
  set disabled(value) { if (value) this.attrs.disabled = ''; else delete this.attrs.disabled; }
  append(node) { node.parent = this; this.children.push(node); }
  get textContent() { return this.tag === '#text' ? this.text : this.children.map((child) => child.textContent).join(''); }
  set textContent(value) { this.children = [new ViewNode('#text', {}, value)]; }
  getAttribute(name) { return this.attrs[name] ?? null; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  removeAttribute(name) { delete this.attrs[name]; }
  hasAttribute(name) { return Object.hasOwn(this.attrs, name); }
  contains(node) { for (let cursor = node; cursor; cursor = cursor.parent) if (cursor === this) return true; return false; }
  focus() { fakeDocument.activeElement = this; }
  get selectionStart() { return this.tag === 'input' ? (this._selectionStart ?? 0) : undefined; }
  get selectionEnd() { return this.tag === 'input' ? (this._selectionEnd ?? 0) : undefined; }
  setSelectionRange(start, end) { this._selectionStart = start; this._selectionEnd = end; }
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

/**
 * Run `fn` with a pinned host time zone.
 *
 * DST behavior is a property of the zone, so an assertion about a spring gap is
 * meaningless unless the zone is stated. Pinning it here — rather than relying
 * on how the suite was invoked — makes these tests deterministic under both the
 * default run and the mandatory `TZ=Europe/Amsterdam` run, with no skips.
 */
function withTimeZone(timeZone, fn) {
  const previous = process.env.TZ;
  process.env.TZ = timeZone;
  try {
    return fn();
  } finally {
    if (previous === undefined) delete process.env.TZ;
    else process.env.TZ = previous;
  }
}

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
  const state = { active: true, renders: 0, syncs: [], polite: [], assertive: [], urls: [], reads: [] };
  const runtime = new AuditLogWorkspaceRuntime({
    read: (url) => { state.urls.push(url); const d = deferred(); state.reads.push(d); return d.promise; },
    ownsRoute: () => state.active,
    render: () => { state.renders += 1; },
    announce: (message, kind) => state[kind === 'assertive' ? 'assertive' : 'polite'].push(message),
    syncFilters: (sync) => state.syncs.push(sync),
  });
  return { state, runtime };
}

async function loaded(payload = page([item()])) {
  const { state, runtime } = harness();
  runtime.enter();
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

function queryOf(url) {
  return new URLSearchParams(url.split('?')[1] ?? '');
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
  const plan = auditLogRequestPlan({ ...EMPTY_AUDIT_LOG_FILTERS, action: 'client.created', entityType: 'client', actorType: 'user' }, { limit: 50, offset: 0 });
  assert.equal(plan.ok, true);
  const parameters = queryOf(plan.url);
  assert.deepEqual([...parameters.keys()].sort(), ['action', 'actor_type', 'entity_type', 'limit', 'offset']);
  assert.equal(parameters.get('action'), 'client.created');
  assert.equal(parameters.get('entity_type'), 'client');
  assert.equal(parameters.get('actor_type'), 'user');
});

test('no source filter and no free-text search parameter is ever sent', () => {
  const plan = auditLogRequestPlan({ ...EMPTY_AUDIT_LOG_FILTERS, action: 'client.created' }, { limit: 50, offset: 0 });
  for (const forbidden of ['source', 'source_label', 'search', 'q', 'entity_id', 'metadata']) {
    assert.equal(plan.url.includes(forbidden), false, forbidden);
  }
});

test('blank filters are omitted rather than sent empty', () => {
  const plan = auditLogRequestPlan(EMPTY_AUDIT_LOG_FILTERS, { limit: 50, offset: 0 });
  assert.deepEqual(plan, { ok: true, url: '/api/audit-logs?limit=50&offset=0' });
});

test('filters are compared field by field, not by identity', () => {
  const left = { ...EMPTY_AUDIT_LOG_FILTERS, action: 'client.created' };
  assert.equal(auditLogFiltersEqual(left, { ...left }), true);
  assert.equal(auditLogFiltersEqual(left, { ...left, action: 'other' }), false);
  assert.equal(auditLogFiltersEqual(EMPTY_AUDIT_LOG_FILTERS, { ...EMPTY_AUDIT_LOG_FILTERS }), true);
});

// --------------------------------------------------------------------------
// Local time conversion and DST safety
// --------------------------------------------------------------------------

test('a blank date is a valid "no filter" conversion', () => {
  assert.deepEqual(convertLocalInputToUtc(''), { ok: true, value: '' });
  assert.deepEqual(convertLocalInputToUtc('   '), { ok: true, value: '' });
});

test('an impossible or incomplete local date is rejected, never normalized', () => {
  for (const value of ['2026-02-30T10:00', '2026-13-01T10:00', '2026-07', '2026-07-01', '01.07.2026 10:30', 'nonsense']) {
    const result = convertLocalInputToUtc(value);
    assert.equal(result.ok, false, value);
    assert.equal(result.reason, 'invalid', value);
    assert.equal(result.message, INVALID_LOCAL_TIME_MESSAGE);
  }
});

test('Europe/Amsterdam spring gap: 02:30 does not exist and is rejected', () => {
  withTimeZone('Europe/Amsterdam', () => {
    assert.deepEqual(convertLocalInputToUtc('2026-03-29T01:30'), { ok: true, value: '2026-03-29T00:30:00Z' });

    const gap = convertLocalInputToUtc('2026-03-29T02:30');
    assert.equal(gap.ok, false);
    assert.equal(gap.reason, 'nonexistent-local-time');
    assert.equal(gap.message, NONEXISTENT_LOCAL_TIME_MESSAGE);

    assert.deepEqual(convertLocalInputToUtc('2026-03-29T03:30'), { ok: true, value: '2026-03-29T01:30:00Z' });
  });
});

test('Europe/Amsterdam autumn overlap: 02:30 happens twice and is rejected', () => {
  withTimeZone('Europe/Amsterdam', () => {
    assert.deepEqual(convertLocalInputToUtc('2026-10-25T01:30'), { ok: true, value: '2026-10-24T23:30:00Z' });

    const overlap = convertLocalInputToUtc('2026-10-25T02:30');
    assert.equal(overlap.ok, false);
    assert.equal(overlap.reason, 'ambiguous-local-time');
    assert.equal(overlap.message, AMBIGUOUS_LOCAL_TIME_MESSAGE);

    assert.deepEqual(convertLocalInputToUtc('2026-10-25T03:30'), { ok: true, value: '2026-10-25T02:30:00Z' });
  });
});

test('an explicit seconds component is preserved through conversion', () => {
  withTimeZone('Europe/Amsterdam', () => {
    assert.deepEqual(convertLocalInputToUtc('2026-07-01T10:30:45'), { ok: true, value: '2026-07-01T08:30:45Z' });
  });
  withTimeZone('UTC', () => {
    assert.deepEqual(convertLocalInputToUtc('2026-07-01T10:30:45'), { ok: true, value: '2026-07-01T10:30:45Z' });
  });
});

test('a zone without a transition accepts every hour around the same dates', () => {
  withTimeZone('UTC', () => {
    for (const value of ['2026-03-29T02:30', '2026-10-25T02:30']) {
      assert.equal(convertLocalInputToUtc(value).ok, true, value);
    }
  });
});

test('a failed conversion refuses the request instead of dropping the filter', () => {
  withTimeZone('Europe/Amsterdam', () => {
    const plan = auditLogRequestPlan({ ...EMPTY_AUDIT_LOG_FILTERS, createdFrom: '2026-03-29T02:30' }, { limit: 50, offset: 0 });
    assert.equal(plan.ok, false);
    assert.equal(plan.fieldErrors.createdFrom, NONEXISTENT_LOCAL_TIME_MESSAGE);
    assert.equal(plan.fieldErrors.createdBefore, '');
  });
});

test('each date control reports its own conversion failure', () => {
  withTimeZone('Europe/Amsterdam', () => {
    const plan = auditLogRequestPlan(
      { ...EMPTY_AUDIT_LOG_FILTERS, createdFrom: '2026-10-25T02:30', createdBefore: '2026-03-29T02:30' },
      { limit: 50, offset: 0 },
    );
    assert.equal(plan.ok, false);
    assert.equal(plan.fieldErrors.createdFrom, AMBIGUOUS_LOCAL_TIME_MESSAGE);
    assert.equal(plan.fieldErrors.createdBefore, NONEXISTENT_LOCAL_TIME_MESSAGE);
  });
});

test('a locally impossible date starts no request and keeps the accepted list', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  const requestsBefore = state.reads.length;
  withTimeZone('Europe/Amsterdam', () => {
    runtime.setFilter('createdBefore', '2026-03-29T02:30');
    const started = runtime.applyFilters();
    assert.deepEqual(started, { accepted: false, reason: 'invalid-local-time' });
  });
  assert.equal(state.reads.length, requestsBefore, 'no network request may be issued');
  const presentation = view(runtime);
  assert.equal(presentation.fieldErrors.createdBefore, NONEXISTENT_LOCAL_TIME_MESSAGE);
  assert.equal(presentation.rows.length, 1);
  assert.deepEqual(runtime.state.appliedFilters, EMPTY_AUDIT_LOG_FILTERS);
  assert.equal(runtime.state.draftFilters.createdBefore, '2026-03-29T02:30', 'the draft value is kept so the user can correct it');
  assert.equal(state.assertive.at(-1), NONEXISTENT_LOCAL_TIME_MESSAGE);
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
// Route entry and re-entry
// --------------------------------------------------------------------------

test('first entry issues the initial request and shows the loading state', () => {
  const { state, runtime } = harness();
  const started = runtime.enter();
  assert.equal(started.accepted, true);
  assert.equal(started.kind, 'initial');
  assert.equal(state.urls.at(-1), '/api/audit-logs?limit=50&offset=0');
  assert.equal(view(runtime).listState, 'loading');
});

test('re-entry with accepted data automatically refreshes instead of doing nothing', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.leave();
  const started = runtime.enter();
  assert.equal(started.accepted, true);
  assert.equal(started.kind, 'refresh', 're-entry must refresh, not sit on stale data');
  assert.equal(state.urls.at(-1), '/api/audit-logs?limit=50&offset=0');
  // Rows stay visible while the refresh is in flight.
  assert.equal(view(runtime).rows.length, 1);
  assert.equal(view(runtime).listState, 'rows');
});

test('a successful re-entry refresh replaces the accepted rows', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.leave();
  runtime.enter();
  state.reads.at(-1).resolve(page([item({ id: 2, display_summary: 'Заказ создан: Дневной крем' }), item({ id: 1 })], 2));
  await flush();
  assert.deepEqual(view(runtime).rows.map((row) => row.id), [2, 1]);
  assert.equal(view(runtime).rows[0].displaySummary, 'Заказ создан: Дневной крем');
});

test('a failed re-entry refresh keeps the previous rows and shows the refresh warning', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.leave();
  runtime.enter();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  const presentation = view(runtime);
  assert.equal(presentation.listState, 'rows', 'never the initial-failure screen');
  assert.equal(presentation.rows.length, 1);
  assert.equal(presentation.refreshError, AUDIT_LOG_REFRESH_FAILURE);
  assert.equal(presentation.initialError, '');
});

test('re-entry after an initial failure with no data starts a new initial request', async () => {
  const { state, runtime } = harness();
  runtime.enter();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  assert.equal(view(runtime).listState, 'error');
  runtime.leave();
  const started = runtime.enter();
  assert.equal(started.kind, 'initial');
  state.reads.at(-1).resolve(page([item()], 1));
  await flush();
  assert.equal(view(runtime).listState, 'rows');
});

test('leaving during a request prevents its response from settling anything', async () => {
  const { state, runtime } = harness();
  runtime.enter();
  runtime.leave();
  state.reads.at(-1).resolve(page([item()], 1));
  await flush();
  assert.equal(runtime.state.items.length, 0);
  assert.equal(runtime.state.loaded, false);
});

test('after leaving and re-entering, only the new response is authoritative', async () => {
  const { state, runtime } = harness();
  runtime.enter();
  const abandoned = state.reads.at(-1);
  runtime.leave();
  runtime.enter();
  const current = state.reads.at(-1);

  current.resolve(page([item({ id: 5 })], 1));
  await flush();
  abandoned.resolve(page([item({ id: 99 })], 1));
  await flush();

  assert.deepEqual(view(runtime).rows.map((row) => row.id), [5]);
});

test('a duplicate route entry during an active request creates no second request', () => {
  const { state, runtime } = harness();
  assert.equal(runtime.enter().accepted, true);
  assert.deepEqual(runtime.enter(), { accepted: false, reason: 'busy' });
  assert.deepEqual(runtime.enter(), { accepted: false, reason: 'busy' });
  assert.equal(state.reads.length, 1);
});

test('leaving preserves rows, draft filters and applied filters for the next visit', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('action', 'client.created');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 3 })], 1));
  await flush();
  runtime.setFilter('actorType', 'user');

  runtime.leave();
  assert.equal(runtime.state.items.length, 1);
  assert.equal(runtime.state.appliedFilters.action, 'client.created');
  assert.equal(runtime.state.draftFilters.actorType, 'user');
});

// --------------------------------------------------------------------------
// Draft versus applied filters
// --------------------------------------------------------------------------

test('editing a control changes only the draft: no request, no rows, no applied change', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  const requestsBefore = state.reads.length;
  const rendersBefore = state.renders;

  runtime.setFilter('action', 'client_wish.created');

  assert.equal(state.reads.length, requestsBefore, 'editing must start no request');
  assert.equal(state.renders, rendersBefore, 'editing must not trigger a full render');
  assert.equal(runtime.state.draftFilters.action, 'client_wish.created');
  assert.deepEqual(runtime.state.appliedFilters, EMPTY_AUDIT_LOG_FILTERS);
  assert.equal(view(runtime).rows.length, 1);
  assert.equal(runtime.filtersDirty(), true);
});

test('a draft edit reports its consequences through a targeted sync, not a render', async () => {
  const { state, runtime } = await loaded(page([item()], 5));
  state.syncs.length = 0;
  runtime.setFilter('action', 'client.created');
  assert.equal(state.syncs.length, 1);
  assert.deepEqual(state.syncs[0], {
    filtersDirty: true,
    fieldErrors: { createdFrom: '', createdBefore: '' },
    canLoadMore: false,
  });
});

test('manual refresh uses the applied filters, never an unapplied draft', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('action', 'client.created');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 2 })], 1));
  await flush();

  runtime.setFilter('action', 'client_wish.created');
  runtime.refresh();

  assert.equal(queryOf(state.urls.at(-1)).get('action'), 'client.created');
  assert.equal(runtime.state.draftFilters.action, 'client_wish.created', 'the control keeps showing the pending choice');
});

test('re-entry refresh uses the applied filters, never an unapplied draft', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('actorType', 'user');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 2 })], 1));
  await flush();

  runtime.setFilter('actorType', 'system');
  runtime.leave();
  runtime.enter();

  assert.equal(queryOf(state.urls.at(-1)).get('actor_type'), 'user');
});

test('load more uses the applied filters and the accepted row count as offset', async () => {
  const { state, runtime } = await loaded(page([item(), item({ id: 2 })], 9));
  runtime.setFilter('action', 'client.created');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 3 }), item({ id: 4 })], 9));
  await flush();

  runtime.loadMore();
  const query = queryOf(state.urls.at(-1));
  assert.equal(query.get('action'), 'client.created');
  assert.equal(query.get('offset'), '2');
});

test('explicit apply uses the draft filters and adopts them only after success', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('entityType', 'client');
  const started = runtime.applyFilters();
  assert.equal(started.accepted, true);
  assert.equal(queryOf(state.urls.at(-1)).get('entity_type'), 'client');
  assert.deepEqual(runtime.state.appliedFilters, EMPTY_AUDIT_LOG_FILTERS, 'not adopted while in flight');

  state.reads.at(-1).resolve(page([item({ id: 7 })], 1));
  await flush();
  assert.equal(runtime.state.appliedFilters.entityType, 'client');
  assert.equal(runtime.state.draftFilters.entityType, 'client');
  assert.equal(runtime.filtersDirty(), false);
  assert.equal(view(runtime).filtersDirty, false);
});

test('a failed apply keeps the previous applied filters, rows and draft controls', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('action', 'client.created');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 2 })], 1));
  await flush();

  runtime.setFilter('action', 'client_wish.created');
  runtime.applyFilters();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();

  assert.equal(runtime.state.appliedFilters.action, 'client.created', 'previous applied filters survive');
  assert.equal(runtime.state.draftFilters.action, 'client_wish.created', 'the draft survives for correction');
  assert.deepEqual(view(runtime).rows.map((row) => row.id), [2]);
  assert.equal(view(runtime).refreshError, AUDIT_LOG_FILTER_FAILURE);
  assert.equal(runtime.filtersDirty(), true);

  // A later refresh still refreshes the previously applied result.
  runtime.refresh();
  assert.equal(queryOf(state.urls.at(-1)).get('action'), 'client.created');
});

test('load more is refused while the controls differ from the applied filters', async () => {
  const { state, runtime } = await loaded(page([item()], 9));
  assert.equal(view(runtime).canLoadMore, true);
  const requestsBefore = state.reads.length;

  runtime.setFilter('action', 'client.created');

  assert.deepEqual(runtime.loadMore(), { accepted: false, reason: 'filters-pending' });
  assert.equal(state.reads.length, requestsBefore);
  assert.equal(view(runtime).canLoadMore, false);
  assert.equal(view(runtime).filtersDirty, true);
});

test('clearing filters requests the unfiltered history and resets both sides on success', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('action', 'client.created');
  runtime.setFilter('createdFrom', '2026-07-01T10:00');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 2 })], 1));
  await flush();

  runtime.clearFilters();
  assert.equal(state.urls.at(-1), '/api/audit-logs?limit=50&offset=0');
  state.reads.at(-1).resolve(page([item({ id: 3 })], 1));
  await flush();

  assert.deepEqual(runtime.state.draftFilters, EMPTY_AUDIT_LOG_FILTERS);
  assert.deepEqual(runtime.state.appliedFilters, EMPTY_AUDIT_LOG_FILTERS);
  assert.equal(runtime.filtersDirty(), false);
});

test('a failed clear empties the controls but keeps the previous applied result', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('action', 'client.created');
  runtime.applyFilters();
  state.reads.at(-1).resolve(page([item({ id: 2 })], 1));
  await flush();

  runtime.clearFilters();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();

  assert.deepEqual(runtime.state.draftFilters, EMPTY_AUDIT_LOG_FILTERS, 'the controls stay cleared');
  assert.equal(runtime.state.appliedFilters.action, 'client.created', 'the previous conditions still produced the rows');
  assert.equal(runtime.filtersDirty(), true);
  assert.deepEqual(view(runtime).rows.map((row) => row.id), [2]);
  assert.equal(view(runtime).refreshError, AUDIT_LOG_FILTER_FAILURE);
});

// --------------------------------------------------------------------------
// Read lifecycle
// --------------------------------------------------------------------------

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
  runtime.enter();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  const presentation = view(runtime);
  assert.equal(presentation.listState, 'error');
  assert.equal(presentation.initialError, AUDIT_LOG_INITIAL_FAILURE);
  assert.equal(state.assertive.at(-1), AUDIT_LOG_INITIAL_FAILURE);
});

test('retry after an initial failure succeeds', async () => {
  const { state, runtime } = harness();
  runtime.enter();
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
// Stale responses
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
  assert.equal(runtime.state.appliedFilters.action, 'client_wish.created');
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

test('a structured date-range rejection is attached to the end-date control', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('createdFrom', '2026-07-05T00:00');
  runtime.setFilter('createdBefore', '2026-07-09T00:00');
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
  runtime.enter();
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

test('every required focus key is present in the rendered workspace', async () => {
  const { runtime } = await loaded(page([item()], 5));
  const root = markupView(runtime);
  const required = [
    'audit-log-workspace',
    'audit-log-refresh',
    'audit-log-filter-created-from',
    'audit-log-filter-created-before',
    'audit-log-filter-action',
    'audit-log-filter-entity-type',
    'audit-log-filter-actor-type',
    'audit-log-apply-filters',
    'audit-log-clear-filters',
    'audit-log-load-more',
  ];
  for (const key of required) assert.ok(root.querySelector(`[data-focus-key="${key}"]`), key);
  // Focus keys are addressing, never user-visible text.
  for (const key of required) assert.equal(root.textContent.includes(key), false, key);
});

test('the retry focus key exists on the initial-failure screen', async () => {
  const { state, runtime } = harness();
  runtime.enter();
  state.reads.at(-1).reject(new Error('offline'));
  await flush();
  assert.ok(markupView(runtime).querySelector('[data-focus-key="audit-log-retry"]'));
});

test('the pending-filter hint is always present and revealed only when dirty', async () => {
  const { runtime } = await loaded(page([item()], 5));
  const clean = markupView(runtime).querySelector('[data-state="audit-log-filters-pending"]');
  assert.ok(clean, 'the hint must exist so a draft edit can reveal it without a render');
  assert.equal(clean.hasAttribute('hidden'), true);

  runtime.setFilter('action', 'client.created');
  const dirty = markupView(runtime).querySelector('[data-state="audit-log-filters-pending"]');
  assert.equal(dirty.hasAttribute('hidden'), false);
  assert.equal(dirty.textContent, AUDIT_LOG_FILTERS_PENDING);
  assert.equal(dirty.textContent.toLowerCase().includes('draft'), false);
  assert.equal(dirty.textContent.toLowerCase().includes('applied'), false);
});

test('load more is disabled in the markup while filters are dirty', async () => {
  const { runtime } = await loaded(page([item()], 9));
  assert.equal(markupView(runtime).querySelector('[data-action="load-more-audit-log"]').hasAttribute('disabled'), false);
  runtime.setFilter('action', 'client.created');
  assert.equal(markupView(runtime).querySelector('[data-action="load-more-audit-log"]').hasAttribute('disabled'), true);
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
  failed.runtime.enter();
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
  const { runtime } = await loaded(page([item()], 1));
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
      total: 1, filterOptions: FILTER_OPTIONS, draftFilters: { ...EMPTY_AUDIT_LOG_FILTERS }, appliedFilters: { ...EMPTY_AUDIT_LOG_FILTERS },
      loaded: true, onRoute: true, initialError: '', refreshError: '', loadMoreError: '', fieldErrors: { createdFrom: '', createdBefore: '' },
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
// Targeted DOM updates and focus preservation
// --------------------------------------------------------------------------

/** A live fake document holding the current rendered workspace. */
function workspaceDom(runtime) {
  const container = new ViewNode('body');
  const mount = () => {
    container.children = [];
    const rendered = renderView(auditLogWorkspaceMarkup(view(runtime), renderFeedback));
    for (const child of rendered.children) container.append(child);
  };
  mount();
  return { container, mount };
}

test('a draft edit updates the hint, load more and field error in place', async () => {
  const { runtime } = await loaded(page([item()], 9));
  const { container } = workspaceDom(runtime);
  const hintBefore = container.querySelector('[data-state="audit-log-filters-pending"]');
  const loadMore = container.querySelector('[data-action="load-more-audit-log"]');

  runtime.setFilter('action', 'client.created');
  syncAuditLogFilterState(container, runtime.filterSync());

  assert.equal(hintBefore.hasAttribute('hidden'), false, 'the same node is revealed, not replaced');
  assert.equal(loadMore.disabled, true);
  assert.equal(container.querySelector('[data-state="audit-log-filters-pending"]'), hintBefore);
});

test('editing a date clears only that field error and leaves the other alone', async () => {
  const { state, runtime } = await loaded(page([item()], 1));
  runtime.setFilter('createdFrom', '2026-07-05T00:00');
  runtime.setFilter('createdBefore', '2026-07-09T00:00');
  runtime.applyFilters();
  state.reads.at(-1).reject({ status: 422, payload: { detail: { code: 'invalid_date', message: 'Конец периода должен быть позже его начала.', field: 'created_before', value: 'x', next_action: 'Выберите дату позже.' } } });
  await flush();

  const { container } = workspaceDom(runtime);
  const endError = container.querySelector('[data-audit-log-field-error="created-before"]');
  const startError = container.querySelector('[data-audit-log-field-error="created-from"]');
  assert.equal(endError.hasAttribute('hidden'), false);

  runtime.setFilter('createdBefore', '2026-07-20T00:00');
  syncAuditLogFilterState(container, runtime.filterSync());

  assert.equal(endError.hasAttribute('hidden'), true, 'the corrected field clears');
  assert.equal(endError.textContent, '');
  assert.equal(container.querySelector('[data-audit-log-filter="created-before"]').getAttribute('aria-invalid'), 'false');
  assert.equal(startError.hasAttribute('hidden'), true);
});

test('each filter control keeps keyboard focus when its value changes', async () => {
  const { state, runtime } = await loaded(page([item()], 9));
  const { container } = workspaceDom(runtime);

  for (const [filter, key, value] of [
    ['action', 'action', 'client.created'],
    ['entity-type', 'entityType', 'client'],
    ['actor-type', 'actorType', 'user'],
    ['created-from', 'createdFrom', '2026-07-01T10:00'],
    ['created-before', 'createdBefore', '2026-07-09T10:00'],
  ]) {
    const control = container.querySelector(`[data-audit-log-filter="${filter}"]`);
    control.focus();
    const rendersBefore = state.renders;

    runtime.setFilter(key, value);
    syncAuditLogFilterState(container, runtime.filterSync());

    assert.equal(state.renders, rendersBefore, `${filter}: a draft edit must not trigger a full render`);
    assert.equal(fakeDocument.activeElement, control, `${filter}: focus must stay on the edited control`);
  }
});

test('a required render restores focus to the equivalent control', async () => {
  const { runtime } = await loaded(page([item()], 9));
  const { container, mount } = workspaceDom(runtime);
  const before = container.querySelector('[data-audit-log-filter="action"]');
  before.focus();

  globalThis.document = fakeDocument;
  try {
    renderAuditLogWithFocus(container, mount);
  } finally {
    delete globalThis.document;
  }

  const after = container.querySelector('[data-audit-log-filter="action"]');
  assert.notEqual(after, before, 'the render really did replace the node');
  assert.equal(fakeDocument.activeElement, after, 'focus followed the focus key onto the new node');
});

test('a render falls back to the workspace container when the control is gone', async () => {
  const { runtime } = await loaded(page([item()], 9));
  const { container, mount } = workspaceDom(runtime);
  container.querySelector('[data-action="load-more-audit-log"]').focus();

  globalThis.document = fakeDocument;
  try {
    // Every row is loaded now, so the load-more control disappears entirely.
    runtime.state.total = 1;
    renderAuditLogWithFocus(container, mount);
  } finally {
    delete globalThis.document;
  }

  assert.equal(container.querySelector('[data-action="load-more-audit-log"]'), null);
  assert.equal(fakeDocument.activeElement.getAttribute('data-focus-key'), 'audit-log-workspace');
});

test('a render never steals focus from outside the workspace', async () => {
  const { runtime } = await loaded(page([item()], 9));
  const { container, mount } = workspaceDom(runtime);
  const elsewhere = new ViewNode('button', { 'data-focus-key': 'somewhere-else' });
  elsewhere.focus();

  globalThis.document = fakeDocument;
  try {
    renderAuditLogWithFocus(container, mount);
  } finally {
    delete globalThis.document;
  }

  assert.equal(fakeDocument.activeElement, elsewhere);
});

test('after leaving the route no focus is restored into absent workspace markup', async () => {
  const { runtime } = await loaded(page([item()], 9));
  const { container } = workspaceDom(runtime);
  container.querySelector('[data-audit-log-filter="action"]').focus();
  const focusedBefore = fakeDocument.activeElement;

  runtime.leave();
  globalThis.document = fakeDocument;
  try {
    // The route is gone: the render swaps the workspace out for another page.
    renderAuditLogWithFocus(container, () => { container.children = [new ViewNode('div', { 'data-page': 'settings' })]; });
  } finally {
    delete globalThis.document;
  }

  assert.equal(fakeDocument.activeElement, focusedBefore, 'focus was left alone, not pushed into missing markup');
  assert.equal(container.querySelector('[data-page="audit-log"]'), null);
});

test('a sync against markup that is no longer the workspace is a safe no-op', () => {
  const container = new ViewNode('body');
  container.append(new ViewNode('div', { 'data-page': 'settings' }));
  assert.doesNotThrow(() => syncAuditLogFilterState(container, { filtersDirty: true, fieldErrors: { createdFrom: '', createdBefore: '' }, canLoadMore: false }));
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
