import { LocalArtifactsReportsFeedbackLifecycle, type AnnouncementKind, type LocalArtifactFinishResult, type LocalArtifactMutationKind, type LocalArtifactReadKind, type LocalArtifactRouteKey, type LocalArtifactStartResult } from './local-artifacts-reports-feedback.js';
import { localArtifactReportPresentation, type LocalArtifactReportPresentation } from './local-artifacts-reports-presentation.js';

export type LocalArtifactRuntimeMessages = ConstructorParameters<typeof LocalArtifactsReportsFeedbackLifecycle<any, any>>[0]['messages'];
export type LocalArtifactRuntimeDeps<TRead, TCreated, TPayload> = {
  route: LocalArtifactRouteKey;
  mutationKind?: LocalArtifactMutationKind;
  messages: LocalArtifactRuntimeMessages;
  read: () => Promise<TRead>;
  mutate?: (payload: TPayload) => Promise<{ created: TCreated; message: string; commitAccepted?: () => void }>;
  validateCreated?: (created: TCreated) => boolean;
  lifecycle?: LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated>;
  createAvailable?: () => boolean;
  ownsRoute: () => boolean;
  applyRead: (snapshot: TRead) => void;
  applyCreated?: (created: TCreated) => void;
  render: () => void;
  announce: (message: string, kind: Exclude<AnnouncementKind, 'none'>) => void;
  focus: (key: string) => void;
};

export class LocalArtifactRouteRuntime<TRead, TCreated, TPayload = void> {
  readonly lifecycle: LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated>;
  private announcedOwners = new Set<string>();
  constructor(private readonly deps: LocalArtifactRuntimeDeps<TRead, TCreated, TPayload>) {
    this.lifecycle = deps.lifecycle ?? new LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated>({ route: deps.route, messages: deps.messages, validateCreated: deps.validateCreated, focus: this.focusMap(deps.route) });
  }
  enter() { this.lifecycle.enter(); }
  leave() { this.lifecycle.leave(); }
  presentation(): LocalArtifactReportPresentation { return localArtifactReportPresentation(this.deps.route, this.lifecycle, this.deps.createAvailable ? this.deps.createAvailable() : true); }

  load(kind: LocalArtifactReadKind = this.lifecycle.state.snapshot ? 'refresh' : 'initial') {
    const started = this.lifecycle.startRead(kind);
    if (!started.accepted) return started;
    this.deps.render();
    this.deps.read().then((snapshot) => {
      const result = this.lifecycle.finishReadSuccess(started, snapshot);
      if (!result.accepted || !this.deps.ownsRoute()) return;
      this.deps.applyRead(snapshot); this.deps.render(); this.complete(result); if (result.needsRefresh) this.queueReconciliation();
    }).catch(() => {
      const result = this.lifecycle.finishReadFailure(started);
      if (!result.accepted || !this.deps.ownsRoute()) return;
      this.deps.render(); this.complete(result); if (result.needsRefresh) this.queueReconciliation();
    });
    return started;
  }

  create(payload: TPayload) {
    if (!this.deps.mutate || !this.deps.mutationKind) return { accepted: false, requestId: 0, routeGeneration: this.lifecycle.state.routeGeneration, reason: 'no-mutation' } as LocalArtifactStartResult;
    const started = this.lifecycle.startMutation(this.deps.mutationKind);
    if (!started.accepted) return started;
    this.deps.render();
    this.deps.mutate(payload).then(({ created, message, commitAccepted }) => {
      const result = this.lifecycle.finishMutationSuccess(started, created, message);
      if (!result.accepted || !this.deps.ownsRoute()) { if (result.needsRefresh && this.deps.ownsRoute()) this.queueReconciliation(); return; }
      if (!result.reconciliationRequired) commitAccepted?.(); this.deps.applyCreated?.(created); this.deps.render(); this.complete(result);
      if (result.needsRefresh && !result.reconciliationRequired) this.load('mutation-refresh');
    }).catch((error) => {
      const result = this.lifecycle.finishMutationFailure(started, this.isAmbiguous(error));
      if (!result.accepted || !this.deps.ownsRoute()) { if (result.needsRefresh && this.deps.ownsRoute()) this.queueReconciliation(); return; }
      this.deps.render(); this.complete(result);
    });
    return started;
  }

  reconcile() { return this.load('reconciliation'); }

  private queueReconciliation() {
    if (!this.deps.ownsRoute() || this.lifecycle.state.read) { this.lifecycle.state.pendingReconciliationAfterRead = true; return; }
    this.lifecycle.state.pendingReconciliationAfterRead = false;
    this.load('reconciliation');
  }

  private complete(result: LocalArtifactFinishResult) {
    if (!result.accepted || !this.deps.ownsRoute()) return;
    if (result.message && result.announcement !== 'none' && result.announcementOwnerKey && !this.announcedOwners.has(result.announcementOwnerKey)) {
      this.announcedOwners.add(result.announcementOwnerKey);
      this.deps.announce(result.message, result.announcement);
    }
    if (result.focusKey) this.deps.focus(result.focusKey);
  }
  private isAmbiguous(error: unknown) {
    if (error instanceof TypeError) return true;
    if (error && typeof error === 'object' && 'status' in error) return false;
    if (error instanceof Error && /network|fetch|failed to fetch|load failed/i.test(error.message)) return true;
    return false;
  }
  private focusMap(route: LocalArtifactRouteKey) {
    const map = {
      backups: { initialError: 'b3-backups-retry', refreshSuccess: 'b3-backups-content', mutationSuccess: 'b3-backups-last-created', mutationError: 'b3-backups-create', mutationRefreshWarning: 'b3-backups-refresh', reconciliation: 'b3-backups-refresh' },
      exports: { initialError: 'b3-exports-retry', refreshSuccess: 'b3-exports-content', mutationSuccess: 'b3-exports-last-created', mutationError: 'b3-exports-create', mutationRefreshWarning: 'b3-exports-refresh', reconciliation: 'b3-exports-refresh' },
      reportDocuments: { initialError: 'b3-report-documents-retry', refreshSuccess: 'b3-report-documents-content', mutationSuccess: 'b3-report-documents-last-created', mutationError: 'b3-report-documents-create', mutationRefreshWarning: 'b3-report-documents-refresh', reconciliation: 'b3-report-documents-refresh' },
      reports: { initialError: 'b3-reports-retry', refreshSuccess: 'b3-reports-content', mutationSuccess: 'b3-reports-content', mutationError: 'b3-reports-content', mutationRefreshWarning: 'b3-reports-refresh', reconciliation: 'b3-reports-refresh' },
    } as const;
    return map[route];
  }
}

export function createLocalArtifactRouteRuntime<TRead, TCreated, TPayload = void>(deps: LocalArtifactRuntimeDeps<TRead, TCreated, TPayload>) { return new LocalArtifactRouteRuntime<TRead, TCreated, TPayload>(deps); }
