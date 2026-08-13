"""Read-only ordinary-startup schema compatibility preflight for D4-A."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import os
import sqlite3

from app.db.config import DatabaseConfig
from app.db.migration_lineage import LineageRejection, inspect_migration_lineage
from app.db.migrations import expected_migration_ids

StartupSchemaState = Literal["fresh", "current", "supported_older"]
SQLITE_READ_ONLY_TIMEOUT_SECONDS = 5.0


class StartupSchemaCompatibilityError(RuntimeError):
    """An existing database cannot be safely opened by this application."""

    def __init__(self, rejection: LineageRejection) -> None:
        super().__init__(f"Startup schema compatibility rejected: {rejection}")
        self.rejection = rejection


@dataclass(frozen=True)
class StartupSchemaCompatibility:
    state: StartupSchemaState
    applied_migration_ids: tuple[str, ...]
    target_migration_ids: tuple[str, ...]

    @property
    def migrations_pending(self) -> bool:
        return self.state == "supported_older"


def _open_read_only(database_path: Path) -> sqlite3.Connection:
    try:
        uri = database_path.resolve().as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True, timeout=SQLITE_READ_ONLY_TIMEOUT_SECONDS)
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise StartupSchemaCompatibilityError("migration-history-unreadable") from exc


def inspect_startup_schema_compatibility(
    config: DatabaseConfig,
) -> StartupSchemaCompatibility:
    """Classify the canonical DB before any mutation-capable startup helper runs."""
    target = tuple(expected_migration_ids())
    database_path = Path(config.path)
    if not os.path.lexists(database_path):
        return StartupSchemaCompatibility(
            state="fresh",
            applied_migration_ids=(),
            target_migration_ids=target,
        )

    if database_path.is_symlink() or not database_path.is_file():
        raise StartupSchemaCompatibilityError("migration-history-unreadable")

    connection = _open_read_only(database_path)
    try:
        lineage = inspect_migration_lineage(connection)
    finally:
        connection.close()

    if not lineage.is_known_prefix:
        raise StartupSchemaCompatibilityError(
            lineage.rejection or "migration-history-unreadable"
        )

    return StartupSchemaCompatibility(
        state="current" if lineage.is_current_head else "supported_older",
        applied_migration_ids=lineage.applied_ids,
        target_migration_ids=target,
    )
