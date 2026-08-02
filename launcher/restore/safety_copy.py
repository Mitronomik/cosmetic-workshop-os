"""The mandatory `before_restore` safety copy of the current working database.

`CR-010` § 5. This is the one artifact that makes the destructive step
reversible, so it is created and **verified** before `replacement_intent`, and it
is never silently deleted afterwards — not after a successful Restore, not after
rollback, and least of all in `recovery_blocked`.

Two reuse decisions, both deliberate:

**The copy is taken by the accepted SQLite backup engine.** `backup_sqlite_database`
performs one single-step `sqlite3.Connection.backup`, which is a transactionally
consistent snapshot of committed state. `shutil.copy2` of a live main database
file is not a backup — `CR-004` measured it silently omitting every
committed-but-uncheckpointed WAL row while still returning `quick_check = ok` —
and it is not reintroduced here. No second backup implementation is created.

**Verification does not reuse `BackupAuditService.verify`.** That method verifies
an artifact *against a CR-009 ledger operation embedded in it*, and this backup
has no ledger row by design: the safety copy is launcher recovery infrastructure,
not a user action. Reusing it would either fail every time or require writing the
ledger row § 12 forbids. The read-only checks that do apply — safe name, regular
file, non-empty, read-only open, `quick_check`, migration table present — are
applied here against the same reasoning, with the ledger-identity step replaced
by the lineage check the launcher already owns.

Explicitly **not** created for this backup: an `artifact_audit_operations` row, a
`backup.created` AuditLog event, or any Restore AuditLog event.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

SAFETY_COPY_REASON = "before_restore"

SQLITE_TIMEOUT_SECONDS = 5.0


class SafetyCopyError(RuntimeError):
    """Raised when the pre-restore safety copy cannot be created or verified.

    Always fatal to the attempt, and always fatal *before* `replacement_intent`.
    A Restore that cannot prove it has a recovery point does not enter the
    replacement boundary.
    """


@dataclass(frozen=True)
class SafetyCopy:
    """One verified `before_restore` artifact.

    `filename` is the safe relative name persisted in the durable operation
    record; `path` is resolved from the configured backup directory and is never
    persisted.
    """

    path: Path
    filename: str
    size_bytes: int


def create_verified_safety_copy(database_path: Path, backup_dir: Path) -> SafetyCopy:
    """Create and verify the mandatory safety copy of the exact working database.

    The working database must already exist: `C4-I` requires one, and § 10 of the
    task contract forbids weakening the safety gate or creating an empty fallback
    database to satisfy it. A missing working database is refused here, before
    `safety_copy_verified`.
    """
    from app.services.backup import BackupError, backup_sqlite_database

    resolved_database = Path(database_path)
    if not resolved_database.is_file():
        raise SafetyCopyError(
            "Restore requires an existing working database to copy before replacement."
        )

    try:
        result = backup_sqlite_database(
            source_path=resolved_database,
            backup_dir=Path(backup_dir),
            reason=SAFETY_COPY_REASON,
        )
    except BackupError as exc:
        raise SafetyCopyError(f"The pre-restore safety copy failed: {type(exc).__name__}") from exc

    verify_safety_copy(result.backup_path)
    return SafetyCopy(
        path=result.backup_path,
        filename=result.backup_path.name,
        size_bytes=result.size_bytes,
    )


def verify_safety_copy(safety_copy_path: Path) -> None:
    """Prove the safety copy is a usable workspace snapshot, without changing it.

    Read-only throughout. A safety copy that cannot be verified is treated as no
    safety copy at all, because its whole purpose is to be trustworthy at the one
    moment nothing else is.
    """
    path = Path(safety_copy_path)
    if path.is_symlink() or not path.is_file():
        raise SafetyCopyError("The pre-restore safety copy is not a regular file.")
    try:
        if path.stat().st_size == 0:
            # A zero-byte file is a valid empty SQLite database and passes
            # `quick_check`; CR-004 produced exactly that from an aborted copy.
            raise SafetyCopyError("The pre-restore safety copy is empty.")
    except OSError as exc:
        raise SafetyCopyError("The pre-restore safety copy could not be read.") from exc

    try:
        connection = sqlite3.connect(
            f"file:{path}?mode=ro", uri=True, timeout=SQLITE_TIMEOUT_SECONDS
        )
    except sqlite3.Error as exc:
        raise SafetyCopyError("The pre-restore safety copy could not be opened.") from exc
    try:
        from app.db.migration_lineage import inspect_migration_lineage

        row = connection.execute("PRAGMA quick_check").fetchone()
        if not row or row[0] != "ok":
            raise SafetyCopyError("The pre-restore safety copy failed its structural check.")
        # `quick_check` alone never authorizes anything here either. The safety
        # copy is a snapshot of a database this application just had open, so its
        # lineage must be a known prefix — if it is not, the copy is not of the
        # workspace it was supposed to protect.
        lineage = inspect_migration_lineage(connection)
        if not lineage.is_known_prefix:
            raise SafetyCopyError("The pre-restore safety copy is not a workshop database.")
    except sqlite3.Error as exc:
        raise SafetyCopyError("The pre-restore safety copy could not be verified.") from exc
    finally:
        connection.close()
