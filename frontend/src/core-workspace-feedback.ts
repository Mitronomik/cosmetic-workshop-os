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

export type WorkspaceReconciliationSpec<TRead extends string> = {
  readOperation: TRead;
  readContextKey: string;
};

export type WorkspaceReconciliationObligation<
  TRoute extends string,
  TRead extends string,
  TMutation extends string,
> = {
  route: TRoute;
  mutationOperation: TMutation;
  mutationContextKey: string;
  mutationRequestId: number;
  readOperation: TRead;
  readContextKey: string;
  epoch: number;
  mutationSettledEpoch: number;
  detachedMutationPending: boolean;
  queuedAutomatic: boolean;
  automaticAttemptConsumed: boolean;
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

export type WorkspaceMutationOwner<TRoute extends string, TRead extends string, TMutation extends string> = {
  requestId: number;
  route: TRoute;
  operation: TMutation;
  contextKey: string;
  routeGeneration: number;
  detached: boolean;
  reconciliation: WorkspaceReconciliationSpec<TRead>;
};

export type WorkspaceStartReason =
  | 'duplicate-read'
  | 'read-active'
  | 'mutation-active'
  | 'reconciliation-required'
  | 'inactive-route';

export type WorkspaceStartResult<TOwner> =
  | { accepted: true; owner: TOwner }
  | { accepted: false; reason: WorkspaceStartReason };

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

export function finalizeWorkspaceMutationUi(options: {
  clearBusy: () => void;
  ownsRoute: () => boolean;
  resumeRoute: () => void;
}): void {
  options.clearBusy();
  if (options.ownsRoute()) options.resumeRoute();
}

type RouteState<TRoute extends string, TRead extends string, TMutation extends string> = {
  generation: number;
  feedback: WorkspaceFeedback;
  hasSnapshot: boolean;
  reconciliationEpoch: number;
  mutationSettledEpoch: number;
  obligation: WorkspaceReconciliationObligation<TRoute, TRead, TMutation> | null;
};

type ReconciliationResolver<TRoute extends string, TRead extends string, TMutation extends string> = (
  route: TRoute,
  mutation: TMutation,
  mutationContextKey: string,
) => WorkspaceReconciliationSpec<TRead>;

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
 * Ownership primitive shared only by the two B3.4+B3.5 domain adapters.
 *
 * Read policy: the same route + operation + context is a duplicate, while a
 * different context explicitly supersedes the older owner for that operation.
 * Reconciliation endpoint knowledge remains in the domain resolver.
 */
export class CoreWorkspaceFeedbackLifecycle<
  TRoute extends string,
  TRead extends string,
  TMutation extends string,
> {
  private requestId = 0;
  private activeRoute: TRoute | null = null;
  private readonly routeStates = new Map<TRoute, RouteState<TRoute, TRead, TMutation>>();
  private readonly reads = new Map<string, WorkspaceReadOwner<TRoute, TRead>>();
  private readonly mutations = new Map<TRoute, WorkspaceMutationOwner<TRoute, TRead, TMutation>>();
  private readonly announcedOwners = new Set<string>();

  constructor(
    private readonly messages: Record<TRoute, WorkspaceRouteMessages>,
    private readonly focus: Record<TRoute, { retry: string; refresh: string; mutation: string; success: string }>,
    private readonly reconciliationFor: ReconciliationResolver<TRoute, TRead, TMutation>,
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
      this.ensureObligation(mutation, true);
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
    return this.state(route).obligation !== null;
  }

  reconciliationObligation(route: TRoute): Readonly<WorkspaceReconciliationObligation<TRoute, TRead, TMutation>> | null {
    const obligation = this.state(route).obligation;
    return obligation ? { ...obligation } : null;
  }

  isRequiredReconciliation(route: TRoute, operation: TRead, contextKey: string): boolean {
    const obligation = this.state(route).obligation;
    return Boolean(
      obligation
      && obligation.readOperation === operation
      && obligation.readContextKey === contextKey,
    );
  }

  mutationActive(route: TRoute): boolean {
    const mutation = this.mutations.get(route);
    return Boolean(mutation && !mutation.detached);
  }

  startRead(
    route: TRoute,
    operation: TRead,
    kind: WorkspaceReadKind,
    contextKey = '',
  ): WorkspaceStartResult<WorkspaceReadOwner<TRoute, TRead>> {
    if (!this.ownsRoute(route)) return { accepted: false, reason: 'inactive-route' };
    const operationOwners = [...this.reads.entries()].filter(([, owner]) => owner.route === route && owner.operation === operation);
    if (operationOwners.some(([, owner]) => owner.contextKey === contextKey)) {
      return { accepted: false, reason: 'duplicate-read' };
    }
    if (this.mutationActive(route) && kind !== 'mutation-refresh') {
      return { accepted: false, reason: 'mutation-active' };
    }
    // A different entity context is an explicit supersession boundary.
    for (const [key] of operationOwners) this.reads.delete(key);
    const state = this.state(route);
    const obligation = state.obligation;
    const owner: WorkspaceReadOwner<TRoute, TRead> = {
      requestId: ++this.requestId,
      route,
      operation,
      kind,
      contextKey,
      routeGeneration: state.generation,
      reconciliationEpoch: obligation?.epoch ?? 0,
      mutationSettledEpoch: state.mutationSettledEpoch,
      detachedMutationPending: obligation?.detachedMutationPending ?? false,
    };
    this.reads.set(this.readKey(route, operation, contextKey), owner);
    if (!obligation || this.readMatchesObligation(owner, obligation)) state.feedback.error = '';
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
    if (!this.readMatches(owner)) return ignored(Boolean(state.obligation));
    this.reads.delete(this.readKey(owner.route, owner.operation, owner.contextKey));
    if (!this.ownerOwnsPresentation(owner)) return ignored(Boolean(state.obligation));
    const obligation = state.obligation;
    const matchesObligation = Boolean(obligation && this.readMatchesObligation(owner, obligation));
    if (!validate(value)) {
      state.feedback.neutral = '';
      state.feedback.error = this.messages[owner.route].invalidResponse;
      if (matchesObligation) state.feedback.warning = this.messages[owner.route].reconciliationFailed;
      return this.result(owner, false, false, 'assertive', matchesObligation ? this.focus[owner.route].refresh : this.focus[owner.route].retry, state.feedback.error);
    }
    state.hasSnapshot = true;
    const canClear = owner.kind === 'reconciliation'
      && obligation !== null
      && matchesObligation
      && owner.reconciliationEpoch === obligation.epoch
      && !obligation.detachedMutationPending
      && owner.mutationSettledEpoch >= obligation.mutationSettledEpoch;
    if (canClear) {
      state.obligation = null;
      state.feedback.warning = '';
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
      Boolean(state.obligation),
    );
  }

  finishReadFailure(owner: WorkspaceReadOwner<TRoute, TRead>): WorkspaceFinishResult {
    const state = this.state(owner.route);
    if (!this.readMatches(owner)) return ignored(Boolean(state.obligation));
    this.reads.delete(this.readKey(owner.route, owner.operation, owner.contextKey));
    if (!this.ownerOwnsPresentation(owner)) return ignored(Boolean(state.obligation));
    const matchesObligation = Boolean(state.obligation && this.readMatchesObligation(owner, state.obligation));
    state.feedback.neutral = '';
    if (state.hasSnapshot || owner.kind === 'mutation-refresh' || Boolean(state.feedback.success)) {
      state.feedback.error = '';
      state.feedback.warning = matchesObligation
        ? this.messages[owner.route].reconciliationFailed
        : this.messages[owner.route].refreshError;
      return this.result(owner, false, false, 'polite', matchesObligation ? this.focus[owner.route].refresh : null, state.feedback.warning, matchesObligation);
    }
    state.feedback.warning = matchesObligation ? this.messages[owner.route].reconciliationFailed : '';
    state.feedback.error = this.messages[owner.route].initialError;
    return this.result(owner, false, false, 'assertive', matchesObligation ? this.focus[owner.route].refresh : this.focus[owner.route].retry, state.feedback.error, matchesObligation);
  }

  discardRead(owner: WorkspaceReadOwner<TRoute, TRead>): boolean {
    if (!this.readMatches(owner)) return false;
    this.reads.delete(this.readKey(owner.route, owner.operation, owner.contextKey));
    if (![...this.reads.values()].some((read) => read.route === owner.route)) this.state(owner.route).feedback.neutral = '';
    return true;
  }

  startMutation(
    route: TRoute,
    operation: TMutation,
    contextKey = '',
  ): WorkspaceStartResult<WorkspaceMutationOwner<TRoute, TRead, TMutation>> {
    if (!this.ownsRoute(route)) return { accepted: false, reason: 'inactive-route' };
    const state = this.state(route);
    if (state.obligation) return { accepted: false, reason: 'reconciliation-required' };
    if (this.mutations.has(route)) return { accepted: false, reason: 'mutation-active' };
    if ([...this.reads.values()].some((owner) => owner.route === route)) return { accepted: false, reason: 'read-active' };
    const owner: WorkspaceMutationOwner<TRoute, TRead, TMutation> = {
      requestId: ++this.requestId,
      route,
      operation,
      contextKey,
      routeGeneration: state.generation,
      detached: false,
      reconciliation: this.reconciliationFor(route, operation, contextKey),
    };
    this.mutations.set(route, owner);
    state.feedback = { ...emptyFeedback(), neutral: this.messages[route].mutationBusy };
    return { accepted: true, owner };
  }

  finishMutationSuccess<T>(
    owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>,
    value: T,
    validate: (value: T) => boolean,
    successMessage: string,
  ): WorkspaceFinishResult {
    const state = this.state(owner.route);
    const current = this.mutations.get(owner.route);
    if (!this.mutationMatches(owner)) return ignored(Boolean(state.obligation), Boolean(current?.detached));
    this.mutations.delete(owner.route);
    if (current?.detached || !this.ownerOwnsPresentation(owner)) {
      this.settleDetachedMutation(owner);
      return ignored(true, true);
    }
    state.feedback.neutral = '';
    if (!validate(value)) {
      this.ensureObligation(owner, false);
      state.feedback = { ...emptyFeedback(), error: this.messages[owner.route].invalidResponse };
      return this.result(owner, false, false, 'assertive', this.focus[owner.route].refresh, state.feedback.error, true);
    }
    state.feedback = { ...emptyFeedback(), success: successMessage };
    return this.result(owner, true, true, 'polite', this.focus[owner.route].success, successMessage, true);
  }

  finishMutationFailure(
    owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>,
    error: unknown,
  ): WorkspaceFinishResult {
    const state = this.state(owner.route);
    const current = this.mutations.get(owner.route);
    if (!this.mutationMatches(owner)) return ignored(Boolean(state.obligation), Boolean(current?.detached));
    this.mutations.delete(owner.route);
    if (current?.detached || !this.ownerOwnsPresentation(owner)) {
      this.settleDetachedMutation(owner);
      return ignored(true, true);
    }
    state.feedback.neutral = '';
    if (isAmbiguousTransportError(error)) {
      this.ensureObligation(owner, false);
      state.feedback = { ...emptyFeedback(), warning: this.messages[owner.route].mutationAmbiguous };
      return this.result(owner, false, false, 'assertive', this.focus[owner.route].refresh, state.feedback.warning, true);
    }
    state.feedback = { ...emptyFeedback(), error: this.messages[owner.route].mutationError };
    return this.result(owner, false, false, 'assertive', this.focus[owner.route].mutation, state.feedback.error);
  }

  settleMutationObsolete(owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>): WorkspaceFinishResult {
    const state = this.state(owner.route);
    if (!this.mutationMatches(owner)) return ignored(Boolean(state.obligation), owner.detached);
    this.mutations.delete(owner.route);
    this.ensureObligation(owner, false);
    state.mutationSettledEpoch += 1;
    const obligation = state.obligation;
    if (obligation) {
      obligation.detachedMutationPending = false;
      obligation.mutationSettledEpoch = state.mutationSettledEpoch;
    }
    return ignored(true, owner.detached);
  }

  cancelMutation(owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>): boolean {
    if (!this.mutationMatches(owner)) return false;
    this.mutations.delete(owner.route);
    this.state(owner.route).feedback.neutral = '';
    return true;
  }

  consumeQueuedReconciliation(route: TRoute): Readonly<WorkspaceReconciliationObligation<TRoute, TRead, TMutation>> | null {
    const obligation = this.state(route).obligation;
    if (!obligation || obligation.detachedMutationPending || !obligation.queuedAutomatic || obligation.automaticAttemptConsumed) return null;
    obligation.queuedAutomatic = false;
    obligation.automaticAttemptConsumed = true;
    return { ...obligation };
  }

  clearTransientFeedback(route: TRoute): void {
    const state = this.state(route);
    state.feedback = state.obligation && state.feedback.warning
      ? { ...emptyFeedback(), warning: state.feedback.warning }
      : emptyFeedback();
  }

  shouldAnnounce(result: WorkspaceFinishResult): boolean {
    if (!result.accepted || result.announcement === 'none' || !result.announcementOwnerKey) return false;
    if (this.announcedOwners.has(result.announcementOwnerKey)) return false;
    this.announcedOwners.add(result.announcementOwnerKey);
    return true;
  }

  private state(route: TRoute): RouteState<TRoute, TRead, TMutation> {
    let state = this.routeStates.get(route);
    if (!state) {
      state = {
        generation: 0,
        feedback: emptyFeedback(),
        hasSnapshot: false,
        reconciliationEpoch: 0,
        mutationSettledEpoch: 0,
        obligation: null,
      };
      this.routeStates.set(route, state);
    }
    return state;
  }

  private ensureObligation(owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>, detachedMutationPending: boolean): void {
    const state = this.state(owner.route);
    const existing = state.obligation;
    if (existing?.mutationRequestId === owner.requestId) {
      existing.detachedMutationPending = existing.detachedMutationPending || detachedMutationPending;
      return;
    }
    state.reconciliationEpoch += 1;
    state.obligation = {
      route: owner.route,
      mutationOperation: owner.operation,
      mutationContextKey: owner.contextKey,
      mutationRequestId: owner.requestId,
      readOperation: owner.reconciliation.readOperation,
      readContextKey: owner.reconciliation.readContextKey,
      epoch: state.reconciliationEpoch,
      mutationSettledEpoch: state.mutationSettledEpoch,
      detachedMutationPending,
      queuedAutomatic: true,
      automaticAttemptConsumed: false,
    };
  }

  private settleDetachedMutation(owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>): void {
    const state = this.state(owner.route);
    this.ensureObligation(owner, true);
    state.mutationSettledEpoch += 1;
    const obligation = state.obligation;
    if (!obligation) return;
    obligation.detachedMutationPending = false;
    obligation.mutationSettledEpoch = state.mutationSettledEpoch;
    if (!obligation.automaticAttemptConsumed) obligation.queuedAutomatic = true;
  }

  private readKey(route: TRoute, operation: TRead, contextKey: string): string {
    return `${route}:${operation}:${contextKey}`;
  }

  private readMatches(owner: WorkspaceReadOwner<TRoute, TRead>): boolean {
    const current = this.reads.get(this.readKey(owner.route, owner.operation, owner.contextKey));
    return Boolean(
      current
      && current.requestId === owner.requestId
      && current.routeGeneration === owner.routeGeneration
      && current.operation === owner.operation
      && current.contextKey === owner.contextKey,
    );
  }

  private mutationMatches(owner: WorkspaceMutationOwner<TRoute, TRead, TMutation>): boolean {
    const current = this.mutations.get(owner.route);
    return Boolean(
      current
      && current.requestId === owner.requestId
      && current.routeGeneration === owner.routeGeneration
      && current.operation === owner.operation
      && current.contextKey === owner.contextKey,
    );
  }

  private readMatchesObligation(
    owner: WorkspaceReadOwner<TRoute, TRead>,
    obligation: WorkspaceReconciliationObligation<TRoute, TRead, TMutation>,
  ): boolean {
    return owner.route === obligation.route
      && owner.operation === obligation.readOperation
      && owner.contextKey === obligation.readContextKey;
  }

  private ownerOwnsPresentation(owner: { route: TRoute; routeGeneration: number }): boolean {
    return this.activeRoute === owner.route && this.state(owner.route).generation === owner.routeGeneration;
  }

  private result(
    owner: { route: TRoute; operation: string; requestId: number; routeGeneration: number; contextKey: string },
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
      reconciliationRequired: this.reconciliationRequired(owner.route),
      announcement,
      announcementOwnerKey: `${owner.route}:${owner.routeGeneration}:${owner.requestId}:${owner.operation}:${owner.contextKey}`,
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
