"""Durable manual-backup AuditLog coverage: reserve, verify, finalize, reconcile.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
(CR-009), ``docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md``
(CR-004) and ``docs/backup-and-restore.md`` § "CR-009 manual-backup AuditLog
boundary".

This is the manual-backup third of the accepted rule already implemented for
report documents (B1) and JSON exports (B2), and it deliberately reuses that
ledger, those statuses, that finalizer shape and that three-way verification
outcome rather than growing a second architecture beside them:

- the fully written and verified backup is the **primary** result and is
  authoritative once it exists;
- the AuditLog event is a **secondary** result;
- a secondary failure never deletes the backup and never reports total failure;
- but it is never silently forgotten either — the operation stays unresolved, is
  counted, and is retried at exactly two bounded moments.

Those two moments are normal application startup (after migrations) and once
before the next manual backup. There is no background thread, timer, queue,
worker or unbounded retry here.

**A backup is not just another artifact.** A report document is Markdown and an
export is JSON, but a manual backup is a SQLite database — the same shape as the
live database, containing the same ledger and AuditLog tables. Two consequences
run through this module and neither exists for B1 or B2.

First, verification cannot stop at "this parses". A completely unrelated but
perfectly valid SQLite database sitting at the reserved path would pass every
structural check, and an *empty* file passes ``PRAGMA quick_check`` because an
empty file is a valid empty SQLite database. So the artifact must prove its own
identity: it must contain the very ledger row that reserved it.

Second, the accepted operation order puts the snapshot *after* the prepared
ledger row is committed. The backup therefore contains its own matching
operation in ``status = prepared`` with no ``backup.created`` event for itself.
That is intentional and is exactly what makes the artifact self-identifying — it
is proof the snapshot was taken by this operation and not by anything else. The
completed backup is never rewritten afterwards to tidy that row up.
"""

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Final, Literal

from app.db.config import DatabaseConfig, get_database_config
from app.db.transactions import transaction
from app.domain.artifact_audit_operations import (
    ARTIFACT_KIND_MANUAL_BACKUP,
    AUDIT_ACTION_BACKUP_CREATED,
    ArtifactAuditOperationError,
    STATUS_AUDITED,
    STATUS_PREPARED,
    UNRESOLVED_STATUSES,
    is_safe_artifact_filename,
    new_operation_id,
)
from app.repositories.artifact_audit_operations import (
    ArtifactAuditOperation,
    ArtifactAuditOperationRepository,
    TABLE_NAME as LEDGER_TABLE,
)
from app.repositories.audit import AuditLogRepository
from app.services.backup import (
    SQLITE_BACKUP_SUFFIXES,
    parse_generated_backup_filename,
    resolve_backup_dir,
)

AUDIT_ENTITY_TYPE: Final = "backup_file"
AUDIT_ACTOR_TYPE: Final = "user"
AUDIT_SUMMARY: Final = "Backup created"

# The migration that creates the ledger table. A valid snapshot must contain it,
# because a snapshot taken after the prepared row was committed necessarily
# contains the table that row lives in.
LEDGER_MIGRATION_ID: Final = "0020_artifact_audit_operations"
MIGRATION_TABLE: Final = "schema_migrations"

# `docs/backup-and-restore.md`. The user is told the two bounded retry moments
# and nothing technical: no filename, no path, no operation ID, no SQLite
# wording.
PENDING_AUDIT_MESSAGE: Final = (
    "Резервная копия создана, но запись в журнал действий пока не добавлена. "
    "Приложение повторит попытку при следующем запуске или перед созданием следующей резервной копии."
)

TRACKING_UNAVAILABLE_CODE: Final = "artifact_audit_tracking_unavailable"
TRACKING_UNAVAILABLE_MESSAGE: Final = (
    "Не удалось безопасно подготовить создание резервной копии. Резервная копия не создана."
)
TRACKING_UNAVAILABLE_NEXT_ACTION: Final = (
    "Повторите создание резервной копии. Если ошибка повторяется, перезапустите приложение."
)

VerificationOutcome = Literal["valid", "definitely_absent", "ambiguous"]


class BackupAuditTrackingUnavailableError(RuntimeError):
    """Raised when manual-backup audit tracking cannot be durably prepared.

    This is the *only* failure that prevents the backup from being created at
    all. It happens strictly before anything is written, so nothing needs to be
    compensated when it is raised.
    """

    code = TRACKING_UNAVAILABLE_CODE
    message = TRACKING_UNAVAILABLE_MESSAGE
    next_action = TRACKING_UNAVAILABLE_NEXT_ACTION


@dataclass(frozen=True)
class BackupVerification:
    outcome: VerificationOutcome
    reason: str

    @property
    def is_valid(self) -> bool:
        return self.outcome == "valid"


@dataclass(frozen=True)
class BackupReconciliationResult:
    """What one bounded reconciliation pass did. Internal; never user-facing."""

    examined: int = 0
    audited: int = 0
    abandoned: int = 0
    unresolved: int = 0
    failed: int = 0


class BackupAuditService:
    """The single owner of manual-backup artifact-audit operations.

    One instance covers all three entry points — immediate finalization after a
    create, startup reconciliation and pre-create reconciliation — because all
    three must use the *same* verifier and the *same* finalizer. Two
    near-identical code paths would be exactly how a duplicate event or an
    inconsistent verification rule gets in.
    """

    def __init__(self, backup_dir: Path, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()
        self.backup_dir = backup_dir
        self.repository = ArtifactAuditOperationRepository(self.config)
        self.audit_repository = AuditLogRepository(self.config)

    # ---------------------------------------------------------------- reserve

    def is_identity_active(self, primary_filename: str) -> bool:
        """Whether an unresolved operation already owns this backup filename."""
        return self.repository.has_active_identity(
            ARTIFACT_KIND_MANUAL_BACKUP, primary_filename=primary_filename
        )

    def prepare_operation(self, *, primary_filename: str) -> str:
        """Commit one `prepared` ledger row and return its operation ID.

        Called before the snapshot is taken — and therefore this row is part of
        the state the snapshot captures. If it raises, no backup exists and none
        will: the caller maps the error to the accepted HTTP 500 contract, which
        is the one case where a create is refused outright.
        """
        try:
            operation_id = new_operation_id()
            self.repository.prepare_operation(
                operation_id=operation_id,
                artifact_kind=ARTIFACT_KIND_MANUAL_BACKUP,
                primary_filename=primary_filename,
                companion_filename=None,
                audit_action=AUDIT_ACTION_BACKUP_CREATED,
            )
            return operation_id
        except (ArtifactAuditOperationError, sqlite3.Error, OSError) as failure:
            raise BackupAuditTrackingUnavailableError(TRACKING_UNAVAILABLE_MESSAGE) from failure

    def pending_count(self) -> int:
        """`pending_audit_count`. Reads only — never reconciles, never mutates.

        Deliberately does **not** degrade to `0` on failure. `0` is a factual
        claim — "no backup is awaiting a Journal entry" — and the frontend acts
        on it by clearing a standing warning. Returning it when the ledger could
        not actually be read would turn "I don't know" into "definitely
        nothing", which is precisely the silent audit gap CR-009 prevents.

        A read failure is therefore raised and surfaced through the existing safe
        API error boundary, which returns fixed Russian text and no SQLite
        detail.
        """
        return self.repository.count_unresolved(ARTIFACT_KIND_MANUAL_BACKUP)

    # ----------------------------------------------------------------- verify

    def verify(self, operation: ArtifactAuditOperation) -> BackupVerification:
        """Classify one operation's backup file without ever changing it.

        Three outcomes, and the distinction between the last two is the whole
        safety argument:

        `valid`
            Every accepted condition holds; the backup may be audited.
        `definitely_absent`
            The name is safe and the exact file does not exist, so creation
            failed. The operation may be abandoned.
        `ambiguous`
            Anything else — an unsafe name, a name outside the grammar, a
            directory, an escaping symlink, an empty or unreadable file, a
            database missing the ledger, or one whose embedded operation does not
            match. Never audited *and* never deleted; left unresolved, counted,
            and surfaced as a pending warning rather than guessed at.

        Nothing here writes to the backup, migrates it, or compares its historical
        business rows with the current live database. A snapshot is a snapshot: it
        is *supposed* to disagree with a database that has moved on since.
        """
        name = operation.primary_filename

        # 1 — safe-name validation, repeated on read, not trusted from write.
        if not is_safe_artifact_filename(name):
            return BackupVerification("ambiguous", "unsafe-filename")

        # 2 — the complete accepted filename grammar, proved by round-tripping the
        # parsed fields back through the one generator. This also settles the
        # accepted SQLite suffix; the explicit re-check below is belt and braces
        # against a future grammar change loosening it.
        generated = parse_generated_backup_filename(name)
        if generated is None:
            return BackupVerification("ambiguous", "filename-grammar-mismatch")
        if generated.extension not in SQLITE_BACKUP_SUFFIXES:
            return BackupVerification("ambiguous", "unexpected-backup-extension")

        # 3 — the name must resolve inside the configured backup directory. This
        # also rejects a symlink that leaves it, which the name check cannot see.
        path = self._resolved_path(name)
        if path is None:
            return BackupVerification("ambiguous", "path-outside-backup-directory")

        # 4 — existence. Absent is the one state that can be resolved safely.
        if not path.exists():
            return BackupVerification("definitely_absent", "backup-absent")
        # 5 — a regular file only. A directory sharing the name is not the
        # artifact this operation created.
        if not path.is_file():
            return BackupVerification("ambiguous", "backup-not-regular-file")

        # 6 — a zero-byte file is a *valid empty SQLite database* and passes
        # `quick_check`. CR-004 produced exactly that from an aborted copy, so the
        # size check has to come before any structural one means anything.
        try:
            if path.stat().st_size == 0:
                return BackupVerification("ambiguous", "backup-empty")
        except OSError:
            return BackupVerification("ambiguous", "backup-unreadable")

        return self._verify_contents(path, operation)

    def _verify_contents(self, path: Path, operation: ArtifactAuditOperation) -> BackupVerification:
        """The read-only database half of verification.

        Opened read-only through a URI so verification cannot create, migrate or
        modify the artifact even by accident, and `immutable=1` is deliberately
        *not* used: a truncated or partially written file must be allowed to fail
        honestly rather than be read through a promise it does not keep.
        """
        try:
            connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5.0)
        except sqlite3.Error:
            return BackupVerification("ambiguous", "backup-not-openable")
        try:
            # 7 — structural health. `quick_check` is necessary and nowhere near
            # sufficient: CR-004 produced `ok` from a file missing every committed
            # row it should have had.
            if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                return BackupVerification("ambiguous", "quick-check-failed")

            # 8 — it is an application database, migrated at least as far as the
            # ledger. A snapshot taken after the prepared row was committed cannot
            # be older than the migration that created the table it lives in.
            if not _table_exists(connection, MIGRATION_TABLE):
                return BackupVerification("ambiguous", "schema-migrations-missing")
            if not _table_exists(connection, LEDGER_TABLE):
                return BackupVerification("ambiguous", "ledger-table-missing")
            applied = connection.execute(
                f"SELECT 1 FROM {MIGRATION_TABLE} WHERE migration_id = ?", (LEDGER_MIGRATION_ID,)
            ).fetchone()
            if applied is None:
                return BackupVerification("ambiguous", "ledger-migration-missing")

            # 9 — the artifact identifies itself. This is what an unrelated but
            # perfectly valid SQLite database placed at the exact path cannot do,
            # and it is the reason `quick_check = ok` alone can never authorize an
            # audit event.
            row = connection.execute(
                f"""
                SELECT artifact_kind, primary_filename, companion_filename, status,
                       audit_action, audit_log_id
                FROM {LEDGER_TABLE} WHERE operation_id = ?
                """,
                (operation.operation_id,),
            ).fetchone()
        except sqlite3.Error:
            return BackupVerification("ambiguous", "backup-unreadable")
        finally:
            connection.close()

        if row is None:
            return BackupVerification("ambiguous", "embedded-operation-missing")
        kind, primary, companion, status, action, audit_log_id = row
        if kind != ARTIFACT_KIND_MANUAL_BACKUP:
            return BackupVerification("ambiguous", "embedded-artifact-kind-mismatch")
        if action != AUDIT_ACTION_BACKUP_CREATED:
            return BackupVerification("ambiguous", "embedded-audit-action-mismatch")
        if primary != operation.primary_filename:
            return BackupVerification("ambiguous", "embedded-filename-mismatch")
        if companion is not None:
            return BackupVerification("ambiguous", "embedded-companion-filename-present")
        # `prepared` exactly, not merely "unresolved". The snapshot was taken
        # between the prepared commit and finalization, so `prepared` is the only
        # state it can honestly have captured. `pending_audit` or `audited` inside
        # the artifact would mean the file was written at some other point in the
        # sequence than the accepted one, which is precisely what this check is
        # here to notice.
        if status != STATUS_PREPARED:
            return BackupVerification("ambiguous", "embedded-status-not-prepared")
        if audit_log_id is not None:
            return BackupVerification("ambiguous", "embedded-audit-log-id-present")

        return BackupVerification("valid", "verified")

    def _resolved_path(self, name: str) -> Path | None:
        """Join one safe name onto the configured directory, or refuse.

        `is_safe_artifact_filename` has already rejected separators and `..`;
        this second, independent check catches whatever the filesystem itself
        does with the name — a symlink that leaves the directory, for instance.
        """
        try:
            root = self.backup_dir.resolve()
            candidate = (self.backup_dir / name).resolve(strict=False)
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
        the backup itself.

        Verification happens *before* the write transaction opens. Reading and
        `quick_check`-ing a whole database file while holding a SQLite write lock
        would block every other writer for the duration of that I/O.
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
            # `finalize` runs on the create path *after* the backup is on disk and
            # is deliberately not wrapped in a `try` there. An unexpected error
            # escaping the verifier would therefore turn a successfully created
            # backup into an HTTP 500 — the false total failure CR-009 exists to
            # prevent. Degrading to `pending` keeps the backup, the count and the
            # warning, so a defect stays visible rather than destroying a result.
            self._try_mark_pending(operation_id)
            return None
        if not verification.is_valid:
            return None

        try:
            return self._commit_finalization(operation, reconciled_after_failure)
        except (sqlite3.Error, OSError, RuntimeError):
            # The backup stays exactly as it is. Only the secondary result
            # failed, so the operation is merely moved to `pending_audit` — and
            # that move happens on a fresh connection, after the failed
            # transaction has already been rolled back and closed.
            #
            # `RuntimeError` is this module's own rollback signal from
            # `_commit_finalization`. Keeping the catch here is deliberate: by
            # this point the backup exists, and the accepted contract requires
            # HTTP 201 with `audit_status: pending`, never a total failure.
            self._try_mark_pending(operation_id)
            return None

    def _commit_finalization(
        self, operation: ArtifactAuditOperation, reconciled_after_failure: bool
    ) -> int | None:
        """The atomic half: one connection, one write-serialized transaction.

        `BEGIN IMMEDIATE` takes the write lock up front, so two concurrent
        finalizers are ordered rather than racing: the loser waits, re-reads the
        row it was going to audit, sees `audited`, and returns the existing ID
        without inserting anything.

        The re-read inside the transaction is not redundant with the one in
        `finalize`. That earlier read happened on a different connection and is
        already stale by the time the lock is held.

        The metadata is exactly the two keys ADR 0013 allows for
        `backup.created`. No filename, path, reason, database size, table name,
        row count or migration list is ever carried here.
        """
        with transaction(self.config, immediate=True) as connection:
            current = self.repository.get_operation(operation.operation_id, connection=connection)
            if current is None:
                return None
            if current.status == STATUS_AUDITED:
                return current.audit_log_id
            if current.status not in UNRESOLVED_STATUSES:
                return None
            audit_log_id = self.audit_repository.create_log(
                action=AUDIT_ACTION_BACKUP_CREATED,
                entity_type=AUDIT_ENTITY_TYPE,
                entity_id=current.operation_id,
                summary=AUDIT_SUMMARY,
                actor_type=AUDIT_ACTOR_TYPE,
                metadata={
                    "operation_id": current.operation_id,
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

    def reconcile(self) -> BackupReconciliationResult:
        """One bounded, deterministic pass over unresolved backup operations.

        Bounded in the literal sense: it reads the unresolved rows once, handles
        each exactly once, and returns. No loop, no retry, and no scan of the
        backup directory — only the filenames the ledger itself recorded, so a
        legacy backup that predates the ledger, and every automatic
        `before_migration` backup, is never discovered, audited or touched.

        This never raises. Both callers — application startup and the create
        path — must survive a reconciliation problem: startup must still serve
        the UI, and an older unresolved operation must never turn a brand-new
        backup into a failure.
        """
        try:
            operations = self.repository.list_unresolved(ARTIFACT_KIND_MANUAL_BACKUP)
        except (sqlite3.Error, OSError):
            return BackupReconciliationResult(failed=1)

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
        return BackupReconciliationResult(
            examined=examined, audited=audited, abandoned=abandoned, unresolved=unresolved, failed=failed
        )


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        is not None
    )


def reconcile_manual_backups(
    config: DatabaseConfig | None = None, backup_dir: Path | None = None
) -> BackupReconciliationResult:
    """Startup entry point: reconcile manual backups after migrations.

    `resolve_backup_dir` only computes a path, so a workspace that has never
    created a manual backup reconciles an empty ledger without side effects. The
    automatic `before_migration` backup is deliberately outside this: it runs
    before migrations, is not a user action, and has no ledger row to reconcile.
    """
    resolved_config = config or get_database_config()
    resolved_dir = backup_dir if backup_dir is not None else resolve_backup_dir(resolved_config)
    return BackupAuditService(resolved_dir, resolved_config).reconcile()
