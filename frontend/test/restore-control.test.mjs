import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  RESTORE_HISTORY_STATE_KEY,
  RESTORE_SESSION_STORAGE_KEYS,
  captureRestoreBootstrap,
  parseRestoreBootstrapFragment,
  readRestoreReplayState,
  restoreCommandRequestBody,
  restoreSnapshotDto,
} from '../dist-tests/restore-control/restore-control-contract.js';
import { RestoreControlRuntime } from '../dist-tests/restore-control/restore-control-runtime.js';
import { restoreControlMarkup } from '../dist-tests/restore-control/restore-control-presentation.js';
import { sectionForLocation } from '../dist-tests/restore-control/app-navigation-routes.js';

const TOKEN = 'A'.repeat(43);
const SESSION = 'B'.repeat(43);
const RUN_ID = 'run_12345678';
const CONTROL_ORIGIN = 'http://127.0.0.1:43123';

class MemoryStorage {
  constructor(entries = {}) { this.map = new Map(Object.entries(entries)); }
  getItem(key) { return this.map.get(key) ?? null; }
  setItem(key, value) { this.map.set(key, String(value)); }
  removeItem(key) { this.map.delete(key); }
  keys() { return [...this.map.keys()].sort(); }
}

class MemoryHistory {
  constructor(state = {}) { this.state = state; this.urls = []; }
  replaceState(data, _unused, url) { this.state = data; if (url !== undefined) this.urls.push(String(url)); }
}

function snapshot(overrides = {}) {
  return { run_id: RUN_ID, state: 'idle', generation: 0, filename: '', message: '', compatibility: null, failure: null, ...overrides };
}

function bootstrapPayload(overrides = {}) {
  return { ok: true, run_id: RUN_ID, control_origin: CONTROL_ORIGIN, session_token: SESSION, heartbeat_interval_seconds: 15, session_expiry_seconds: 60, state: snapshot(), ...overrides };
}

function response(status, payload) {
  return { ok: status >= 200 && status < 300, status, async json() { return payload; } };
}

function harness({ fetches = [], storageEntries = {}, historyState = {} } = {}) {
  const requests = [];
  const storage = new MemoryStorage(storageEntries);
  const history = new MemoryHistory(historyState);
  const intervals = new Map();
  const timeouts = new Map();
  let nextTimer = 1;
  const env = {
    async fetch(input, init = {}) {
      requests.push({ input, init });
      if (!fetches.length) throw new Error('unexpected fetch');
      const item = fetches.shift();
      if (item instanceof Error) throw item;
      return typeof item === 'function' ? item(input, init) : item;
    },
    sessionStorage: storage,
    history,
    crypto: { getRandomValues(bytes) { for (let i = 0; i < bytes.length; i += 1) bytes[i] = i; return bytes; } },
    setInterval(handler, ms) { const id = nextTimer++; intervals.set(id, { handler, ms }); return id; },
    clearInterval(id) { intervals.delete(id); },
    setTimeout(handler, ms) { const id = nextTimer++; timeouts.set(id, { handler, ms }); return id; },
    clearTimeout(id) { timeouts.delete(id); },
  };
  return { env, storage, history, requests, intervals, timeouts, runtime: new RestoreControlRuntime(env) };
}

function storedSession() {
  return {
    [RESTORE_SESSION_STORAGE_KEYS.controlOrigin]: CONTROL_ORIGIN,
    [RESTORE_SESSION_STORAGE_KEYS.runId]: RUN_ID,
    [RESTORE_SESSION_STORAGE_KEYS.sessionToken]: SESSION,
  };
}

function acceptedCommand(commandSeq = 1, generation = 1) {
  return response(200, {
    ok: true,
    code: 'candidate_accepted',
    command_seq: commandSeq,
    state: snapshot({ state: 'accepted', generation, filename: 'backup.sqlite', compatibility: 'compatible' }),
  });
}

test('valid bootstrap fragment is captured and removed synchronously', () => {
  const history = new MemoryHistory({ keep: true });
  const location = { hash: `#cw-control=43123:${TOKEN}`, pathname: '/backups', search: '?safe=1' };
  const capture = captureRestoreBootstrap(location, history);
  assert.deepEqual(capture, { kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  assert.deepEqual(history.state, { keep: true });
  assert.equal(history.urls.at(-1), '/backups?safe=1');
});

test('malformed cw-control fragment is removed and fails closed', () => {
  const history = new MemoryHistory();
  assert.deepEqual(parseRestoreBootstrapFragment('#cw-control=0:bad'), { kind: 'invalid' });
  const capture = captureRestoreBootstrap({ hash: '#cw-control=0:bad', pathname: '/', search: '' }, history);
  assert.equal(capture.kind, 'invalid');
  assert.equal(history.urls.at(-1), '/');
});

test('unrelated legacy hash is untouched', () => {
  const history = new MemoryHistory();
  const capture = captureRestoreBootstrap({ hash: '#help', pathname: '/', search: '' }, history);
  assert.deepEqual(capture, { kind: 'none' });
  assert.deepEqual(history.urls, []);
});

test('bootstrap stores only the three run-scoped session descriptors', async () => {
  const h = harness({ fetches: [response(200, bootstrapPayload())] });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  assert.equal(h.runtime.view.availability, 'ready');
  assert.deepEqual(h.storage.keys(), Object.values(RESTORE_SESSION_STORAGE_KEYS).sort());
  assert.equal(h.requests[0].input, `${CONTROL_ORIGIN}/v1/bootstrap`);
  assert.equal(h.requests[0].init.credentials, 'omit');
  assert.equal(h.requests[0].init.cache, 'no-store');
  assert.equal(h.requests[0].init.referrerPolicy, 'no-referrer');
  assert.ok(!String(h.requests[0].input).includes(TOKEN));
  assert.equal(JSON.parse(h.requests[0].init.body).bootstrap_token, TOKEN);
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).nextCommandSeq, 1);
  assert.deepEqual([...h.intervals.values()].map((item) => item.ms), [15000]);
  h.runtime.dispose();
});

test('state DTO rejects unexpected fields including filesystem paths', () => {
  assert.equal(restoreSnapshotDto({ ...snapshot(), source_path: '/Users/private/backup.sqlite' }), null);
  assert.equal(restoreSnapshotDto({ ...snapshot(), staged_path: '/tmp/staged.sqlite' }), null);
});

test('state DTO accepts exactly the four merged B2 execution states and rejects unknown state', () => {
  for (const state of ['restoring', 'restore_completed', 'restore_failed', 'restore_blocked']) {
    assert.equal(restoreSnapshotDto(snapshot({ state, generation: 3 }))?.state, state);
  }
  assert.equal(restoreSnapshotDto(snapshot({ state: 'restore_maybe', generation: 3 })), null);
});

test('select consumes sequence one and advances replay state after a typed reply', async () => {
  const h = harness({ fetches: [response(200, bootstrapPayload()), acceptedCommand()] });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h.runtime.select();
  const request = h.requests[1];
  const body = JSON.parse(request.init.body);
  assert.equal(request.input, `${CONTROL_ORIGIN}/v1/restore/select`);
  assert.equal(body.command_seq, 1);
  assert.match(body.request_id, /^[0-9a-f]{32}$/);
  assert.equal(h.runtime.view.snapshot.state, 'accepted');
  assert.equal(h.runtime.view.snapshot.filename, 'backup.sqlite');
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).nextCommandSeq, 2);
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).pending, null);
  h.runtime.dispose();
});

test('network-uncertain command retries exact same request id and sequence', async () => {
  const h = harness({ fetches: [response(200, bootstrapPayload()), new Error('network'), acceptedCommand()] });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h.runtime.select();
  const first = JSON.parse(h.requests[1].init.body);
  assert.equal(h.runtime.view.availability, 'network_error');
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).pending.commandSeq, 1);
  await h.runtime.retryPending();
  const retry = JSON.parse(h.requests[2].init.body);
  assert.deepEqual(retry, first);
  assert.equal(h.runtime.view.snapshot.state, 'accepted');
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).nextCommandSeq, 2);
  h.runtime.dispose();
});

test('B3 replay parser keeps legacy select/cancel pending shape backward-safe', () => {
  const requestId = 'a'.repeat(32);
  const raw = {
    [RESTORE_HISTORY_STATE_KEY]: {
      version: 1,
      runId: RUN_ID,
      nextCommandSeq: 4,
      pending: { action: 'select', requestId, commandSeq: 3 },
    },
  };
  assert.deepEqual(readRestoreReplayState(raw, RUN_ID)?.pending, { action: 'select', requestId, commandSeq: 3 });
});

test('B3 replay parser requires exact generation for execute and rejects filesystem authority', () => {
  const requestId = 'b'.repeat(32);
  const valid = {
    [RESTORE_HISTORY_STATE_KEY]: {
      version: 1,
      runId: RUN_ID,
      nextCommandSeq: 3,
      pending: { action: 'execute', requestId, commandSeq: 2, generation: 7 },
    },
  };
  assert.deepEqual(readRestoreReplayState(valid, RUN_ID)?.pending, { action: 'execute', requestId, commandSeq: 2, generation: 7 });
  assert.equal(readRestoreReplayState({ [RESTORE_HISTORY_STATE_KEY]: { ...valid[RESTORE_HISTORY_STATE_KEY], pending: { action: 'execute', requestId, commandSeq: 2 } } }, RUN_ID), null);
  assert.equal(readRestoreReplayState({ [RESTORE_HISTORY_STATE_KEY]: { ...valid[RESTORE_HISTORY_STATE_KEY], pending: { action: 'execute', requestId, commandSeq: 2, generation: 7, sourcePath: '/private/backup.sqlite' } } }, RUN_ID), null);
});

test('command request body is exact and execute adds only generation', () => {
  const requestId = 'c'.repeat(32);
  assert.deepEqual(restoreCommandRequestBody({ action: 'select', requestId, commandSeq: 4 }), { request_id: requestId, command_seq: 4 });
  assert.deepEqual(restoreCommandRequestBody({ action: 'execute', requestId, commandSeq: 5, generation: 9 }), { request_id: requestId, command_seq: 5, generation: 9 });
  assert.deepEqual(Object.keys(restoreCommandRequestBody({ action: 'execute', requestId, commandSeq: 5, generation: 9 })).sort(), ['command_seq', 'generation', 'request_id']);
});

test('B3 execute uses exact current accepted generation and enters restoring', async () => {
  const h = harness({
    fetches: [
      response(200, bootstrapPayload()),
      acceptedCommand(1, 7),
      response(200, { ok: true, code: 'restore_accepted', command_seq: 2, state: snapshot({ state: 'restoring', generation: 7, filename: 'backup.sqlite', message: 'Восстановление выполняется.' }) }),
    ],
  });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h.runtime.select();
  await h.runtime.execute();

  const request = h.requests[2];
  const body = JSON.parse(request.init.body);
  assert.equal(request.input, `${CONTROL_ORIGIN}/v1/restore/execute`);
  assert.deepEqual(Object.keys(body).sort(), ['command_seq', 'generation', 'request_id']);
  assert.equal(body.command_seq, 2);
  assert.equal(body.generation, 7);
  assert.match(body.request_id, /^[0-9a-f]{32}$/);
  assert.equal(h.runtime.view.snapshot.state, 'restoring');
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).nextCommandSeq, 3);
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).pending, null);
  assert.equal(h.timeouts.size, 1, 'restoring state must continue launcher-control polling');
  h.runtime.dispose();
});

test('B3 execute cannot begin from non-accepted state', async () => {
  const h = harness({ fetches: [response(200, bootstrapPayload())] });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h.runtime.execute();
  assert.equal(h.requests.length, 1);
  assert.match(h.runtime.view.notice, /Сначала выберите резервную копию/);
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).pending, null);
  h.runtime.dispose();
});

test('network-uncertain execute retries exact request id sequence and generation', async () => {
  const restoringReply = response(200, { ok: true, code: 'restore_accepted', command_seq: 2, state: snapshot({ state: 'restoring', generation: 11, filename: 'backup.sqlite' }) });
  const h = harness({ fetches: [response(200, bootstrapPayload()), acceptedCommand(1, 11), new Error('network'), restoringReply] });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h.runtime.select();
  await h.runtime.execute();

  const first = JSON.parse(h.requests[2].init.body);
  const replayAfterFailure = readRestoreReplayState(h.history.state, RUN_ID);
  assert.deepEqual(replayAfterFailure.pending, { action: 'execute', requestId: first.request_id, commandSeq: 2, generation: 11 });
  assert.equal(replayAfterFailure.nextCommandSeq, 2, 'ambiguous execute must not allocate another sequence');
  assert.equal(h.runtime.view.availability, 'network_error');

  await h.runtime.retryPending();
  const retry = JSON.parse(h.requests[3].init.body);
  assert.deepEqual(retry, first);
  assert.equal(h.runtime.view.snapshot.state, 'restoring');
  assert.equal(readRestoreReplayState(h.history.state, RUN_ID).nextCommandSeq, 3);
  h.runtime.dispose();
});

test('reload resumes strict next sequence from same-tab history state', async () => {
  const replay = { version: 1, runId: RUN_ID, nextCommandSeq: 2, pending: null };
  const h = harness({
    storageEntries: storedSession(),
    historyState: { [RESTORE_HISTORY_STATE_KEY]: replay },
    fetches: [response(200, { ok: true, state: snapshot({ state: 'accepted', generation: 1, filename: 'old.sqlite' }) }), response(200, { ok: true, code: 'select_started', command_seq: 2, state: snapshot({ state: 'selecting', generation: 2 }) })],
  });
  await h.runtime.start({ kind: 'none' });
  await h.runtime.select();
  assert.equal(JSON.parse(h.requests[1].init.body).command_seq, 2);
  h.runtime.dispose();
});

test('reload can safely preserve an ambiguous execute command', async () => {
  const requestId = 'd'.repeat(32);
  const replay = { version: 1, runId: RUN_ID, nextCommandSeq: 2, pending: { action: 'execute', requestId, commandSeq: 2, generation: 5 } };
  const h = harness({
    storageEntries: storedSession(),
    historyState: { [RESTORE_HISTORY_STATE_KEY]: replay },
    fetches: [
      response(200, { ok: true, state: snapshot({ state: 'accepted', generation: 5, filename: 'backup.sqlite' }) }),
      response(200, { ok: true, code: 'restore_accepted', command_seq: 2, state: snapshot({ state: 'restoring', generation: 5, filename: 'backup.sqlite' }) }),
    ],
  });
  await h.runtime.start({ kind: 'none' });
  assert.deepEqual(h.runtime.view.pending, replay.pending);
  await h.runtime.retryPending();
  assert.deepEqual(JSON.parse(h.requests[1].init.body), { request_id: requestId, command_seq: 2, generation: 5 });
  assert.equal(h.runtime.view.snapshot.state, 'restoring');
  h.runtime.dispose();
});

test('reload without replay metadata is fail-closed after any prior generation', async () => {
  const h = harness({ storageEntries: storedSession(), fetches: [response(200, { ok: true, state: snapshot({ state: 'accepted', generation: 1, filename: 'backup.sqlite' }) })] });
  await h.runtime.start({ kind: 'none' });
  assert.equal(h.runtime.view.availability, 'protocol_error');
  assert.equal(h.runtime.view.protocolSafe, false);
  assert.equal(h.requests.length, 1);
  h.runtime.dispose();
});

test('invalid session clears only Restore session descriptors', async () => {
  const entries = { ...storedSession(), unrelated: 'keep' };
  const h = harness({ storageEntries: entries, fetches: [response(401, { ok: false, code: 'invalid_session' })] });
  await h.runtime.start({ kind: 'none' });
  assert.equal(h.runtime.view.hasSession, false);
  assert.deepEqual(h.storage.keys(), ['unrelated']);
  h.runtime.dispose();
});

test('accepted presentation requires explicit destructive confirmation', () => {
  const view = { availability: 'ready', hasSession: true, protocolSafe: true, pending: null, notice: '', snapshot: snapshot({ state: 'accepted', generation: 1, filename: '<copy>.sqlite', compatibility: 'compatible' }) };
  const markup = restoreControlMarkup(view);
  assert.match(markup, /Рабочие данные не изменены/);
  assert.match(markup, /восстановление ещё не запускалось/);
  assert.match(markup, /data-restore-action="confirm-open"/);
  assert.match(markup, /class="danger-action"/);
  assert.ok(!markup.includes('<dialog'));
  assert.ok(!markup.includes('execute_restore'));
  assert.ok(!markup.includes('source_path'));
  assert.ok(!markup.includes('<input type="file"'));
  assert.ok(markup.includes('&lt;copy&gt;.sqlite'));
});

test('confirmation dialog explains replacement protective copy and has safe default focus', () => {
  const view = { availability: 'ready', hasSession: true, protocolSafe: true, pending: null, notice: '', snapshot: snapshot({ state: 'accepted', generation: 6, filename: '<copy>.sqlite', compatibility: 'compatible' }) };
  const markup = restoreControlMarkup(view, { confirmationOpen: true });
  assert.match(markup, /<dialog/);
  assert.match(markup, /data-restore-confirmation/);
  assert.match(markup, /данные мастерской будут заменены/i);
  assert.match(markup, /защитную копию текущей базы данных/i);
  assert.match(markup, /data-restore-action="confirm-dismiss" autofocus/);
  assert.match(markup, /data-restore-action="confirm-execute"/);
  assert.ok(markup.includes('&lt;copy&gt;.sqlite'));
  assert.ok(!markup.includes('/v1/restore/execute'));
  assert.ok(!markup.includes('source_path'));
});

test('restoring presentation offers no select cancel or destructive duplicate and no fake percentage', () => {
  const markup = restoreControlMarkup({ availability: 'ready', hasSession: true, protocolSafe: true, pending: null, notice: '', snapshot: snapshot({ state: 'restoring', generation: 6, filename: 'backup.sqlite', message: 'Восстановление выполняется.' }) });
  assert.match(markup, /Восстанавливаем данные мастерской/);
  assert.match(markup, /нельзя выбрать другой файл или отменить восстановление/i);
  assert.ok(!markup.includes('data-restore-action="select"'));
  assert.ok(!markup.includes('data-restore-action="cancel"'));
  assert.ok(!markup.includes('data-restore-action="confirm-open"'));
  assert.ok(!markup.includes('data-restore-action="confirm-execute"'));
  assert.ok(!markup.includes('%'));
});

test('final B2 states minimally present only safe launcher message', () => {
  const cases = [
    ['restore_completed', 'Восстановление завершено безопасно.'],
    ['restore_failed', 'Восстановление не выполнено. Рабочие данные доступны.'],
    ['restore_blocked', 'Перезапустите приложение для безопасного продолжения.'],
  ];
  for (const [state, message] of cases) {
    const markup = restoreControlMarkup({ availability: 'ready', hasSession: true, protocolSafe: true, pending: null, notice: '', snapshot: snapshot({ state, generation: 8, message }) });
    assert.ok(markup.includes(message));
    assert.ok(!markup.includes('data-restore-action="confirm-execute"'));
    assert.ok(!markup.includes('source_path'));
  }
});

test('nested Restore route stays inside the backups shell section', () => {
  assert.equal(sectionForLocation('/backups/restore'), 'Резервные копии');
  assert.equal(sectionForLocation('/backups/restore/'), 'Резервные копии');
});

test('browser runtime source contains no localStorage or browser file input fallback', async () => {
  const runtimeSource = await readFile(new URL('../src/restore-control-runtime.ts', import.meta.url), 'utf8');
  const entrySource = await readFile(new URL('../src/restore-control-entry.ts', import.meta.url), 'utf8');
  const presentationSource = await readFile(new URL('../src/restore-control-presentation.ts', import.meta.url), 'utf8');
  const combined = `${runtimeSource}\n${entrySource}\n${presentationSource}`;
  assert.ok(!combined.includes('localStorage'));
  assert.ok(!combined.includes('type="file"'));
  assert.ok(!combined.includes('source_path'));
  assert.ok(!combined.includes('execute_restore'));
  assert.ok(!combined.includes('/v1/restore/confirm'));
});

test('entry owns confirmation locally and Escape dismiss never becomes restore cancel', async () => {
  const entrySource = await readFile(new URL('../src/restore-control-entry.ts', import.meta.url), 'utf8');
  assert.ok(entrySource.includes('confirmationGeneration'));
  assert.ok(entrySource.includes('dialog.showModal()'));
  assert.ok(entrySource.includes("document.addEventListener('cancel'"));
  assert.ok(entrySource.includes("if (action === 'confirm-dismiss') { dismissConfirmation(); return; }"));
  assert.ok(entrySource.includes("if (action === 'confirm-execute') { executeConfirmedRestore(); }"));
  assert.ok(entrySource.includes('void runtime.execute();'));
  assert.ok(entrySource.includes("if (action === 'cancel') { void runtime.cancel(); return; }"));
});

test('entry avoids self-triggering heading mutation loop', async () => {
  const entrySource = await readFile(new URL('../src/restore-control-entry.ts', import.meta.url), 'utf8');
  assert.ok(entrySource.includes("heading && heading.textContent !== 'Восстановление'"));
});
