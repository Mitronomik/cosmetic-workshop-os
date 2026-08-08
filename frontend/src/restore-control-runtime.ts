import {
  HEARTBEAT_INTERVAL_SECONDS,
  RESTORE_HISTORY_STATE_KEY,
  type RestoreBootstrapCapture,
  type RestoreControlAction,
  type RestoreControlSnapshot,
  type RestorePendingCommand,
  type RestoreReplayState,
  type RestoreStoredSession,
  type StorageLike,
  clearRestoreSession,
  newRestoreRequestId,
  readRestoreReplayState,
  readRestoreSession,
  restoreBootstrapDto,
  restoreCommandDto,
  restoreStateDto,
  withRestoreReplayState,
  writeRestoreSession,
} from './restore-control-contract.js';

export type RestoreBrowserAvailability = 'initializing' | 'ready' | 'unavailable' | 'network_error' | 'protocol_error';

export type RestoreControlView = {
  availability: RestoreBrowserAvailability;
  snapshot: RestoreControlSnapshot | null;
  pending: RestorePendingCommand | null;
  notice: string;
  hasSession: boolean;
  protocolSafe: boolean;
};

export interface RestoreControlEnvironment {
  fetch(input: string, init?: RequestInit): Promise<Response>;
  sessionStorage: StorageLike;
  history: { state: unknown; replaceState(data: unknown, unused: string, url?: string | URL | null): void };
  crypto: Pick<Crypto, 'getRandomValues'>;
  setInterval(handler: () => void, milliseconds: number): number;
  clearInterval(handle: number): void;
  setTimeout(handler: () => void, milliseconds: number): number;
  clearTimeout(handle: number): void;
}

const POLL_INTERVAL_MS = 250;
const OPEN_RESTART_GUIDANCE = 'Восстановление сейчас недоступно. Закройте эту вкладку и откройте или перезапустите «Мастерскую косметолога» обычным способом.';
const NETWORK_GUIDANCE = 'Не удалось связаться с локальным каналом восстановления. Рабочие данные не изменялись. Проверьте, что приложение запущено, и повторите попытку.';
const RETRY_GUIDANCE = 'Ответ на последнее действие не получен. Не запускайте новое действие: безопасно повторите именно предыдущую команду.';
const PROTOCOL_GUIDANCE = 'Сессия восстановления больше не может безопасно продолжать команды. Перезапустите «Мастерскую косметолога» и откройте восстановление снова.';

export class RestoreControlRuntime {
  private session: RestoreStoredSession | null = null;
  private replay: RestoreReplayState | null = null;
  private snapshot: RestoreControlSnapshot | null = null;
  private availability: RestoreBrowserAvailability = 'initializing';
  private notice = '';
  private protocolSafe = true;
  private heartbeatHandle: number | null = null;
  private pollHandle: number | null = null;
  private listeners = new Set<(view: RestoreControlView) => void>();
  private disposed = false;

  constructor(private readonly env: RestoreControlEnvironment) {}

  get view(): RestoreControlView {
    return {
      availability: this.availability,
      snapshot: this.snapshot,
      pending: this.replay?.pending ?? null,
      notice: this.notice,
      hasSession: this.session !== null,
      protocolSafe: this.protocolSafe,
    };
  }

  subscribe(listener: (view: RestoreControlView) => void): () => void {
    this.listeners.add(listener);
    listener(this.view);
    return () => this.listeners.delete(listener);
  }

  async start(capture: RestoreBootstrapCapture): Promise<void> {
    if (this.disposed) return;
    this.availability = 'initializing';
    this.notice = '';
    this.emit();
    if (capture.kind === 'invalid') {
      this.invalidateSession(OPEN_RESTART_GUIDANCE, 'unavailable');
      return;
    }
    if (capture.kind === 'valid') {
      clearRestoreSession(this.env.sessionStorage);
      this.clearReplayHistory();
      await this.bootstrap(capture.controlOrigin, capture.bootstrapToken);
      return;
    }
    await this.resume();
  }

  async refresh(): Promise<void> {
    if (!this.session || this.disposed) {
      this.availability = 'unavailable';
      this.notice = OPEN_RESTART_GUIDANCE;
      this.emit();
      return;
    }
    await this.refreshState();
  }

  async select(): Promise<void> { await this.beginCommand('select'); }
  async cancel(): Promise<void> { await this.beginCommand('cancel'); }

  async retryPending(): Promise<void> {
    if (!this.replay?.pending || !this.session || !this.protocolSafe || this.disposed) return;
    await this.sendPendingCommand(this.replay.pending);
  }

  syncReplayToHistory(): void {
    if (!this.replay) return;
    this.env.history.replaceState(withRestoreReplayState(this.env.history.state, this.replay), '');
  }

  dispose(): void {
    this.disposed = true;
    this.stopHeartbeat();
    this.stopPolling();
    this.listeners.clear();
  }

  private async bootstrap(controlOrigin: string, bootstrapToken: string): Promise<void> {
    let response: Response;
    try {
      response = await this.env.fetch(`${controlOrigin}/v1/bootstrap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bootstrap_token: bootstrapToken }),
        credentials: 'omit',
        cache: 'no-store',
        referrerPolicy: 'no-referrer',
      });
    } catch {
      this.invalidateSession(NETWORK_GUIDANCE, 'network_error');
      return;
    }
    const payload = await safeJson(response);
    if (!response.ok) {
      this.invalidateSession(OPEN_RESTART_GUIDANCE, 'unavailable');
      return;
    }
    const dto = restoreBootstrapDto(payload, controlOrigin);
    if (!dto) {
      this.invalidateSession(PROTOCOL_GUIDANCE, 'protocol_error');
      return;
    }
    this.session = { controlOrigin: dto.control_origin, runId: dto.run_id, sessionToken: dto.session_token };
    writeRestoreSession(this.env.sessionStorage, this.session);
    this.snapshot = dto.state;
    this.replay = { version: 1, runId: dto.run_id, nextCommandSeq: 1, pending: null };
    this.protocolSafe = true;
    this.availability = 'ready';
    this.notice = '';
    this.persistReplay();
    this.startHeartbeat();
    this.schedulePollingIfNeeded();
    this.emit();
  }

  private async resume(): Promise<void> {
    const stored = readRestoreSession(this.env.sessionStorage);
    if (!stored) {
      clearRestoreSession(this.env.sessionStorage);
      this.availability = 'unavailable';
      this.notice = OPEN_RESTART_GUIDANCE;
      this.emit();
      return;
    }
    this.session = stored;
    this.replay = readRestoreReplayState(this.env.history.state, stored.runId);
    this.protocolSafe = this.replay !== null;
    let response: Response;
    try {
      response = await this.authFetch('/v1/state', { method: 'GET' });
    } catch {
      this.availability = 'network_error';
      this.notice = this.replay?.pending ? RETRY_GUIDANCE : NETWORK_GUIDANCE;
      this.startHeartbeat();
      this.emit();
      return;
    }
    if (response.status === 401) {
      this.invalidateSession(OPEN_RESTART_GUIDANCE, 'unavailable');
      return;
    }
    const payload = await safeJson(response);
    const dto = response.ok ? restoreStateDto(payload) : null;
    if (!dto || dto.state.run_id !== stored.runId) {
      this.invalidateSession(PROTOCOL_GUIDANCE, 'protocol_error');
      return;
    }
    this.snapshot = dto.state;
    if (!this.adoptReplayAfterAuthenticatedState(dto.state)) return;
    this.startHeartbeat();
    this.schedulePollingIfNeeded();
    this.emit();
  }

  private adoptReplayAfterAuthenticatedState(state: RestoreControlSnapshot): boolean {
    if (this.replay) {
      this.protocolSafe = true;
      this.availability = 'ready';
      this.notice = this.replay.pending ? RETRY_GUIDANCE : '';
      return true;
    }
    if (state.state === 'idle' && state.generation === 0 && this.session) {
      this.replay = { version: 1, runId: this.session.runId, nextCommandSeq: 1, pending: null };
      this.protocolSafe = true;
      this.availability = 'ready';
      this.notice = '';
      this.persistReplay();
      return true;
    }
    this.protocolSafe = false;
    this.availability = 'protocol_error';
    this.notice = PROTOCOL_GUIDANCE;
    this.stopPolling();
    this.emit();
    return false;
  }

  private async beginCommand(action: RestoreControlAction): Promise<void> {
    if (!this.session || !this.replay || !this.protocolSafe || this.disposed) {
      this.notice = this.session ? PROTOCOL_GUIDANCE : OPEN_RESTART_GUIDANCE;
      this.emit();
      return;
    }
    if (this.replay.pending) {
      this.notice = RETRY_GUIDANCE;
      this.emit();
      return;
    }
    const pending: RestorePendingCommand = {
      action,
      requestId: newRestoreRequestId(this.env.crypto),
      commandSeq: this.replay.nextCommandSeq,
    };
    this.replay = { ...this.replay, pending };
    this.notice = '';
    this.persistReplay();
    this.emit();
    await this.sendPendingCommand(pending);
  }

  private async sendPendingCommand(pending: RestorePendingCommand): Promise<void> {
    if (!this.session || !this.replay || this.replay.pending?.requestId !== pending.requestId) return;
    const endpoint = pending.action === 'select' ? '/v1/restore/select' : '/v1/restore/cancel';
    let response: Response;
    try {
      response = await this.authFetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: pending.requestId, command_seq: pending.commandSeq }),
      });
    } catch {
      this.availability = 'network_error';
      this.notice = RETRY_GUIDANCE;
      this.emit();
      return;
    }
    if (response.status === 401) {
      this.invalidateSession(OPEN_RESTART_GUIDANCE, 'unavailable');
      return;
    }
    if (response.status === 409) {
      this.invalidateSession(PROTOCOL_GUIDANCE, 'protocol_error');
      return;
    }
    const payload = await safeJson(response);
    const dto = response.ok ? restoreCommandDto(payload) : null;
    if (!dto || dto.command_seq !== pending.commandSeq || dto.state.run_id !== this.session.runId) {
      this.invalidateSession(PROTOCOL_GUIDANCE, 'protocol_error');
      return;
    }
    this.snapshot = dto.state;
    this.replay = { ...this.replay, nextCommandSeq: pending.commandSeq + 1, pending: null };
    this.availability = 'ready';
    this.notice = '';
    this.persistReplay();
    this.schedulePollingIfNeeded();
    this.emit();
  }

  private async refreshState(): Promise<void> {
    if (!this.session || this.disposed) return;
    let response: Response;
    try {
      response = await this.authFetch('/v1/state', { method: 'GET' });
    } catch {
      this.availability = 'network_error';
      this.notice = this.replay?.pending ? RETRY_GUIDANCE : NETWORK_GUIDANCE;
      this.emit();
      return;
    }
    if (response.status === 401) {
      this.invalidateSession(OPEN_RESTART_GUIDANCE, 'unavailable');
      return;
    }
    const payload = await safeJson(response);
    const dto = response.ok ? restoreStateDto(payload) : null;
    if (!dto || dto.state.run_id !== this.session.runId) {
      this.invalidateSession(PROTOCOL_GUIDANCE, 'protocol_error');
      return;
    }
    this.snapshot = dto.state;
    if (!this.adoptReplayAfterAuthenticatedState(dto.state)) return;
    this.schedulePollingIfNeeded();
    this.emit();
  }

  private async heartbeat(): Promise<void> {
    if (!this.session || this.disposed) return;
    let response: Response;
    try {
      response = await this.authFetch('/v1/heartbeat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
    } catch {
      if (this.availability === 'ready') {
        this.availability = 'network_error';
        this.notice = this.replay?.pending ? RETRY_GUIDANCE : NETWORK_GUIDANCE;
        this.emit();
      }
      return;
    }
    if (response.status === 401) {
      this.invalidateSession(OPEN_RESTART_GUIDANCE, 'unavailable');
      return;
    }
    const payload = await safeJson(response);
    const dto = response.ok ? restoreStateDto(payload) : null;
    if (!dto || dto.state.run_id !== this.session.runId) {
      this.invalidateSession(PROTOCOL_GUIDANCE, 'protocol_error');
      return;
    }
    this.snapshot = dto.state;
    if (!this.adoptReplayAfterAuthenticatedState(dto.state)) return;
    this.schedulePollingIfNeeded();
    this.emit();
  }

  private authFetch(path: string, init: RequestInit): Promise<Response> {
    if (!this.session) return Promise.reject(new Error('restore_session_unavailable'));
    const headers = new Headers(init.headers ?? {});
    headers.set('Authorization', `Bearer ${this.session.sessionToken}`);
    return this.env.fetch(`${this.session.controlOrigin}${path}`, {
      ...init,
      headers,
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
    });
  }

  private startHeartbeat(): void {
    if (this.heartbeatHandle !== null || !this.session || this.disposed) return;
    this.heartbeatHandle = this.env.setInterval(() => { void this.heartbeat(); }, HEARTBEAT_INTERVAL_SECONDS * 1000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatHandle === null) return;
    this.env.clearInterval(this.heartbeatHandle);
    this.heartbeatHandle = null;
  }

  private schedulePollingIfNeeded(): void {
    this.stopPolling();
    if (!this.snapshot || (this.snapshot.state !== 'selecting' && this.snapshot.state !== 'validating') || !this.session || this.disposed) return;
    this.pollHandle = this.env.setTimeout(() => {
      this.pollHandle = null;
      void this.refreshState();
    }, POLL_INTERVAL_MS);
  }

  private stopPolling(): void {
    if (this.pollHandle === null) return;
    this.env.clearTimeout(this.pollHandle);
    this.pollHandle = null;
  }

  private persistReplay(): void {
    if (!this.replay) return;
    this.env.history.replaceState(withRestoreReplayState(this.env.history.state, this.replay), '');
  }

  private clearReplayHistory(): void {
    const state = this.env.history.state;
    const base: Record<string, unknown> = state && typeof state === 'object' && !Array.isArray(state) ? { ...(state as Record<string, unknown>) } : {};
    delete base[RESTORE_HISTORY_STATE_KEY];
    this.env.history.replaceState(base, '');
  }

  private invalidateSession(notice: string, availability: RestoreBrowserAvailability): void {
    clearRestoreSession(this.env.sessionStorage);
    this.stopHeartbeat();
    this.stopPolling();
    this.session = null;
    this.replay = null;
    this.snapshot = null;
    this.protocolSafe = availability !== 'protocol_error';
    this.availability = availability;
    this.notice = notice;
    this.clearReplayHistory();
    this.emit();
  }

  private emit(): void {
    if (this.disposed) return;
    const view = this.view;
    for (const listener of this.listeners) listener(view);
  }
}

async function safeJson(response: Response): Promise<unknown> {
  try { return await response.json(); } catch { return null; }
}
