/**
 * The CR-009 B1 report-document audit contract, as the frontend is allowed to see it.
 *
 * Durable contract: `docs/decisions/0013-file-backed-artifact-audit-semantics.md`
 * and `docs/report-documents.md`.
 *
 * Two results arrive in one HTTP 201 response and must stay visibly separate:
 * the document was created (primary, authoritative) and the Journal entry was
 * or was not recorded (secondary). A pending Journal entry is **not** a failed
 * document, so it must never be rendered as an error and must never provoke a
 * second POST — the retry is the backend's, at two bounded moments it names.
 *
 * The backend owns every user-facing string here. This module only recognizes
 * them; it never composes its own wording for an audit state, so the UI cannot
 * drift from the accepted contract.
 */

/** The exact accepted warning for one document whose Journal entry is pending. */
export const REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE =
  'Документ создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего документа.';

/** The exact accepted warning while any document still awaits its Journal entry. */
export const REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING =
  'Некоторые созданные документы ещё не добавлены в журнал действий. Приложение повторит попытку при следующем запуске или перед созданием следующего документа.';

export type ReportDocumentAuditStatus = 'recorded' | 'pending';

export type ReportDocumentAuditResult = {
  /** False when the 201 body does not carry a complete, recognized audit contract. */
  valid: boolean;
  status: ReportDocumentAuditStatus | null;
  /** The exact backend warning for `pending`, and empty for `recorded`. */
  warning: string;
};

const invalid: ReportDocumentAuditResult = { valid: false, status: null, warning: '' };

/**
 * Classify the audit half of a create response.
 *
 * Only the two accepted shapes are honoured:
 *
 *   `recorded` + no message, or `pending` + exactly the accepted warning.
 *
 * Anything else — a missing field, an unknown status, a `pending` carrying
 * different or absent text — is invalid. Invalid is deliberately not treated as
 * success: the document may well exist, so the caller must fall back to its
 * existing ambiguous-response reconciliation (refresh and let the list say what
 * is really there) rather than either inventing a success or re-POSTing.
 */
export function reportDocumentAuditResult(response: unknown): ReportDocumentAuditResult {
  if (!response || typeof response !== 'object') return invalid;
  const record = response as Record<string, unknown>;
  const status = record.audit_status;
  const message = record.audit_message;
  if (status === 'recorded') {
    return message === null || message === undefined
      ? { valid: true, status: 'recorded', warning: '' }
      : invalid;
  }
  if (status === 'pending') {
    return message === REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE
      ? { valid: true, status: 'pending', warning: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE }
      : invalid;
  }
  return invalid;
}

/** A non-negative pending count from a status response, or 0 when unusable. */
export function reportDocumentPendingAuditCount(status: unknown): number {
  if (!status || typeof status !== 'object') return 0;
  const value = (status as Record<string, unknown>).pending_audit_count;
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return 0;
  return Math.floor(value);
}

/**
 * The single audit warning to show, given both sources.
 *
 * One region, not two. The just-created document's warning takes precedence
 * while it is set, because it is the more specific answer to what the user just
 * did; otherwise the standing count warning shows. Showing both at once would
 * say the same thing twice to a non-technical user.
 *
 * Neither string mentions a filename, path, operation ID, ledger or SQLite —
 * they are the backend's accepted wording, used verbatim.
 */
export function reportDocumentAuditWarning(state: { auditWarning: string; pendingAuditCount: number }): string {
  if (state.auditWarning) return state.auditWarning;
  return state.pendingAuditCount > 0 ? REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING : '';
}

/**
 * Adopt the authoritative pending count from a status read.
 *
 * The just-created document's warning is kept while the count still confirms
 * something is outstanding, so a create keeps its own wording through the
 * refresh that immediately follows it. A count of zero is the only signal the
 * accepted contract allows for clearing the standing warning — notably, a
 * *failed* read is not one, because it confirms nothing.
 */
export function adoptReportDocumentPendingAuditCount(state: ReportDocumentAuditUiState, status: unknown): void {
  state.pendingAuditCount = reportDocumentPendingAuditCount(status);
  if (state.pendingAuditCount === 0) state.auditWarning = '';
}

export type ReportDocumentAuditUiState = { auditWarning: string; pendingAuditCount: number };
