import {
  InventoryCatalogWorkspaceFeedbackLifecycle,
  isStockMovementDto,
  isStockReconciliationDto,
  type InventoryCatalogMutation,
  type InventoryCatalogRead,
  type InventoryCatalogRoute,
} from './inventory-catalog-workspace-feedback.js';
import type { WorkspaceFinishResult, WorkspaceReadKind } from './core-workspace-feedback.js';

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
  }) {
    const started = this.lifecycle.startRead(options.route, options.operation, options.kind, options.contextKey);
    if (!started.accepted) return started;
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
    request: () => Promise<T>;
    validate: (value: T) => boolean;
    successMessage: string;
    apply: (value: T) => void;
    failed?: (error: unknown, ambiguous: boolean) => void;
  }) {
    const started = this.lifecycle.startMutation(options.route, options.operation, options.contextKey);
    if (!started.accepted) return started;
    this.deps.render();
    options.request().then((value) => {
      const result = this.lifecycle.finishMutationSuccess(started.owner, value, options.validate, options.successMessage);
      if (result.knownSuccess && result.canApply && this.deps.ownsRoute(options.route)) options.apply(value);
      this.present(options.route, result);
    }).catch((error) => {
      const result = this.lifecycle.finishMutationFailure(started.owner, error);
      if (result.accepted && this.deps.ownsRoute(options.route)) options.failed?.(error, result.reconciliationRequired);
      this.present(options.route, result);
    });
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
  }) {
    const started = this.lifecycle.startMutation('stockMovements', 'stock-movement-create', `lot:${options.lotId}`);
    if (!started.accepted) return started;
    this.deps.render();
    options.create().then((movement) => {
      const result = this.lifecycle.finishMutationSuccess(started.owner, movement, isStockMovementDto, 'Движение создано. Остаток пересчитан по истории движений.');
      if (result.knownSuccess && result.canApply && this.deps.ownsRoute('stockMovements')) options.applyCreated(movement);
      this.present('stockMovements', result);
      if (result.knownSuccess) this.reconcileStockMovement(options.lotId, options.reconcile, options.applyReconciliation, false, options.reconciliationFailed);
      else this.startQueuedStockReconciliation(options.lotId, options.reconcile, options.applyReconciliation, options.reconciliationFailed);
    }).catch((error) => {
      const result = this.lifecycle.finishMutationFailure(started.owner, error);
      if (result.accepted && !result.reconciliationRequired && this.deps.ownsRoute('stockMovements')) options.definiteFailure?.(error);
      this.present('stockMovements', result);
      this.startQueuedStockReconciliation(options.lotId, options.reconcile, options.applyReconciliation, options.reconciliationFailed);
    });
    return started;
  }

  reconcileStockMovement<T>(
    lotId: number,
    request: () => Promise<T>,
    apply: (value: T) => void,
    manual = true,
    failed?: (retainedSnapshot: boolean) => void,
  ) {
    const kind = this.lifecycle.reconciliationRequired('stockMovements') ? 'reconciliation' : 'mutation-refresh';
    return this.read({
      route: 'stockMovements',
      operation: 'stock-reconciliation',
      kind,
      contextKey: `lot:${lotId}:${manual ? 'manual' : 'automatic'}`,
      request,
      validate: isStockReconciliationDto,
      apply,
      failed,
    });
  }

  startQueuedStockReconciliation<T>(lotId: number, request: () => Promise<T>, apply: (value: T) => void, failed?: (retainedSnapshot: boolean) => void): void {
    if (!this.deps.ownsRoute('stockMovements')) return;
    if (!this.lifecycle.consumeQueuedReconciliation('stockMovements')) return;
    this.reconcileStockMovement(lotId, request, apply, false, failed);
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
