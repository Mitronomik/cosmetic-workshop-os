/**
 * Local wall-clock → canonical UTC conversion for the AuditLog date filters.
 *
 * Durable contract: `docs/audit-log.md` § 7.4 and § 10.
 *
 * The user picks a wall-clock time in their own zone; the backend accepts only
 * `YYYY-MM-DDTHH:MM:SSZ`. Doing that conversion carelessly is unsafe around a
 * daylight-saving transition, and both failure modes are silent:
 *
 * * **Spring gap** — the selected local time never happens. `new Date(2026, 2,
 *   29, 2, 30)` in `Europe/Amsterdam` quietly yields `03:30`, so the request
 *   would filter on an instant the user never chose.
 * * **Autumn overlap** — the selected local time happens twice. One of the two
 *   UTC instants would be picked silently, and the user has no way to know
 *   which.
 *
 * Neither is repaired here. Both are rejected so the workspace can show the
 * person a Russian explanation and let them choose again. Omitting the filter
 * instead would silently *broaden* the query, which is equally wrong.
 *
 * The module is pure and uses no date library and no dependency: everything is
 * derived from the platform `Date` and the host time zone.
 */

/** Why a non-blank local value could not become one certain UTC instant. */
export type LocalTimestampRejection = 'invalid' | 'nonexistent-local-time' | 'ambiguous-local-time';

/**
 * The outcome of converting one date control.
 *
 * A successful conversion carries `''` when the control is empty — a blank date
 * filter is valid and simply means "no filter" — and the canonical UTC instant
 * otherwise.
 */
export type LocalTimestampConversion =
  | { ok: true; value: string }
  | { ok: false; reason: LocalTimestampRejection; message: string };

export const NONEXISTENT_LOCAL_TIME_MESSAGE =
  'Выбранное местное время не существует из-за перевода часов. Выберите другое время.';
export const AMBIGUOUS_LOCAL_TIME_MESSAGE =
  'Выбранное местное время повторяется из-за перевода часов. Выберите время вне перехода часов.';
export const INVALID_LOCAL_TIME_MESSAGE =
  'Дата указана неверно. Выберите дату и время ещё раз.';

/** What an `<input type="datetime-local">` produces, seconds optional. */
const LOCAL_INPUT_TIMESTAMP = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/;

/**
 * How far around the candidate instant to look for a second instant carrying
 * the same wall-clock components, and how finely.
 *
 * Three hours in fifteen-minute steps covers every transition size in practical
 * use — the common one hour, the half-hour shifts of Lord Howe, and the
 * historical two-hour shifts — while staying a fixed 25 comparisons rather than
 * an open-ended scan.
 */
const AMBIGUITY_WINDOW_MINUTES = 180;
const AMBIGUITY_STEP_MINUTES = 15;
const MINUTE = 60_000;

type LocalParts = { year: number; month: number; day: number; hours: number; minutes: number; seconds: number };

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function parts(value: string): LocalParts | null {
  const match = LOCAL_INPUT_TIMESTAMP.exec(value.trim());
  if (!match) return null;
  const [, year, month, day, hours, minutes, seconds] = match;
  return {
    year: Number(year),
    month: Number(month),
    day: Number(day),
    hours: Number(hours),
    minutes: Number(minutes),
    seconds: Number(seconds ?? '0'),
  };
}

/** Whether the calendar date exists at all, independently of any time zone. */
function calendarDateExists({ year, month, day }: LocalParts): boolean {
  const probe = new Date(Date.UTC(year, month - 1, day));
  return probe.getUTCFullYear() === year && probe.getUTCMonth() === month - 1 && probe.getUTCDate() === day;
}

/** Whether an instant's local components are exactly the requested ones. */
function matchesLocalParts(instant: Date, wanted: LocalParts): boolean {
  return (
    instant.getFullYear() === wanted.year &&
    instant.getMonth() === wanted.month - 1 &&
    instant.getDate() === wanted.day &&
    instant.getHours() === wanted.hours &&
    instant.getMinutes() === wanted.minutes &&
    instant.getSeconds() === wanted.seconds
  );
}

/**
 * How many distinct UTC instants near `candidate` show exactly these local
 * components.
 *
 * Zero means the wall-clock time does not exist, one means it is unambiguous,
 * and more than one means the clock repeated it.
 */
function matchingInstantCount(candidate: Date, wanted: LocalParts): number {
  const found = new Set<number>();
  for (let offset = -AMBIGUITY_WINDOW_MINUTES; offset <= AMBIGUITY_WINDOW_MINUTES; offset += AMBIGUITY_STEP_MINUTES) {
    const probe = new Date(candidate.getTime() + offset * MINUTE);
    if (matchesLocalParts(probe, wanted)) found.add(probe.getTime());
  }
  return found.size;
}

function canonicalUtc(instant: Date): string {
  return (
    `${instant.getUTCFullYear()}-${pad(instant.getUTCMonth() + 1)}-${pad(instant.getUTCDate())}` +
    `T${pad(instant.getUTCHours())}:${pad(instant.getUTCMinutes())}:${pad(instant.getUTCSeconds())}Z`
  );
}

/**
 * Convert one local date-control value into the canonical backend UTC instant.
 *
 * Every one of the six local components is verified after construction, not
 * just the date: checking only year, month and day is exactly what lets a spring
 * gap through, because the platform normalizes the *hour* while leaving the day
 * intact.
 */
export function convertLocalInputToUtc(value: string): LocalTimestampConversion {
  const text = value.trim();
  if (!text) return { ok: true, value: '' };

  const wanted = parts(text);
  if (!wanted) return { ok: false, reason: 'invalid', message: INVALID_LOCAL_TIME_MESSAGE };
  if (!calendarDateExists(wanted)) return { ok: false, reason: 'invalid', message: INVALID_LOCAL_TIME_MESSAGE };

  const candidate = new Date(wanted.year, wanted.month - 1, wanted.day, wanted.hours, wanted.minutes, wanted.seconds, 0);
  if (Number.isNaN(candidate.getTime())) return { ok: false, reason: 'invalid', message: INVALID_LOCAL_TIME_MESSAGE };

  // The calendar date is real, so any surviving component mismatch means the
  // platform moved the wall clock — a nonexistent local time, not bad input.
  if (!matchesLocalParts(candidate, wanted)) {
    return { ok: false, reason: 'nonexistent-local-time', message: NONEXISTENT_LOCAL_TIME_MESSAGE };
  }

  const matches = matchingInstantCount(candidate, wanted);
  if (matches === 0) return { ok: false, reason: 'nonexistent-local-time', message: NONEXISTENT_LOCAL_TIME_MESSAGE };
  if (matches > 1) return { ok: false, reason: 'ambiguous-local-time', message: AMBIGUOUS_LOCAL_TIME_MESSAGE };

  return { ok: true, value: canonicalUtc(candidate) };
}
