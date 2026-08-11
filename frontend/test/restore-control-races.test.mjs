import test from 'node:test';
import assert from 'node:assert/strict';
import {
  RESTORE_SESSION_STORAGE_KEYS,
} from '../dist-tests/restore-control/restore-control-contract.js';
import { RestoreControlRuntime } from '../dist-tests/restore-control/restore-control-runtime.js';
import { restoreControlMarkup } from '../dist-tests/restore-control/restore-control-presentation.js';

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

function harness({ fetches = [], storageEntries = {}, historyState = {} } = {}) {
  const storage = new MemoryStorage(storageEntries);
  const history = new MemoryHistory(historyState);
  const requests = [];
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
    setInterval() { return 1; },
    clearInterval() {},
    setTimeout() { return 1; },
    clearTimeout() {},
  };
  return { runtime: new RestoreControlRuntime(env), storage, history, requests };
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

test('double execute while first destructive request is in flight sends exactly one command', async () => {
  const executeReply = deferred();
  const h = harness({
    fetches: [
      response(200, bootstrapPayload()),
      response(200, {
        ok: true,
        code: 'candidate_accepted',
        command_seq: 1,
        state: snapshot({ state: 'accepted', generation: 4, filename: 'backup.sqlite', compatibility: 'compatible' }),
      }),
      () => executeReply.promise,
    ],
  });

  await h.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h.runtime.select();

  const first = h.runtime.execute();
  const second = h.runtime.execute();
  await second;

  assert.equal(h.requests.length, 3, 'bootstrap + select + exactly one execute request');
  assert.equal(h.requests[2].input, `${CONTROL_ORIGIN}/v1/restore/execute`);
  assert.deepEqual(JSON.parse(h.requests[2].init.body), {
    request_id: '000102030405060708090a0b0c0d0e0f',
    command_seq: 2,
    generation: 4,
  });
  assert.equal(h.runtime.view.pending?.action, 'execute');
  assert.match(h.runtime.view.notice, /предыдущую команду/);

  executeReply.resolve(response(200, {
    ok: true,
    code: 'restore_accepted',
    command_seq: 2,
    state: snapshot({ state: 'restoring', generation: 4, filename: 'backup.sqlite' }),
  }));
  await first;

  assert.equal(h.runtime.view.snapshot.state, 'restoring');
  assert.equal(h.runtime.view.pending, null);
});

test('pending execute presentation never claims Restore has not started', () => {
  const pending = {
    action: 'execute',
    requestId: 'e'.repeat(32),
    commandSeq: 2,
    generation: 7,
  };
  const accepted = snapshot({
    state: 'accepted',
    generation: 7,
    filename: 'backup.sqlite',
    compatibility: 'compatible',
  });

  const cases = [
    { availability: 'ready', notice: '' },
    { availability: 'network_error', notice: 'Ответ на последнее действие не получен. Безопасно повторите именно предыдущую команду.' },
  ];

  for (const current of cases) {
    const markup = restoreControlMarkup({
      availability: current.availability,
      hasSession: true,
      protocolSafe: true,
      pending,
      notice: current.notice,
      snapshot: accepted,
    });

    assert.match(markup, /Статус восстановления/);
    assert.match(markup, /Запрос на восстановление отправлен/);
    assert.match(markup, /Восстановление уже могло начаться/);
    assert.match(markup, /В процессе/);
    assert.doesNotMatch(markup, /Рабочие данные не изменены/);
    assert.doesNotMatch(markup, /восстановление ещё не запускалось/);
    assert.doesNotMatch(markup, /Выбор и проверка не меняют/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-open"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-execute"/);
  }
});
