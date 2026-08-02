"""The audited JSON-export create operation, in its one required order.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
§ "Required operation sequence" and
``docs/decisions/0014-json-export-create-confirmation-semantics.md``.

This module exists so that one place — not the route handler, and not the
writer — owns the exact order the accepted decisions require:

```text
normalize request
→ bounded pre-create reconciliation
→ reserve the exact unique final export path
→ commit one prepared ledger row
→ write the export to that exact reserved path
→ verify the exact artifact
→ finalize AuditLog
```

It sits above ``export`` (which writes) and ``export_audit`` (which tracks and
verifies) and below the API, so neither of those two has to know about the
other.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Literal

from app.db.config import DatabaseConfig, get_database_config
from app.services.export import (
    ExportPaths,
    ExportResult,
    create_json_export,
    normalize_export_reason,
    parse_export_reason,
    require_exportable_source,
    reserve_export_path,
)
from app.services.export_audit import (
    PENDING_AUDIT_MESSAGE,
    ExportArtifactUnverifiedError,
    ExportAuditService,
    ExportAuditTrackingUnavailableError,
)

AuditStatus = Literal["recorded", "pending"]


@dataclass(frozen=True)
class AuditedExportResult:
    """One created export plus the separate result of recording it in the Journal.

    `result` is the creator's exact `ExportResult` and is authoritative. CR-006
    forbids re-reading the export directory to decide what was created, so this
    is the only description of the new export the response may use.
    """

    result: ExportResult
    operation_id: str
    audit_status: AuditStatus

    @property
    def audit_message(self) -> str | None:
        return None if self.audit_status == "recorded" else PENDING_AUDIT_MESSAGE

    @property
    def canonical_reason(self) -> str | None:
        """The API `reason`, parsed from the exact final filename.

        Never `ExportResult.reason` — that is the human manifest reason, and
        returning it here is exactly the CR-006 defect this slice corrects.
        """
        return parse_export_reason(self.result.export_path)


def create_audited_json_export(
    paths: ExportPaths,
    reason: str | None = None,
    *,
    config: DatabaseConfig | None = None,
) -> AuditedExportResult:
    """Create one JSON export and record it in the Journal, in that order.

    The failure modes stay distinct on purpose, because they mean different
    things to the user and to recovery:

    - `ExportSourceMissingError` / `ExportError` — the export itself could not be
      produced, so there is no artifact;
    - `ExportAuditTrackingUnavailableError` — the operation could not be durably
      tracked, so nothing was written at all;
    - `ExportArtifactUnverifiedError` — something exists at the reserved path but
      did not pass mandatory verification, so it is not a trustworthy export;
    - a returned result with `audit_status="pending"` — the export is **verified**
      and authoritative, and only its Journal entry is outstanding.
    """
    resolved_config = config or get_database_config()
    audit_service = ExportAuditService(paths.export_dir, resolved_config)
    normalized_reason = normalize_export_reason(reason)

    # The source precondition is checked here, before any ledger work, so that a
    # missing or unusable database still returns its existing `404`/`409` rather
    # than a tracking failure — and so that a create which cannot succeed leaves
    # behind no prepared operation and no newly created database file.
    require_exportable_source(paths.database_path)

    # One bounded pre-create reconciliation pass, before anything is reserved.
    # An older unresolved operation gets its chance here; it never blocks this
    # export by itself, and this never loops.
    audit_service.reconcile()

    created_at = datetime.now(UTC)
    reserved_path = reserve_export_path(
        paths.export_dir,
        created_at,
        normalized_reason,
        is_identity_active=lambda name: _is_identity_active(audit_service, name),
    )
    # The prepared row must be committed before the file is written. If it
    # cannot be, no export is created at all — refusing is honest: an artifact
    # we could not have tracked would be an artifact we could never audit.
    operation_id = audit_service.prepare_operation(primary_filename=reserved_path.name)

    # A creation failure deliberately leaves the committed `prepared` row alone
    # rather than abandoning it. This code cannot tell "never written" from
    # "written but not confirmed" — the creator's own post-write `stat` failure
    # raises a raw `OSError` after a complete export is already on disk — and
    # abandoning the second would permanently orphan a real export. Leaving the
    # row unresolved lets startup or pre-create reconciliation verify the exact
    # reserved file later: finalize it exactly once if it is valid, abandon it
    # only once it is proven absent.
    result = create_json_export(
        paths.database_path,
        paths.export_dir,
        reason=normalized_reason,
        reserved_export_path=reserved_path,
    )

    # Verification decides whether there is an authoritative result at all, and
    # the Journal entry is a separate, secondary question. Collapsing the two is
    # how an unverified file would be reported as a created export with a merely
    # pending Journal entry.
    finalization = audit_service.finalize(operation_id, reconciled_after_failure=False)
    if not finalization.artifact_is_authoritative:
        # Something is at the reserved path, but this operation could not prove it
        # is the export it just wrote. It is left exactly where it is — deleting a
        # path whose ownership is precisely what failed to verify could destroy
        # someone else's file — and the ledger row stays unresolved and counted.
        raise ExportArtifactUnverifiedError(ExportArtifactUnverifiedError.message)

    # From here the export is verified and is the authoritative result. No audit
    # outcome below deletes it or turns this into a failure.
    return AuditedExportResult(
        result=result,
        operation_id=operation_id,
        audit_status="recorded" if finalization.is_recorded else "pending",
    )


def _is_identity_active(audit_service: ExportAuditService, name: str) -> bool:
    """Treat an active ledger identity as a filename collision.

    A `prepared` operation owns its filename before that file exists, so file
    existence alone cannot tell whether a candidate identity is free. Failing to
    read the ledger here is a preparation failure, not a silent "no collision":
    guessing would let two operations claim one export identity.

    Only the expected persistence failures are translated. This runs before the
    file is written, so letting an unexpected defect propagate is safe — the
    create still fails with nothing on disk — and it keeps a `TypeError` from
    being reported to the user as the specific, recoverable "tracking
    unavailable" condition.
    """
    try:
        return audit_service.is_identity_active(name)
    except (sqlite3.Error, OSError) as failure:
        raise ExportAuditTrackingUnavailableError(ExportAuditTrackingUnavailableError.message) from failure


def pending_export_audit_count(export_dir: Path, config: DatabaseConfig | None = None) -> int:
    """`pending_audit_count` for JSON exports. Read-only; never reconciles."""
    return ExportAuditService(export_dir, config or get_database_config()).pending_count()
