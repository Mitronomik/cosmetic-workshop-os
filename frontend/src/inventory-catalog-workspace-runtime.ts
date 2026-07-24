import {
  InventoryCatalogWorkspaceFeedbackLifecycle,
  isStockReconciliationForLot,
  isStockMovementDto,
  type InventoryCatalogMutation,
  type InventoryCatalogRead,
  type InventoryCatalogRoute,
} from './inventory-catalog-workspace-feedback.js';
import type { WorkspaceFinishResult, WorkspaceReadKind, WorkspaceStartReason } from './core-workspace-feedback.js';

export type InventoryCatalogMutationSettlement = (result: WorkspaceFinishResult) => void;

export type InventoryCatalogRuntimeDependencies = {
  lifecycle?: InventoryCatalogWorkspaceFeedbackLifecycle;
  ownsRoute: (route: InventoryCatalogRoute) => boolean;
  render: () => void;
  announce: (message: string, kind: 'polite' | 'assertive') => void;
  focus: (key: string) => void;
};

export class InventoryCatalogWorkspaceRuntime {
  readonly lifecycle: InventoryCatalogWorkspaceFeedbackLifecycle;

  constructor(private readonly deps: InventoryCatalogRuntimeDependencies) {
    this.lifecycle = deps.lifecycle ?? new InventoryCatalogWorkspaceFeedbackLifecycle();
  }

  read<T>(options: {
    route: InventoryCatalogRoute;
    operation: InventoryCatalogRead;
    kind: WorkspaceReadKind;
    contextKey?: string;
    ownsContext?: () => boolean;
    request: () => Promise<T>;
    validate?: (value: T) => boolean;
    apply: (value: T) => void;
    failed?: (retainedSnapshot: boolean) => void;
    rejected?: (reason: WorkspaceStartReason) => void;
  }) {
    const started = this.lifecycle.startRead(options.route, options.operation, options.kind, options.contextKey);
    if (!started.accepted) {
      options.rejected?.(started.reason);
      return started;
    }
    this.deps.render();
    options.request().then((value) => {
      if (options.ownsContext && !options.ownsContext()) {
        this.lifecycle.discardRead(started.owner);
        return;
      }
      const result = this.lifecycle.finishReadSuccess(started.owner, value, options.validate);
      if (result.canApply && this.deps.ownsRoute(options.route)) options.apply(value);
      this.present(options.route, result);
    }).catch(() => {
      if (options.ownsContext && !options.ownsContext()) {
        this.lifecycle.discardRead(started.owner);
        return;
      }
      const result = this.lifecycle.finishReadFailure(started.owner);
      if (result.accepted && this.deps.ownsRoute(options.route)) options.failed?.(this.lifecycle.hasSnapshot(options.route));
      this.present(options.route, result);
    });
    return started;
  }

  mutate<T>(options: {
    route: InventoryCatalogRoute;
    operation: InventoryCatalogMutation;
    contextKey?: string;
    ownsContext?: () => boolean;
    request: () => Promise<T>;
    validate: (value: T) => boolean;
    successMessage: string;
    apply: (value: T) => void;
    failed?: (error: unknown, ambiguous: boolean) => void;
    rejected?: (reason: WorkspaceStartReason) => void;
    settled?: InventoryCatalogMutationSettlement;
  }) {
    const started = this.lifecycle.startMutation(options.route, options.operation, options.contextKey);
    if (!started.accepted) {
      options.rejected?.(started.reason);
      return started;
    }
    this.deps.render();
    let request: Promise<T>;
    try {
      request = options.request();
    } catch (error) {
      request = Promise.reject(error);
    }
    let settlement!: WorkspaceFinishResult;
    void request.then((value) => {
      if (options.ownsContext && !options.ownsContext()) {
        settlement = this.lifecycle.settleMutationObsolete(started.owner);
        return;
      }
      const result = this.lifecycle.finishMutationSuccess(started.owner, value, options.validate, options.successMessage);
      settlement = result;
      if (result.knownSuccess && result.canApply && this.deps.ownsRoute(options.route)) options.apply(value);
      if (result.accepted && !result.knownSuccess && result.reconciliationRequired && this.deps.ownsRoute(options.route)) {
        options.failed?.(new Error('invalid-authoritative-mutation-response'), true);
      }
      this.present(options.route, result);
    }, (error) => {
      if (options.ownsContext && !options.ownsContext()) {
        settlement = this.lifecycle.settleMutationObsolete(started.owner);
        return;
      }
      const result = this.lifecycle.finishMutationFailure(started.owner, error);
      settlement = result;
      if (result.accepted && this.deps.ownsRoute(options.route)) options.failed?.(error, result.reconciliationRequired);
      this.present(options.route, result);
    }).finally(() => options.settled?.(settlement));
    return started;
  }

  createStockMovement<TMovement, TReconciliation>(options: {
    lotId: number;
    create: () => Promise<TMovement>;
    reconcile: () => Promise<TReconciliation>;
    applyCreated: (movement: TMovement) => void;
    applyReconciliation: (value: TReconciliation) => void;
    definiteFailure?: (error: unknown) => void;
    reconciliationFailed?: (retainedSnapshot: boolean) => void;
    settled?: InventoryCatalogMutationSettlement;
  }) {
    const started = this.lifecycle.startMutation('stockMovements', 'stock-movement-create', `lot:${options.lotId}`);
    if (!started.accepted) return started;
    this.deps.render();
    let request: Promise<TMovement>;
    try {
      request = options.create();
    } catch (error) {
      request = Promise.reject(error);
    }
    let settlement!: WorkspaceFinishResult;
    void request.then((movement) => {
      const result = this.lifecycle.finishMutationSuccess(started.owner, movement, isStockMovementDto, 'Движение создано. Остаток пересчитан по истории движений.');
      settlement = result;
      if (result.knownSuccess && result.canApply && this.deps.ownsRoute('stockMovements')) options.applyCreated(movement);
      this.present('stockMovements', result);
      if (result.knownSuccess) this.reconcileStockMovement(options.lotId, options.reconcile, options.applyReconciliation, false, options.reconciliationFailed);
      else this.startQueuedStockReconciliation(options.lotId, options.reconcile, options.applyReconciliation, options.reconciliationFailed);
    }, (error) => {
      const result = this.lifecycle.finishMutationFailure(started.owner, error);
      settlement = result;
      if (result.accepted && !result.reconciliationRequired && this.deps.ownsRoute('stockMovements')) options.definiteFailure?.(error);
      this.present('stockMovements', result);
      this.startQueuedStockReconciliation(options.lotId, options.reconcile, options.applyReconciliation, options.reconciliationFailed);
    }).finally(() => options.settled?.(settlement));
    return started;
  }

  reconcileStockMovement<T>(
    lotId: number,
    request: () => Promise<T>,
    apply: (value: T) => void,
    manual = true,
    failed?: (retainedSnapshot: boolean) => void,
  ) {
    const contextKey = `lot:${lotId}`;
    const kind = this.lifecycle.isRequiredReconciliation('stockMovements', 'stock-reconciliation', contextKey)
      ? 'reconciliation'
      : manual ? 'detail' : 'mutation-refresh';
    return this.read({
      route: 'stockMovements',
      operation: 'stock-reconciliation',
      kind,
      contextKey,
      request,
      validate: (value) => isStockReconciliationForLot(value, lotId),
      apply,
      failed,
    });
  }

  stockMovementObligationLotId(): number | null {
    const obligation = this.lifecycle.reconciliationObligation('stockMovements');
    if (!obligation || obligation.mutationOperation !== 'stock-movement-create') return null;
    const match = obligation.readContextKey.match(/^lot:(\d+)$/);
    return match ? Number(match[1]) : null;
  }

  startQueuedStockReconciliation<T>(lotId: number, request: () => Promise<T>, apply: (value: T) => void, failed?: (retainedSnapshot: boolean) => void) {
    if (!this.deps.ownsRoute('stockMovements')) return null;
    const obligation = this.lifecycle.reconciliationObligation('stockMovements');
    if (!obligation || obligation.readOperation !== 'stock-reconciliation' || obligation.readContextKey !== `lot:${lotId}`) return null;
    const consumed = this.lifecycle.consumeQueuedReconciliation('stockMovements');
    if (!consumed || consumed.readContextKey !== `lot:${lotId}`) return null;
    return this.reconcileStockMovement(lotId, request, apply, false, failed);
  }

  private present(route: InventoryCatalogRoute, result: WorkspaceFinishResult): void {
    if (!result.accepted || !this.deps.ownsRoute(route)) return;
    this.deps.render();
    if (this.lifecycle.shouldAnnounce(result) && result.announcement !== 'none') {
      this.deps.announce(result.message, result.announcement);
    }
    if (result.focusKey) this.deps.focus(result.focusKey);
  }
}
