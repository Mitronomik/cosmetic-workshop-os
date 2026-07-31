"""The bounded CR-009 artifact-audit operation vocabulary and its validators.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
and ``docs/report-documents.md`` § "CR-009 B1 durable AuditLog contract".

This module is pure. It opens no connection, touches no filesystem, imports
neither FastAPI nor Pydantic and writes nothing. It exists so that the ledger
repository, the report-document service and the reconciliation service all agree
on one definition of a valid operation identity, and so that those definitions
can be tested without a database.

Two identities matter here and they are deliberately different in kind:

``operation_id``
    The idempotency identity. Backend-generated, opaque, never supplied by a
    request and never exposed through the Journal read API. Exactly-once
    AuditLog finalization is tied to this value rather than to a filename,
    because filenames are ambiguous across formats and numeric suffixes.

``primary_filename`` / ``companion_filename``
    Internal reconciliation identities. They are *relative* names inside one
    already-resolved artifact directory, never unrestricted paths, so a stored
    row can never be used to reach outside that directory later.
"""

from pathlib import Path
from typing import Final
import uuid

ARTIFACT_KIND_REPORT_DOCUMENT: Final = "report_document"
ARTIFACT_KIND_JSON_EXPORT: Final = "json_export"
ARTIFACT_KIND_MANUAL_BACKUP: Final = "manual_backup"

# The table reserves the whole accepted CR-009 vocabulary so that B2 and B3 need
# no second migration, but only `report_document` has a runtime writer in B1.
ARTIFACT_KINDS: Final[frozenset[str]] = frozenset(
    {ARTIFACT_KIND_REPORT_DOCUMENT, ARTIFACT_KIND_JSON_EXPORT, ARTIFACT_KIND_MANUAL_BACKUP}
)

AUDIT_ACTION_REPORT_DOCUMENT_CREATED: Final = "report_document.created"
AUDIT_ACTION_EXPORT_CREATED: Final = "export.created"
AUDIT_ACTION_BACKUP_CREATED: Final = "backup.created"

AUDIT_ACTIONS: Final[frozenset[str]] = frozenset(
    {AUDIT_ACTION_REPORT_DOCUMENT_CREATED, AUDIT_ACTION_EXPORT_CREATED, AUDIT_ACTION_BACKUP_CREATED}
)

STATUS_PREPARED: Final = "prepared"
STATUS_PENDING_AUDIT: Final = "pending_audit"
STATUS_AUDITED: Final = "audited"
STATUS_ABANDONED: Final = "abandoned"

OPERATION_STATUSES: Final[frozenset[str]] = frozenset(
    {STATUS_PREPARED, STATUS_PENDING_AUDIT, STATUS_AUDITED, STATUS_ABANDONED}
)

# `prepared` and `pending_audit` are both *unresolved*: the artifact may exist
# but its AuditLog event has not been committed. Both are counted by
# `pending_audit_count` and both are eligible for reconciliation.
UNRESOLVED_STATUSES: Final[tuple[str, ...]] = (STATUS_PREPARED, STATUS_PENDING_AUDIT)


class ArtifactAuditOperationError(ValueError):
    """Raised when an artifact-audit operation identity is not safe to persist."""


def new_operation_id() -> str:
    """A fresh canonical lowercase UUID operation identity."""
    return str(uuid.uuid4())


def is_canonical_operation_id(value: object) -> bool:
    """Whether `value` is exactly the canonical lowercase form of a UUID.

    `uuid.UUID` accepts uppercase, braces, URNs and unhyphenated input, so
    parsing alone would let several spellings of one identity into the table and
    quietly break the primary-key idempotency the whole contract rests on.
    Round-tripping through `str(uuid.UUID(value))` and comparing byte for byte
    admits exactly one spelling per identity.
    """
    if not isinstance(value, str) or not value:
        return False
    try:
        return str(uuid.UUID(value)) == value
    except (ValueError, AttributeError, TypeError):
        return False


def validate_operation_id(value: object) -> str:
    """Return `value` when it is a canonical operation ID, else raise."""
    if not is_canonical_operation_id(value):
        raise ArtifactAuditOperationError("Operation identity is not a canonical lowercase UUID.")
    return str(value)


def is_safe_artifact_filename(value: object) -> bool:
    """Whether `value` is a plain relative filename safe to store and re-resolve.

    Checked on write *and* again on reconciliation read: a name is only ever as
    trustworthy as the moment it is used, and reconciliation joins it onto a real
    directory long after it was persisted.

    `Path(value).name != value` is the load-bearing check — it rejects `..`,
    every separator form and any trailing-slash spelling on this platform in one
    step. The explicit character checks come first so that NUL and control
    characters are rejected on their own terms rather than incidentally.
    """
    if not isinstance(value, str) or not value or value.strip() != value or not value.strip():
        return False
    if "\x00" in value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    if "/" in value or "\\" in value:
        return False
    if value in {".", ".."} or ".." in value:
        return False
    try:
        candidate = Path(value)
    except (ValueError, OSError):
        return False
    if candidate.is_absolute() or candidate.name != value:
        return False
    return True


def validate_artifact_filename(value: object) -> str:
    """Return `value` when it is a safe relative artifact filename, else raise."""
    if not is_safe_artifact_filename(value):
        raise ArtifactAuditOperationError("Artifact filename is not a safe relative name.")
    return str(value)


__all__ = [
    "ARTIFACT_KINDS",
    "ARTIFACT_KIND_JSON_EXPORT",
    "ARTIFACT_KIND_MANUAL_BACKUP",
    "ARTIFACT_KIND_REPORT_DOCUMENT",
    "AUDIT_ACTIONS",
    "AUDIT_ACTION_BACKUP_CREATED",
    "AUDIT_ACTION_EXPORT_CREATED",
    "AUDIT_ACTION_REPORT_DOCUMENT_CREATED",
    "ArtifactAuditOperationError",
    "OPERATION_STATUSES",
    "STATUS_ABANDONED",
    "STATUS_AUDITED",
    "STATUS_PENDING_AUDIT",
    "STATUS_PREPARED",
    "UNRESOLVED_STATUSES",
    "is_canonical_operation_id",
    "is_safe_artifact_filename",
    "new_operation_id",
    "validate_artifact_filename",
    "validate_operation_id",
]
