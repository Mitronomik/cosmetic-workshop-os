/**
 * The tax-rate context a production confirmation must echo back (`C2-II`).
 *
 * Durable contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.
 *
 * The frontend owns exactly one financial responsibility here: carry the pair
 * the latest accepted readiness result returned, unchanged, into the
 * confirmation request. It never calculates a rate, never normalizes one, never
 * parses either value into a JavaScript number, never reformats the timestamp,
 * never invents one, and never substitutes the settings endpoint.
 *
 * Absent context fields are not the same as explicit `null/null`. A readiness
 * DTO that does not carry the pair is not a valid no-rate result — it is an
 * outdated or untrusted response, and confirmation is blocked rather than
 * fabricated.
 */

/** The exact pair readiness returned: both configured, or both `null`. */
export type ReadinessTaxRateContext = {
  expected_tax_rate_percent: string | null;
  expected_tax_rate_effective_at: string | null;
};

export type ProductionConfirmRequestBody = ReadinessTaxRateContext & {
  confirm: true;
  notes: string | null;
};

export const TAX_RATE_CONTEXT_STALE_CODE = 'tax_rate_context_stale';

export const TAX_RATE_CONTEXT_STALE_MESSAGE =
  'Налоговая ставка изменилась. Изготовление не выполнено: заказ, склад и партии не тронуты.';

export const TAX_RATE_CONTEXT_STALE_NEXT_ACTION =
  'Запустите проверку готовности заново и подтвердите изготовление ещё раз.';

/** Canonical `YYYY-MM-DDTHH:MM:SSZ`, matching the backend contract exactly. */
const CANONICAL_EFFECTIVE_AT = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$/;

/**
 * Canonical percentage shape: exactly two fractional digits, no sign, no
 * exponent, and no leading zero padding — `06.00` is not what readiness returns.
 */
const CANONICAL_PERCENT = /^(0|[1-9]\d*)\.\d{2}$/;

/**
 * Whether a percentage string is exactly the canonical backend form.
 *
 * Boundary validation only. The range check compares the integer and fractional
 * digits directly rather than parsing a float, so no JavaScript floating-point
 * arithmetic is introduced and `100.01` is rejected without ever computing a
 * money value.
 */
export function isCanonicalTaxRatePercent(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  const match = CANONICAL_PERCENT.exec(value);
  if (!match) return false;
  const [whole, fraction] = value.split('.');
  if (whole.length > 3) return false;
  // Range is 0.00–100.00 inclusive; above 100 the only legal value is 100.00.
  if (Number(whole) > 100) return false;
  if (Number(whole) === 100 && fraction !== '00') return false;
  return true;
}

const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function isRealCalendarDay(year: number, month: number, day: number): boolean {
  if (month < 1 || month > 12 || day < 1) return false;
  const leap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
  const limit = month === 2 && leap ? 29 : DAYS_IN_MONTH[month - 1];
  return day <= limit;
}

/**
 * Whether a timestamp is exactly one real canonical UTC instant.
 *
 * The shape check alone would accept `2026-02-30T00:00:00Z` and `25:00:00`, so
 * the calendar and clock fields are validated explicitly. Offsets and
 * fractional seconds cannot match the pattern at all.
 */
export function isCanonicalTaxRateTimestamp(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  const match = CANONICAL_EFFECTIVE_AT.exec(value);
  if (!match) return false;
  const [, year, month, day, hour, minute, second] = match.map(Number) as unknown as number[];
  if (!isRealCalendarDay(year, month, day)) return false;
  return hour <= 23 && minute <= 59 && second <= 59;
}

/**
 * The one shared canonical pair check, used by both the readiness context and
 * the `ProductionBatch` snapshots so they can never drift apart.
 */
function isCanonicalRatePair(percent: unknown, effectiveAt: unknown): boolean {
  return isCanonicalTaxRatePercent(percent) && isCanonicalTaxRateTimestamp(effectiveAt);
}

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

/**
 * Whether a readiness payload carries a usable tax context.
 *
 * Both fields must be present. Either both are `null`, or both are canonical
 * strings — a half-populated pair is rejected rather than repaired.
 */
export function readinessTaxRateContextIsValid(value: unknown): boolean {
  const payload = record(value);
  if (!payload) return false;
  if (!('tax_rate_percent' in payload) || !('tax_rate_effective_at' in payload)) return false;
  const percent = payload.tax_rate_percent;
  const effectiveAt = payload.tax_rate_effective_at;
  if (percent === null && effectiveAt === null) return true;
  return isCanonicalRatePair(percent, effectiveAt);
}

/**
 * Take the confirmation context from an accepted readiness result.
 *
 * Returns `null` when the readiness result cannot supply one, so the caller
 * blocks confirmation instead of sending a guessed pair.
 */
export function taxRateContextFromReadiness(value: unknown): ReadinessTaxRateContext | null {
  if (!readinessTaxRateContextIsValid(value)) return null;
  const payload = record(value) as Record<string, unknown>;
  return {
    expected_tax_rate_percent: payload.tax_rate_percent as string | null,
    expected_tax_rate_effective_at: payload.tax_rate_effective_at as string | null,
  };
}

/** Build the confirmation body, passing the readiness pair through untouched. */
export function productionConfirmRequestBody(
  notes: string | undefined,
  context: ReadinessTaxRateContext,
): ProductionConfirmRequestBody {
  return {
    confirm: true,
    notes: notes?.trim() || null,
    expected_tax_rate_percent: context.expected_tax_rate_percent,
    expected_tax_rate_effective_at: context.expected_tax_rate_effective_at,
  };
}

/** Whether a production failure is the known no-write stale-context conflict. */
export function isTaxRateContextStaleFailure(
  failure: { status?: number; code?: string } | null | undefined,
): boolean {
  return failure?.status === 409 && failure?.code === TAX_RATE_CONTEXT_STALE_CODE;
}

/** Whether the two snapshot fields on a batch DTO are shaped as contracted. */
export function batchTaxRateSnapshotsAreValid(value: unknown): boolean {
  const payload = record(value);
  if (!payload) return false;
  const percent = payload.tax_rate_percent_snapshot;
  const effectiveAt = payload.tax_rate_effective_at_snapshot;
  if (percent === undefined && effectiveAt === undefined) return true;
  if (percent === null && effectiveAt === null) return true;
  return isCanonicalRatePair(percent, effectiveAt);
}
