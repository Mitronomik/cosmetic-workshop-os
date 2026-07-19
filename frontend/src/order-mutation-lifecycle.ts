import { clearFieldValidation, type FormValidationState } from './form-validation.js';

export type OrderFormMode = 'create' | 'edit';
export type OrderSourceType = 'recipe_version' | 'client_recipe';
export type OrderContextSnapshot = {
  contextToken: number;
  targetedValidationToken: number;
  formMode: OrderFormMode;
  editedOrderId: number | null;
  selectedOrderId: number | null;
  showForm: boolean;
};
export type OrderContextState = OrderContextSnapshot;

export type OrderRequestKind = 'list' | 'postSaveRefresh' | 'reference' | 'detail' | 'readiness' | 'production' | 'productionHistory' | 'cancel' | 'archive';
export type OrderRequestSnapshot = OrderContextSnapshot & {
  kind: OrderRequestKind;
  generation: number;
  submitToken: number;
  savedOrderId?: number | null;
  requestedOrderId?: number | null;
};
export type OrderSubmitSnapshot = OrderContextSnapshot & { submitToken: number };

export type OrderTransientRequestOwner = {
  kind: 'readiness' | 'production' | 'productionHistory' | 'cancel' | 'archive';
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
  private generations: Record<OrderRequestKind, number> = {
    list: 0,
    postSaveRefresh: 0,
    reference: 0,
    detail: 0,
    readiness: 0,
    production: 0,
    productionHistory: 0,
    cancel: 0,
    archive: 0,
  };

  snapshot(workspace: OrderWorkspaceState): OrderContextSnapshot {
    return {
      contextToken: this.contextToken,
      targetedValidationToken: this.targetedValidationToken,
      formMode: workspace.formMode,
      editedOrderId: workspace.editedOrderId,
      selectedOrderId: workspace.selectedOrderId,
      showForm: workspace.showForm,
    };
  }

  getContextToken(): number { return this.contextToken; }
  getTargetedValidationToken(): number { return this.targetedValidationToken; }
  isSubmitting(): boolean { return this.submitting; }

  bumpContext(): number {
    this.contextToken += 1;
    this.invalidateRequest('detail');
    this.invalidateRequest('readiness');
    this.invalidateRequest('production');
    this.invalidateRequest('productionHistory');
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
    if (this.submitting) return null;
    this.submitting = true;
    this.submitToken += 1;
    return { ...context, submitToken: this.submitToken };
  }

  finishSubmit(snapshot: OrderSubmitSnapshot): boolean {
    if (snapshot.submitToken !== this.submitToken) return false;
    this.submitting = false;
    return true;
  }

  canApplySubmit(snapshot: OrderSubmitSnapshot, current: OrderContextSnapshot): boolean {
    return snapshot.submitToken === this.submitToken && orderReadCanRender(snapshot, current);
  }

  beginRequest(kind: OrderRequestKind, context: OrderContextSnapshot, extra: Partial<Pick<OrderRequestSnapshot, 'savedOrderId' | 'requestedOrderId'>> = {}): OrderRequestSnapshot {
    this.generations[kind] += 1;
    return { ...context, kind, generation: this.generations[kind], submitToken: this.submitToken, ...extra };
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
    return this.isCurrentRequest(snapshot) && orderReadCanRender(snapshot, current);
  }

  canApplyPostSaveRefresh(snapshot: OrderRequestSnapshot, current: OrderContextSnapshot): boolean {
    return snapshot.kind === 'postSaveRefresh'
      && this.isCurrentRequest(snapshot)
      && snapshot.submitToken === this.submitToken
      && orderReadCanRender(snapshot, current);
  }
}

export function createOrderMutationController(): OrderMutationController {
  return new OrderMutationController();
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
export type ProductionFailurePresentation = { kind: ProductionFailureKind; message: string; invalidateReadiness: boolean; closeConfirmation: boolean; requireRefreshBeforeRetry: boolean };

function safeProductionErrorText(value: string | undefined): string {
  const text = (value ?? '').trim();
  if (!text) return '';
  if (/Traceback|sqlite|SQL|SELECT|INSERT|UPDATE|DELETE|\/workspace|\.py|Error:|Exception|\{"|\[\{/i.test(text)) return '';
  return text;
}

export function productionConfirmationFailurePresentation(failure: { status?: number; message?: string; networkFailure?: boolean; code?: string }): ProductionFailurePresentation {
  const code = failure.code ?? '';
  const safe = safeProductionErrorText(failure.message);
  if (failure.status === 409) {
    if (code === 'readiness_changed' || code === 'readiness_blocked') {
      return { kind: 'business_conflict', message: safe || 'Состояние заказа или склада изменилось. Изготовление не выполнено: запустите проверку готовности ещё раз.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: false };
    }
    if (safe.toLocaleLowerCase('ru-RU').includes('уже изготов')) {
      return { kind: 'business_conflict', message: 'Заказ уже изготовлен или производственная партия уже существует. Повторное изготовление недоступно.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: false };
    }
    return { kind: 'business_conflict', message: safe || 'Заказ нельзя изготовить в текущем состоянии. Обновите заказ и проверьте готовность заново.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: false };
  }
  if (failure.status === 422) return { kind: 'validation', message: safe || 'Локальное приложение отклонило подтверждение. Проверьте форму подтверждения; заметка сохранена.', invalidateReadiness: false, closeConfirmation: false, requireRefreshBeforeRetry: false };
  if (failure.status === 404) return { kind: 'missing_record', message: safe || 'Заказ или связанный рецепт больше не доступны. Обновите список заказов и откройте карточку снова.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: true };
  if (failure.networkFailure) return { kind: 'network_uncertain', message: 'Связь с локальным приложением прервалась. Исход изготовления неизвестен: обновите заказ и историю производства перед повторной попыткой.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: true };
  return { kind: 'unexpected', message: safe || 'Неожиданная ошибка локального приложения. Исход изготовления нужно проверить обновлением заказа перед повторной попыткой.', invalidateReadiness: true, closeConfirmation: true, requireRefreshBeforeRetry: true };
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
