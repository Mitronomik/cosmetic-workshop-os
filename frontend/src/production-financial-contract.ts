/**
 * The `C2-III-A` frontend financial DTO contract.
 *
 * Durable contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.
 *
 * Every financial value the backend owns — money, percentages and the tax rate —
 * is carried here exactly as the API returned it: a string, or `null` when the
 * backend could not produce a value. Nothing in this module converts a financial
 * value into a JavaScript number, and nothing derives one value from another.
 *
 * `"0.00"` is a real zero, `null` is unavailable, and a negative margin stays
 * negative. The three states are kept apart at the type level so presentation
 * can never collapse them into one another.
 *
 * The canonical tax-rate pair checks stay in `order-production-context.ts`, the
 * module that already owns the confirmation context, so the readiness estimate,
 * the confirmation request and the `ProductionBatch` snapshots can never drift
 * apart into two different definitions of "canonical".
 */

import { readinessTaxRateContextIsValid } from './order-production-context.js';

/** The backend-owned availability of a readiness financial estimate. */
export const FINANCIAL_ESTIMATE_STATUSES = ['available', 'partial', 'unavailable'] as const;

export type FinancialEstimateStatus = (typeof FINANCIAL_ESTIMATE_STATUSES)[number];

/**
 * The additive readiness financial fields (`C2-I`).
 *
 * `financial_estimate_status` is stated by the backend. The frontend never
 * infers it from which of the other fields happen to be `null`.
 */
export type ReadinessFinancials = {
  sale_price: string | null;
  estimated_cost: string | null;
  tax_rate_percent: string | null;
  tax_rate_effective_at: string | null;
  estimated_tax: string | null;
  estimated_margin: string | null;
  estimated_margin_percent: string | null;
  financial_estimate_status: FinancialEstimateStatus;
};

/**
 * The immutable `ProductionBatch` detail snapshot (`C2-II`).
 *
 * The two rate-snapshot fields are detail-only by contract and are deliberately
 * absent from `BatchListFinancials`.
 */
export type BatchFinancialSnapshot = {
  sale_price: string | null;
  total_cost: string | null;
  tax_rate_percent_snapshot: string | null;
  tax_rate_effective_at_snapshot: string | null;
  tax: string | null;
  margin: string | null;
  margin_percent: string | null;
};

/** The five financial fields the existing `ProductionBatch` list item carries. */
export type BatchListFinancials = {
  sale_price: string | null;
  total_cost: string | null;
  tax: string | null;
  margin: string | null;
  margin_percent: string | null;
};

/** The per-line cost snapshots a produced batch persisted for one ingredient. */
export type BatchIngredientCostLine = {
  ingredient_name_snapshot: string;
  lot_code_snapshot: string;
  required_quantity: string;
  consumed_quantity: string;
  unit: string;
  unit_cost_snapshot: string | null;
  total_cost_snapshot: string | null;
  expiration_date_snapshot: string | null;
};

/** The per-line cost snapshots a produced batch persisted for one packaging item. */
export type BatchPackagingCostLine = {
  packaging_name_snapshot: string;
  quantity: string;
  unit: string;
  unit_cost_snapshot: string | null;
  total_cost_snapshot: string | null;
};

const READINESS_RESULT_KEYS = [
  'sale_price',
  'estimated_cost',
  'estimated_tax',
  'estimated_margin',
  'estimated_margin_percent',
] as const;

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

/**
 * Whether a financial result field is present and shaped as the contract states.
 *
 * The key must exist: an absent key is an outdated response, not a backend
 * statement that the value is unavailable. Only a string or an explicit `null`
 * is accepted, and neither is normalized or repaired.
 */
function presentStringOrNull(payload: Record<string, unknown>, key: string): boolean {
  if (!(key in payload)) return false;
  const value = payload[key];
  return value === null || typeof value === 'string';
}

/** Whether a value is exactly one of the three backend financial statuses. */
export function financialEstimateStatusIsValid(value: unknown): value is FinancialEstimateStatus {
  return typeof value === 'string' && (FINANCIAL_ESTIMATE_STATUSES as readonly string[]).includes(value);
}

/**
 * Whether a readiness payload carries the complete current financial contract.
 *
 * A readiness result missing any additive financial key is no longer a trusted
 * current result — it is an outdated response, and the caller must use the
 * existing untrusted-readiness failure path instead of rendering a guess.
 */
export function readinessFinancialsAreValid(value: unknown): boolean {
  const payload = record(value);
  if (!payload) return false;
  if (!READINESS_RESULT_KEYS.every((key) => presentStringOrNull(payload, key))) return false;
  if (!financialEstimateStatusIsValid(payload.financial_estimate_status)) return false;
  return readinessTaxRateContextIsValid(payload);
}
