"""Persistence for the bounded CR-009 `artifact_audit_operations` ledger.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
§ "Bounded durable operation ledger".

This repository is internal. No API route reads or writes it, there is no
user-facing ledger CRUD surface, and none of its columns reach the Journal read
model. It stores exactly the identities reconciliation needs and nothing about
what the artifact contains: no reason text, no profile value, no report body, no
path.

Every method accepts an optional caller-owned connection so that the
exactly-once finalizer can run its AuditLog insert and its ledger transition
inside one transaction on one connection, as the accepted decision requires.
"""

from contextlib import nullcontext
from dataclasses import dataclass
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.artifact_audit_operations import (
    STATUS_ABANDONED,
    STATUS_AUDITED,
    STATUS_PENDING_AUDIT,
    STATUS_PREPARED,
    UNRESOLVED_STATUSES,
    validate_artifact_filename,
    validate_operation_id,
)

TABLE_NAME = "artifact_audit_operations"

_COLUMNS = (
    "operation_id, artifact_kind, primary_filename, companion_filename, "
    "status, audit_action, audit_log_id, created_at, updated_at"
)

_UNRESOLVED_PLACEHOLDERS = ", ".join("?" for _ in UNRESOLVED_STATUSES)


@dataclass(frozen=True)
class ArtifactAuditOperation:
    operation_id: str
    artifact_kind: str
    primary_filename: str
    companion_filename: str | None
    status: str
    audit_action: str
    audit_log_id: int | None
    created_at: str
    updated_at: str

    @property
    def is_unresolved(self) -> bool:
        return self.status in UNRESOLVED_STATUSES


class ArtifactAuditOperationRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def prepare_operation(
        self,
        *,
        operation_id: str,
        artifact_kind: str,
        primary_filename: str,
        companion_filename: str | None,
        audit_action: str,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        """Insert one `prepared` operation, or raise without inserting.

        Both filename fields are validated here rather than only at the call
        site, because this is the boundary that makes the stored value durable:
        anything that reaches the table will later be joined onto a real
        directory by reconciliation.
        """
        validate_operation_id(operation_id)
        validate_artifact_filename(primary_filename)
        if companion_filename is not None:
            validate_artifact_filename(companion_filename)
        with _connection_scope(self.config, connection) as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_NAME}
                    (operation_id, artifact_kind, primary_filename, companion_filename, status, audit_action)
                VALUES (?, ?, ?, ?, '{STATUS_PREPARED}', ?)
                """,
                (operation_id, artifact_kind, primary_filename, companion_filename, audit_action),
            )

    def get_operation(
        self, operation_id: str, *, connection: sqlite3.Connection | None = None
    ) -> ArtifactAuditOperation | None:
        with _connection_scope(self.config, connection) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM {TABLE_NAME} WHERE operation_id = ?", (operation_id,)
            ).fetchone()
        return _operation(row)

    def list_unresolved(
        self, artifact_kind: str, *, connection: sqlite3.Connection | None = None
    ) -> list[ArtifactAuditOperation]:
        """Every unresolved operation of one kind, oldest first.

        Deterministic ordering matters: reconciliation must process the same
        operations in the same order on every run so that a repeated pass is
        genuinely idempotent rather than merely usually idempotent.
        """
        with _connection_scope(self.config, connection) as connection:
            rows = connection.execute(
                f"""
                SELECT {_COLUMNS} FROM {TABLE_NAME}
                WHERE artifact_kind = ? AND status IN ({_UNRESOLVED_PLACEHOLDERS})
                ORDER BY created_at ASC, operation_id ASC
                """,
                (artifact_kind, *UNRESOLVED_STATUSES),
            ).fetchall()
        return [operation for operation in (_operation(row) for row in rows) if operation is not None]

    def count_unresolved(self, artifact_kind: str, *, connection: sqlite3.Connection | None = None) -> int:
        """The exact `pending_audit_count`: `prepared` plus `pending_audit` only."""
        with _connection_scope(self.config, connection) as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*) FROM {TABLE_NAME}
                WHERE artifact_kind = ? AND status IN ({_UNRESOLVED_PLACEHOLDERS})
                """,
                (artifact_kind, *UNRESOLVED_STATUSES),
            ).fetchone()[0]
        return int(total)

    def has_active_identity(
        self,
        artifact_kind: str,
        *,
        primary_filename: str,
        companion_filename: str | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> bool:
        """Whether an active operation already owns either candidate name.

        The companion name is checked as well as the primary one. Two formats of
        the same document ID share one `.json` sidecar name, so an active
        Markdown operation whose files are not on disk yet would otherwise let a
        PDF request reserve the very sidecar the first operation is about to
        write.
        """
        names = [primary_filename] + ([companion_filename] if companion_filename else [])
        placeholders = ", ".join("?" for _ in names)
        with _connection_scope(self.config, connection) as connection:
            row = connection.execute(
                f"""
                SELECT 1 FROM {TABLE_NAME}
                WHERE artifact_kind = ?
                  AND status IN ({_UNRESOLVED_PLACEHOLDERS})
                  AND (primary_filename IN ({placeholders}) OR companion_filename IN ({placeholders}))
                LIMIT 1
                """,
                (artifact_kind, *UNRESOLVED_STATUSES, *names, *names),
            ).fetchone()
        return row is not None

    def mark_pending_audit(self, operation_id: str, *, connection: sqlite3.Connection | None = None) -> bool:
        """Record that finalization was attempted and did not commit.

        Only a `prepared` row moves; an already `audited` or `abandoned` row is
        resolved history and is never reopened.
        """
        return self._transition(operation_id, STATUS_PENDING_AUDIT, (STATUS_PREPARED,), connection=connection)

    def mark_abandoned(self, operation_id: str, *, connection: sqlite3.Connection | None = None) -> bool:
        """Resolve an operation whose artifact definitely does not exist."""
        return self._transition(operation_id, STATUS_ABANDONED, UNRESOLVED_STATUSES, connection=connection)

    def mark_audited(
        self, operation_id: str, audit_log_id: int, *, connection: sqlite3.Connection | None = None
    ) -> bool:
        """Attach the committed AuditLog row to its operation.

        The `status IN (unresolved)` guard is the in-transaction half of
        duplicate-event protection: if a concurrent finalizer already audited
        this operation, this update matches no row and the caller must roll its
        own insert back rather than commit a second event.
        """
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                f"""
                UPDATE {TABLE_NAME}
                SET status = '{STATUS_AUDITED}', audit_log_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE operation_id = ? AND status IN ({_UNRESOLVED_PLACEHOLDERS})
                """,
                (audit_log_id, operation_id, *UNRESOLVED_STATUSES),
            )
            return cursor.rowcount == 1

    def _transition(
        self,
        operation_id: str,
        status: str,
        allowed_from: tuple[str, ...],
        *,
        connection: sqlite3.Connection | None,
    ) -> bool:
        placeholders = ", ".join("?" for _ in allowed_from)
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                f"""
                UPDATE {TABLE_NAME}
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE operation_id = ? AND status IN ({placeholders})
                """,
                (status, operation_id, *allowed_from),
            )
            return cursor.rowcount == 1


def _operation(row: sqlite3.Row | None) -> ArtifactAuditOperation | None:
    if row is None:
        return None
    return ArtifactAuditOperation(
        operation_id=row["operation_id"],
        artifact_kind=row["artifact_kind"],
        primary_filename=row["primary_filename"],
        companion_filename=row["companion_filename"],
        status=row["status"],
        audit_action=row["audit_action"],
        audit_log_id=None if row["audit_log_id"] is None else int(row["audit_log_id"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
