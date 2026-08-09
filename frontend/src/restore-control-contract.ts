export const RESTORE_CONTROL_FRAGMENT_PREFIX = '#cw-control=';
export const RESTORE_ROUTE = '/backups/restore';
export const HEARTBEAT_INTERVAL_SECONDS = 15;
export const SESSION_EXPIRY_SECONDS = 60;

export const RESTORE_SESSION_STORAGE_KEYS = {
  controlOrigin: 'cw.restore.control_origin',
  runId: 'cw.restore.run_id',
  sessionToken: 'cw.restore.session_token',
} as const;

export const RESTORE_HISTORY_STATE_KEY = '__cwRestoreControl';

export type RestoreControlStateName =
  | 'idle'
  | 'selecting'
  | 'validating'
  | 'accepted'
  | 'rejected'
  | 'cancelled'
  | 'technical_failure';

export type RestoreControlAction = 'select' | 'cancel';

export type RestoreControlSnapshot = {
  run_id: string;
  state: RestoreControlStateName;
  generation: number;
  filename: string;
  message: string;
  compatibility: string | null;
  failure: string | null;
};

export type RestoreBootstrapResponse = {
  ok: true;
  run_id: string;
  control_origin: string;
  session_token: string;
  heartbeat_interval_seconds: number;
  session_expiry_seconds: number;
  state: RestoreControlSnapshot;
};

export type RestoreStateResponse = { ok: true; state: RestoreControlSnapshot };
export type RestoreCommandResponse = {
  ok: boolean;
  code: string;
  command_seq: number;
  state: RestoreControlSnapshot;
};
export type RestoreErrorResponse = { ok: false; code: string };

export type RestoreStoredSession = {
  controlOrigin: string;
  runId: string;
  sessionToken: string;
};

export type RestorePendingCommand = {
  action: RestoreControlAction;
  requestId: string;
  commandSeq: number;
};

export type RestoreReplayState = {
  version: 1;
  runId: string;
  nextCommandSeq: number;
  pending: RestorePendingCommand | null;
};

export type RestoreBootstrapCapture =
  | { kind: 'none' }
  | { kind: 'invalid' }
  | { kind: 'valid'; controlOrigin: string; bootstrapToken: string };

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export interface HistoryLike {
  state: unknown;
  replaceState(data: unknown, unused: string, url?: string | URL | null): void;
}

export interface LocationLike {
  hash: string;
  pathname: string;
  search: string;
}

const TOKEN_PATTERN = /^[A-Za-z0-9_-]{43,256}$/;
const REQUEST_ID_PATTERN = /^[0-9a-f]{32}$/;
const RUN_ID_PATTERN = /^[A-Za-z0-9_-]{8,160}$/;
const SAFE_CODE_PATTERN = /^[a-z0-9_]{1,80}$/;
const CONTROL_STATES = new Set<RestoreControlStateName>([
  'idle',
  'selecting',
  'validating',
  'accepted',
  'rejected',
  'cancelled',
  'technical_failure',
]);

function plainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function boundedString(value: unknown, max: number): value is string {
  return typeof value === 'string' && value.length <= max;
}

export function exactLoopbackControlOrigin(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    return (
      url.protocol === 'http:' &&
      url.hostname === '127.0.0.1' &&
      Boolean(url.port) &&
      url.username === '' &&
      url.password === '' &&
      url.pathname === '/' &&
      url.search === '' &&
      url.hash === ''
    );
  } catch {
    return false;
  }
}

export function parseRestoreBootstrapFragment(hash: string): RestoreBootstrapCapture {
  if (!hash.startsWith(RESTORE_CONTROL_FRAGMENT_PREFIX)) return { kind: 'none' };
  const raw = hash.slice(RESTORE_CONTROL_FRAGMENT_PREFIX.length);
  const separator = raw.indexOf(':');
  if (separator <= 0 || separator !== raw.lastIndexOf(':')) return { kind: 'invalid' };
  const portRaw = raw.slice(0, separator);
  const token = raw.slice(separator + 1);
  if (!/^\d{1,5}$/.test(portRaw) || !TOKEN_PATTERN.test(token)) return { kind: 'invalid' };
  const port = Number(portRaw);
  if (!Number.isInteger(port) || port < 1 || port > 65535) return { kind: 'invalid' };
  return { kind: 'valid', controlOrigin: `http://127.0.0.1:${port}`, bootstrapToken: token };
}

export function captureRestoreBootstrap(
  location: LocationLike,
  history: HistoryLike,
): RestoreBootstrapCapture {
  const capture = parseRestoreBootstrapFragment(location.hash);
  if (capture.kind !== 'none') {
    history.replaceState(history.state, '', `${location.pathname}${location.search}`);
  }
  return capture;
}

export function restoreSnapshotDto(value: unknown): RestoreControlSnapshot | null {
  if (!plainObject(value) || !exactKeys(value, ['run_id', 'state', 'generation', 'filename', 'message', 'compatibility', 'failure'])) return null;
  if (typeof value.run_id !== 'string' || !RUN_ID_PATTERN.test(value.run_id)) return null;
  if (typeof value.state !== 'string' || !CONTROL_STATES.has(value.state as RestoreControlStateName)) return null;
  if (!Number.isInteger(value.generation) || Number(value.generation) < 0) return null;
  if (!boundedString(value.filename, 160) || !boundedString(value.message, 1200)) return null;
  if (value.compatibility !== null && !boundedString(value.compatibility, 80)) return null;
  if (value.failure !== null && !boundedString(value.failure, 80)) return null;
  return value as RestoreControlSnapshot;
}

export function restoreBootstrapDto(value: unknown, expectedOrigin: string): RestoreBootstrapResponse | null {
  if (!plainObject(value) || !exactKeys(value, ['ok', 'run_id', 'control_origin', 'session_token', 'heartbeat_interval_seconds', 'session_expiry_seconds', 'state'])) return null;
  const state = restoreSnapshotDto(value.state);
  if (
    value.ok !== true ||
    typeof value.run_id !== 'string' ||
    !RUN_ID_PATTERN.test(value.run_id) ||
    value.run_id !== state?.run_id ||
    value.control_origin !== expectedOrigin ||
    !exactLoopbackControlOrigin(value.control_origin) ||
    typeof value.session_token !== 'string' ||
    !TOKEN_PATTERN.test(value.session_token) ||
    value.heartbeat_interval_seconds !== HEARTBEAT_INTERVAL_SECONDS ||
    value.session_expiry_seconds !== SESSION_EXPIRY_SECONDS ||
    !state
  ) return null;
  return { ...value, state } as RestoreBootstrapResponse;
}

export function restoreStateDto(value: unknown): RestoreStateResponse | null {
  if (!plainObject(value) || !exactKeys(value, ['ok', 'state']) || value.ok !== true) return null;
  const state = restoreSnapshotDto(value.state);
  return state ? { ok: true, state } : null;
}

export function restoreCommandDto(value: unknown): RestoreCommandResponse | null {
  if (!plainObject(value) || !exactKeys(value, ['ok', 'code', 'command_seq', 'state'])) return null;
  const state = restoreSnapshotDto(value.state);
  if (
    typeof value.ok !== 'boolean' ||
    typeof value.code !== 'string' ||
    !SAFE_CODE_PATTERN.test(value.code) ||
    !Number.isInteger(value.command_seq) ||
    Number(value.command_seq) < 1 ||
    !state
  ) return null;
  return { ok: value.ok, code: value.code, command_seq: Number(value.command_seq), state };
}

export function restoreErrorDto(value: unknown): RestoreErrorResponse | null {
  if (!plainObject(value) || !exactKeys(value, ['ok', 'code'])) return null;
  if (value.ok !== false || typeof value.code !== 'string' || !SAFE_CODE_PATTERN.test(value.code)) return null;
  return { ok: false, code: value.code };
}

export function readRestoreSession(storage: StorageLike): RestoreStoredSession | null {
  const controlOrigin = storage.getItem(RESTORE_SESSION_STORAGE_KEYS.controlOrigin);
  const runId = storage.getItem(RESTORE_SESSION_STORAGE_KEYS.runId);
  const sessionToken = storage.getItem(RESTORE_SESSION_STORAGE_KEYS.sessionToken);
  if (!exactLoopbackControlOrigin(controlOrigin) || !runId || !RUN_ID_PATTERN.test(runId) || !sessionToken || !TOKEN_PATTERN.test(sessionToken)) return null;
  return { controlOrigin, runId, sessionToken };
}

export function writeRestoreSession(storage: StorageLike, session: RestoreStoredSession): void {
  if (!exactLoopbackControlOrigin(session.controlOrigin) || !RUN_ID_PATTERN.test(session.runId) || !TOKEN_PATTERN.test(session.sessionToken)) throw new Error('invalid_restore_session_descriptor');
  storage.setItem(RESTORE_SESSION_STORAGE_KEYS.controlOrigin, session.controlOrigin);
  storage.setItem(RESTORE_SESSION_STORAGE_KEYS.runId, session.runId);
  storage.setItem(RESTORE_SESSION_STORAGE_KEYS.sessionToken, session.sessionToken);
}

export function clearRestoreSession(storage: StorageLike): void {
  storage.removeItem(RESTORE_SESSION_STORAGE_KEYS.controlOrigin);
  storage.removeItem(RESTORE_SESSION_STORAGE_KEYS.runId);
  storage.removeItem(RESTORE_SESSION_STORAGE_KEYS.sessionToken);
}

export function newRestoreRequestId(cryptoSource: Pick<Crypto, 'getRandomValues'>): string {
  const bytes = new Uint8Array(16);
  cryptoSource.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
}

export function readRestoreReplayState(rawState: unknown, runId: string): RestoreReplayState | null {
  if (!plainObject(rawState)) return null;
  const candidate = rawState[RESTORE_HISTORY_STATE_KEY];
  if (!plainObject(candidate) || !exactKeys(candidate, ['version', 'runId', 'nextCommandSeq', 'pending'])) return null;
  if (candidate.version !== 1 || candidate.runId !== runId || !Number.isInteger(candidate.nextCommandSeq) || Number(candidate.nextCommandSeq) < 1) return null;
  let pending: RestorePendingCommand | null = null;
  if (candidate.pending !== null) {
    if (!plainObject(candidate.pending) || !exactKeys(candidate.pending, ['action', 'requestId', 'commandSeq'])) return null;
    if ((candidate.pending.action !== 'select' && candidate.pending.action !== 'cancel') || typeof candidate.pending.requestId !== 'string' || !REQUEST_ID_PATTERN.test(candidate.pending.requestId) || !Number.isInteger(candidate.pending.commandSeq) || Number(candidate.pending.commandSeq) < 1) return null;
    pending = { action: candidate.pending.action, requestId: candidate.pending.requestId, commandSeq: Number(candidate.pending.commandSeq) };
  }
  return { version: 1, runId, nextCommandSeq: Number(candidate.nextCommandSeq), pending };
}

export function withRestoreReplayState(rawState: unknown, replay: RestoreReplayState): Record<string, unknown> {
  const base = plainObject(rawState) ? { ...rawState } : {};
  return { ...base, [RESTORE_HISTORY_STATE_KEY]: replay };
}
