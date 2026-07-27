import {
  checkTaxRateInput,
  isTaxRateSettingDto,
  taxRateInputValue,
  type TaxRateSettingDto,
} from './settings-tax-contract.js';
import {
  canDischargeReconciliation,
  clearReconciliation,
  detachMutation,
  emptyReconciliation,
  mutationsBlocked,
  requireReconciliation,
  settleDetachedMutation,
  TAX_RATE_RECONCILE_FAILED_MESSAGE,
  TAX_RATE_RECONCILED_MESSAGE,
  TAX_RATE_RECONCILING_MESSAGE,
  type TaxRateReconciliationFields,
} from './settings-tax-reconciliation.js';
import { busyMessage, TAX_RATE_CANCEL_MESSAGE, TAX_RATE_CLEAR_ERROR, TAX_RATE_CLEARING_MESSAGE, TAX_RATE_INITIAL_ERROR, TAX_RATE_INVALID_RESPONSE, TAX_RATE_REFRESH_SUCCESS, TAX_RATE_REFRESH_WARNING, TAX_RATE_SAVE_ERROR, TAX_RATE_SAVING_MESSAGE } from './settings-tax-messages.js';

export * from './settings-tax-messages.js';

export type TaxRateReadKind = 'initial' | 'refresh' | 'mutation-refresh' | 'reconciliation';
export type TaxRateMutationKind = 'save' | 'clear';
export type TaxRateFeedbackTone = 'none' | 'neutral' | 'success' | 'warning' | 'error';
export type TaxRateAnnouncement = 'none' | 'polite' | 'assertive';

export type TaxRateOwner = { requestId: number; routeGeneration: number };
export type TaxRateReadOwner = TaxRateOwner & { kind: TaxRateReadKind; reconciliationEpoch: number };
export type TaxRateMutationOwner = TaxRateOwner & { kind: TaxRateMutationKind };
export type TaxRateStart<TOwner> =
  | { accepted: true; owner: TOwner; payload?: string | null }
  | { accepted: false; reason: TaxRateRejection };
export type TaxRateRejection =
  | 'read-active'
  | 'mutation-active'
  | 'not-ready'
  | 'invalid-input'
  | 'not-confirmed'
  | 'nothing-to-clear'
  | 'reconciliation-required'
  | 'detached-mutation-pending';
export type TaxRateSettled = {
  accepted: boolean;
  announcement: TaxRateAnnouncement;
  message: string;
  knownSuccess?: boolean;
  detached?: boolean;
  needsReconciliation?: boolean;
};

export type TaxRateFeedback = { tone: TaxRateFeedbackTone; neutral: string; success: string; warning: string; error: string };
export type TaxRateState = TaxRateReconciliationFields & {
  routeGeneration: number;
  status: 'idle' | 'loading' | 'ready' | 'error';
  confirmed: TaxRateSettingDto | null;
  draft: string;
  fieldError: string;
  read: TaxRateReadOwner | null;
  mutation: TaxRateMutationOwner | null;
  clearConfirmVisible: boolean;
  feedback: TaxRateFeedback;
};


const idleFeedback = (): TaxRateFeedback => ({ tone: 'none', neutral: '', success: '', warning: '', error: '' });
const ignored = (): TaxRateSettled => ({ accepted: false, announcement: 'none', message: '' });

export class SettingsTaxRateFeedbackLifecycle {
  readonly state: TaxRateState;
  private nextRequestId = 0;

  constructor() {
    this.state = { ...emptyReconciliation(), routeGeneration: 0, status: 'idle', confirmed: null, draft: '', fieldError: '', read: null, mutation: null, clearConfirmVisible: false, feedback: idleFeedback() };
  }

  enterRoute() {
    this.state.routeGeneration += 1;
    this.state.read = null;
    this.state.clearConfirmVisible = false;
    this.state.feedback = this.state.reconciliationRequired
      ? { ...idleFeedback(), tone: 'warning', warning: this.state.feedback.warning || TAX_RATE_RECONCILE_FAILED_MESSAGE }
      : idleFeedback();
  }

  /**
   * Leaving the route must not discard a pending mutation: the backend may still
   * commit it, so the mutation is detached and its reconciliation obligation is
   * recorded instead. The detached settlement never presents or applies.
   */
  leaveRoute() {
    this.state.routeGeneration += 1;
    this.state.read = null;
    if (this.state.mutation) detachMutation(this.state);
    this.state.clearConfirmVisible = false;
    this.state.feedback = idleFeedback();
  }

  startRead(kind: TaxRateReadKind): TaxRateStart<TaxRateReadOwner> {
    if (this.state.read) return { accepted: false, reason: 'read-active' };
    // A read started while a detached mutation is still in flight could return
    // before the PUT commits and be applied as if it were authoritative.
    if (this.state.detachedMutationPending) return { accepted: false, reason: 'detached-mutation-pending' };
    if (this.state.mutation) return { accepted: false, reason: 'mutation-active' };
    const owner: TaxRateReadOwner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind, reconciliationEpoch: this.state.reconciliationEpoch };
    this.state.read = owner;
    if (kind === 'initial' && !this.state.confirmed) this.state.status = 'loading';
    // A mutation-refresh reconciles an already-confirmed success, so it must not
    // add a busy message next to that success.
    if (kind !== 'mutation-refresh') {
      // A reconciliation read keeps the error that caused it visible until it
      // actually resolves, so the user is never left without an explanation.
      const error = kind === 'reconciliation' ? this.state.feedback.error : '';
      this.state.feedback = { ...this.state.feedback, tone: error ? 'error' : 'neutral', neutral: busyMessage(kind), error };
    }
    return { accepted: true, owner };
  }

  finishReadSuccess(owner: TaxRateReadOwner, value: unknown): TaxRateSettled {
    if (!this.owns(this.state.read, owner)) return ignored();
    this.state.read = null;
    if (!isTaxRateSettingDto(value)) return this.presentInvalidResponse();
    const keptSuccess = owner.kind === 'mutation-refresh' ? this.state.feedback.success : '';
    this.applyConfirmed(value);
    const dischargesObligation = owner.kind === 'reconciliation' && canDischargeReconciliation(this.state, owner.reconciliationEpoch);
    if (dischargesObligation) clearReconciliation(this.state);
    if (owner.kind === 'reconciliation') {
      this.state.feedback = dischargesObligation
        ? { ...idleFeedback(), tone: 'success', success: TAX_RATE_RECONCILED_MESSAGE }
        : { ...idleFeedback(), tone: 'warning', warning: TAX_RATE_RECONCILE_FAILED_MESSAGE };
      return { accepted: true, announcement: 'polite', message: dischargesObligation ? TAX_RATE_RECONCILED_MESSAGE : TAX_RATE_RECONCILE_FAILED_MESSAGE };
    }
    const refreshed = owner.kind === 'refresh';
    this.state.feedback = { ...idleFeedback(), tone: refreshed ? 'success' : keptSuccess ? 'success' : 'none', success: refreshed ? TAX_RATE_REFRESH_SUCCESS : keptSuccess };
    return refreshed ? { accepted: true, announcement: 'polite', message: TAX_RATE_REFRESH_SUCCESS } : { accepted: true, announcement: 'none', message: '' };
  }

  finishReadFailure(owner: TaxRateReadOwner): TaxRateSettled {
    if (!this.owns(this.state.read, owner)) return ignored();
    this.state.read = null;
    if (!this.state.confirmed) {
      this.state.status = 'error';
      this.state.feedback = { ...idleFeedback(), tone: 'error', error: TAX_RATE_INITIAL_ERROR };
      return { accepted: true, announcement: 'assertive', message: TAX_RATE_INITIAL_ERROR };
    }
    // A failed reconciliation keeps the last known value visible but never
    // upgrades it back to confirmed, so Save and Clear stay blocked.
    const message = this.state.reconciliationRequired ? TAX_RATE_RECONCILE_FAILED_MESSAGE : TAX_RATE_REFRESH_WARNING;
    this.state.feedback = { ...this.state.feedback, tone: 'warning', neutral: '', warning: message, error: '' };
    return { accepted: true, announcement: 'polite', message };
  }

  setDraft(text: string) {
    this.state.draft = text;
    this.state.fieldError = '';
    this.state.feedback = { ...idleFeedback(), tone: this.state.feedback.warning ? 'warning' : 'none', warning: this.state.feedback.warning };
  }

  cancelEdit(): TaxRateSettled {
    if (!this.canEdit()) return ignored();
    this.state.draft = taxRateInputValue(this.state.confirmed);
    this.state.fieldError = '';
    this.state.clearConfirmVisible = false;
    this.state.feedback = { ...idleFeedback(), tone: 'neutral', neutral: TAX_RATE_CANCEL_MESSAGE };
    return { accepted: true, announcement: 'polite', message: TAX_RATE_CANCEL_MESSAGE };
  }

  requestClearConfirmation(): TaxRateStart<never> {
    const blocked = this.mutationBlocked();
    if (blocked) return { accepted: false, reason: blocked };
    if (!this.state.confirmed?.is_configured) return { accepted: false, reason: 'nothing-to-clear' };
    this.state.clearConfirmVisible = true;
    this.state.fieldError = '';
    return { accepted: true, owner: undefined as never };
  }

  cancelClearConfirmation() {
    this.state.clearConfirmVisible = false;
  }

  startSave(): TaxRateStart<TaxRateMutationOwner> {
    const blocked = this.mutationBlocked();
    if (blocked) return { accepted: false, reason: blocked };
    const checked = checkTaxRateInput(this.state.draft);
    if (!checked.ok) {
      this.state.fieldError = checked.message;
      this.state.feedback = { ...idleFeedback(), tone: 'error', error: checked.message };
      return { accepted: false, reason: 'invalid-input' };
    }
    return { accepted: true, owner: this.beginMutation('save', TAX_RATE_SAVING_MESSAGE), payload: checked.payload };
  }

  startClear(): TaxRateStart<TaxRateMutationOwner> {
    const blocked = this.mutationBlocked();
    if (blocked) return { accepted: false, reason: blocked };
    if (!this.state.clearConfirmVisible) return { accepted: false, reason: 'not-confirmed' };
    return { accepted: true, owner: this.beginMutation('clear', TAX_RATE_CLEARING_MESSAGE), payload: null };
  }

  finishMutationSuccess(owner: TaxRateMutationOwner, value: unknown): TaxRateSettled {
    if (!this.mutationMatches(owner)) return ignored();
    if (this.isDetached(owner)) return this.settleDetachedMutation();
    this.state.mutation = null;
    if (!isTaxRateSettingDto(value)) return this.presentInvalidResponse();
    this.applyConfirmed(value);
    this.state.clearConfirmVisible = false;
    this.state.feedback = { ...idleFeedback(), tone: 'success', success: value.message };
    return { accepted: true, announcement: 'polite', message: value.message, knownSuccess: true };
  }

  finishMutationFailure(owner: TaxRateMutationOwner, fieldError = ''): TaxRateSettled {
    if (!this.mutationMatches(owner)) return ignored();
    if (this.isDetached(owner)) return this.settleDetachedMutation();
    const kind = this.state.mutation?.kind;
    this.state.mutation = null;
    const message = kind === 'clear' ? TAX_RATE_CLEAR_ERROR : TAX_RATE_SAVE_ERROR;
    this.state.fieldError = kind === 'save' ? fieldError : '';
    this.state.feedback = { ...idleFeedback(), tone: 'error', error: fieldError || message };
    return { accepted: true, announcement: 'assertive', message: fieldError || message };
  }

  /**
   * A mutation that outlived its route settles silently. Its result — success or
   * failure — is never applied or announced; only the obligation to re-read the
   * authoritative value survives.
   */
  private settleDetachedMutation(): TaxRateSettled {
    this.state.mutation = null;
    settleDetachedMutation(this.state);
    return { accepted: false, announcement: 'none', message: '', detached: true, needsReconciliation: true };
  }

  canEdit() {
    return this.state.status === 'ready' && this.state.confirmed !== null && this.state.mutation === null;
  }

  /** Save and Clear need a confirmed value, which an open obligation denies. */
  canMutate() {
    return this.canEdit() && !mutationsBlocked(this.state);
  }

  private beginMutation(kind: TaxRateMutationKind, busyMessage: string): TaxRateMutationOwner {
    const owner: TaxRateMutationOwner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind };
    this.state.mutation = owner;
    this.state.fieldError = '';
    this.state.feedback = { ...idleFeedback(), tone: 'neutral', neutral: busyMessage };
    return owner;
  }

  private mutationBlocked(): TaxRateRejection | null {
    if (this.state.mutation) return 'mutation-active';
    if (this.state.detachedMutationPending) return 'detached-mutation-pending';
    if (this.state.reconciliationRequired) return 'reconciliation-required';
    if (this.state.read) return 'read-active';
    if (this.state.status !== 'ready' || this.state.confirmed === null) return 'not-ready';
    return null;
  }

  private applyConfirmed(dto: TaxRateSettingDto) {
    this.state.status = 'ready';
    this.state.confirmed = dto;
    this.state.draft = taxRateInputValue(dto);
    this.state.fieldError = '';
  }

  private presentInvalidResponse(): TaxRateSettled {
    this.state.clearConfirmVisible = false;
    if (!this.state.confirmed) this.state.status = 'error';
    requireReconciliation(this.state, 'invalid-response');
    this.state.feedback = { ...idleFeedback(), tone: 'error', error: TAX_RATE_INVALID_RESPONSE };
    return { accepted: true, announcement: 'assertive', message: TAX_RATE_INVALID_RESPONSE, needsReconciliation: true };
  }

  private owns<T extends TaxRateOwner>(current: T | null, owner: TaxRateOwner) {
    return Boolean(current && current.requestId === owner.requestId && current.routeGeneration === owner.routeGeneration && owner.routeGeneration === this.state.routeGeneration);
  }

  /** Detached mutations belong to an older generation, so they match on identity. */
  private mutationMatches(owner: TaxRateMutationOwner) {
    return Boolean(this.state.mutation && this.state.mutation.requestId === owner.requestId);
  }

  private isDetached(owner: TaxRateMutationOwner) {
    return owner.routeGeneration !== this.state.routeGeneration || this.state.detachedMutationPending;
  }
}
