import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  RESTORE_HISTORY_STATE_KEY,
  RESTORE_SESSION_STORAGE_KEYS,
  captureRestoreBootstrap,
  parseRestoreBootstrapFragment,
  readRestoreReplayState,
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

test('select consumes sequence one and advances replay state after a typed reply', async () => {
  const h = harness({ fetches: [response(200, bootstrapPayload()), response(200, { ok: true, code: 'candidate_accepted', command_seq: 1, state: snapshot({ state: 'accepted', generation: 1, filename: 'backup.sqlite', compatibility: 'compatible' }) })] });
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
  const accepted = response(200, { ok: true, code: 'candidate_accepted', command_seq: 1, state: snapshot({ state: 'accepted', generation: 1, filename: 'backup.sqlite' }) });
  const h = harness({ fetches: [response(200, bootstrapPayload()), new Error('network'), accepted] });
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

test('accepted presentation is explicit that destructive Restore has not run', () => {
  const markup = restoreControlMarkup({ availability: 'ready', hasSession: true, protocolSafe: true, pending: null, notice: '', snapshot: snapshot({ state: 'accepted', generation: 1, filename: '<copy>.sqlite', compatibility: 'compatible' }) });
  assert.match(markup, /Рабочие данные не изменены/);
  assert.match(markup, /восстановление ещё не запускалось/);
  assert.ok(!markup.includes('execute_restore'));
  assert.ok(!markup.includes('source_path'));
  assert.ok(!markup.includes('<input type="file"'));
  assert.ok(markup.includes('&lt;copy&gt;.sqlite'));
});

test('nested Restore route stays inside the backups shell section', () => {
  assert.equal(sectionForLocation('/backups/restore'), 'Резервные копии');
  assert.equal(sectionForLocation('/backups/restore/'), 'Резервные копии');
});

test('A4 browser runtime source contains no localStorage or browser file input fallback', async () => {
  const runtimeSource = await readFile(new URL('../src/restore-control-runtime.ts', import.meta.url), 'utf8');
  const entrySource = await readFile(new URL('../src/restore-control-entry.ts', import.meta.url), 'utf8');
  const presentationSource = await readFile(new URL('../src/restore-control-presentation.ts', import.meta.url), 'utf8');
  const combined = `${runtimeSource}\n${entrySource}\n${presentationSource}`;
  assert.ok(!combined.includes('localStorage'));
  assert.ok(!combined.includes('type="file"'));
  assert.ok(!combined.includes('source_path'));
  assert.ok(!combined.includes('execute_restore'));
});
