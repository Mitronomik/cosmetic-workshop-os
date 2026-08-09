import test from 'node:test';
import assert from 'node:assert/strict';
import {
  RESTORE_SESSION_STORAGE_KEYS,
} from '../dist-tests/restore-control/restore-control-contract.js';
import { RestoreControlRuntime } from '../dist-tests/restore-control/restore-control-runtime.js';

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
  constructor(state = {}) { this.state = state; }
  replaceState(data) { this.state = data; }
}

function snapshot(overrides = {}) {
  return { run_id: RUN_ID, state: 'idle', generation: 0, filename: '', message: '', compatibility: null, failure: null, ...overrides };
}

function bootstrapPayload() {
  return { ok: true, run_id: RUN_ID, control_origin: CONTROL_ORIGIN, session_token: SESSION, heartbeat_interval_seconds: 15, session_expiry_seconds: 60, state: snapshot() };
}

function response(status, payload) {
  return { ok: status >= 200 && status < 300, status, async json() { return payload; } };
}

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

function storedSession() {
  return {
    [RESTORE_SESSION_STORAGE_KEYS.controlOrigin]: CONTROL_ORIGIN,
    [RESTORE_SESSION_STORAGE_KEYS.runId]: RUN_ID,
    [RESTORE_SESSION_STORAGE_KEYS.sessionToken]: SESSION,
  };
}

function harness({ fetches = [], storageEntries = {} } = {}) {
  const storage = new MemoryStorage(storageEntries);
  const history = new MemoryHistory();
  const env = {
    async fetch(input, init = {}) {
      void input;
      void init;
      if (!fetches.length) throw new Error('unexpected fetch');
      const item = fetches.shift();
      if (item instanceof Error) throw item;
      return typeof item === 'function' ? item() : item;
    },
    sessionStorage: storage,
    history,
    crypto: { getRandomValues(bytes) { for (let i = 0; i < bytes.length; i += 1) bytes[i] = i; return bytes; } },
    setInterval() { return 1; },
    clearInterval() {},
    setTimeout() { return 1; },
    clearTimeout() {},
  };
  return { runtime: new RestoreControlRuntime(env), storage };
}

test('network-uncertain one-use bootstrap is restart-only, never retry guidance', async () => {
  const h = harness({ fetches: [new Error('network')] });
  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  assert.equal(h.runtime.view.availability, 'unavailable');
  assert.equal(h.runtime.view.hasSession, false);
  assert.match(h.runtime.view.notice, /перезапустите/);
  assert.doesNotMatch(h.runtime.view.notice, /повторите попытку/);
  assert.deepEqual(h.storage.keys(), []);
});

test('late state response is ignored after a concurrent request invalidates the session', async () => {
  const lateState = deferred();
  const h = harness({
    storageEntries: storedSession(),
    fetches: [
      response(200, { ok: true, state: snapshot() }),
      () => lateState.promise,
      response(401, { ok: false, code: 'invalid_session' }),
    ],
  });

  await h.runtime.start({ kind: 'none' });
  const refreshPromise = h.runtime.refresh();
  await h.runtime.select();

  assert.equal(h.runtime.view.hasSession, false);
  assert.equal(h.runtime.view.availability, 'unavailable');

  lateState.resolve(response(200, { ok: true, state: snapshot() }));
  await assert.doesNotReject(refreshPromise);

  assert.equal(h.runtime.view.hasSession, false);
  assert.equal(h.runtime.view.availability, 'unavailable');
  assert.deepEqual(h.storage.keys(), []);
});
