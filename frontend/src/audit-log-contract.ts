/**
 * The `C3-I` AuditLog read DTO contract.
 *
 * Durable contract: `docs/audit-log.md` § 5, § 7 and § 8.
 *
 * Privacy for this screen is **backend-owned**: the API decides what leaves the
 * database and the frontend cannot widen it. So nothing in this module — or in
 * anything downstream of it — reconstructs a summary, translates a raw code into
 * Russian, parses metadata, derives an entity name, or uses a raw code as a
 * visible fallback. The backend already sent `display_summary`, `action_label`,
 * `entity_label` and `actor_label`; those are what the user reads.
 *
 * Validation is strict on purpose. A response carrying a field the contract
 * excludes — the raw persisted `summary`, `metadata_json`, `entity_id`, or a
 * `source` / `source_label` — is an outdated or damaged backend, not a value to
 * render carefully. Such a response is rejected outright so the caller takes the
 * ordinary read-failure path, which retains the previously accepted list, rather
 * than displaying data the backend was supposed to withhold.
 */

import { convertLocalInputToUtc } from './audit-log-local-time.js';

/** One selectable filter value with the Russian label the backend resolved. */
export type AuditLogFilterOption = { value: string; label: string };

/** The filter values that actually exist as rows, never a hard-coded catalogue. */
export type AuditLogFilterOptions = {
  actions: AuditLogFilterOption[];
  entity_types: AuditLogFilterOption[];
  actor_types: AuditLogFilterOption[];
};

/** One safe history entry — exactly the nine fields of § 5.2. */
export type AuditLogItemDto = {
  id: number;
  created_at: string;
  action: string;
  action_label: string;
  entity_type: string | null;
  entity_label: string;
  display_summary: string;
  actor_type: string;
  actor_label: string;
};

export type AuditLogListResponse = {
  items: AuditLogItemDto[];
  total: number;
  limit: number;
  offset: number;
  filter_options: AuditLogFilterOptions;
};

/** The UI-side filter selection. Raw codes live here as select values only. */
export type AuditLogFilters = {
  createdFrom: string;
  createdBefore: string;
  action: string;
  entityType: string;
  actorType: string;
};

/** One structured backend rejection, already reduced to what the UI can show. */
export type AuditLogValidationIssue = {
  code: string;
  field: string;
  message: string;
  nextAction: string;
};

export const AUDIT_LOG_ENDPOINT = '/api/audit-logs';
export const AUDIT_LOG_PAGE_SIZE = 50;

/** The two date controls, and the filter keys they map to. */
export const AUDIT_LOG_DATE_FILTERS = [
  { filter: 'createdFrom', parameter: 'created_from' },
  { filter: 'createdBefore', parameter: 'created_before' },
] as const;

const TOP_LEVEL_KEYS = ['items', 'total', 'limit', 'offset', 'filter_options'] as const;
const ITEM_KEYS = [
  'id',
  'created_at',
  'action',
  'action_label',
  'entity_type',
  'entity_label',
  'display_summary',
  'actor_type',
  'actor_label',
] as const;

/**
 * Fields the backend must never send. Their presence means privacy filtering did
 * not happen where it was supposed to, so the response is refused rather than
 * partially rendered.
 */
export const FORBIDDEN_ITEM_KEYS = ['summary', 'metadata_json', 'entity_id', 'source', 'source_label'] as const;

/** The canonical API instant: `YYYY-MM-DDTHH:MM:SSZ`, UTC, second precision. */
const CANONICAL_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

export const EMPTY_AUDIT_LOG_FILTER_OPTIONS: AuditLogFilterOptions = { actions: [], entity_types: [], actor_types: [] };

export const EMPTY_AUDIT_LOG_FILTERS: AuditLogFilters = {
  createdFrom: '',
  createdBefore: '',
  action: '',
  entityType: '',
  actorType: '',
};

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function nonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

function wholeNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}

function filterOptionIsValid(value: unknown): value is AuditLogFilterOption {
  const option = record(value);
  if (!option) return false;
  if (Object.keys(option).length !== 2) return false;
  return nonEmptyString(option.value) && nonEmptyString(option.label);
}

function filterOptionsAreValid(value: unknown): value is AuditLogFilterOptions {
  const options = record(value);
  if (!options) return false;
  const keys = Object.keys(options).sort();
  if (keys.join(',') !== 'actions,actor_types,entity_types') return false;
  return Object.values(options).every((group) => Array.isArray(group) && group.every(filterOptionIsValid));
}

/**
 * Whether one item carries exactly the nine safe fields and nothing more.
 *
 * The key-set check is what makes the forbidden-field rule enforceable: an item
 * that also carries `summary` or `entity_id` fails here, so it can never reach
 * the DOM. `entity_type` is the one nullable field — the column is nullable and
 * a `null` there is ordinary, carrying the backend's unknown-entity label.
 */
export function auditLogItemDtoIsValid(value: unknown): value is AuditLogItemDto {
  const item = record(value);
  if (!item) return false;
  if (FORBIDDEN_ITEM_KEYS.some((key) => key in item)) return false;
  if (Object.keys(item).length !== ITEM_KEYS.length) return false;
  if (!ITEM_KEYS.every((key) => key in item)) return false;
  if (!wholeNumber(item.id)) return false;
  if (!nonEmptyString(item.created_at) || !CANONICAL_TIMESTAMP.test(item.created_at)) return false;
  if (item.entity_type !== null && !nonEmptyString(item.entity_type)) return false;
  return (['action', 'action_label', 'entity_label', 'display_summary', 'actor_type', 'actor_label'] as const)
    .every((key) => nonEmptyString(item[key]));
}

/** Whether a payload is a complete, current and safe AuditLog page. */
export function auditLogListDtoIsValid(value: unknown): value is AuditLogListResponse {
  const payload = record(value);
  if (!payload) return false;
  if (Object.keys(payload).length !== TOP_LEVEL_KEYS.length) return false;
  if (!TOP_LEVEL_KEYS.every((key) => key in payload)) return false;
  if (!wholeNumber(payload.total) || !wholeNumber(payload.limit) || !wholeNumber(payload.offset)) return false;
  if (!Array.isArray(payload.items) || !payload.items.every(auditLogItemDtoIsValid)) return false;
  // A page cannot claim more rows than the total it was counted against.
  if (payload.items.length > payload.total) return false;
  return filterOptionsAreValid(payload.filter_options);
}

/** Whether two filter selections are the same, compared field by field. */
export function auditLogFiltersEqual(left: AuditLogFilters, right: AuditLogFilters): boolean {
  return (Object.keys(EMPTY_AUDIT_LOG_FILTERS) as (keyof AuditLogFilters)[]).every((key) => left[key] === right[key]);
}

/**
 * A request that can be sent, or the date-control errors that stop it.
 *
 * There is deliberately no third outcome where a non-blank date is dropped and
 * the request proceeds: silently omitting a filter the user set would broaden
 * the query behind their back, which is as wrong as sending the wrong instant.
 */
export type AuditLogRequestPlan =
  | { ok: true; url: string }
  | { ok: false; fieldErrors: AuditLogDateFieldErrors };

export type AuditLogDateFieldErrors = { createdFrom: string; createdBefore: string };

export const NO_AUDIT_LOG_FIELD_ERRORS: AuditLogDateFieldErrors = { createdFrom: '', createdBefore: '' };

/**
 * Build the request for one page, or refuse with per-control Russian errors.
 *
 * Both date controls are converted before anything is sent, so a nonexistent or
 * ambiguous local time is reported against the exact control that carries it
 * rather than surfacing later as a generic network failure.
 */
export function auditLogRequestPlan(filters: AuditLogFilters, page: { limit: number; offset: number }): AuditLogRequestPlan {
  const search = new URLSearchParams();
  const fieldErrors: AuditLogDateFieldErrors = { ...NO_AUDIT_LOG_FIELD_ERRORS };
  let rejected = false;

  for (const { filter, parameter } of AUDIT_LOG_DATE_FILTERS) {
    const conversion = convertLocalInputToUtc(filters[filter]);
    if (!conversion.ok) {
      fieldErrors[filter] = conversion.message;
      rejected = true;
      continue;
    }
    if (conversion.value) search.set(parameter, conversion.value);
  }
  if (rejected) return { ok: false, fieldErrors };

  if (filters.action) search.set('action', filters.action);
  if (filters.entityType) search.set('entity_type', filters.entityType);
  if (filters.actorType) search.set('actor_type', filters.actorType);
  search.set('limit', String(page.limit));
  search.set('offset', String(page.offset));
  return { ok: true, url: `${AUDIT_LOG_ENDPOINT}?${search.toString()}` };
}

/**
 * The structured `{"detail": {...}}` rejection carried by a failed request.
 *
 * Returns `null` for anything that is not the project's own envelope — a network
 * failure, an HTML error page, or raw framework internals — so the caller falls
 * back to its own safe Russian copy instead of showing a technical body.
 */
export function auditLogValidationIssue(error: unknown): AuditLogValidationIssue | null {
  const failure = record(error);
  if (!failure || failure.status !== 422) return null;
  const payload = record(failure.payload);
  const detail = payload ? record(payload.detail) : null;
  if (!detail) return null;
  if (!nonEmptyString(detail.code) || !nonEmptyString(detail.message)) return null;
  return {
    code: detail.code,
    field: nonEmptyString(detail.field) ? detail.field : '',
    message: detail.message,
    nextAction: nonEmptyString(detail.next_action) ? detail.next_action : '',
  };
}

/** Whether every matching row has already been accepted into the list. */
export function auditLogAllRowsLoaded(loadedCount: number, total: number): boolean {
  return loadedCount >= total;
}

/**
 * Append a page while keeping list identity stable.
 *
 * `id` is used purely as a key here — never as a business value — and the guard
 * exists so a repeated or overlapping page can never produce two DOM rows with
 * the same identity.
 */
export function appendAuditLogPage(current: AuditLogItemDto[], page: AuditLogItemDto[]): AuditLogItemDto[] {
  const seen = new Set(current.map((item) => item.id));
  return [...current, ...page.filter((item) => !seen.has(item.id))];
}
