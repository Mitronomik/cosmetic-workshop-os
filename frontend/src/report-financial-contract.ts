/**
 * The `C2-III-B` finance-report DTO contract.
 *
 * Durable contract: `docs/reports.md` § *Accepted `C2-III-B` snapshot
 * aggregation contract*.
 *
 * Every financial value the backend owns is carried here exactly as the API
 * returned it: a decimal string, or `null` when the backend has no value.
 * Nothing in this module converts a financial value into a JavaScript number,
 * sums one, or derives one field from another.
 *
 * `"0.00"` is a real zero, `null` is unavailable, and a negative margin stays
 * negative — three distinct states that presentation must never collapse.
 *
 * Validation is strict on purpose. A finance response missing an additive key,
 * or carrying a counter pair that does not add up, is an outdated or damaged
 * response rather than a backend statement that something is unavailable, and
 * the caller must take the existing Reports read-failure path — which retains
 * the previously accepted snapshot — instead of rendering a guess. Nothing here
 * repairs or normalizes a malformed value.
 */

/** One backend-owned report warning. Codes and text are never invented here. */
export type ReportWarning = { code: string; message: string; field: string | null };

/**
 * The snapshot-backed finance report.
 *
 * `complete_finance_record_count` and `incomplete_margin_count` are the legacy
 * paired sale-price/cost coverage counters, kept for backward compatibility.
 * The four `*_snapshot_*` counters are the authoritative tax and margin
 * coverage. The two kinds describe different sets of batches and are never
 * presented as one another.
 */
export type FinanceReportResponse = {
  generated_at: string;
  produced_order_count: number;
  produced_orders_with_sale_price: number;
  known_revenue: string | null;
  known_production_cost: string | null;
  known_tax: string | null;
  known_margin: string | null;
  known_margin_percent: string | null;
  complete_finance_record_count: number;
  incomplete_margin_count: number;
  missing_sale_price_count: number;
  missing_cost_count: number;
  tax_snapshot_record_count: number;
  missing_tax_snapshot_count: number;
  margin_snapshot_record_count: number;
  missing_margin_snapshot_count: number;
  warnings: ReportWarning[];
};

/** The finance-carrying part of the overview report, typed as the same DTO. */
export type OverviewFinanceSummary = { finance_summary: FinanceReportResponse };

/** Every money or percentage field, each a decimal string or an explicit null. */
const MONETARY_KEYS = [
  'known_revenue',
  'known_production_cost',
  'known_tax',
  'known_margin',
  'known_margin_percent',
] as const;

/** Every counter, each a non-negative integer. */
const COUNTER_KEYS = [
  'produced_order_count',
  'produced_orders_with_sale_price',
  'complete_finance_record_count',
  'incomplete_margin_count',
  'missing_sale_price_count',
  'missing_cost_count',
  'tax_snapshot_record_count',
  'missing_tax_snapshot_count',
  'margin_snapshot_record_count',
  'missing_margin_snapshot_count',
] as const;

/** The counter pairs the backend guarantees cover every produced batch once. */
const COUNTER_PAIRS = [
  ['tax_snapshot_record_count', 'missing_tax_snapshot_count'],
  ['margin_snapshot_record_count', 'missing_margin_snapshot_count'],
] as const;

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

/**
 * The one shape a backend money or percentage value may take.
 *
 * An anchored, non-backtracking check on the characters themselves — an
 * optional minus, no leading zero unless the whole part *is* zero, a decimal
 * point, and exactly two fractional digits. The value is never converted to a
 * number, so a decimal string keeps the precision the backend sent it with and
 * a shape the presentation layer cannot misread.
 *
 * `"0.00"`, `"-0.01"` and `"1000000.00"` pass. `""`, `"1"`, `"1.0"`,
 * `"1.000"`, `"+1.00"`, `"01.00"`, `"1e3"`, `"6,00"`, `"NaN"` and `"Infinity"`
 * do not.
 */
const CANONICAL_DECIMAL = /^-?(?:0|[1-9]\d*)\.\d{2}$/;

/**
 * Whether a monetary field is present and shaped as the contract states.
 *
 * The key must exist: an absent key is an outdated response, not a statement
 * that the value is unavailable. Only an explicit `null` or a canonical decimal
 * string passes. A value that is nearly right — untrimmed, unpadded, comma-
 * separated, or in exponent form — is rejected rather than trimmed, padded,
 * rounded or otherwise repaired here.
 */
function monetaryValueIsValid(payload: Record<string, unknown>, key: string): boolean {
  if (!(key in payload)) return false;
  const value = payload[key];
  if (value === null) return true;
  return typeof value === 'string' && CANONICAL_DECIMAL.test(value);
}

/** Whether a counter is present as a non-negative whole number. */
function counterIsValid(payload: Record<string, unknown>, key: string): boolean {
  if (!(key in payload)) return false;
  const value = payload[key];
  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}

/** Whether the warning list is well-formed and states each code at most once. */
function warningsAreValid(value: unknown): boolean {
  if (!Array.isArray(value)) return false;
  const seen = new Set<string>();
  for (const entry of value) {
    const warning = record(entry);
    if (!warning) return false;
    if (typeof warning.code !== 'string' || !warning.code) return false;
    if (typeof warning.message !== 'string' || !warning.message) return false;
    if (!('field' in warning)) return false;
    if (warning.field !== null && typeof warning.field !== 'string') return false;
    if (seen.has(warning.code)) return false;
    seen.add(warning.code);
  }
  return true;
}

/**
 * Whether a payload carries the complete current finance contract.
 *
 * The counter-pair check below is a rejection guard, not a displayed value: it
 * confirms the backend's own coverage arithmetic is internally consistent
 * before any of it is shown. The frontend never computes a coverage number of
 * its own from it.
 */
export function financeReportDtoIsValid(value: unknown): value is FinanceReportResponse {
  const payload = record(value);
  if (!payload) return false;
  if (typeof payload.generated_at !== 'string' || !payload.generated_at) return false;
  if (!MONETARY_KEYS.every((key) => monetaryValueIsValid(payload, key))) return false;
  if (!COUNTER_KEYS.every((key) => counterIsValid(payload, key))) return false;
  if (!COUNTER_PAIRS.every(([known, missing]) => (payload[known] as number) + (payload[missing] as number) === payload.produced_order_count)) return false;
  return warningsAreValid(payload.warnings);
}

/** Whether an overview payload nests the same complete finance contract. */
export function overviewFinanceSummaryIsValid(value: unknown): value is OverviewFinanceSummary {
  const payload = record(value);
  return payload !== null && financeReportDtoIsValid(payload.finance_summary);
}

/**
 * Whether both Reports finance surfaces are current and trustworthy together.
 *
 * The Finance tab and the Overview tab render one authoritative DTO, so a
 * malformed response on either side fails the whole read rather than leaving
 * one tab showing a validated result next to an unvalidated one.
 */
export function reportsFinanceContractIsValid(finance: unknown, overview: unknown): boolean {
  return financeReportDtoIsValid(finance) && overviewFinanceSummaryIsValid(overview);
}
