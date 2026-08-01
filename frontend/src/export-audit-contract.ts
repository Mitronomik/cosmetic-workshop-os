/**
 * The CR-009 B2 JSON-export audit contract, as the frontend is allowed to see it.
 *
 * Durable contract: `docs/decisions/0013-file-backed-artifact-audit-semantics.md`,
 * `docs/decisions/0014-json-export-create-confirmation-semantics.md` and
 * `docs/export.md`.
 *
 * Two results arrive in one HTTP 201 response and must stay visibly separate:
 * the export file was created (primary, authoritative) and the Journal entry was
 * or was not recorded (secondary). A pending Journal entry is **not** a failed
 * export, so it must never be rendered as an error and must never provoke a
 * second POST — the retry is the backend's, at two bounded moments it names.
 *
 * The backend owns every user-facing string here. This module only recognizes
 * them; it never composes its own wording for an audit state, so the UI cannot
 * drift from the accepted contract.
 *
 * This deliberately mirrors `report-document-audit-contract.ts` rather than
 * generalizing it. The two artifact kinds have different backend-owned Russian
 * wording, and a shared "artifact" abstraction would make it possible to show a
 * document's warning on the exports page.
 */

/** The exact accepted warning for one export whose Journal entry is pending. */
export const EXPORT_PENDING_AUDIT_MESSAGE =
  'Экспорт создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта.';

/** The exact accepted warning while any export still awaits its Journal entry. */
export const EXPORT_PENDING_AUDIT_COUNT_WARNING =
  'Некоторые созданные экспорты ещё не добавлены в журнал действий. Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта.';

export type ExportAuditStatus = 'recorded' | 'pending';

export type ExportAuditResult = {
  /** False when the 201 body does not carry a complete, recognized audit contract. */
  valid: boolean;
  status: ExportAuditStatus | null;
  /** The exact backend warning for `pending`, and empty for `recorded`. */
  warning: string;
};

const invalid: ExportAuditResult = { valid: false, status: null, warning: '' };

/**
 * Classify the audit half of a create response.
 *
 * Only the two accepted shapes are honoured:
 *
 *   `recorded` + no message, or `pending` + exactly the accepted warning.
 *
 * Anything else — a missing field, an unknown status, a `pending` carrying
 * different or absent text — is invalid. Invalid is deliberately not treated as
 * success: the export may well exist, so the caller must fall back to its
 * existing ambiguous-response reconciliation (refresh and let the list say what
 * is really there) rather than either inventing a success or re-POSTing.
 */
export function exportAuditResult(response: unknown): ExportAuditResult {
  if (!response || typeof response !== 'object') return invalid;
  const record = response as Record<string, unknown>;
  const status = record.audit_status;
  const message = record.audit_message;
  if (status === 'recorded') {
    // Explicit `null`, not merely absent. An omitted `audit_message` means the
    // response did not carry the field at all, which is an *incomplete* contract
    // — it cannot be distinguished from a truncated or older-shaped body, so it
    // must not be read as a confident "recorded with no warning".
    return message === null && 'audit_message' in record
      ? { valid: true, status: 'recorded', warning: '' }
      : invalid;
  }
  if (status === 'pending') {
    return message === EXPORT_PENDING_AUDIT_MESSAGE
      ? { valid: true, status: 'pending', warning: EXPORT_PENDING_AUDIT_MESSAGE }
      : invalid;
  }
  return invalid;
}

/**
 * The pending count from a status response, or `null` when it is not knowable.
 *
 * `null` and `0` are deliberately different answers. `0` is a factual claim that
 * no export is awaiting a Journal entry, and the UI clears a standing warning on
 * it. A missing, non-numeric, non-finite, negative or fractional value tells us
 * nothing, so it must not be coerced into that claim — an older or truncated
 * response could otherwise erase a real warning.
 *
 * Fractional values are rejected rather than floored: a count is a whole number
 * of operations, and `0.5` is a malformed body, not "zero-ish".
 */
export function exportPendingAuditCount(status: unknown): number | null {
  if (!status || typeof status !== 'object') return null;
  const value = (status as Record<string, unknown>).pending_audit_count;
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0) return null;
  return value;
}

/**
 * The single audit warning to show, given both sources.
 *
 * One region, not two. The just-created export's warning takes precedence while
 * it is set, because it is the more specific answer to what the user just did;
 * otherwise the standing count warning shows. Showing both at once would say the
 * same thing twice to a non-technical user.
 *
 * Neither string mentions a filename, path, operation ID, ledger or SQLite —
 * they are the backend's accepted wording, used verbatim.
 */
export function exportAuditWarning(state: { auditWarning: string; pendingAuditCount: number | null }): string {
  if (state.auditWarning) return state.auditWarning;
  return (state.pendingAuditCount ?? 0) > 0 ? EXPORT_PENDING_AUDIT_COUNT_WARNING : '';
}

/**
 * Adopt a pending count from a status read, but only a knowable one.
 *
 * An unusable value leaves both the previous count and the previous warning
 * exactly as they were. That is the whole point: the last thing we actually
 * knew stays on screen until something authoritative replaces it, so a
 * malformed body can never quietly retract a real warning.
 *
 * A validated `0` is the only signal the accepted contract allows for clearing
 * the standing warning — a failed or malformed read is not one, because it
 * confirms nothing.
 */
export function adoptExportPendingAuditCount(state: ExportAuditUiState, status: unknown): void {
  const count = exportPendingAuditCount(status);
  if (count === null) return;
  state.pendingAuditCount = count;
  if (count === 0) state.auditWarning = '';
}

export type ExportAuditUiState = { auditWarning: string; pendingAuditCount: number | null };
