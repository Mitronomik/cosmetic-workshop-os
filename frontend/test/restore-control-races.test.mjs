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

async function resumeFinalWithoutReplay(finalSnapshot) {
  const h = harness({
    storageEntries: storedSession(),
    historyState: {},
    fetches: [response(200, { ok: true, state: finalSnapshot })],
  });
  await h.runtime.start({ kind: 'none' });
  assert.equal(h.runtime.view.availability, 'protocol_error');
  assert.equal(h.runtime.view.hasSession, true);
  assert.equal(h.runtime.view.protocolSafe, false);
  assert.equal(h.runtime.view.pending, null);
  assert.equal(h.runtime.view.snapshot?.state, finalSnapshot.state);
  return h;
}

function assertNoUnknownOverlay(markup) {
  assert.doesNotMatch(markup, /Статус неизвестен/);
  assert.doesNotMatch(markup, /Состояние восстановления сейчас неизвестно/);
  assert.doesNotMatch(markup, /Сессия восстановления больше не может безопасно продолжать команды/);
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

  const readyMarkup = restoreControlMarkup({
    availability: 'ready',
    hasSession: true,
    protocolSafe: true,
    pending,
    notice: '',
    snapshot: accepted,
  });
  assert.match(readyMarkup, /Статус восстановления/);
  assert.match(readyMarkup, /Запрос на восстановление отправлен/);
  assert.match(readyMarkup, /Восстановление уже могло начаться/);
  assert.match(readyMarkup, /В процессе/);

  const networkMarkup = restoreControlMarkup({
    availability: 'network_error',
    hasSession: true,
    protocolSafe: true,
    pending,
    notice: 'Ответ на последнее действие не получен. Безопасно повторите именно предыдущую команду.',
    snapshot: accepted,
  });
  assert.match(networkMarkup, /Итог восстановления пока неизвестен/);
  assert.match(networkMarkup, /Связь с приложением прервана/);
  assert.match(networkMarkup, /Повторить только предыдущую команду/);

  for (const markup of [readyMarkup, networkMarkup]) {
    assert.doesNotMatch(markup, /Рабочие данные не изменены/);
    assert.doesNotMatch(markup, /восстановление ещё не запускалось/);
    assert.doesNotMatch(markup, /Выбор и проверка не меняют/);
    assert.doesNotMatch(markup, /data-restore-action="back"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-open"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-execute"/);
  }
});

test('C4-II-C completed result is truthful and allows ordinary navigation', async () => {
  const assertCompleted = (markup) => {
    assert.match(markup, /Восстановление завершено безопасно/);
    assert.match(markup, /Обычная работа снова доступна/);
    assert.match(markup, /Можно продолжать работу/);
    assert.match(markup, /data-restore-action="back"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-execute"/);
    assert.doesNotMatch(markup, /data-restore-action="retry"/);
    assert.doesNotMatch(markup, /source_path|operation_id|traceback/);
    assertNoUnknownOverlay(markup);
  };

  const finalSnapshot = snapshot({ state: 'restore_completed', generation: 8, filename: 'backup.sqlite', message: 'Восстановление завершено безопасно.' });
  const readyMarkup = restoreControlMarkup({
    availability: 'ready',
    hasSession: true,
    protocolSafe: true,
    pending: null,
    notice: '',
    snapshot: finalSnapshot,
  });
  assertCompleted(readyMarkup);

  const h = await resumeFinalWithoutReplay(finalSnapshot);
  const resumedMarkup = restoreControlMarkup(h.runtime.view);
  assertCompleted(resumedMarkup);
  assert.doesNotMatch(resumedMarkup, /Восстановление недоступно/);
  assert.doesNotMatch(resumedMarkup, /Перезапустите «Мастерскую косметолога»/);
  h.runtime.dispose();
});

test('C4-II-C failed result avoids rollback and unchanged-data inference', async () => {
  const assertFailed = (markup) => {
    assert.match(markup, /Восстановление не выполнено/);
    assert.match(markup, /Обычная работа снова доступна/);
    assert.match(markup, /не означает автоматически, что рабочие данные остались прежними/);
    assert.match(markup, /не запускайте новое восстановление вслепую/i);
    assert.match(markup, /data-restore-action="back"/);
    assert.doesNotMatch(markup, /Рабочие данные не изменены/);
    assert.doesNotMatch(markup, /старые данные восстановлены|откат выполнен/i);
    assert.doesNotMatch(markup, /data-restore-action="confirm-execute"/);
    assert.doesNotMatch(markup, /data-restore-action="retry"/);
    assertNoUnknownOverlay(markup);
  };

  const finalSnapshot = snapshot({ state: 'restore_failed', generation: 8, filename: 'backup.sqlite', message: 'Восстановление не выполнено.' });
  const readyMarkup = restoreControlMarkup({
    availability: 'ready',
    hasSession: true,
    protocolSafe: true,
    pending: null,
    notice: '',
    snapshot: finalSnapshot,
  });
  assertFailed(readyMarkup);

  const h = await resumeFinalWithoutReplay(finalSnapshot);
  const resumedMarkup = restoreControlMarkup(h.runtime.view);
  assertFailed(resumedMarkup);
  assert.doesNotMatch(resumedMarkup, /Восстановление недоступно/);
  h.runtime.dispose();
});

test('C4-II-C blocked result requires restart and offers no normal-work action', async () => {
  const assertBlocked = (markup) => {
    assert.match(markup, /Перезапустите «Мастерскую косметолога»/);
    assert.match(markup, /Обычная работа в текущем запуске не подтверждена как безопасная/);
    assert.match(markup, /разделом «Помощь»/);
    assert.doesNotMatch(markup, /data-restore-action="back"/);
    assert.doesNotMatch(markup, /data-restore-action="select"/);
    assert.doesNotMatch(markup, /data-restore-action="cancel"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-open"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-execute"/);
    assert.doesNotMatch(markup, /data-restore-action="retry"/);
    assert.doesNotMatch(markup, /Можно продолжать работу/);
    assertNoUnknownOverlay(markup);
  };

  const finalSnapshot = snapshot({ state: 'restore_blocked', generation: 8, filename: 'backup.sqlite', message: 'Перезапустите приложение для безопасного продолжения.' });
  const readyMarkup = restoreControlMarkup({
    availability: 'ready',
    hasSession: true,
    protocolSafe: true,
    pending: null,
    notice: '',
    snapshot: finalSnapshot,
  });
  assertBlocked(readyMarkup);

  const h = await resumeFinalWithoutReplay(finalSnapshot);
  const resumedMarkup = restoreControlMarkup(h.runtime.view);
  assertBlocked(resumedMarkup);
  assert.doesNotMatch(resumedMarkup, /Восстановление недоступно/);
  h.runtime.dispose();
});

test('C4-II-C destructive-result uncertainty stays unknown after connection loss and session invalidation', async () => {
  const pending = {
    action: 'execute',
    requestId: 'f'.repeat(32),
    commandSeq: 2,
    generation: 9,
  };
  const accepted = snapshot({ state: 'accepted', generation: 9, filename: 'backup.sqlite', compatibility: 'compatible' });
  const networkMarkup = restoreControlMarkup({
    availability: 'network_error',
    hasSession: true,
    protocolSafe: true,
    pending,
    notice: 'Связь потеряна.',
    snapshot: accepted,
  });
  assert.match(networkMarkup, /Итог восстановления пока неизвестен/);
  assert.match(networkMarkup, /не подтверждает ни успешное завершение, ни ошибку(?: восстановления)?/);
  assert.match(networkMarkup, /Не запускайте новое восстановление/);
  assert.match(networkMarkup, /data-restore-action="retry"/);
  assert.match(networkMarkup, /Повторить только предыдущую команду/);
  assert.doesNotMatch(networkMarkup, /data-restore-action="back"/);
  assert.doesNotMatch(networkMarkup, /Можно продолжать работу/);
  assert.doesNotMatch(networkMarkup, /Рабочие данные не изменены/);

  const assertUnavailableMarkup = (markup) => {
    assert.match(markup, /Состояние восстановления сейчас неизвестно/);
    assert.match(markup, /Статус неизвестен/);
    assert.match(markup, /Локальная сессия восстановления сейчас недоступна/);
    assert.match(markup, /этот экран не может подтвердить текущий результат восстановления или состояние данных/i);
    assert.match(markup, /перезапустите «Мастерскую косметолога»/i);
    assert.doesNotMatch(markup, /Без изменения данных/);
    assert.doesNotMatch(markup, /Выбор и проверка не меняют/);
    assert.doesNotMatch(markup, /рабочая база данных не заменяется/i);
    assert.doesNotMatch(markup, /Подключаем безопасное восстановление/);
    assert.doesNotMatch(markup, /Проверяем локальную сессию приложения/);
    assert.doesNotMatch(markup, /Выберите резервную копию/);
    assert.doesNotMatch(markup, /data-restore-action="back"/);
    assert.doesNotMatch(markup, /data-restore-action="select"/);
    assert.doesNotMatch(markup, /data-restore-action="cancel"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-open"/);
    assert.doesNotMatch(markup, /data-restore-action="confirm-execute"/);
    assert.doesNotMatch(markup, /data-restore-action="retry"/);
    assert.doesNotMatch(markup, /data-restore-action="refresh"/);
    assert.doesNotMatch(markup, /Можно продолжать работу/);
    assert.doesNotMatch(markup, /Рабочие данные не изменены/);
    assert.doesNotMatch(markup, /Восстановление завершено|Восстановление не завершено/);
  };

  const h401 = harness({
    fetches: [
      response(200, bootstrapPayload()),
      response(200, {
        ok: true,
        code: 'candidate_accepted',
        command_seq: 1,
        state: snapshot({ state: 'accepted', generation: 9, filename: 'backup.sqlite', compatibility: 'compatible' }),
      }),
      response(200, {
        ok: true,
        code: 'restore_accepted',
        command_seq: 2,
        state: snapshot({ state: 'restoring', generation: 9, filename: 'backup.sqlite', message: 'Восстановление выполняется.' }),
      }),
      response(401, { ok: false, code: 'invalid_session' }),
    ],
  });
  await h401.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h401.runtime.select();
  await h401.runtime.execute();
  assert.equal(h401.runtime.view.snapshot?.state, 'restoring');
  await h401.runtime.refresh();
  assert.deepEqual(
    {
      availability: h401.runtime.view.availability,
      snapshot: h401.runtime.view.snapshot,
      pending: h401.runtime.view.pending,
      hasSession: h401.runtime.view.hasSession,
      protocolSafe: h401.runtime.view.protocolSafe,
    },
    { availability: 'unavailable', snapshot: null, pending: null, hasSession: false, protocolSafe: true },
  );
  assertUnavailableMarkup(restoreControlMarkup(h401.runtime.view));
  h401.runtime.dispose();

  const h409 = harness({
    fetches: [
      response(200, bootstrapPayload()),
      response(200, {
        ok: true,
        code: 'candidate_accepted',
        command_seq: 1,
        state: snapshot({ state: 'accepted', generation: 9, filename: 'backup.sqlite', compatibility: 'compatible' }),
      }),
      response(409, { ok: false, code: 'command_conflict' }),
    ],
  });
  await h409.runtime.start({ kind: 'valid', controlOrigin: CONTROL_ORIGIN, bootstrapToken: TOKEN });
  await h409.runtime.select();
  await h409.runtime.execute();
  assert.deepEqual(
    {
      availability: h409.runtime.view.availability,
      snapshot: h409.runtime.view.snapshot,
      pending: h409.runtime.view.pending,
      hasSession: h409.runtime.view.hasSession,
      protocolSafe: h409.runtime.view.protocolSafe,
    },
    { availability: 'protocol_error', snapshot: null, pending: null, hasSession: false, protocolSafe: false },
  );
  assertUnavailableMarkup(restoreControlMarkup(h409.runtime.view));
  h409.runtime.dispose();
});
