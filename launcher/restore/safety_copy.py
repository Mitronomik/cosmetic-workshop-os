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

**Verification reuses the Restore candidate contract, not
`BackupAuditService.verify`.** That method verifies an artifact *against a CR-009
ledger operation embedded in it*, and this backup has no ledger row by design:
the safety copy is launcher recovery infrastructure, not a user action. Reusing
it would either fail every time or require writing the ledger row § 12 forbids.

So verification calls `validate_workspace_snapshot` — the same read-only checker
the staged candidate passes through. A safety copy verified more weakly than a
candidate would be a recovery point that might not be one, and it is the artifact
the entire destructive boundary rests on. It therefore has to prove the same
things: regular non-symlink file, non-empty, read-only open, structural check, a
known ordered migration prefix, recognizable workspace identity, the required
tables for that prefix, and no external sidecar dependency.

Explicitly **not** created for this backup: an `artifact_audit_operations` row, a
`backup.created` AuditLog event, or any Restore AuditLog event.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SAFETY_COPY_REASON = "before_restore"


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

    Read-only throughout, and held to the **same** contract as a Restore
    candidate: `quick_check` alone never authorizes anything here either, and a
    copy that carries a migration history the file itself does not back up is not
    a recovery point.

    A safety copy that cannot be verified is treated as no safety copy at all,
    because its whole purpose is to be trustworthy at the one moment nothing else
    is.
    """
    from launcher.restore.validation import CandidateRejectedError, validate_workspace_snapshot

    try:
        validate_workspace_snapshot(Path(safety_copy_path))
    except CandidateRejectedError as exc:
        raise SafetyCopyError(
            f"The pre-restore safety copy did not verify: {exc.rejection}"
        ) from exc
