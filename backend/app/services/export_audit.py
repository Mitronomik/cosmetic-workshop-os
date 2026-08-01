"""Durable JSON-export AuditLog coverage: reserve, verify, finalize, reconcile.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
(CR-009), ``docs/decisions/0014-json-export-create-confirmation-semantics.md``
(CR-006) and ``docs/export.md`` § "CR-009 JSON-export AuditLog boundary".

This is the JSON-export half of the same accepted rule ``C3-II-B1`` implemented
for report documents, and it deliberately reuses that slice's ledger, statuses,
finalizer shape and three-way verification outcome rather than growing a second
architecture beside it:

- the fully written and verified export file is the **primary** result and is
  authoritative once it exists;
- the AuditLog event is a **secondary** result;
- a secondary failure never deletes the export and never reports total failure;
- but it is never silently forgotten either — the operation stays unresolved, is
  counted, and is retried at exactly two bounded moments.

Those two moments are normal application startup (after migrations) and once
before the next export is created. There is no background thread, timer, queue,
worker or unbounded retry here.

An export is **one** file, unlike the report-document pair, so this module's
ledger rows carry a `primary_filename` and no `companion_filename`.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Final, Literal

from app.db.config import DatabaseConfig, get_database_config
from app.db.transactions import transaction
from app.domain.artifact_audit_operations import (
    ARTIFACT_KIND_JSON_EXPORT,
    AUDIT_ACTION_EXPORT_CREATED,
    ArtifactAuditOperationError,
    STATUS_AUDITED,
    UNRESOLVED_STATUSES,
    is_safe_artifact_filename,
    new_operation_id,
)
from app.repositories.artifact_audit_operations import ArtifactAuditOperation, ArtifactAuditOperationRepository
from app.repositories.audit import AuditLogRepository
from app.services.export import (
    EXPORT_FILENAME_MARKER,
    EXPORT_FILE_SUFFIX,
    EXPORT_PAYLOAD_KEYS,
    EXPORT_SOURCE,
    SUPPORTED_EXPORT_SCHEMA_VERSIONS,
    parse_export_reason,
    resolve_export_dir,
)

AUDIT_ENTITY_TYPE: Final = "export_file"
AUDIT_ACTOR_TYPE: Final = "user"
AUDIT_SUMMARY: Final = "JSON export created"

# `docs/export.md`. The user is told the two bounded retry moments and nothing
# technical: no filename, no path, no operation ID, no SQLite wording.
PENDING_AUDIT_MESSAGE: Final = (
    "Экспорт создан, но запись в журнал действий пока не добавлена. "
    "Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта."
)

TRACKING_UNAVAILABLE_CODE: Final = "artifact_audit_tracking_unavailable"
TRACKING_UNAVAILABLE_MESSAGE: Final = "Не удалось безопасно подготовить создание экспорта. Экспорт не создан."
TRACKING_UNAVAILABLE_NEXT_ACTION: Final = (
    "Повторите создание экспорта. Если ошибка повторяется, перезапустите приложение."
)

VerificationOutcome = Literal["valid", "definitely_absent", "ambiguous"]


class ExportAuditTrackingUnavailableError(RuntimeError):
    """Raised when JSON-export audit tracking cannot be durably prepared.

    This is the *only* failure that prevents the export from being created at
    all. It happens strictly before the file is written, so nothing needs to be
    compensated when it is raised.
    """

    code = TRACKING_UNAVAILABLE_CODE
    message = TRACKING_UNAVAILABLE_MESSAGE
    next_action = TRACKING_UNAVAILABLE_NEXT_ACTION


@dataclass(frozen=True)
class ExportVerification:
    outcome: VerificationOutcome
    reason: str
    export_schema_version: int | None = None

    @property
    def is_valid(self) -> bool:
        return self.outcome == "valid"


@dataclass(frozen=True)
class ExportReconciliationResult:
    """What one bounded reconciliation pass did. Internal; never user-facing."""

    examined: int = 0
    audited: int = 0
    abandoned: int = 0
    unresolved: int = 0
    failed: int = 0


class ExportAuditService:
    """The single owner of JSON-export artifact-audit operations.

    One instance covers all three entry points — immediate finalization after a
    create, startup reconciliation and pre-create reconciliation — because all
    three must use the *same* verifier and the *same* finalizer. Two
    near-identical code paths would be exactly how a duplicate event or an
    inconsistent verification rule gets in.
    """

    def __init__(self, export_dir: Path, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()
        self.export_dir = export_dir
        self.repository = ArtifactAuditOperationRepository(self.config)
        self.audit_repository = AuditLogRepository(self.config)

    # ---------------------------------------------------------------- reserve

    def is_identity_active(self, primary_filename: str) -> bool:
        """Whether an unresolved operation already owns this export filename."""
        return self.repository.has_active_identity(
            ARTIFACT_KIND_JSON_EXPORT, primary_filename=primary_filename
        )

    def prepare_operation(self, *, primary_filename: str) -> str:
        """Commit one `prepared` ledger row and return its operation ID.

        Called before the export file is written. If it raises, no export exists
        and none will: the caller maps the error to the accepted HTTP 500
        contract, which is the one case where a create is refused outright.
        """
        try:
            operation_id = new_operation_id()
            self.repository.prepare_operation(
                operation_id=operation_id,
                artifact_kind=ARTIFACT_KIND_JSON_EXPORT,
                primary_filename=primary_filename,
                companion_filename=None,
                audit_action=AUDIT_ACTION_EXPORT_CREATED,
            )
            return operation_id
        except (ArtifactAuditOperationError, sqlite3.Error, OSError) as failure:
            raise ExportAuditTrackingUnavailableError(TRACKING_UNAVAILABLE_MESSAGE) from failure

    def abandon_operation(self, operation_id: str) -> bool:
        """Resolve an operation whose export creation definitely failed.

        Best-effort by contract: if this transition cannot be persisted, the
        original export-creation error must still reach the user unchanged and
        the operation simply stays unresolved for a later reconciliation pass.
        """
        try:
            return self.repository.mark_abandoned(operation_id)
        except (sqlite3.Error, OSError):
            return False

    def pending_count(self) -> int:
        """`pending_audit_count`. Reads only — never reconciles, never mutates.

        Deliberately does **not** degrade to `0` on failure. `0` is a factual
        claim — "no export is awaiting a Journal entry" — and the frontend acts
        on it by clearing a standing warning. Returning it when the ledger could
        not actually be read would turn "I don't know" into "definitely
        nothing", which is precisely the silent audit gap CR-009 prevents.

        A read failure is therefore raised and surfaced through the existing safe
        API error boundary, which returns fixed Russian text and no SQLite
        detail.
        """
        return self.repository.count_unresolved(ARTIFACT_KIND_JSON_EXPORT)

    # ----------------------------------------------------------------- verify

    def verify(self, operation: ArtifactAuditOperation) -> ExportVerification:
        """Classify one operation's export file without ever changing it.

        Three outcomes, and the distinction between the last two is the whole
        safety argument:

        `valid`
            Every accepted condition holds; the export may be audited.
        `definitely_absent`
            The name is safe and the exact file does not exist, so creation
            failed. The operation may be abandoned.
        `ambiguous`
            Anything else — malformed JSON, an unsupported schema version, a
            mismatched manifest, an unsafe name, a directory or an escaping
            symlink. Never audited *and* never deleted; left unresolved,
            counted, and surfaced as a pending warning rather than guessed at.

        Nothing here rewrites the export, and nothing compares the historical
        exported data with the current database. A snapshot is a snapshot: it is
        *supposed* to disagree with a database that has moved on since.
        """
        name = operation.primary_filename

        # 1 — safe-name validation, repeated on read, not trusted from write.
        if not is_safe_artifact_filename(name):
            return ExportVerification("ambiguous", "unsafe-filename")

        # 2 — the name must resolve inside the configured export directory. This
        # also rejects a symlink that leaves it, which the name check cannot see.
        path = self._resolved_path(name)
        if path is None:
            return ExportVerification("ambiguous", "path-outside-export-directory")

        # 6 and 7 — the accepted filename grammar, and a reason that parses.
        if not name.endswith(EXPORT_FILE_SUFFIX) or EXPORT_FILENAME_MARKER not in name:
            return ExportVerification("ambiguous", "filename-grammar-mismatch")
        canonical_reason = parse_export_reason(Path(name))
        if not canonical_reason:
            return ExportVerification("ambiguous", "filename-reason-unparsable")
        # 8 — the uniqueness suffix is a filename mechanism, never a reason. A
        # canonical segment is never digits-only, so a parsed reason that is
        # would mean the suffix leaked into it.
        if canonical_reason.isdigit():
            return ExportVerification("ambiguous", "uniqueness-suffix-in-reason")

        # 3 — existence. Absent is the one state that can be resolved safely.
        if not path.exists():
            return ExportVerification("definitely_absent", "export-absent")
        # 4 — a regular file only. A directory sharing the name is not the
        # artifact this operation created.
        if not path.is_file():
            return ExportVerification("ambiguous", "export-not-regular-file")

        # 9 — the export must still parse as JSON.
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ExportVerification("ambiguous", "export-unreadable")
        if not isinstance(payload, dict):
            return ExportVerification("ambiguous", "payload-not-object")

        # 10 — exactly the existing top-level contract: `manifest` and `data`.
        if set(payload) != EXPORT_PAYLOAD_KEYS:
            return ExportVerification("ambiguous", "unexpected-top-level-keys")
        manifest = payload["manifest"]
        data = payload["data"]
        if not isinstance(manifest, dict) or not isinstance(data, dict):
            return ExportVerification("ambiguous", "unexpected-top-level-shape")

        # 11 — a supported export schema version, compared as an integer so a
        # boolean or numeric string cannot pass as one.
        schema_version = manifest.get("export_schema_version")
        if not isinstance(schema_version, int) or isinstance(schema_version, bool):
            return ExportVerification("ambiguous", "schema-version-missing")
        if schema_version not in SUPPORTED_EXPORT_SCHEMA_VERSIONS:
            return ExportVerification("ambiguous", "unsupported-schema-version")

        # 12 — this application wrote it.
        if manifest.get("source") != EXPORT_SOURCE:
            return ExportVerification("ambiguous", "unexpected-source")

        # 13 — `manifest.reason` is the *human* reason and is deliberately not
        # required to equal the canonical filename slug. CR-005 keeps the two
        # representations distinct on purpose; requiring them to match here
        # would quietly reopen that decision.
        if not isinstance(manifest.get("reason"), str):
            return ExportVerification("ambiguous", "manifest-reason-missing")

        # 14 — the manifest's own table counts must agree with the data it ships.
        if not _table_counts_agree(manifest.get("tables"), data):
            return ExportVerification("ambiguous", "table-counts-mismatch")

        return ExportVerification("valid", "verified", schema_version)

    def _resolved_path(self, name: str) -> Path | None:
        """Join one safe name onto the configured directory, or refuse.

        `is_safe_artifact_filename` has already rejected separators and `..`;
        this second, independent check catches whatever the filesystem itself
        does with the name — a symlink that leaves the directory, for instance.
        """
        try:
            root = self.export_dir.resolve()
            candidate = (self.export_dir / name).resolve(strict=False)
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
        the export itself.

        Verification happens *before* the write transaction opens. Parsing a
        whole export file while holding a SQLite write lock would block every
        other writer for the duration of that filesystem I/O.
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

        try:
            verification = self.verify(operation)
        except Exception:
            # `finalize` runs on the create path *after* the export is on disk
            # and is deliberately not wrapped in a `try` there. An unexpected
            # error escaping the verifier would therefore turn a successfully
            # created export into an HTTP 500 — the false total failure CR-009
            # exists to prevent. Degrading to `pending` keeps the export, the
            # count and the warning, so a defect stays visible rather than
            # destroying a result.
            self._try_mark_pending(operation_id)
            return None
        if not verification.is_valid:
            return None

        try:
            return self._commit_finalization(operation, verification, reconciled_after_failure)
        except (sqlite3.Error, OSError, RuntimeError):
            # The export stays exactly as it is. Only the secondary result
            # failed, so the operation is merely moved to `pending_audit` — and
            # that move happens on a fresh connection, after the failed
            # transaction has already been rolled back and closed.
            #
            # `RuntimeError` is this module's own rollback signal from
            # `_commit_finalization`. Keeping the catch here is deliberate: by
            # this point the export exists, and the accepted contract requires
            # HTTP 201 with `audit_status: pending`, never a total failure.
            self._try_mark_pending(operation_id)
            return None

    def _commit_finalization(
        self,
        operation: ArtifactAuditOperation,
        verification: ExportVerification,
        reconciled_after_failure: bool,
    ) -> int | None:
        """The atomic half: one connection, one write-serialized transaction.

        `BEGIN IMMEDIATE` takes the write lock up front, so two concurrent
        finalizers are ordered rather than racing: the loser waits, re-reads the
        row it was going to audit, sees `audited`, and returns the existing ID
        without inserting anything.

        The re-read inside the transaction is not redundant with the one in
        `finalize`. That earlier read happened on a different connection and is
        already stale by the time the lock is held.

        The metadata is exactly the three keys ADR 0013 allows for
        `export.created`. No filename, path, reason, manifest, entity count or
        exported value is ever carried here.
        """
        if verification.export_schema_version is None:
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
                action=AUDIT_ACTION_EXPORT_CREATED,
                entity_type=AUDIT_ENTITY_TYPE,
                entity_id=current.operation_id,
                summary=AUDIT_SUMMARY,
                actor_type=AUDIT_ACTOR_TYPE,
                metadata={
                    "operation_id": current.operation_id,
                    "export_schema_version": verification.export_schema_version,
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

    def reconcile(self) -> ExportReconciliationResult:
        """One bounded, deterministic pass over unresolved export operations.

        Bounded in the literal sense: it reads the unresolved rows once, handles
        each exactly once, and returns. No loop, no retry, and no scan of the
        export directory — only the filenames the ledger itself recorded, so a
        legacy export that predates the ledger is never discovered, audited or
        touched.

        This never raises. Both callers — application startup and the create
        path — must survive a reconciliation problem: startup must still serve
        the UI, and an older unresolved operation must never turn a brand-new
        export into a failure.
        """
        try:
            operations = self.repository.list_unresolved(ARTIFACT_KIND_JSON_EXPORT)
        except (sqlite3.Error, OSError):
            return ExportReconciliationResult(failed=1)

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
                # One broken operation must not stop the others, and must not
                # stop startup.
                failed += 1
        return ExportReconciliationResult(
            examined=examined, audited=audited, abandoned=abandoned, unresolved=unresolved, failed=failed
        )


def _table_counts_agree(tables: Any, data: dict[str, Any]) -> bool:
    """Whether `manifest.tables` describes exactly the exported `data`.

    Both directions matter. A count that is too low would hide rows the export
    actually carries; a table named in the manifest but absent from `data` would
    promise rows that are not there.
    """
    if not isinstance(tables, dict):
        return False
    if set(tables) != set(data):
        return False
    for table_name, count in tables.items():
        rows = data.get(table_name)
        if not isinstance(count, int) or isinstance(count, bool) or not isinstance(rows, list):
            return False
        if count != len(rows):
            return False
    return True


def reconcile_json_exports(
    config: DatabaseConfig | None = None, export_dir: Path | None = None
) -> ExportReconciliationResult:
    """Startup entry point: reconcile JSON exports after migrations.

    `resolve_export_dir` only computes a path; it creates no directory, so a
    workspace that has never exported anything reconciles an empty ledger
    without side effects.
    """
    resolved_config = config or get_database_config()
    resolved_dir = export_dir or resolve_export_dir(resolved_config)
    return ExportAuditService(resolved_dir, resolved_config).reconcile()
