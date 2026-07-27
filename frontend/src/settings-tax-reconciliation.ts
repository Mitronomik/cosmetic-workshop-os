/**
 * Reconciliation-obligation bookkeeping for the tax setting.
 *
 * When a Save or Clear outlives its route, its result must never be applied, but
 * the fact that the backend may have changed underneath the cached value must
 * survive. That surviving fact is the obligation tracked here: exactly one
 * authoritative read discharges it, and until it is discharged the displayed
 * value is not confirmed enough to mutate from.
 */

export type TaxRateReconciliationReason = 'detached-mutation' | 'invalid-response' | null;

export type TaxRateReconciliationFields = {
  /** A detached mutation is still in flight; a read now would race the PUT. */
  detachedMutationPending: boolean;
  reconciliationRequired: boolean;
  reconciliationReason: TaxRateReconciliationReason;
  /**
   * True only after an authoritative read actually rejected. An open obligation
   * on its own is not a failure, so the two must never share one message.
   */
  reconciliationFailed: boolean;
  /** Bumped per obligation, so a stale read cannot discharge a newer one. */
  reconciliationEpoch: number;
};

export const TAX_RATE_RECONCILING_MESSAGE = 'Проверяем сохранённую налоговую ставку…';
export const TAX_RATE_RECONCILED_MESSAGE = 'Показано подтверждённое значение налоговой ставки.';
export const TAX_RATE_RECONCILE_FAILED_MESSAGE = 'Не удалось подтвердить налоговую ставку. Показано последнее известное значение. Сохранение и очистка недоступны, пока значение не подтверждено.';

export const emptyReconciliation = (): TaxRateReconciliationFields => ({
  detachedMutationPending: false,
  reconciliationRequired: false,
  reconciliationReason: null,
  reconciliationFailed: false,
  reconciliationEpoch: 0,
});

export function requireReconciliation(state: TaxRateReconciliationFields, reason: Exclude<TaxRateReconciliationReason, null>): void {
  if (!state.reconciliationRequired || state.reconciliationReason !== reason) {
    state.reconciliationEpoch += 1;
    state.reconciliationFailed = false;
  }
  state.reconciliationRequired = true;
  state.reconciliationReason = reason;
}

export function clearReconciliation(state: TaxRateReconciliationFields): void {
  state.reconciliationRequired = false;
  state.reconciliationReason = null;
  state.reconciliationFailed = false;
}

/** Record that an authoritative read rejected, which is what licenses failure copy. */
export function markReconciliationFailed(state: TaxRateReconciliationFields): void {
  state.reconciliationFailed = true;
}

/** Record that a pending mutation outlived its route. */
export function detachMutation(state: TaxRateReconciliationFields): void {
  state.detachedMutationPending = true;
  requireReconciliation(state, 'detached-mutation');
}

/** The detached mutation landed; only its obligation remains. */
export function settleDetachedMutation(state: TaxRateReconciliationFields): void {
  state.detachedMutationPending = false;
  requireReconciliation(state, 'detached-mutation');
}

export function canDischargeReconciliation(state: TaxRateReconciliationFields, epoch: number): boolean {
  return state.reconciliationRequired && epoch === state.reconciliationEpoch && !state.detachedMutationPending;
}

export function mutationsBlocked(state: TaxRateReconciliationFields): boolean {
  return state.reconciliationRequired || state.detachedMutationPending;
}
