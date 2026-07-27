/**
 * Composes the tax-setting feedback banner from lifecycle facts.
 *
 * Kept apart from the state machine because the delicate part is which message a
 * given situation is allowed to show: an open reconciliation obligation is not a
 * failure, and only an authoritative read that actually rejected licenses the
 * failure copy.
 */
import {
  TAX_RATE_RECONCILE_FAILED_MESSAGE,
  TAX_RATE_RECONCILING_MESSAGE,
  type TaxRateReconciliationFields,
} from './settings-tax-reconciliation.js';
import { busyMessage, TAX_RATE_DETACHED_PENDING_MESSAGE } from './settings-tax-messages.js';
import type { TaxRateReadKind } from './settings-tax-feedback.js';

export type TaxRateFeedbackTone = 'none' | 'neutral' | 'success' | 'warning' | 'error';
export type TaxRateFeedback = { tone: TaxRateFeedbackTone; neutral: string; success: string; warning: string; error: string };

export const idleFeedback = (): TaxRateFeedback => ({ tone: 'none', neutral: '', success: '', warning: '', error: '' });

/** Returning to the route: wait quietly while pending, warn only after a real failure. */
export function reentryFeedback(fields: TaxRateReconciliationFields): TaxRateFeedback {
  if (fields.detachedMutationPending) return { ...idleFeedback(), tone: 'neutral', neutral: TAX_RATE_DETACHED_PENDING_MESSAGE };
  if (fields.reconciliationFailed) return { ...idleFeedback(), tone: 'warning', warning: TAX_RATE_RECONCILE_FAILED_MESSAGE };
  return idleFeedback();
}

/**
 * A first reconciliation shows only the checking message. An explicit retry after
 * a real failure keeps that failure visible until it resolves, and an invalid
 * response keeps its own error for the same reason.
 */
export function reconciliationBusyFeedback(fields: TaxRateReconciliationFields, current: TaxRateFeedback): TaxRateFeedback {
  const busy: TaxRateFeedback = { ...idleFeedback(), tone: 'neutral', neutral: TAX_RATE_RECONCILING_MESSAGE };
  if (fields.reconciliationReason === 'invalid-response' && current.error) return { ...busy, tone: 'error', error: current.error };
  if (fields.reconciliationFailed) return { ...busy, tone: 'warning', warning: TAX_RATE_RECONCILE_FAILED_MESSAGE };
  return busy;
}

export function readBusyFeedback(current: TaxRateFeedback, kind: TaxRateReadKind): TaxRateFeedback {
  return { ...current, tone: 'neutral', neutral: busyMessage(kind), error: '' };
}
