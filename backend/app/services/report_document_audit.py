"""Durable report-document AuditLog coverage: reserve, verify, finalize, reconcile.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
(CR-009) and ``docs/report-documents.md`` § "CR-009 B1 durable AuditLog
contract".

The problem this module exists to solve is that writing two files to disk and
inserting a row into SQLite is not one transaction and cannot be made into one.
The accepted decision resolves that honestly rather than pretending otherwise:

- the fully written and verified document pair is the **primary** result and is
  authoritative once it exists;
- the AuditLog event is a **secondary** result;
- a secondary failure never deletes the primary result and never reports total
  failure;
- but it is also never silently forgotten — the operation stays unresolved,
  is counted, and is retried at exactly two bounded moments.

Those two moments are normal application startup (after migrations) and once
before the next document is created. There is deliberately no background
thread, timer, queue, worker or unbounded retry here; adding one would turn a
bounded local ledger into the generic outbox the decision rejected.

This module intentionally does not import ``app.services.report_documents``.
The dependency runs the other way, and the verifier owns its own copy of the
accepted format vocabulary below; ``test_report_document_audit.py`` asserts the
two stay in agreement so the duplication cannot drift.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Final, Literal

from app.db.config import DatabaseConfig, get_database_config
from app.db.transactions import transaction
from app.domain.artifact_audit_operations import (
    ARTIFACT_KIND_REPORT_DOCUMENT,
    AUDIT_ACTION_REPORT_DOCUMENT_CREATED,
    ArtifactAuditOperationError,
    STATUS_AUDITED,
    UNRESOLVED_STATUSES,
    is_safe_artifact_filename,
    new_operation_id,
)
from app.repositories.artifact_audit_operations import ArtifactAuditOperation, ArtifactAuditOperationRepository
from app.repositories.audit import AuditLogRepository
from app.schemas.report_documents import ReportDocumentMetadata

# The verifier's own accepted contract table, kept independent of the renderer so
# that this module has no import cycle with the service that calls it.
SUPPORTED_DOCUMENT_TYPE: Final = "workshop_overview"
SUPPORTED_FORMAT_EXTENSIONS: Final[dict[str, str]] = {"markdown": ".md", "pdf": ".pdf"}
METADATA_EXTENSION: Final = ".json"

AUDIT_ENTITY_TYPE: Final = "report_document"
AUDIT_ACTOR_TYPE: Final = "user"
AUDIT_SUMMARY: Final = "Report document created"

# `docs/report-documents.md`. The user is told the two bounded retry moments and
# nothing technical: no filename, no path, no operation ID, no SQLite wording.
PENDING_AUDIT_MESSAGE: Final = (
    "Документ создан, но запись в журнал действий пока не добавлена. "
    "Приложение повторит попытку при следующем запуске или перед созданием следующего документа."
)

TRACKING_UNAVAILABLE_CODE: Final = "artifact_audit_tracking_unavailable"
TRACKING_UNAVAILABLE_MESSAGE: Final = "Не удалось безопасно подготовить создание документа. Документ не создан."
TRACKING_UNAVAILABLE_NEXT_ACTION: Final = (
    "Повторите создание документа. Если ошибка повторяется, перезапустите приложение."
)

VerificationOutcome = Literal["valid", "definitely_absent", "ambiguous"]


class ReportDocumentAuditTrackingUnavailableError(RuntimeError):
    """Raised when report-document audit tracking cannot be durably prepared.

    This is the *only* failure that prevents the document from being created at
    all. It happens strictly before either file is written, so nothing needs to
    be compensated when it is raised.
    """

    code = TRACKING_UNAVAILABLE_CODE
    message = TRACKING_UNAVAILABLE_MESSAGE
    next_action = TRACKING_UNAVAILABLE_NEXT_ACTION


@dataclass(frozen=True)
class ReportDocumentVerification:
    outcome: VerificationOutcome
    reason: str
    metadata: ReportDocumentMetadata | None = None

    @property
    def is_valid(self) -> bool:
        return self.outcome == "valid"


@dataclass(frozen=True)
class ReportDocumentReconciliationResult:
    """What one bounded reconciliation pass did. Internal; never user-facing."""

    examined: int = 0
    audited: int = 0
    abandoned: int = 0
    unresolved: int = 0
    failed: int = 0


class ReportDocumentAuditService:
    """The single owner of report-document artifact-audit operations.

    One instance covers all three entry points — immediate finalization after a
    create, startup reconciliation and pre-create reconciliation — because all
    three must use the *same* verifier and the *same* finalizer. Two
    near-identical code paths would be exactly how a duplicate event or an
    inconsistent verification rule gets in.
    """

    def __init__(self, documents_dir: Path, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()
        self.documents_dir = documents_dir
        self.repository = ArtifactAuditOperationRepository(self.config)
        self.audit_repository = AuditLogRepository(self.config)

    # ---------------------------------------------------------------- reserve

    def is_identity_active(self, primary_filename: str, companion_filename: str) -> bool:
        """Whether an unresolved operation already owns this artifact identity."""
        return self.repository.has_active_identity(
            ARTIFACT_KIND_REPORT_DOCUMENT,
            primary_filename=primary_filename,
            companion_filename=companion_filename,
        )

    def prepare_operation(self, *, primary_filename: str, companion_filename: str) -> str:
        """Commit one `prepared` ledger row and return its operation ID.

        Called before either file is written. If it raises, no document exists
        and none will: the caller maps the error to the accepted HTTP 500
        contract, which is the one case where a create is refused outright.
        """
        try:
            operation_id = new_operation_id()
            self.repository.prepare_operation(
                operation_id=operation_id,
                artifact_kind=ARTIFACT_KIND_REPORT_DOCUMENT,
                primary_filename=primary_filename,
                companion_filename=companion_filename,
                audit_action=AUDIT_ACTION_REPORT_DOCUMENT_CREATED,
            )
            return operation_id
        except (ArtifactAuditOperationError, sqlite3.Error, OSError) as failure:
            raise ReportDocumentAuditTrackingUnavailableError(TRACKING_UNAVAILABLE_MESSAGE) from failure

    def abandon_operation(self, operation_id: str) -> bool:
        """Resolve an operation whose artifact creation definitely failed.

        Best-effort by contract: if this transition cannot be persisted, the
        original artifact-creation error must still reach the user unchanged and
        the operation simply stays unresolved for a later reconciliation pass.
        """
        try:
            return self.repository.mark_abandoned(operation_id)
        except (sqlite3.Error, OSError):
            return False

    def pending_count(self) -> int:
        """`pending_audit_count`. Reads only — never reconciles, never mutates.

        Degrades to `0` when the ledger cannot be consulted at all, rather than
        propagating. This field is additive to an endpoint whose other values are
        filesystem-derived and still perfectly valid: letting an unreadable
        ledger raise would take the entire report-documents workspace down over a
        warning counter, which is a worse failure than the one it reports. The
        same tolerance already governs `reconcile`.

        The narrow exception list matters. Only "the ledger is unreachable"
        degrades; a programming error still surfaces normally.
        """
        try:
            return self.repository.count_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT)
        except (sqlite3.Error, OSError):
            return 0

    # ----------------------------------------------------------------- verify

    def verify(self, operation: ArtifactAuditOperation) -> ReportDocumentVerification:
        """Classify one operation's artifact pair without ever changing it.

        Three outcomes, and the distinction between the last two is the whole
        safety argument:

        `valid`
            Every accepted condition holds; the pair may be audited.
        `definitely_absent`
            Both names are safe and neither file exists, so creation failed and
            its compensation succeeded. The operation may be abandoned.
        `ambiguous`
            Anything else — one file present, malformed metadata, a mismatch, an
            unsafe name. Never audited *and* never deleted; left unresolved,
            counted, and surfaced as a pending warning rather than guessed at.

        Nothing here rerenders the document, compares it with current report
        data, or writes to either file. Historical documents are immutable.
        """
        primary_name = operation.primary_filename
        companion_name = operation.companion_filename

        # 1 and 2 — safe-name validation, repeated on read, not trusted from write.
        if not is_safe_artifact_filename(primary_name):
            return ReportDocumentVerification("ambiguous", "unsafe-primary-filename")
        if not is_safe_artifact_filename(companion_name):
            return ReportDocumentVerification("ambiguous", "unsafe-companion-filename")

        # 3 — both must resolve inside the configured report-documents directory.
        primary_path = self._resolved_path(primary_name)
        companion_path = self._resolved_path(companion_name)
        if primary_path is None or companion_path is None:
            return ReportDocumentVerification("ambiguous", "path-outside-documents-directory")

        # 4 — existence. Neither present is the one state we can safely resolve.
        primary_exists = primary_path.exists()
        companion_exists = companion_path.exists()
        if not primary_exists and not companion_exists:
            return ReportDocumentVerification("definitely_absent", "pair-absent")
        if not primary_exists:
            return ReportDocumentVerification("ambiguous", "primary-missing")
        if not companion_exists:
            return ReportDocumentVerification("ambiguous", "companion-missing")

        # 5 — regular files only. A directory or symlink-to-directory sharing the
        # name is not the artifact this operation created.
        if not primary_path.is_file():
            return ReportDocumentVerification("ambiguous", "primary-not-regular-file")
        if not companion_path.is_file():
            return ReportDocumentVerification("ambiguous", "companion-not-regular-file")

        # 6 — the sidecar must still parse as the existing metadata model.
        try:
            raw = json.loads(companion_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ReportDocumentVerification("ambiguous", "metadata-unreadable")
        try:
            metadata = ReportDocumentMetadata.model_validate(raw)
        except Exception:
            return ReportDocumentVerification("ambiguous", "metadata-invalid")

        # 7 and 8 — the sidecar must describe this operation's own pair.
        if metadata.filename != primary_name:
            return ReportDocumentVerification("ambiguous", "metadata-filename-mismatch")
        if metadata.metadata_filename != companion_name:
            return ReportDocumentVerification("ambiguous", "metadata-companion-mismatch")

        # 9 and 10 — accepted document type and a supported generated format.
        if metadata.document_type != SUPPORTED_DOCUMENT_TYPE:
            return ReportDocumentVerification("ambiguous", "unexpected-document-type")
        extension = SUPPORTED_FORMAT_EXTENSIONS.get(metadata.format)
        if extension is None:
            return ReportDocumentVerification("ambiguous", "unsupported-format")

        # 11 and 12 — the generated filename contract: `<id><ext>` plus `<id>.json`.
        if primary_name != f"{metadata.id}{extension}":
            return ReportDocumentVerification("ambiguous", "primary-name-contract-mismatch")
        if companion_name != f"{metadata.id}{METADATA_EXTENSION}":
            return ReportDocumentVerification("ambiguous", "companion-name-contract-mismatch")

        # 13 — the recorded size must still match the bytes on disk.
        try:
            actual_size = primary_path.stat().st_size
        except OSError:
            return ReportDocumentVerification("ambiguous", "primary-unreadable")
        if metadata.size_bytes != actual_size:
            return ReportDocumentVerification("ambiguous", "size-mismatch")

        return ReportDocumentVerification("valid", "verified", metadata)

    def _resolved_path(self, name: str) -> Path | None:
        """Join one safe name onto the configured directory, or refuse.

        `is_safe_artifact_filename` has already rejected separators and `..`;
        this second, independent check catches whatever the filesystem itself
        does with the name — a symlink that leaves the directory, for instance.
        """
        try:
            root = self.documents_dir.resolve()
            candidate = (self.documents_dir / name).resolve(strict=False)
            candidate.relative_to(root)
        except (OSError, ValueError):
            return None
        return candidate

    # --------------------------------------------------------------- finalize

    def finalize(self, operation_id: str, *, reconciled_after_failure: bool) -> int | None:
        """Idempotently commit this operation's single AuditLog event.

        Returns the AuditLog row ID when the operation is audited — whether this
        call inserted it or found it already there — and `None` when it could
        not be, which the caller must treat as `pending`, never as a failure of
        the document itself.

        Verification happens *before* the write transaction opens. Parsing JSON
        and stat-ing files while holding a SQLite write lock would block every
        other writer for the duration of filesystem I/O, and the accepted
        decision requires that ordering explicitly.
        """
        try:
            operation = self.repository.get_operation(operation_id)
        except (sqlite3.Error, OSError):
            return None
        if operation is None:
            return None
        if operation.status == STATUS_AUDITED:
            return operation.audit_log_id
        if operation.status not in UNRESOLVED_STATUSES:
            return None

        verification = self.verify(operation)
        if not verification.is_valid:
            return None

        try:
            return self._commit_finalization(operation, verification, reconciled_after_failure)
        except (sqlite3.Error, OSError, RuntimeError):
            # The artifact stays exactly as it is. Only the secondary result
            # failed, so the operation is merely moved to `pending_audit` — and
            # that move happens on a fresh connection, after the failed
            # transaction has already been rolled back and closed.
            self._try_mark_pending(operation_id)
            return None

    def _commit_finalization(
        self,
        operation: ArtifactAuditOperation,
        verification: ReportDocumentVerification,
        reconciled_after_failure: bool,
    ) -> int | None:
        """The atomic half: one connection, one write-serialized transaction.

        `BEGIN IMMEDIATE` takes the write lock up front, so two concurrent
        finalizers are ordered rather than racing: the loser waits, re-reads the
        row it was going to audit, sees `audited`, and returns the existing ID
        without inserting anything.

        The re-read inside the transaction is not redundant with the one in
        `finalize`. That earlier read happened on a different connection and is
        already stale by the time the lock is held; only this one is serialized
        against other writers.
        """
        metadata = verification.metadata
        if metadata is None:
            return None
        with transaction(self.config, immediate=True) as connection:
            current = self.repository.get_operation(operation.operation_id, connection=connection)
            if current is None:
                return None
            if current.status == STATUS_AUDITED:
                return current.audit_log_id
            if current.status not in UNRESOLVED_STATUSES:
                return None
            audit_log_id = self.audit_repository.create_log(
                action=AUDIT_ACTION_REPORT_DOCUMENT_CREATED,
                entity_type=AUDIT_ENTITY_TYPE,
                entity_id=current.operation_id,
                summary=AUDIT_SUMMARY,
                actor_type=AUDIT_ACTOR_TYPE,
                metadata={
                    "operation_id": current.operation_id,
                    "document_type": metadata.document_type,
                    "format": metadata.format,
                    "reconciled_after_failure": bool(reconciled_after_failure),
                },
                connection=connection,
            )
            if not self.repository.mark_audited(current.operation_id, audit_log_id, connection=connection):
                # Nothing to update means the row moved under us. Raising leaves
                # the transaction to roll the insert back, so the event and the
                # ledger transition still commit together or not at all.
                raise RuntimeError("Ledger transition did not apply; rolling back the AuditLog insert.")
            return audit_log_id

    def _try_mark_pending(self, operation_id: str) -> None:
        try:
            self.repository.mark_pending_audit(operation_id)
        except (sqlite3.Error, OSError):
            # `prepared` is unresolved too, so the operation is still counted and
            # still reconciled later. Losing this transition costs nothing.
            pass

    # ------------------------------------------------------------- reconcile

    def reconcile(self) -> ReportDocumentReconciliationResult:
        """One bounded, deterministic pass over unresolved operations.

        Bounded in the literal sense: it reads the unresolved rows once, handles
        each exactly once, and returns. No loop, no retry, no scan of the
        documents directory — only the filenames the ledger itself recorded.
        An operation that cannot be resolved stays unresolved for the next of
        the two authorized triggers.

        This never raises. Both callers — application startup and the create
        path — must survive a reconciliation problem: startup must still serve
        the UI, and an older unresolved operation must never turn a brand-new
        document into a failure.
        """
        try:
            operations = self.repository.list_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT)
        except (sqlite3.Error, OSError):
            return ReportDocumentReconciliationResult(failed=1)

        examined = audited = abandoned = unresolved = failed = 0
        for operation in operations:
            examined += 1
            try:
                verification = self.verify(operation)
                if verification.outcome == "definitely_absent":
                    self.repository.mark_abandoned(operation.operation_id)
                    abandoned += 1
                elif verification.outcome == "valid":
                    if self.finalize(operation.operation_id, reconciled_after_failure=True) is None:
                        unresolved += 1
                    else:
                        audited += 1
                else:
                    self._try_mark_pending(operation.operation_id)
                    unresolved += 1
            except (sqlite3.Error, OSError, ValueError):
                failed += 1
        return ReportDocumentReconciliationResult(
            examined=examined, audited=audited, abandoned=abandoned, unresolved=unresolved, failed=failed
        )


def reconcile_report_documents(
    config: DatabaseConfig | None = None, documents_dir: Path | None = None
) -> ReportDocumentReconciliationResult:
    """Startup entry point: reconcile report documents after migrations.

    Imported lazily from `app.services.report_documents` so that this module
    stays free of an import cycle with the renderer it supports.
    """
    from app.services.report_documents import resolve_report_documents_dir

    resolved_config = config or get_database_config()
    resolved_dir = documents_dir or resolve_report_documents_dir(resolved_config)
    return ReportDocumentAuditService(resolved_dir, resolved_config).reconcile()
