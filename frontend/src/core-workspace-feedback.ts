export type WorkspaceReadKind =
  | 'initial'
  | 'refresh'
  | 'detail'
  | 'related'
  | 'reference'
  | 'calculation'
  | 'mutation-refresh'
  | 'reconciliation';

export type WorkspaceFeedback = {
  neutral: string;
  success: string;
  warning: string;
  error: string;
};

export type WorkspaceReadOwner<TRoute extends string, TRead extends string> = {
  requestId: number;
  route: TRoute;
  operation: TRead;
  kind: WorkspaceReadKind;
  contextKey: string;
  routeGeneration: number;
  reconciliationEpoch: number;
  mutationSettledEpoch: number;
  detachedMutationPending: boolean;
};

export type WorkspaceMutationOwner<TRoute extends string, TMutation extends string> = {
  requestId: number;
  route: TRoute;
  operation: TMutation;
  contextKey: string;
  routeGeneration: number;
  detached: boolean;
};

export type WorkspaceStartResult<TOwner> =
  | { accepted: true; owner: TOwner }
  | { accepted: false; reason: 'duplicate-read' | 'read-active' | 'mutation-active' | 'reconciliation-required' | 'inactive-route' };

export type WorkspaceFinishResult = {
  accepted: boolean;
  canApply: boolean;
  detached: boolean;
  knownSuccess: boolean;
  needsRefresh: boolean;
  reconciliationRequired: boolean;
  announcement: 'none' | 'polite' | 'assertive';
  announcementOwnerKey: string;
  focusKey: string | null;
  message: string;
};

export type WorkspaceRouteMessages = {
  loading: string;
  refreshing: string;
  refreshSuccess: string;
  initialError: string;
  refreshError: string;
  mutationBusy: string;
  mutationError: string;
  mutationAmbiguous: string;
  invalidResponse: string;
  reconciliationFailed: string;
};

type RouteState = {
  generation: number;
  feedback: WorkspaceFeedback;
  hasSnapshot: boolean;
  reconciliationRequired: boolean;
  reconciliationEpoch: number;
  mutationSettledEpoch: number;
  detachedMutationPending: boolean;
  queuedReconciliation: boolean;
};

const emptyFeedback = (): WorkspaceFeedback => ({ neutral: '', success: '', warning: '', error: '' });
const ignored = (reconciliationRequired = false, detached = false): WorkspaceFinishResult => ({
  accepted: false,
  canApply: false,
  detached,
  knownSuccess: false,
  needsRefresh: false,
  reconciliationRequired,
  announcement: 'none',
  announcementOwnerKey: '',
  focusKey: null,
  message: '',
});

/**
 * Small ownership primitive shared only by the two B3.4+B3.5 domain adapters.
 * Route data and domain mutations remain in their existing bounded runtimes.
 */
export class CoreWorkspaceFeedbackLifecycle<
  TRoute extends string,
  TRead extends string,
  TMutation extends string,
> {
  private requestId = 0;
  private activeRoute: TRoute | null = null;
  private readonly routeStates = new Map<TRoute, RouteState>();
  private readonly reads = new Map<string, WorkspaceReadOwner<TRoute, TRead>>();
  private readonly mutations = new Map<TRoute, WorkspaceMutationOwner<TRoute, TMutation>>();
  private readonly announcedOwners = new Set<string>();

  constructor(
    private readonly messages: Record<TRoute, WorkspaceRouteMessages>,
    private readonly focus: Record<TRoute, { retry: string; refresh: string; mutation: string; success: string }>,
  ) {}

  enter(route: TRoute): void {
    const state = this.state(route);
    state.generation += 1;
    this.activeRoute = route;
    state.feedback.neutral = '';
  }

  leave(route: TRoute): void {
    const state = this.state(route);
    state.generation += 1;
    if (this.activeRoute === route) this.activeRoute = null;
    for (const [key, owner] of this.reads) if (owner.route === route) this.reads.delete(key);
    const mutation = this.mutations.get(route);
    if (mutation) {
      mutation.detached = true;
      state.reconciliationRequired = true;
      state.reconciliationEpoch += 1;
      state.detachedMutationPending = true;
    }
    state.feedback.neutral = '';
  }

  transition(previous: TRoute | null, next: TRoute | null): void {
    if (previous === next) return;
    if (previous) this.leave(previous);
    if (next) this.enter(next);
  }

  ownsRoute(route: TRoute): boolean {
    return this.activeRoute === route;
  }

  feedback(route: TRoute): Readonly<WorkspaceFeedback> {
    return this.state(route).feedback;
  }

  hasSnapshot(route: TRoute): boolean {
    return this.state(route).hasSnapshot;
  }

  reconciliationRequired(route: TRoute): boolean {
    return this.state(route).reconciliationRequired;
  }

  mutationActive(route: TRoute): boolean {
    return Boolean(this.mutations.get(route) && !this.mutations.get(route)?.detached);
  }

  startRead(
    route: TRoute,
    operation: TRead,
    kind: WorkspaceReadKind,
    contextKey = '',
  ): WorkspaceStartResult<WorkspaceReadOwner<TRoute, TRead>> {
    if (!this.ownsRoute(route)) return { accepted: false, reason: 'inactive-route' };
    const key = this.readKey(route, operation);
    if (this.reads.has(key)) return { accepted: false, reason: 'duplicate-read' };
    if (this.mutationActive(route) && kind !== 'mutation-refresh') return { accepted: false, reason: 'mutation-active' };
    const state = this.state(route);
    const owner: WorkspaceReadOwner<TRoute, TRead> = {
      requestId: ++this.requestId,
      route,
      operation,
      kind,
      contextKey,
      routeGeneration: state.generation,
      reconciliationEpoch: state.reconciliationEpoch,
      mutationSettledEpoch: state.mutationSettledEpoch,
      detachedMutationPending: state.detachedMutationPending,
    };
    this.reads.set(key, owner);
    state.feedback.error = '';
    if (kind === 'initial' && !state.hasSnapshot) state.feedback = { ...emptyFeedback(), neutral: this.messages[route].loading };
    else if (kind === 'refresh') state.feedback = { ...emptyFeedback(), neutral: this.messages[route].refreshing };
    return { accepted: true, owner };
  }

  finishReadSuccess<T>(
    owner: WorkspaceReadOwner<TRoute, TRead>,
    value: T,
    validate: (value: T) => boolean = () => true,
  ): WorkspaceFinishResult {
    const state = this.state(owner.route);
    if (!this.readMatches(owner)) return ignored(state.reconciliationRequired);
    this.reads.delete(this.readKey(owner.route, owner.operation));
    if (!this.ownerOwnsPresentation(owner)) return ignored(state.reconciliationRequired);
    if (!validate(value)) {
      state.feedback = { ...emptyFeedback(), error: this.messages[owner.route].invalidResponse };
      return this.result(owner, false, false, 'assertive', this.focus[owner.route].retry, state.feedback.error);
    }
    state.hasSnapshot = true;
    const reconciliation = owner.kind === 'reconciliation';
    const canClear = reconciliation
      && owner.reconciliationEpoch === state.reconciliationEpoch
      && !state.detachedMutationPending
      && owner.mutationSettledEpoch >= state.mutationSettledEpoch;
    if (canClear) {
      state.reconciliationRequired = false;
      state.queuedReconciliation = false;
      state.feedback.warning = '';
    } else if (reconciliation && state.reconciliationRequired && !state.detachedMutationPending) {
      state.queuedReconciliation = true;
    }
    const manualRefresh = owner.kind === 'refresh';
    state.feedback.neutral = '';
    state.feedback.error = '';
    if (manualRefresh) state.feedback.success = this.messages[owner.route].refreshSuccess;
    return this.result(
      owner,
      true,
      false,
      manualRefresh ? 'polite' : 'none',
      manualRefresh ? this.focus[owner.route].refresh : null,
      manualRefresh ? state.feedback.success : '',
      state.queuedReconciliation,
    );
  }

  finishReadFailure(owner: WorkspaceReadOwner<TRoute, TRead>): WorkspaceFinishResult {
    const state = this.state(owner.route);
    if (!this.readMatches(owner)) return ignored(state.reconciliationRequired);
    this.reads.delete(this.readKey(owner.route, owner.operation));
    if (!this.ownerOwnsPresentation(owner)) return ignored(state.reconciliationRequired);
    const queued = owner.kind === 'reconciliation'
      && state.queuedReconciliation
      && !state.detachedMutationPending;
    state.feedback.neutral = '';
    if (state.hasSnapshot || owner.kind === 'mutation-refresh' || Boolean(state.feedback.success)) {
      state.feedback.error = '';
      state.feedback.warning = state.reconciliationRequired
        ? this.messages[owner.route].reconciliationFailed
        : this.messages[owner.route].refreshError;
      return this.result(owner, false, false, 'polite', state.reconciliationRequired ? this.focus[owner.route].refresh : null, state.feedback.warning, queued);
    }
    state.feedback.warning = '';
    state.feedback.error = this.messages[owner.route].initialError;
    return this.result(owner, false, false, 'assertive', this.focus[owner.route].retry, state.feedback.error, queued);
  }

  discardRead(owner: WorkspaceReadOwner<TRoute, TRead>): boolean {
    if (!this.readMatches(owner)) return false;
    this.reads.delete(this.readKey(owner.route, owner.operation));
    if (![...this.reads.values()].some((read) => read.route === owner.route)) this.state(owner.route).feedback.neutral = '';
    return true;
  }

  startMutation(
    route: TRoute,
    operation: TMutation,
    contextKey = '',
  ): WorkspaceStartResult<WorkspaceMutationOwner<TRoute, TMutation>> {
    if (!this.ownsRoute(route)) return { accepted: false, reason: 'inactive-route' };
    const state = this.state(route);
    if (state.reconciliationRequired) return { accepted: false, reason: 'reconciliation-required' };
    if (this.mutations.has(route)) return { accepted: false, reason: 'mutation-active' };
    if ([...this.reads.values()].some((owner) => owner.route === route)) return { accepted: false, reason: 'read-active' };
    const owner: WorkspaceMutationOwner<TRoute, TMutation> = {
      requestId: ++this.requestId,
      route,
      operation,
      contextKey,
      routeGeneration: state.generation,
      detached: false,
    };
    this.mutations.set(route, owner);
    state.feedback = { ...emptyFeedback(), neutral: this.messages[route].mutationBusy };
    return { accepted: true, owner };
  }

  finishMutationSuccess<T>(
    owner: WorkspaceMutationOwner<TRoute, TMutation>,
    value: T,
    validate: (value: T) => boolean,
    successMessage: string,
  ): WorkspaceFinishResult {
    const state = this.state(owner.route);
    const current = this.mutations.get(owner.route);
    if (!this.mutationMatches(owner)) return ignored(state.reconciliationRequired, Boolean(current?.detached));
    this.mutations.delete(owner.route);
    if (current?.detached || !this.ownerOwnsPresentation(owner)) {
      state.detachedMutationPending = false;
      state.mutationSettledEpoch += 1;
      state.reconciliationRequired = true;
      state.queuedReconciliation = true;
      return ignored(true, true);
    }
    state.feedback.neutral = '';
    if (!validate(value)) {
      state.reconciliationRequired = true;
      state.reconciliationEpoch += 1;
      state.queuedReconciliation = true;
      state.feedback = { ...emptyFeedback(), error: this.messages[owner.route].invalidResponse };
      return this.result(owner, false, false, 'assertive', this.focus[owner.route].refresh, state.feedback.error, true);
    }
    state.feedback = { ...emptyFeedback(), success: successMessage };
    return this.result(owner, true, true, 'polite', this.focus[owner.route].success, successMessage, true);
  }

  finishMutationFailure(
    owner: WorkspaceMutationOwner<TRoute, TMutation>,
    error: unknown,
  ): WorkspaceFinishResult {
    const state = this.state(owner.route);
    const current = this.mutations.get(owner.route);
    if (!this.mutationMatches(owner)) return ignored(state.reconciliationRequired, Boolean(current?.detached));
    this.mutations.delete(owner.route);
    if (current?.detached || !this.ownerOwnsPresentation(owner)) {
      state.detachedMutationPending = false;
      state.mutationSettledEpoch += 1;
      state.reconciliationRequired = true;
      state.queuedReconciliation = true;
      return ignored(true, true);
    }
    state.feedback.neutral = '';
    if (isAmbiguousTransportError(error)) {
      state.reconciliationRequired = true;
      state.reconciliationEpoch += 1;
      state.queuedReconciliation = true;
      state.feedback = { ...emptyFeedback(), warning: this.messages[owner.route].mutationAmbiguous };
      return this.result(owner, false, false, 'assertive', this.focus[owner.route].refresh, state.feedback.warning, true);
    }
    state.feedback = { ...emptyFeedback(), error: this.messages[owner.route].mutationError };
    return this.result(owner, false, false, 'assertive', this.focus[owner.route].mutation, state.feedback.error);
  }

  consumeQueuedReconciliation(route: TRoute): boolean {
    const state = this.state(route);
    if (!state.queuedReconciliation || state.detachedMutationPending) return false;
    state.queuedReconciliation = false;
    return true;
  }

  clearTransientFeedback(route: TRoute): void {
    const state = this.state(route);
    state.feedback = state.reconciliationRequired && state.feedback.warning
      ? { ...emptyFeedback(), warning: state.feedback.warning }
      : emptyFeedback();
  }

  shouldAnnounce(result: WorkspaceFinishResult): boolean {
    if (!result.accepted || result.announcement === 'none' || !result.announcementOwnerKey) return false;
    if (this.announcedOwners.has(result.announcementOwnerKey)) return false;
    this.announcedOwners.add(result.announcementOwnerKey);
    return true;
  }

  private state(route: TRoute): RouteState {
    let state = this.routeStates.get(route);
    if (!state) {
      state = {
        generation: 0,
        feedback: emptyFeedback(),
        hasSnapshot: false,
        reconciliationRequired: false,
        reconciliationEpoch: 0,
        mutationSettledEpoch: 0,
        detachedMutationPending: false,
        queuedReconciliation: false,
      };
      this.routeStates.set(route, state);
    }
    return state;
  }

  private readKey(route: TRoute, operation: TRead): string {
    return `${route}:${operation}`;
  }

  private readMatches(owner: WorkspaceReadOwner<TRoute, TRead>): boolean {
    const current = this.reads.get(this.readKey(owner.route, owner.operation));
    return Boolean(current && current.requestId === owner.requestId && current.routeGeneration === owner.routeGeneration);
  }

  private mutationMatches(owner: WorkspaceMutationOwner<TRoute, TMutation>): boolean {
    const current = this.mutations.get(owner.route);
    return Boolean(current && current.requestId === owner.requestId && current.routeGeneration === owner.routeGeneration);
  }

  private ownerOwnsPresentation(owner: { route: TRoute; routeGeneration: number }): boolean {
    return this.activeRoute === owner.route && this.state(owner.route).generation === owner.routeGeneration;
  }

  private result(
    owner: { route: TRoute; operation: string; requestId: number; routeGeneration: number },
    canApply: boolean,
    knownSuccess: boolean,
    announcement: WorkspaceFinishResult['announcement'],
    focusKey: string | null,
    message: string,
    needsRefresh = false,
  ): WorkspaceFinishResult {
    return {
      accepted: true,
      canApply,
      detached: false,
      knownSuccess,
      needsRefresh,
      reconciliationRequired: this.state(owner.route).reconciliationRequired,
      announcement,
      announcementOwnerKey: `${owner.route}:${owner.routeGeneration}:${owner.requestId}:${owner.operation}`,
      focusKey,
      message,
    };
  }
}

export function isAmbiguousTransportError(error: unknown): boolean {
  if (error && typeof error === 'object' && 'status' in error) return false;
  if (error instanceof TypeError) return true;
  return error instanceof Error && /network|failed to fetch|load failed|connection/i.test(error.message);
}
