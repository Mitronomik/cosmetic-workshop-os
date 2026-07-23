export type LocalArtifactRouteKey = 'backups' | 'exports' | 'reportDocuments' | 'reports';
export type LocalArtifactReadKind = 'initial' | 'refresh' | 'mutation-refresh' | 'reconciliation';
export type LocalArtifactMutationKind = 'create-backup' | 'create-export' | 'create-report-document';
export type ReconciliationReason = 'ambiguous-mutation' | 'detached-mutation' | 'invalid-mutation-response' | null;
export type FeedbackTone = 'none' | 'neutral' | 'success' | 'warning' | 'error';
export type AnnouncementKind = 'none' | 'polite' | 'assertive';

export type LocalArtifactSnapshot<TRead> = { data: TRead; loadedAtRequestId: number };
export type LocalArtifactReadOwner = { requestId: number; routeGeneration: number; kind: LocalArtifactReadKind };
export type LocalArtifactMutationOwner = { requestId: number; routeGeneration: number; kind: LocalArtifactMutationKind; detached: boolean };
export type LocalArtifactStartResult = { accepted: boolean; requestId: number; routeGeneration: number; reason: string; kind?: LocalArtifactReadKind | LocalArtifactMutationKind };
export type LocalArtifactFinishResult = { accepted: boolean; detached: boolean; announcement: AnnouncementKind; message: string; focusKey: string | null; needsRefresh: boolean; reconciliationRequired: boolean };

export type LocalArtifactFeedback = { tone: FeedbackTone; neutral: string; success: string; warning: string; error: string };
export type LocalArtifactLifecycleState<TRead, TCreated> = {
  routeGeneration: number;
  read: LocalArtifactReadOwner | null;
  mutation: LocalArtifactMutationOwner | null;
  snapshot: LocalArtifactSnapshot<TRead> | null;
  lastCreated: TCreated | null;
  feedback: LocalArtifactFeedback;
  reconciliationRequired: boolean;
  reconciliationReason: ReconciliationReason;
};
export type LocalArtifactLifecycleMessages = {
  loading: string; refreshing: string; reconciling: string; initialError: string; refreshError: string; refreshSuccess: string;
  mutationBusy: string; mutationSuccess: string; mutationError: string; mutationAmbiguous: string; invalidMutationResponse: string; mutationRefreshWarning: string; reconciliationFailed: string;
};
export type LocalArtifactLifecycleOptions<TCreated> = {
  route: LocalArtifactRouteKey;
  messages: LocalArtifactLifecycleMessages;
  focus?: Partial<Record<'initialError' | 'refreshSuccess' | 'mutationSuccess' | 'mutationError' | 'mutationRefreshWarning' | 'reconciliation', string>>;
  validateCreated?: (created: TCreated) => boolean;
};

const idleFeedback = (): LocalArtifactFeedback => ({ tone: 'none', neutral: '', success: '', warning: '', error: '' });
const ignored = (detached = false, needsRefresh = false, reconciliationRequired = false): LocalArtifactFinishResult => ({ accepted: false, detached, announcement: 'none', message: '', focusKey: null, needsRefresh, reconciliationRequired });
const accepted = (message: string, announcement: AnnouncementKind, focusKey: string | null, needsRefresh = false, reconciliationRequired = false, detached = false): LocalArtifactFinishResult => ({ accepted: true, detached, announcement, message, focusKey, needsRefresh, reconciliationRequired });

export class LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated = never> {
  readonly state: LocalArtifactLifecycleState<TRead, TCreated>;
  private nextRequestId = 0;
  constructor(private readonly options: LocalArtifactLifecycleOptions<TCreated>) {
    this.state = { routeGeneration: 0, read: null, mutation: null, snapshot: null, lastCreated: null, feedback: idleFeedback(), reconciliationRequired: false, reconciliationReason: null };
  }

  enter() { this.state.routeGeneration += 1; this.state.read = null; this.clearNeutral(); }
  leave() { this.state.routeGeneration += 1; this.state.read = null; if (this.state.mutation) { this.state.mutation.detached = true; this.requireReconciliation('detached-mutation'); } this.clearNeutral(); }

  startRead(kind: LocalArtifactReadKind): LocalArtifactStartResult {
    if (this.state.read) return { accepted: false, requestId: this.state.read.requestId, routeGeneration: this.state.routeGeneration, reason: 'read-active', kind: this.state.read.kind };
    if (this.state.mutation && !this.state.mutation.detached) return { accepted: false, requestId: this.state.mutation.requestId, routeGeneration: this.state.routeGeneration, reason: 'mutation-active', kind: this.state.mutation.kind };
    const owner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind };
    this.state.read = owner;
    this.state.feedback.error = '';
    if (kind === 'initial' && !this.state.snapshot) this.state.feedback = { ...idleFeedback(), tone: 'neutral', neutral: this.options.messages.loading };
    else if (kind === 'refresh') this.state.feedback = { ...this.state.feedback, tone: 'neutral', neutral: this.options.messages.refreshing, warning: '', error: '' };
    else if (kind === 'reconciliation' || kind === 'mutation-refresh') this.state.feedback = { ...this.state.feedback, tone: 'neutral', neutral: this.options.messages.reconciling, error: '' };
    return { accepted: true, ...owner, reason: '' };
  }

  finishReadSuccess(owner: LocalArtifactReadOwner | LocalArtifactStartResult, data: TRead): LocalArtifactFinishResult {
    if (!this.readMatches(owner)) return ignored(false, false, this.state.reconciliationRequired);
    this.state.read = null;
    this.state.snapshot = { data, loadedAtRequestId: owner.requestId };
    const wasRefresh = owner.kind === 'refresh';
    const wasReconciliation = owner.kind === 'reconciliation' || owner.kind === 'mutation-refresh';
    if (wasReconciliation) { this.state.reconciliationRequired = false; this.state.reconciliationReason = null; }
    this.state.feedback = { ...this.state.feedback, tone: wasRefresh ? 'success' : 'none', neutral: '', error: '', warning: '', success: wasRefresh ? this.options.messages.refreshSuccess : this.state.feedback.success };
    return accepted(wasRefresh ? this.options.messages.refreshSuccess : '', wasRefresh ? 'polite' : 'none', wasRefresh ? this.options.focus?.refreshSuccess ?? null : null, false, this.state.reconciliationRequired);
  }

  finishReadFailure(owner: LocalArtifactReadOwner | LocalArtifactStartResult): LocalArtifactFinishResult {
    if (!this.readMatches(owner)) return ignored(false, false, this.state.reconciliationRequired);
    this.state.read = null;
    this.clearNeutral();
    if (this.state.snapshot) {
      this.state.feedback.tone = 'warning';
      this.state.feedback.warning = owner.kind === 'mutation-refresh' ? this.options.messages.mutationRefreshWarning : this.state.reconciliationRequired ? this.options.messages.reconciliationFailed : this.options.messages.refreshError;
      this.state.feedback.error = '';
      const focusKey = this.state.reconciliationRequired ? this.options.focus?.reconciliation ?? null : owner.kind === 'mutation-refresh' ? this.options.focus?.mutationRefreshWarning ?? null : null;
      return accepted(this.state.feedback.warning, 'polite', focusKey, this.state.reconciliationRequired, this.state.reconciliationRequired);
    }
    this.state.feedback = { ...idleFeedback(), tone: 'error', error: this.options.messages.initialError };
    return accepted(this.state.feedback.error, 'assertive', this.options.focus?.initialError ?? null, false, this.state.reconciliationRequired);
  }

  startMutation(kind: LocalArtifactMutationKind): LocalArtifactStartResult {
    if (this.state.reconciliationRequired) return { accepted: false, requestId: 0, routeGeneration: this.state.routeGeneration, reason: 'reconciliation-required', kind };
    if (this.state.mutation) return { accepted: false, requestId: this.state.mutation.requestId, routeGeneration: this.state.routeGeneration, reason: 'mutation-active', kind: this.state.mutation.kind };
    if (this.state.read) return { accepted: false, requestId: this.state.read.requestId, routeGeneration: this.state.routeGeneration, reason: 'read-active', kind: this.state.read.kind };
    const owner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind, detached: false };
    this.state.mutation = owner;
    this.state.feedback = { ...this.state.feedback, tone: 'neutral', neutral: this.options.messages.mutationBusy, error: '', warning: '' };
    return { accepted: true, ...owner, reason: '' };
  }

  finishMutationSuccess(owner: LocalArtifactStartResult, created: TCreated, message?: string): LocalArtifactFinishResult {
    const current = this.state.mutation;
    if (!this.mutationMatches(owner)) return ignored(Boolean(current?.detached), false, this.state.reconciliationRequired);
    const detached = Boolean(current?.detached);
    this.state.mutation = null;
    if (detached) { this.requireReconciliation('detached-mutation'); return ignored(true, true, true); }
    const valid = this.options.validateCreated ? this.options.validateCreated(created) : true;
    this.clearNeutral();
    if (!valid) {
      this.requireReconciliation('invalid-mutation-response');
      this.state.feedback.tone = 'error'; this.state.feedback.error = this.options.messages.invalidMutationResponse;
      return accepted(this.state.feedback.error, 'assertive', this.options.focus?.mutationError ?? null, true, true);
    }
    this.state.lastCreated = created;
    const success = message || this.options.messages.mutationSuccess;
    this.state.feedback.tone = 'success'; this.state.feedback.success = success; this.state.feedback.error = ''; this.state.feedback.warning = '';
    return accepted(success, 'polite', this.options.focus?.mutationSuccess ?? null, true, false);
  }

  finishMutationFailure(owner: LocalArtifactStartResult, ambiguous = false): LocalArtifactFinishResult {
    const current = this.state.mutation;
    if (!this.mutationMatches(owner)) return ignored(Boolean(current?.detached), false, this.state.reconciliationRequired);
    const detached = Boolean(current?.detached);
    this.state.mutation = null;
    if (detached) { this.requireReconciliation('detached-mutation'); return ignored(true, true, true); }
    if (ambiguous) {
      this.requireReconciliation('ambiguous-mutation');
      this.state.feedback = { ...this.state.feedback, tone: 'warning', neutral: '', warning: this.options.messages.mutationAmbiguous, error: '' };
      return accepted(this.state.feedback.warning, 'assertive', this.options.focus?.reconciliation ?? null, true, true);
    }
    this.state.feedback = { ...this.state.feedback, tone: 'error', neutral: '', warning: '', success: '', error: this.options.messages.mutationError };
    return accepted(this.state.feedback.error, 'assertive', this.options.focus?.mutationError ?? null);
  }

  clearTransientFeedback() { this.state.feedback = idleFeedback(); }
  private requireReconciliation(reason: Exclude<ReconciliationReason, null>) { this.state.reconciliationRequired = true; this.state.reconciliationReason = reason; }
  private clearNeutral() { this.state.feedback.neutral = ''; if (this.state.feedback.tone === 'neutral') this.state.feedback.tone = 'none'; }
  private readMatches(owner: { requestId: number; routeGeneration: number }) { return Boolean(this.state.read && this.state.read.requestId === owner.requestId && this.state.read.routeGeneration === owner.routeGeneration); }
  private mutationMatches(owner: { requestId: number; routeGeneration: number }) { return Boolean(this.state.mutation && this.state.mutation.requestId === owner.requestId && this.state.mutation.routeGeneration === owner.routeGeneration); }
}

export function transitionLocalArtifactRouteOwnership<TRead, TCreated>(lifecycles: Partial<Record<LocalArtifactRouteKey, LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated>>>, previous: LocalArtifactRouteKey | null, next: LocalArtifactRouteKey | null) {
  if (previous && previous !== next) lifecycles[previous]?.leave();
  if (next && previous !== next) lifecycles[next]?.enter();
}

export function bindEveryActionControl<T extends { addEventListener: (type: 'click', listener: () => void) => void }>(root: { querySelectorAll: (selector: string) => Iterable<T> }, selector: string, listener: () => void): number {
  let count = 0; for (const control of root.querySelectorAll(selector)) { control.addEventListener('click', listener); count += 1; } return count;
}
