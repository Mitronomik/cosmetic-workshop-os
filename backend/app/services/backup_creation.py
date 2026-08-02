"""The audited manual-backup create operation, in its one required order.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
§ "Required operation sequence" and
``docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md``.

This module exists so that one place — not the route handler, and not the backup
engine — owns the exact order the accepted decisions require:

```text
normalize request
→ source precondition
→ bounded pre-create reconciliation
→ reserve the exact unique final backup path
→ commit one prepared ledger row
→ take the SQLite snapshot at that exact reserved path
→ verify the exact artifact
→ finalize AuditLog
```

The snapshot is deliberately taken *after* the prepared row is committed, so the
backup contains its own matching ledger row in `status = prepared` and no
`backup.created` event for itself. That is what makes the artifact
self-identifying, and it is never rewritten afterwards to tidy the row up.

It sits above ``backup`` (which writes) and ``backup_audit`` (which tracks and
verifies) and below the API, so neither of those two has to know about the other.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Literal

from app.db.config import DatabaseConfig, get_database_config
from app.services.backup import (
    BackupPaths,
    BackupResult,
    backup_sqlite_database,
    canonical_backup_reason,
    normalize_backup_reason,
    require_backupable_source,
    reserve_backup_path,
)
from app.services.backup_audit import (
    PENDING_AUDIT_MESSAGE,
    BackupArtifactUnverifiedError,
    BackupAuditService,
    BackupAuditTrackingUnavailableError,
)

AuditStatus = Literal["recorded", "pending"]


@dataclass(frozen=True)
class AuditedBackupResult:
    """One created backup plus the separate result of recording it in the Journal.

    `result` is the engine's exact `BackupResult` and is authoritative. The
    create response is built from it and never from a re-read of the backup
    directory: CR-004 measured that re-read turning a complete, verified backup
    into an HTTP 500.
    """

    result: BackupResult
    operation_id: str
    audit_status: AuditStatus

    @property
    def audit_message(self) -> str | None:
        return None if self.audit_status == "recorded" else PENDING_AUDIT_MESSAGE

    @property
    def canonical_reason(self) -> str | None:
        """The API `reason`, parsed from the exact final filename.

        Never `BackupResult.reason` — that is the human request reason, and
        returning it here would report a value the filename does not contain.
        """
        return canonical_backup_reason(self.result.backup_path)


def create_audited_backup(
    paths: BackupPaths,
    reason: str | None = None,
    *,
    config: DatabaseConfig | None = None,
) -> AuditedBackupResult:
    """Create one manual backup and record it in the Journal, in that order.

    The failure modes stay distinct on purpose, because they mean different
    things to the user and to recovery:

    - `BackupSourceMissingError` / `BackupError` — the snapshot itself could not
      be produced, so there is no artifact;
    - `BackupAuditTrackingUnavailableError` — the operation could not be durably
      tracked, so nothing was written at all;
    - `BackupArtifactUnverifiedError` — something exists at the reserved path but
      did not pass mandatory verification, so it is not a trustworthy backup;
    - a returned result with `audit_status="pending"` — the backup is **verified**
      and authoritative, and only its Journal entry is outstanding.
    """
    resolved_config = config or get_database_config()
    audit_service = BackupAuditService(paths.backup_dir, resolved_config)
    normalized_reason = normalize_backup_reason(reason)

    # The source precondition is checked here, before any ledger work, so that a
    # missing or unusable database still returns its existing `404`/`409` rather
    # than a tracking failure — and so that a create which cannot succeed leaves
    # behind no prepared operation and no new directory.
    require_backupable_source(paths.database_path)

    # One bounded pre-create reconciliation pass, before anything is reserved.
    # An older unresolved operation gets its chance here; it never blocks this
    # backup by itself, and this never loops.
    audit_service.reconcile()

    created_at = datetime.now(UTC)
    reserved_path = reserve_backup_path(
        paths.backup_dir,
        paths.database_path,
        created_at,
        normalized_reason,
        is_identity_active=lambda name: _is_identity_active(audit_service, name),
    )
    # The prepared row must be committed before the snapshot is taken. If it
    # cannot be, no backup is created at all — refusing is honest: an artifact we
    # could not have tracked would be an artifact we could never audit, and in
    # this slice it is also an artifact that could never prove it was ours.
    operation_id = audit_service.prepare_operation(primary_filename=reserved_path.name)

    # A creation failure deliberately leaves the committed `prepared` row alone
    # rather than abandoning it. This code cannot tell "never written" from
    # "written but not confirmed" — the engine's own post-copy `stat` can fail
    # after a complete snapshot is already on disk — and abandoning the second
    # would permanently orphan a real backup. Leaving the row unresolved lets
    # startup or pre-create reconciliation verify the exact reserved file later:
    # finalize it exactly once if it is valid, abandon it only once it is proven
    # absent.
    result = backup_sqlite_database(
        paths.database_path,
        paths.backup_dir,
        reason=normalized_reason,
        reserved_backup_path=reserved_path,
    )

    # Verification decides whether there is an authoritative result at all, and
    # the Journal entry is a separate, secondary question. Collapsing the two is
    # how an unverified artifact would be reported as a created backup with a
    # merely pending Journal entry.
    finalization = audit_service.finalize(operation_id, reconciled_after_failure=False)
    if not finalization.artifact_is_authoritative:
        # Something is at the reserved path, but this operation could not prove it
        # is the backup it just wrote. It is left exactly where it is — deleting a
        # path whose ownership is precisely what failed to verify could destroy
        # someone else's file — and the ledger row stays unresolved and counted.
        raise BackupArtifactUnverifiedError(BackupArtifactUnverifiedError.message)

    # From here the backup is verified and is the authoritative result. No audit
    # outcome below deletes it or turns this into a failure.
    return AuditedBackupResult(
        result=result,
        operation_id=operation_id,
        audit_status="recorded" if finalization.is_recorded else "pending",
    )


def _is_identity_active(audit_service: BackupAuditService, name: str) -> bool:
    """Treat an active ledger identity as a filename collision.

    A `prepared` operation owns its filename before that file exists, so file
    existence alone cannot tell whether a candidate identity is free. Failing to
    read the ledger here is a preparation failure, not a silent "no collision":
    guessing would let two operations claim one backup identity.

    Only the expected persistence failures are translated. This runs before
    anything is written, so letting an unexpected defect propagate is safe — the
    create still fails with nothing on disk — and it keeps a `TypeError` from
    being reported to the user as the specific, recoverable "tracking
    unavailable" condition.
    """
    try:
        return audit_service.is_identity_active(name)
    except (sqlite3.Error, OSError) as failure:
        raise BackupAuditTrackingUnavailableError(BackupAuditTrackingUnavailableError.message) from failure


def pending_backup_audit_count(backup_dir: Path, config: DatabaseConfig | None = None) -> int:
    """`pending_audit_count` for manual backups. Read-only; never reconciles."""
    return BackupAuditService(backup_dir, config or get_database_config()).pending_count()
