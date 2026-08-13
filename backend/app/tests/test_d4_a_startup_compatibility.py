from __future__ import annotations

from pathlib import Path
import hashlib
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.db.startup_compatibility import (
    StartupSchemaCompatibilityError,
    inspect_startup_schema_compatibility,
)
from app.services import startup as startup_service
from app.version import read_repository_app_version


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migrated_database(path: Path, *, exclude_last: int = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        if exclude_last:
            MIGRATION_MODULES[:] = original[:-exclude_last]
        apply_migrations(DatabaseConfig(path=path))
    finally:
        MIGRATION_MODULES[:] = original
    return path


def test_missing_database_is_the_only_fresh_state(tmp_path):
    database = tmp_path / "missing.sqlite"

    result = inspect_startup_schema_compatibility(DatabaseConfig(path=database))

    assert result.state == "fresh"
    assert result.applied_migration_ids == ()
    assert result.target_migration_ids == tuple(expected_migration_ids())
    assert not database.exists()


def test_current_database_is_accepted_read_only(tmp_path):
    database = migrated_database(tmp_path / "current.sqlite")
    before = digest(database)

    result = inspect_startup_schema_compatibility(DatabaseConfig(path=database))

    assert result.state == "current"
    assert result.applied_migration_ids == tuple(expected_migration_ids())
    assert result.migrations_pending is False
    assert digest(database) == before


def test_supported_older_prefix_is_accepted_without_migrating(tmp_path):
    database = migrated_database(tmp_path / "older.sqlite", exclude_last=1)
    before = digest(database)

    result = inspect_startup_schema_compatibility(DatabaseConfig(path=database))

    assert result.state == "supported_older"
    assert result.migrations_pending is True
    assert result.applied_migration_ids == tuple(expected_migration_ids()[:-1])
    assert digest(database) == before


def test_existing_database_without_lineage_fails_closed_and_is_unchanged(tmp_path):
    database = tmp_path / "foreign.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE notes (value TEXT)")
    before = digest(database)

    with pytest.raises(StartupSchemaCompatibilityError) as caught:
        inspect_startup_schema_compatibility(DatabaseConfig(path=database))

    assert caught.value.rejection == "migration-table-missing"
    assert digest(database) == before


def test_database_from_newer_application_fails_closed_and_is_unchanged(tmp_path):
    database = migrated_database(tmp_path / "newer.sqlite")
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO schema_migrations (migration_id) VALUES ('0021_future')"
        )
    before = digest(database)

    with pytest.raises(StartupSchemaCompatibilityError) as caught:
        inspect_startup_schema_compatibility(DatabaseConfig(path=database))

    assert caught.value.rejection == "schema-newer-than-application"
    assert digest(database) == before


@pytest.mark.parametrize(
    "rows,reason",
    [
        (["0001_infrastructure", "9999_unknown"], "unknown-migration-id"),
        (["0002_ingredients", "0001_infrastructure"], "reordered-migration-id"),
        (["0001_infrastructure", "0003_ingredient_lots"], "skipped-migration-id"),
    ],
)
def test_malformed_existing_lineage_fails_closed(tmp_path, rows, reason):
    database = tmp_path / f"{reason}.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE schema_migrations (migration_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        for migration_id in rows:
            connection.execute(
                "INSERT INTO schema_migrations (migration_id) VALUES (?)", (migration_id,)
            )
    before = digest(database)

    with pytest.raises(StartupSchemaCompatibilityError) as caught:
        inspect_startup_schema_compatibility(DatabaseConfig(path=database))

    assert caught.value.rejection == reason
    assert digest(database) == before


def test_user_startup_rejects_unknown_existing_db_before_backup_or_migration(
    tmp_path, monkeypatch
):
    base = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(base))
    paths = resolve_user_data_paths()
    paths.data_dir.mkdir(parents=True)
    with sqlite3.connect(paths.database_path) as connection:
        connection.execute("CREATE TABLE foreign_data (value TEXT)")
    before = digest(paths.database_path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("mutation-capable startup helper was reached")

    monkeypatch.setattr(startup_service, "create_user_data_directories", forbidden)
    monkeypatch.setattr(startup_service, "reconcile_interrupted_update", forbidden)
    monkeypatch.setattr(startup_service, "execute_staged_update", forbidden)
    monkeypatch.setattr(startup_service, "initialize_database", forbidden)

    with pytest.raises(StartupSchemaCompatibilityError):
        startup_service.initialize_startup("user")

    assert digest(paths.database_path) == before
    assert not paths.backups_dir.exists()
    assert not paths.exports_dir.exists()


def test_user_startup_returns_version_and_preflight_result(tmp_path, monkeypatch):
    base = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(base))

    result = startup_service.initialize_startup("user")

    assert result.app_version == read_repository_app_version()
    assert result.schema_compatibility.state == "fresh"
    assert result.database_path.is_file()
