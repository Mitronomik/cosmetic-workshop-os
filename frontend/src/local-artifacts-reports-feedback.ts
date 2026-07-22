export type LocalArtifactRouteKey = 'backups' | 'exports' | 'reportDocuments' | 'reports';
export type LocalArtifactReadKind = 'initial' | 'refresh' | 'mutation-refresh';
export type LocalArtifactMutationKind = 'create-backup' | 'create-export' | 'create-report-document';
export type FeedbackTone = 'none' | 'neutral' | 'success' | 'warning' | 'error';
export type AnnouncementKind = 'none' | 'polite' | 'assertive';

export type LocalArtifactSnapshot<TRead> = { data: TRead; loadedAtRequestId: number };
export type LocalArtifactReadOwner = { requestId: number; routeGeneration: number; kind: LocalArtifactReadKind };
export type LocalArtifactMutationOwner = { requestId: number; routeGeneration: number; kind: LocalArtifactMutationKind; detached: boolean };
export type LocalArtifactStartResult = { accepted: boolean; requestId: number; routeGeneration: number; reason: string; kind?: LocalArtifactReadKind | LocalArtifactMutationKind };
export type LocalArtifactFinishResult = { accepted: boolean; detached: boolean; announcement: AnnouncementKind; message: string; focusKey: string | null; needsRefresh: boolean };

export type LocalArtifactFeedback = {
  tone: FeedbackTone;
  neutral: string;
  success: string;
  warning: string;
  error: string;
};

export type LocalArtifactLifecycleState<TRead, TCreated> = {
  routeGeneration: number;
  read: LocalArtifactReadOwner | null;
  mutation: LocalArtifactMutationOwner | null;
  snapshot: LocalArtifactSnapshot<TRead> | null;
  lastCreated: TCreated | null;
  feedback: LocalArtifactFeedback;
};

export type LocalArtifactLifecycleMessages = {
  loading: string;
  refreshing: string;
  initialError: string;
  refreshError: string;
  refreshSuccess: string;
  mutationBusy: string;
  mutationSuccess: string;
  mutationError: string;
  mutationAmbiguous: string;
  invalidMutationResponse: string;
  mutationRefreshWarning: string;
};

export type LocalArtifactLifecycleOptions<TCreated> = {
  route: LocalArtifactRouteKey;
  messages: LocalArtifactLifecycleMessages;
  focus?: Partial<Record<'initialError' | 'refreshSuccess' | 'mutationSuccess' | 'mutationError' | 'mutationRefreshWarning', string>>;
  validateCreated?: (created: TCreated) => boolean;
};

const idleFeedback = (): LocalArtifactFeedback => ({ tone: 'none', neutral: '', success: '', warning: '', error: '' });
const finishIgnored = (detached = false): LocalArtifactFinishResult => ({ accepted: false, detached, announcement: 'none', message: '', focusKey: null, needsRefresh: false });
const finishAccepted = (message: string, announcement: AnnouncementKind, focusKey: string | null, needsRefresh = false, detached = false): LocalArtifactFinishResult => ({ accepted: true, detached, announcement, message, focusKey, needsRefresh });

export class LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated = never> {
  readonly state: LocalArtifactLifecycleState<TRead, TCreated>;
  private nextRequestId = 0;
  private readonly options: LocalArtifactLifecycleOptions<TCreated>;

  constructor(options: LocalArtifactLifecycleOptions<TCreated>) {
    this.options = options;
    this.state = { routeGeneration: 0, read: null, mutation: null, snapshot: null, lastCreated: null, feedback: idleFeedback() };
  }

  enter() { this.state.routeGeneration += 1; this.state.read = null; if (this.state.mutation) this.state.mutation.detached = false; this.clearNeutral(); }
  leave() { this.state.routeGeneration += 1; this.state.read = null; if (this.state.mutation) this.state.mutation.detached = true; this.clearNeutral(); }

  startRead(kind: LocalArtifactReadKind): LocalArtifactStartResult {
    if (this.state.read) return { accepted: false, requestId: this.state.read.requestId, routeGeneration: this.state.routeGeneration, reason: 'read-active' };
    if (this.state.mutation && !this.state.mutation.detached) return { accepted: false, requestId: this.state.mutation.requestId, routeGeneration: this.state.routeGeneration, reason: 'mutation-active' };
    const owner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind };
    this.state.read = owner;
    this.state.feedback.error = '';
    if (kind === 'initial' && !this.state.snapshot) this.state.feedback = { ...idleFeedback(), tone: 'neutral', neutral: this.options.messages.loading };
    else if (kind === 'refresh') this.state.feedback = { ...this.state.feedback, tone: 'neutral', neutral: this.options.messages.refreshing, warning: '', error: '' };
    return { accepted: true, ...owner, reason: '' };
  }

  finishReadSuccess(owner: LocalArtifactReadOwner | LocalArtifactStartResult, data: TRead): LocalArtifactFinishResult {
    if (!this.readMatches(owner)) return finishIgnored();
    this.state.read = null;
    this.state.snapshot = { data, loadedAtRequestId: owner.requestId };
    const wasRefresh = owner.kind === 'refresh';
    this.state.feedback = { ...this.state.feedback, tone: wasRefresh ? 'success' : 'none', neutral: '', error: '', warning: '', success: wasRefresh ? this.options.messages.refreshSuccess : this.state.feedback.success };
    return finishAccepted(wasRefresh ? this.options.messages.refreshSuccess : '', wasRefresh ? 'polite' : 'none', wasRefresh ? this.options.focus?.refreshSuccess ?? null : null);
  }

  finishReadFailure(owner: LocalArtifactReadOwner | LocalArtifactStartResult): LocalArtifactFinishResult {
    if (!this.readMatches(owner)) return finishIgnored();
    this.state.read = null;
    this.clearNeutral();
    if (this.state.snapshot) {
      this.state.feedback.tone = 'warning';
      this.state.feedback.warning = owner.kind === 'mutation-refresh' ? this.options.messages.mutationRefreshWarning : this.options.messages.refreshError;
      this.state.feedback.error = '';
      return finishAccepted(this.state.feedback.warning, owner.kind === 'mutation-refresh' ? 'assertive' : 'polite', owner.kind === 'mutation-refresh' ? this.options.focus?.mutationRefreshWarning ?? null : null);
    }
    this.state.feedback = { ...idleFeedback(), tone: 'error', error: this.options.messages.initialError };
    return finishAccepted(this.state.feedback.error, 'assertive', this.options.focus?.initialError ?? null);
  }

  startMutation(kind: LocalArtifactMutationKind): LocalArtifactStartResult {
    if (this.state.mutation) return { accepted: false, requestId: this.state.mutation.requestId, routeGeneration: this.state.routeGeneration, reason: 'mutation-active' };
    if (this.state.read) return { accepted: false, requestId: this.state.read.requestId, routeGeneration: this.state.routeGeneration, reason: 'read-active' };
    const owner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind, detached: false };
    this.state.mutation = owner;
    this.state.feedback = { ...this.state.feedback, tone: 'neutral', neutral: this.options.messages.mutationBusy, error: '', warning: '' };
    return { accepted: true, ...owner, reason: '' };
  }

  finishMutationSuccess(owner: LocalArtifactStartResult, created: TCreated, message?: string): LocalArtifactFinishResult {
    const current = this.state.mutation;
    if (!this.mutationMatches(owner)) return finishIgnored(Boolean(current?.detached));
    const detached = Boolean(current?.detached);
    this.state.mutation = null;
    if (detached) return finishIgnored(true);
    const valid = this.options.validateCreated ? this.options.validateCreated(created) : true;
    this.clearNeutral();
    if (!valid) {
      this.state.feedback.tone = 'error';
      this.state.feedback.error = this.options.messages.invalidMutationResponse;
      return finishAccepted(this.state.feedback.error, 'assertive', this.options.focus?.mutationError ?? null, true);
    }
    this.state.lastCreated = created;
    const success = message || this.options.messages.mutationSuccess;
    this.state.feedback.tone = 'success';
    this.state.feedback.success = success;
    this.state.feedback.error = '';
    this.state.feedback.warning = '';
    return finishAccepted(success, 'polite', this.options.focus?.mutationSuccess ?? null, true);
  }

  finishMutationFailure(owner: LocalArtifactStartResult, ambiguous = false): LocalArtifactFinishResult {
    const current = this.state.mutation;
    if (!this.mutationMatches(owner)) return finishIgnored(Boolean(current?.detached));
    const detached = Boolean(current?.detached);
    this.state.mutation = null;
    if (detached) return finishIgnored(true);
    this.state.feedback = { ...this.state.feedback, tone: 'error', neutral: '', warning: '', success: '', error: ambiguous ? this.options.messages.mutationAmbiguous : this.options.messages.mutationError };
    return finishAccepted(this.state.feedback.error, 'assertive', this.options.focus?.mutationError ?? null, ambiguous);
  }

  clearTransientFeedback() { this.state.feedback = idleFeedback(); }
  private clearNeutral() { this.state.feedback.neutral = ''; if (this.state.feedback.tone === 'neutral') this.state.feedback.tone = 'none'; }
  private readMatches(owner: { requestId: number; routeGeneration: number; kind?: LocalArtifactReadKind | LocalArtifactMutationKind }) { return Boolean(this.state.read && this.state.read.requestId === owner.requestId && this.state.read.routeGeneration === owner.routeGeneration); }
  private mutationMatches(owner: { requestId: number; routeGeneration: number }) { return Boolean(this.state.mutation && this.state.mutation.requestId === owner.requestId && this.state.mutation.routeGeneration === owner.routeGeneration); }
}

export function transitionLocalArtifactRouteOwnership<TRead, TCreated>(lifecycles: Partial<Record<LocalArtifactRouteKey, LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated>>>, previous: LocalArtifactRouteKey | null, next: LocalArtifactRouteKey | null) {
  if (previous && previous !== next) lifecycles[previous]?.leave();
  if (next && previous !== next) lifecycles[next]?.enter();
}

export function bindEveryActionControl<T extends { addEventListener: (type: 'click', listener: () => void) => void }>(root: { querySelectorAll: (selector: string) => Iterable<T> }, selector: string, listener: () => void): number {
  let count = 0;
  for (const control of root.querySelectorAll(selector)) { control.addEventListener('click', listener); count += 1; }
  return count;
}
