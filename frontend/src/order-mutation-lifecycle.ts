import { clearFieldValidation, type FormValidationState } from './form-validation.js';

export type OrderFormMode = 'create' | 'edit';
export type OrderSourceType = 'recipe_version' | 'client_recipe';
export type OrderContextSnapshot = {
  contextToken: number;
  targetedValidationToken: number;
  routeGeneration: number;
  formMode: OrderFormMode;
  editedOrderId: number | null;
  selectedOrderId: number | null;
  showForm: boolean;
};
export type OrderContextState = OrderContextSnapshot;

export type OrderRequestKind = 'list' | 'postSaveRefresh' | 'reference' | 'detail' | 'readiness' | 'production' | 'productionHistory' | 'productionReconciliation' | 'cancel' | 'archive';
export type OrderRequestSnapshot = OrderContextSnapshot & {
  kind: OrderRequestKind;
  generation: number;
  submitToken: number;
  reconciliationEpoch?: number;
  savedOrderId?: number | null;
  requestedOrderId?: number | null;
};
export type OrderSubmitSnapshot = OrderContextSnapshot & { submitToken: number };

export type OrderSharedFeedback = {
  neutral: string;
  success: string;
  warning: string;
  error: string;
};

export type OrderRequestSettlement = {
  accepted: boolean;
  canPresent: boolean;
  detached: boolean;
};

export type OrderFocusTicket = {
  routeGeneration: number;
  contextToken: number;
  targetedValidationToken: number;
  focusToken: number;
  target: string;
};

export type OrderProductionReconciliationObligation = {
  operation: 'production';
  orderId: number;
  productionGeneration: number;
  routeGeneration: number;
  epoch: number;
  detachedSettlement: boolean;
  automaticAttemptConsumed: boolean;
};

export type OrderTransientRequestOwner = {
  kind: 'readiness' | 'production' | 'productionHistory' | 'productionReconciliation' | 'cancel' | 'archive';
  generation: number;
  orderId: number;
} | null;
export type OrderPersistentWriteOwner = {
  kind: 'production' | 'cancel' | 'archive';
  generation: number;
  orderId: number;
};
export type OrderOperationState = {
  owner: OrderTransientRequestOwner;
  loadingOrderId: number | null;
};
export type OrderOperationError = { orderId: number; message: string } | null;
export type OrderProductionGuardOrder = { id: number; is_active: boolean; status: string; updated_at: string } | null | undefined;
export type OrderProductionGuardReadiness = {
  order_id: number;
  can_produce: boolean;
  status: 'ready' | 'blocked' | 'warning';
} | null | undefined;

export type OrderFormErrorOrigin = 'recipe_source' | 'recipe_version_id' | 'client_recipe_id';
export type OrderValidationProvenance = { formErrors: Array<{ origin: OrderFormErrorOrigin; message: string }> };

export type OrderWorkspaceState = {
  formMode: OrderFormMode;
  editedOrderId: number | null;
  selectedOrderId: number | null;
  showForm: boolean;
};

export function emptyOrderValidationProvenance(): OrderValidationProvenance {
  return { formErrors: [] };
}

export function orderReadCanRender(snapshot: OrderContextSnapshot, current: OrderContextState): boolean {
  return snapshot.contextToken === current.contextToken
    && snapshot.targetedValidationToken === current.targetedValidationToken
    && snapshot.formMode === current.formMode
    && snapshot.editedOrderId === current.editedOrderId
    && snapshot.selectedOrderId === current.selectedOrderId
    && snapshot.showForm === current.showForm;
}

export class OrderMutationController {
  private contextToken = 0;
  private targetedValidationToken = 0;
  private submitToken = 0;
  private submitting = false;
  private routeGeneration = 0;
  private routeActive: boolean;
  private reconciliationEpoch = 0;
  private focusToken = 0;
  private productionReconciliation: OrderProductionReconciliationObligation | null = null;
  private feedbackState: OrderSharedFeedback = { neutral: '', success: '', warning: '', error: '' };
  private readonly settledRequests = new Set<string>();
  private readonly announcedResults = new Set<string>();
  private generations: Record<OrderRequestKind, number> = {
    list: 0,
    postSaveRefresh: 0,
    reference: 0,
    detail: 0,
    readiness: 0,
    production: 0,
    productionHistory: 0,
    productionReconciliation: 0,
    cancel: 0,
    archive: 0,
  };

  constructor(initialRouteActive = true) {
    this.routeActive = initialRouteActive;
  }

  snapshot(workspace: OrderWorkspaceState): OrderContextSnapshot {
    return {
      contextToken: this.contextToken,
      targetedValidationToken: this.targetedValidationToken,
      routeGeneration: this.routeGeneration,
      formMode: workspace.formMode,
      editedOrderId: workspace.editedOrderId,
      selectedOrderId: workspace.selectedOrderId,
      showForm: workspace.showForm,
    };
  }

  getContextToken(): number { return this.contextToken; }
  getTargetedValidationToken(): number { return this.targetedValidationToken; }
  getRouteGeneration(): number { return this.routeGeneration; }
  isSubmitting(): boolean { return this.submitting; }
  ownsRoute(): boolean { return this.routeActive; }

  enterRoute(): void {
    this.routeGeneration += 1;
    this.routeActive = true;
    this.feedbackState.neutral = '';
  }

  leaveRoute(): void {
    this.routeGeneration += 1;
    this.routeActive = false;
    this.feedbackState.neutral = '';
    for (const kind of ['list', 'postSaveRefresh', 'reference', 'detail', 'readiness', 'productionHistory', 'productionReconciliation'] as const) {
      this.invalidateRequest(kind);
    }
  }

  transitionRoute(wasOrders: boolean, isOrders: boolean): void {
    if (wasOrders === isOrders) return;
    if (wasOrders) this.leaveRoute();
    if (isOrders) this.enterRoute();
  }

  feedback(): Readonly<OrderSharedFeedback> {
    return this.feedbackState;
  }

  setNeutralFeedback(message: string): void {
    this.feedbackState = { neutral: message, success: '', warning: '', error: '' };
  }

  setSuccessFeedback(message: string): void {
    this.feedbackState = { neutral: '', success: message, warning: '', error: '' };
  }

  setWarningFeedback(message: string, preserveSuccess = false): void {
    this.feedbackState = {
      neutral: '',
      success: preserveSuccess ? this.feedbackState.success : '',
      warning: message,
      error: '',
    };
  }

  setErrorFeedback(message: string): void {
    this.feedbackState = { neutral: '', success: '', warning: '', error: message };
  }

  clearTransientFeedback(): void {
    this.feedbackState = { neutral: '', success: '', warning: '', error: '' };
  }

  shouldAnnounce(
    snapshot: OrderRequestSnapshot | OrderSubmitSnapshot,
    channel: 'polite' | 'assertive',
  ): boolean {
    if (!this.routeActive || snapshot.routeGeneration !== this.routeGeneration) return false;
    const key = 'kind' in snapshot
      ? `${snapshot.kind}:${snapshot.generation}:${channel}`
      : `submit:${snapshot.submitToken}:${channel}`;
    if (this.announcedResults.has(key)) return false;
    this.announcedResults.add(key);
    return true;
  }

  beginFocus(context: OrderContextSnapshot, target: string): OrderFocusTicket | null {
    if (!this.routeActive || context.routeGeneration !== this.routeGeneration) return null;
    this.focusToken += 1;
    return {
      routeGeneration: context.routeGeneration,
      contextToken: context.contextToken,
      targetedValidationToken: context.targetedValidationToken,
      focusToken: this.focusToken,
      target,
    };
  }

  canApplyFocus(ticket: OrderFocusTicket, current: OrderContextSnapshot): boolean {
    return this.routeActive
      && ticket.routeGeneration === this.routeGeneration
      && ticket.contextToken === current.contextToken
      && ticket.targetedValidationToken === current.targetedValidationToken
      && ticket.focusToken === this.focusToken;
  }

  bumpContext(): number {
    this.contextToken += 1;
    this.invalidateRequest('detail');
    this.invalidateRequest('readiness');
    this.invalidateRequest('productionHistory');
    this.invalidateRequest('productionReconciliation');
    return this.contextToken;
  }

  markTargetedValidationApplied(): number {
    this.targetedValidationToken += 1;
    this.invalidateRequest('list');
    this.invalidateRequest('reference');
    this.invalidateRequest('detail');
    return this.targetedValidationToken;
  }

  beginSubmit(context: OrderContextSnapshot): OrderSubmitSnapshot | null {
    if (!this.routeActive || context.routeGeneration !== this.routeGeneration || this.submitting) return null;
    this.submitting = true;
    this.submitToken += 1;
    return { ...context, submitToken: this.submitToken };
  }

  finishSubmit(snapshot: OrderSubmitSnapshot): boolean {
    if (snapshot.submitToken !== this.submitToken || !this.submitting) return false;
    this.submitting = false;
    return true;
  }

  canApplySubmit(snapshot: OrderSubmitSnapshot, current: OrderContextSnapshot): boolean {
    return this.routeActive
      && snapshot.routeGeneration === this.routeGeneration
      && snapshot.submitToken === this.submitToken
      && orderReadCanRender(snapshot, current);
  }

  beginRequest(kind: OrderRequestKind, context: OrderContextSnapshot, extra: Partial<Pick<OrderRequestSnapshot, 'savedOrderId' | 'requestedOrderId'>> = {}): OrderRequestSnapshot {
    this.generations[kind] += 1;
    return {
      ...context,
      kind,
      generation: this.generations[kind],
      submitToken: this.submitToken,
      ...(kind === 'productionReconciliation' ? { reconciliationEpoch: this.productionReconciliation?.epoch ?? 0 } : {}),
      ...extra,
    };
  }

  invalidateRequest(kind: OrderRequestKind): number {
    this.generations[kind] += 1;
    return this.generations[kind];
  }

  isCurrentRequest(snapshot: OrderRequestSnapshot): boolean {
    return this.generations[snapshot.kind] === snapshot.generation;
  }

  canRenderContext(snapshot: OrderContextSnapshot, current: OrderContextSnapshot): boolean {
    return orderReadCanRender(snapshot, current);
  }

  canApplyRequest(snapshot: OrderRequestSnapshot, current: OrderContextSnapshot): boolean {
    return this.routeActive
      && snapshot.routeGeneration === this.routeGeneration
      && this.isCurrentRequest(snapshot)
      && orderReadCanRender(snapshot, current);
  }

  canApplyPostSaveRefresh(snapshot: OrderRequestSnapshot, current: OrderContextSnapshot): boolean {
    return snapshot.kind === 'postSaveRefresh'
      && this.routeActive
      && snapshot.routeGeneration === this.routeGeneration
      && this.isCurrentRequest(snapshot)
      && snapshot.submitToken === this.submitToken
      && orderReadCanRender(snapshot, current);
  }

  settleRequest(snapshot: OrderRequestSnapshot): OrderRequestSettlement {
    const key = this.requestKey(snapshot);
    if (this.settledRequests.has(key)) {
      return { accepted: false, canPresent: false, detached: snapshot.routeGeneration !== this.routeGeneration || !this.routeActive };
    }
    this.settledRequests.add(key);
    const current = this.isCurrentRequest(snapshot);
    return {
      accepted: true,
      canPresent: current && this.routeActive && snapshot.routeGeneration === this.routeGeneration,
      detached: snapshot.routeGeneration !== this.routeGeneration || !this.routeActive,
    };
  }

  requireProductionReconciliation(
    snapshot: OrderRequestSnapshot,
    orderId: number,
  ): Readonly<OrderProductionReconciliationObligation> {
    const existing = this.productionReconciliation;
    if (existing && existing.productionGeneration === snapshot.generation && existing.orderId === orderId) {
      if (!this.routeActive || snapshot.routeGeneration !== this.routeGeneration) existing.detachedSettlement = true;
      return { ...existing };
    }
    this.reconciliationEpoch += 1;
    this.productionReconciliation = {
      operation: 'production',
      orderId,
      productionGeneration: snapshot.generation,
      routeGeneration: snapshot.routeGeneration,
      epoch: this.reconciliationEpoch,
      detachedSettlement: !this.routeActive || snapshot.routeGeneration !== this.routeGeneration,
      automaticAttemptConsumed: false,
    };
    return { ...this.productionReconciliation };
  }

  productionReconciliationRequired(orderId?: number): boolean {
    return Boolean(this.productionReconciliation && (orderId === undefined || this.productionReconciliation.orderId === orderId));
  }

  productionReconciliationObligation(): Readonly<OrderProductionReconciliationObligation> | null {
    return this.productionReconciliation ? { ...this.productionReconciliation } : null;
  }

  consumeAutomaticProductionReconciliation(): Readonly<OrderProductionReconciliationObligation> | null {
    const obligation = this.productionReconciliation;
    if (!this.routeActive || !obligation || obligation.automaticAttemptConsumed) return null;
    obligation.automaticAttemptConsumed = true;
    return { ...obligation };
  }

  canStartProductionReconciliation(orderId: number): boolean {
    return Boolean(
      this.routeActive
      && this.productionReconciliation?.orderId === orderId
      && !this.productionReconciliationRequiredForAnotherOrder(orderId),
    );
  }

  completeProductionReconciliation(
    snapshot: OrderRequestSnapshot,
    order: unknown,
    batch: unknown,
  ): boolean {
    const obligation = this.productionReconciliation;
    if (
      !obligation
      || !this.routeActive
      || snapshot.routeGeneration !== this.routeGeneration
      || snapshot.kind !== 'productionReconciliation'
      || snapshot.reconciliationEpoch !== obligation.epoch
      || snapshot.requestedOrderId !== obligation.orderId
      || !this.isCurrentRequest(snapshot)
      || !productionReconciliationIsCoherent(order, batch, obligation.orderId)
    ) return false;
    this.productionReconciliation = null;
    return true;
  }

  private productionReconciliationRequiredForAnotherOrder(orderId: number): boolean {
    return Boolean(this.productionReconciliation && this.productionReconciliation.orderId !== orderId);
  }

  private requestKey(snapshot: OrderRequestSnapshot): string {
    return `${snapshot.kind}:${snapshot.generation}`;
  }
}

export function createOrderMutationController(options: { routeActive?: boolean } = {}): OrderMutationController {
  return new OrderMutationController(options.routeActive ?? true);
}

const ORDER_STATUSES = new Set(['new', 'waiting_for_materials', 'ready_to_produce', 'in_progress', 'produced', 'delivered', 'cancelled', 'archived']);
const READINESS_STATUSES = new Set(['ready', 'warning', 'blocked']);
const READINESS_SEVERITIES = new Set(['blocking', 'warning', 'info']);

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function positiveInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value > 0;
}

function nullablePositiveInteger(value: unknown): boolean {
  return value === null || positiveInteger(value);
}

function stringOrNull(value: unknown): boolean {
  return value === null || typeof value === 'string';
}

export function orderDtoIsValid(value: unknown, expectedOrderId?: number): boolean {
  const item = record(value);
  return Boolean(
    item
    && positiveInteger(item.id)
    && (expectedOrderId === undefined || item.id === expectedOrderId)
    && positiveInteger(item.client_id)
    && nullablePositiveInteger(item.recipe_version_id)
    && nullablePositiveInteger(item.client_recipe_id)
    && typeof item.product_name === 'string'
    && typeof item.target_batch_size_value === 'string'
    && typeof item.target_batch_size_unit === 'string'
    && nullablePositiveInteger(item.packaging_item_id)
    && stringOrNull(item.packaging_quantity)
    && typeof item.status === 'string'
    && ORDER_STATUSES.has(item.status)
    && stringOrNull(item.sale_price)
    && stringOrNull(item.ordered_at)
    && stringOrNull(item.planned_production_at)
    && stringOrNull(item.produced_at)
    && stringOrNull(item.delivered_at)
    && typeof item.notes === 'string'
    && typeof item.is_active === 'boolean'
    && typeof item.created_at === 'string'
    && typeof item.updated_at === 'string',
  );
}

export function ordersDtoIsValid(value: unknown): boolean {
  const payload = record(value);
  return Boolean(payload && Array.isArray(payload.orders) && payload.orders.every((item) => orderDtoIsValid(item)));
}

export function orderReferenceDataIsValid(value: unknown): boolean {
  const payload = record(value);
  if (!payload) return false;
  for (const key of ['clients', 'templates', 'versions', 'clientRecipes', 'packagingItems']) {
    const list = payload[key];
    if (!Array.isArray(list) || !list.every((item) => positiveInteger(record(item)?.id))) return false;
  }
  return true;
}

function readinessIssueIsValid(value: unknown): boolean {
  const issue = record(value);
  return Boolean(
    issue
    && typeof issue.code === 'string'
    && typeof issue.severity === 'string'
    && READINESS_SEVERITIES.has(issue.severity)
    && typeof issue.message === 'string'
    && stringOrNull(issue.field)
    && stringOrNull(issue.entity_type)
    && nullablePositiveInteger(issue.entity_id),
  );
}

function readinessLotSelectionIsValid(value: unknown): boolean {
  const lot = record(value);
  return Boolean(
    lot
    && positiveInteger(lot.lot_id)
    && typeof lot.lot_code === 'string'
    && typeof lot.selected_quantity === 'string'
    && typeof lot.unit === 'string'
    && stringOrNull(lot.expires_at)
    && typeof lot.is_expired === 'boolean'
    && typeof lot.expires_soon === 'boolean',
  );
}

function readinessIngredientLineIsValid(value: unknown): boolean {
  const line = record(value);
  return Boolean(
    line
    && positiveInteger(line.ingredient_id)
    && typeof line.ingredient_name === 'string'
    && typeof line.required_quantity === 'string'
    && typeof line.required_unit === 'string'
    && typeof line.available_quantity === 'string'
    && stringOrNull(line.missing_quantity)
    && typeof line.can_fulfill === 'boolean'
    && Array.isArray(line.selected_lots)
    && line.selected_lots.every(readinessLotSelectionIsValid)
    && Array.isArray(line.warnings)
    && line.warnings.every(readinessIssueIsValid),
  );
}

function readinessPackagingLineIsValid(value: unknown): boolean {
  const line = record(value);
  return Boolean(
    line
    && positiveInteger(line.packaging_item_id)
    && typeof line.name === 'string'
    && typeof line.required_quantity === 'string'
    && typeof line.available_quantity === 'string'
    && stringOrNull(line.missing_quantity)
    && typeof line.can_fulfill === 'boolean',
  );
}

export function productionReadinessDtoIsValid(value: unknown, expectedOrderId: number): boolean {
  const payload = record(value);
  return Boolean(
    payload
    && payload.order_id === expectedOrderId
    && typeof payload.can_produce === 'boolean'
    && typeof payload.status === 'string'
    && READINESS_STATUSES.has(payload.status)
    && Array.isArray(payload.blocking_issues)
    && payload.blocking_issues.every(readinessIssueIsValid)
    && Array.isArray(payload.warnings)
    && payload.warnings.every(readinessIssueIsValid)
    && Array.isArray(payload.ingredients)
    && payload.ingredients.every(readinessIngredientLineIsValid)
    && Array.isArray(payload.packaging)
    && payload.packaging.every(readinessPackagingLineIsValid)
    && stringOrNull(payload.estimated_cost)
    && stringOrNull(payload.estimated_tax)
    && stringOrNull(payload.estimated_margin)
    && typeof payload.generated_at === 'string',
  );
}

function productionBatchIngredientDtoIsValid(value: unknown, batchId: number): boolean {
  const item = record(value);
  return Boolean(
    item
    && positiveInteger(item.id)
    && item.production_batch_id === batchId
    && positiveInteger(item.ingredient_id)
    && positiveInteger(item.ingredient_lot_id)
    && typeof item.ingredient_name_snapshot === 'string'
    && typeof item.lot_code_snapshot === 'string'
    && typeof item.required_quantity === 'string'
    && typeof item.consumed_quantity === 'string'
    && typeof item.unit === 'string'
    && stringOrNull(item.unit_cost_snapshot)
    && stringOrNull(item.total_cost_snapshot)
    && stringOrNull(item.expiration_date_snapshot)
    && typeof item.created_at === 'string',
  );
}

function productionBatchPackagingDtoIsValid(value: unknown, batchId: number): boolean {
  const item = record(value);
  return Boolean(
    item
    && positiveInteger(item.id)
    && item.production_batch_id === batchId
    && positiveInteger(item.packaging_item_id)
    && typeof item.packaging_name_snapshot === 'string'
    && typeof item.quantity === 'string'
    && typeof item.unit === 'string'
    && stringOrNull(item.unit_cost_snapshot)
    && stringOrNull(item.total_cost_snapshot)
    && typeof item.created_at === 'string',
  );
}

export function productionBatchDtoIsValid(value: unknown, expectedOrderId: number): boolean {
  const payload = record(value);
  if (
    !payload
    || !positiveInteger(payload.id)
    || payload.order_id !== expectedOrderId
    || !stringOrNull(payload.product_name)
    || !nullablePositiveInteger(payload.client_id)
    || !stringOrNull(payload.client_name)
    || !nullablePositiveInteger(payload.recipe_version_id)
    || !nullablePositiveInteger(payload.client_recipe_id)
    || typeof payload.final_batch_value !== 'string'
    || typeof payload.final_batch_unit !== 'string'
    || !stringOrNull(payload.component_cost)
    || !stringOrNull(payload.packaging_cost)
    || typeof payload.other_cost !== 'string'
    || !stringOrNull(payload.total_cost)
    || !stringOrNull(payload.sale_price)
    || !stringOrNull(payload.tax)
    || !stringOrNull(payload.margin)
    || !stringOrNull(payload.margin_percent)
    || typeof payload.produced_at !== 'string'
    || typeof payload.notes !== 'string'
    || typeof payload.created_at !== 'string'
    || !Array.isArray(payload.ingredients)
    || !Array.isArray(payload.packaging)
  ) return false;
  return payload.ingredients.every((item) => productionBatchIngredientDtoIsValid(item, payload.id as number))
    && payload.packaging.every((item) => productionBatchPackagingDtoIsValid(item, payload.id as number));
}

export function productionReconciliationIsCoherent(
  order: unknown,
  batch: unknown,
  expectedOrderId: number,
): boolean {
  const orderRecord = record(order);
  return orderDtoIsValid(order, expectedOrderId)
    && Boolean(orderRecord && (orderRecord.status === 'produced' || orderRecord.status === 'delivered'))
    && productionBatchDtoIsValid(batch, expectedOrderId);
}


export function orderProductionIsClosed(order: OrderProductionGuardOrder): boolean {
  return !order?.is_active || ['cancelled', 'archived', 'delivered', 'produced'].includes(order.status);
}

export function canOpenOrderProductionConfirmation(
  mutationActive: boolean,
  order: OrderProductionGuardOrder,
  readiness: OrderProductionGuardReadiness,
): boolean {
  return !mutationActive
    && !orderProductionIsClosed(order)
    && typeof order?.id === 'number'
    && readiness?.order_id === order?.id
    && readiness?.can_produce === true
    && readiness?.status !== 'blocked';
}

export function orderReadinessRequestActive(
  owner: OrderTransientRequestOwner,
  loadingOrderId: number | null,
  orderId?: number,
): boolean {
  if (owner?.kind !== 'readiness' || loadingOrderId === null || owner.orderId !== loadingOrderId) return false;
  return orderId === undefined || loadingOrderId === orderId;
}

export function canStartOrderReadinessRequest(
  mutationActive: boolean,
  order: OrderProductionGuardOrder,
  owner: OrderTransientRequestOwner,
  loadingOrderId: number | null,
  requestedOrderId: number,
  conflictingOperations: OrderOperationState[] = [],
): order is Exclude<OrderProductionGuardOrder, null | undefined> {
  return !mutationActive
    && order?.id === requestedOrderId
    && !orderProductionIsClosed(order)
    && !orderReadinessRequestActive(owner, loadingOrderId)
    && !orderBoundOperationActive(conflictingOperations, requestedOrderId);
}

export function orderBoundOperationActive(
  operations: OrderOperationState[],
  orderId: number,
  kinds?: NonNullable<OrderTransientRequestOwner>['kind'][],
): boolean {
  return operations.some(({ owner, loadingOrderId }) => Boolean(
    owner
      && owner.orderId === orderId
      && loadingOrderId === orderId
      && (!kinds || kinds.includes(owner.kind)),
  ));
}

export function orderPersistentWriteOwner(
  operations: OrderOperationState[],
): OrderPersistentWriteOwner | null {
  for (const { owner, loadingOrderId } of operations) {
    if (
      owner
      && loadingOrderId === owner.orderId
      && (owner.kind === 'production' || owner.kind === 'cancel' || owner.kind === 'archive')
    ) return owner as OrderPersistentWriteOwner;
  }
  return null;
}

export function orderPersistentWriteActive(operations: OrderOperationState[]): boolean {
  return orderPersistentWriteOwner(operations) !== null;
}

export function canStartOrderWriteRequest(
  mutationActive: boolean,
  order: OrderProductionGuardOrder,
  requestedOrderId: number,
  operations: OrderOperationState[],
): boolean {
  return !mutationActive
    && order?.id === requestedOrderId
    && !orderPersistentWriteActive(operations)
    && !orderBoundOperationActive(operations, requestedOrderId);
}

export function orderReadinessAttemptMatches(
  order: OrderProductionGuardOrder,
  requestedOrderId: number,
  capturedOrderUpdatedAt: string | undefined,
  capturedOperationGeneration: number | undefined,
  currentOperationGeneration: number | undefined,
): boolean {
  return Boolean(
    order
      && order.id === requestedOrderId
      && capturedOrderUpdatedAt !== undefined
      && order.updated_at === capturedOrderUpdatedAt
      && capturedOperationGeneration !== undefined
      && capturedOperationGeneration === currentOperationGeneration,
  );
}

export function orderReadinessResultIsCurrent(
  order: OrderProductionGuardOrder,
  readiness: OrderProductionGuardReadiness,
  latestAttemptGeneration: number | undefined,
  resultGeneration: number | undefined,
  capturedOrderUpdatedAt: string | undefined,
  capturedOperationGeneration: number | undefined,
  currentOperationGeneration: number | undefined,
): boolean {
  return Boolean(
    order
      && readiness
      && readiness.order_id === order.id
      && latestAttemptGeneration !== undefined
      && latestAttemptGeneration === resultGeneration
      && capturedOrderUpdatedAt === order.updated_at
      && capturedOperationGeneration !== undefined
      && capturedOperationGeneration === currentOperationGeneration,
  );
}

export type ProductionReadinessFailure = {
  status?: number;
  message?: string;
  networkFailure?: boolean;
};

export function productionReadinessFailureMessage(failure: ProductionReadinessFailure): string {
  const message = failure.message?.toLocaleLowerCase('ru-RU') ?? '';
  if (failure.status === 404 && (message.includes('recipe') || message.includes('рецепт') || message.includes('формул'))) {
    return 'Связанный рецепт или индивидуальная формула не найдены. Обновите заказ и выберите доступную основу.';
  }
  if (failure.status === 404) return 'Заказ не найден. Обновите список заказов и откройте карточку снова.';
  if (failure.status === 409) return 'Проверка недоступна для текущего состояния заказа. Обновите карточку и проверьте статус заказа.';
  if (failure.status === 422) return 'Локальное приложение отклонило параметры проверки. Обновите заказ и проверьте его обязательные данные.';
  if (failure.networkFailure) return 'Не удалось связаться с локальным приложением. Проверьте, что оно запущено, и повторите проверку.';
  return 'Во время проверки произошла непредвиденная ошибка. Данные заказа и склада не изменены; повторите проверку.';
}


export type ProductionFailureKind = 'business_conflict' | 'validation' | 'missing_record' | 'network_uncertain' | 'unexpected';
export type ProductionFailurePresentation = { kind: ProductionFailureKind; message: string; nextAction: string; invalidateReadiness: boolean; closeConfirmation: boolean; requireRefreshBeforeRetry: boolean };

export type ProductionApiFailure = { status?: number; code?: string; message?: string; nextAction?: string; networkFailure?: boolean };

function safeProductionErrorText(value: string | undefined): string {
  const text = (value ?? '').trim();
  if (!text) return '';
  if (/Traceback|sqlite|SQL|SELECT|INSERT|UPDATE|DELETE|production_batches|stock_movements|packaging_stock_movements|\/workspace|\.py|Error:|Exception|\{"|\[\{/i.test(text)) return '';
  return text;
}


export function extractProductionApiFailure(error: unknown): ProductionApiFailure {
  const status = typeof error === 'object' && error && 'status' in error ? Number((error as { status?: number }).status) : undefined;
  const payload = typeof error === 'object' && error && 'payload' in error ? (error as { payload?: unknown }).payload : null;
  const detail = payload && typeof payload === 'object' && 'detail' in payload ? (payload as { detail?: unknown }).detail : null;
  const structured = detail && typeof detail === 'object' && !Array.isArray(detail) ? detail as { code?: unknown; message?: unknown; next_action?: unknown } : null;
  const message = structured && typeof structured.message === 'string'
    ? safeProductionErrorText(structured.message)
    : error instanceof Error && error.message !== 'API request failed'
      ? safeProductionErrorText(error.message)
      : '';
  const nextAction = structured && typeof structured.next_action === 'string' ? safeProductionErrorText(structured.next_action) : '';
  return {
    status,
    code: structured && typeof structured.code === 'string' ? structured.code : '',
    message,
    nextAction,
    networkFailure: error instanceof TypeError,
  };
}

export function productionConfirmationFailurePresentation(failure: ProductionApiFailure): ProductionFailurePresentation {
  const code = failure.code ?? '';
  const safe = safeProductionErrorText(failure.message);
  const next = safeProductionErrorText(failure.nextAction) || 'Обновите заказ и запустите проверку готовности заново.';
  if (failure.status === 409) {
    if (code === 'readiness_changed' || code === 'readiness_blocked') {
      return { kind: 'business_conflict', message: safe || 'Состояние заказа или склада изменилось. Изготовление не выполнено: запустите проверку готовности ещё раз.', nextAction: next, invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: false };
    }
    if (safe.toLocaleLowerCase('ru-RU').includes('уже изготов')) {
      return { kind: 'business_conflict', message: 'Заказ уже изготовлен или производственная партия уже существует. Повторное изготовление недоступно.', nextAction: next, invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: false };
    }
    return { kind: 'business_conflict', message: safe || 'Заказ нельзя изготовить в текущем состоянии.', nextAction: next, invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: false };
  }
  if (failure.status === 422) return { kind: 'validation', message: safe || 'Локальное приложение отклонило подтверждение. Проверьте форму подтверждения; заметка сохранена.', nextAction: safeProductionErrorText(failure.nextAction) || 'Проверьте подтверждение и повторите только после готовности заказа.', invalidateReadiness: false, closeConfirmation: false, requireRefreshBeforeRetry: false };
  if (failure.status === 404) return { kind: 'missing_record', message: safe || 'Заказ или связанный рецепт больше не доступны.', nextAction: safeProductionErrorText(failure.nextAction) || 'Обновите заказ и историю производства.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: true };
  if (failure.networkFailure) return { kind: 'network_uncertain', message: 'Связь с локальным приложением прервалась. Исход изготовления неизвестен.', nextAction: 'Проверьте заказ и производственную партию через безопасное обновление ниже.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: true };
  return { kind: 'unexpected', message: safe || 'Неожиданная ошибка локального приложения. Исход изготовления нужно проверить.', nextAction: safeProductionErrorText(failure.nextAction) || 'Обновите заказ и историю производства перед повторной попыткой.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: true };
}



export function finishProductionOwnerState(
  owner: OrderTransientRequestOwner,
  loadingOrderId: number | null,
  snapshot: OrderRequestSnapshot,
  orderId: number,
): { owner: OrderTransientRequestOwner; loadingOrderId: number | null; finished: boolean } {
  if (!orderRequestOwnerMatches(owner, snapshot, orderId, 'production')) return { owner, loadingOrderId, finished: false };
  return { owner: null, loadingOrderId: null, finished: true };
}

export function productionFailureForOrder(failures: Record<number, string>, orderId: number): string {
  return failures[orderId] || '';
}

export function restoreOrderOperationGenerationForOwnedNonMutatingFailure(
  currentGeneration: number,
  attemptedGeneration: number,
  previousGeneration: number,
  shouldRestore: boolean,
): number {
  return shouldRestore && currentGeneration === attemptedGeneration ? previousGeneration : currentGeneration;
}

export function productionResponseBelongsToOrder(batch: { order_id?: number } | null | undefined, orderId: number): boolean {
  return batch?.order_id === orderId;
}

export function ownerFromOrderRequest(
  snapshot: OrderRequestSnapshot,
  orderId: number,
  kind: NonNullable<OrderTransientRequestOwner>['kind'],
): OrderTransientRequestOwner {
  return { kind, generation: snapshot.generation, orderId };
}

export function orderRequestOwnerMatches(
  owner: OrderTransientRequestOwner,
  snapshot: OrderRequestSnapshot,
  orderId: number,
  kind: NonNullable<OrderTransientRequestOwner>['kind'],
): boolean {
  return owner?.kind === kind && owner.generation === snapshot.generation && owner.orderId === orderId;
}

export function orderOperationError(orderId: number, message: string): OrderOperationError {
  return { orderId, message };
}

export function orderOperationErrorFor(error: OrderOperationError, orderId: number): string {
  return error?.orderId === orderId ? error.message : '';
}

export function clearOrderSourceValidation(
  validation: FormValidationState,
  provenance: OrderValidationProvenance,
  origins: OrderFormErrorOrigin[],
): { validation: FormValidationState; provenance: OrderValidationProvenance } {
  const originSet = new Set(origins);
  let next = validation;
  for (const origin of origins) next = clearFieldValidation(next, origin === 'recipe_source' ? 'source_type' : origin);
  const removeCounts = new Map<string, number>();
  for (const item of provenance.formErrors) {
    if (originSet.has(item.origin)) removeCounts.set(item.message, (removeCounts.get(item.message) ?? 0) + 1);
  }
  const formErrors: string[] = [];
  for (const message of next.formErrors) {
    const count = removeCounts.get(message) ?? 0;
    if (count > 0) {
      removeCounts.set(message, count - 1);
      continue;
    }
    formErrors.push(message);
  }
  return {
    validation: { ...next, formErrors },
    provenance: { formErrors: provenance.formErrors.filter((item) => !originSet.has(item.origin)) },
  };
}

export type OrderPayloadDraft = {
  client_id: string;
  source_type: OrderSourceType;
  recipe_version_id: string;
  client_recipe_id: string;
  product_name: string;
  target_batch_size_value: string;
  target_batch_size_unit: string;
  packaging_item_id: string;
  packaging_quantity: string;
  sale_price: string;
  ordered_at: string;
  planned_production_at: string;
  notes: string;
};

export type OrderPayload = {
  client_id: number | null;
  recipe_version_id: number | null;
  client_recipe_id: number | null;
  product_name: string;
  target_batch_size_value: string;
  target_batch_size_unit: string;
  packaging_item_id: number | null;
  packaging_quantity: string | null;
  sale_price: string | null;
  ordered_at: string | null;
  planned_production_at: string | null;
  notes: string;
};

export function orderPayloadFromDraft(draft: OrderPayloadDraft): OrderPayload {
  return {
    client_id: Number(draft.client_id) || null,
    recipe_version_id: draft.source_type === 'recipe_version' ? Number(draft.recipe_version_id) || null : null,
    client_recipe_id: draft.source_type === 'client_recipe' ? Number(draft.client_recipe_id) || null : null,
    product_name: draft.product_name.trim(),
    target_batch_size_value: draft.target_batch_size_value,
    target_batch_size_unit: draft.target_batch_size_unit || 'g',
    packaging_item_id: draft.packaging_item_id ? Number(draft.packaging_item_id) : null,
    packaging_quantity: draft.packaging_quantity || null,
    sale_price: draft.sale_price || null,
    ordered_at: draft.ordered_at || null,
    planned_production_at: draft.planned_production_at || null,
    notes: draft.notes,
  };
}
