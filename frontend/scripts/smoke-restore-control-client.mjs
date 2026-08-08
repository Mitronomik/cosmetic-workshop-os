import { webcrypto } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { captureRestoreBootstrap, RESTORE_HISTORY_STATE_KEY, RESTORE_SESSION_STORAGE_KEYS } from '../dist/assets/restore-control-contract.js';
import { RestoreControlRuntime } from '../dist/assets/restore-control-runtime.js';

class MemoryStorage {
  constructor() { this.map = new Map(); }
  getItem(key) { return this.map.get(key) ?? null; }
  setItem(key, value) { this.map.set(key, String(value)); }
  removeItem(key) { this.map.delete(key); }
  keys() { return [...this.map.keys()].sort(); }
}

class MemoryHistory {
  constructor() { this.state = {}; this.lastUrl = null; }
  replaceState(data, _unused, url) { this.state = data; if (url !== undefined) this.lastUrl = String(url); }
}

async function readStdinJson() {
  let raw = '';
  process.stdin.setEncoding('utf8');
  for await (const chunk of process.stdin) raw += chunk;
  return JSON.parse(raw);
}

async function waitForTerminal(runtime) {
  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    const view = runtime.view;
    if (view.snapshot && !['selecting', 'validating'].includes(view.snapshot.state)) return view;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error('restore browser session did not reach a terminal state');
}

const input = await readStdinJson();
const launch = new URL(input.launchUrl);
const frontendOrigin = String(input.frontendOrigin);
const storage = new MemoryStorage();
const history = new MemoryHistory();
const capture = captureRestoreBootstrap(
  { hash: launch.hash, pathname: launch.pathname, search: launch.search },
  history,
);

const browserFetch = async (url, init = {}) => {
  const headers = new Headers(init.headers ?? {});
  headers.set('Origin', frontendOrigin);
  return fetch(url, { ...init, headers });
};

const intervalHandles = new Map();
const timeoutHandles = new Map();
let nextHandle = 1;
const runtime = new RestoreControlRuntime({
  fetch: browserFetch,
  sessionStorage: storage,
  history,
  crypto: webcrypto,
  setInterval: (handler, ms) => { const id = nextHandle++; intervalHandles.set(id, setInterval(handler, ms)); return id; },
  clearInterval: (handle) => { const native = intervalHandles.get(handle); if (native) clearInterval(native); intervalHandles.delete(handle); },
  setTimeout: (handler, ms) => { const id = nextHandle++; timeoutHandles.set(id, setTimeout(() => { timeoutHandles.delete(id); handler(); }, ms)); return id; },
  clearTimeout: (handle) => { const native = timeoutHandles.get(handle); if (native) clearTimeout(native); timeoutHandles.delete(handle); },
});

try {
  await runtime.start(capture);
  if (runtime.view.availability !== 'ready' || !runtime.view.hasSession) throw new Error('bootstrap did not establish a ready session');
  await runtime.select();
  const terminal = await waitForTerminal(runtime);
  if (terminal.snapshot?.state !== 'accepted') throw new Error(`unexpected terminal state: ${terminal.snapshot?.state ?? 'none'}`);
  const replay = history.state?.[RESTORE_HISTORY_STATE_KEY];
  const sourceText = await readFile(new URL('../src/restore-control-runtime.ts', import.meta.url), 'utf8');
  if (sourceText.includes('localStorage')) throw new Error('runtime source contains localStorage');
  process.stdout.write(JSON.stringify({
    state: terminal.snapshot.state,
    filename: terminal.snapshot.filename,
    fragmentRemoved: history.lastUrl === `${launch.pathname}${launch.search}`,
    storedKeys: storage.keys(),
    expectedStorageKeys: Object.values(RESTORE_SESSION_STORAGE_KEYS).sort(),
    nextCommandSeq: replay?.nextCommandSeq ?? null,
    pending: replay?.pending ?? null,
  }));
} finally {
  runtime.dispose();
}
