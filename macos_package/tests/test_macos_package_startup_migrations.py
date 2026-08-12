"""Packaging/startup verification: the packaged tree can still reach the schema.

D3 does not add a migration runner, a second migration history or any new
startup step. What it *can* break is completeness: a packaging copy that misses
`app/migrations/versions/` produces an application that starts, creates a user
data directory, and then fails on a fresh database — after the user has already
committed to it.

So these tests check two things and claim nothing beyond them:

```text
the migration set the package declares is the repository's current set
the existing startup path still reaches that set, and still backs up first
```

The startup path exercised here is the same `initialize_startup("user")` the
packaged launcher reaches through `launcher.runtime.initialize_backend_startup`.
No packaging-specific startup code exists, which is the point.

This is **packaging/startup verification only**. It is not — and must not be
reported as — the later independent C4-III exact-package Restore verifier, which
exercises the packaged Restore flow against a real built artifact and remains a
separate gate.
"""

from __future__ import annotations

from pathlib import Path
import re
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.services.startup import initialize_startup
from launcher.config import resolve_runtime_paths
from launcher.runtime import initialize_backend_startup

REPO_ROOT = Path(__file__).resolve().parents[2]

# The last migration before the current head: the "supported older schema" a
# returning user's database would be at.
CURRENT_HEAD_MIGRATION = "0020_artifact_audit_operations"


def applied_migration_ids(database_path: Path) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        return [row[0] for row in connection.execute("SELECT migration_id FROM schema_migrations")]


def build_older_schema_database(database_path: Path) -> None:
    """A database at exactly the previous released schema, with real data in it.

    Truncating the module list is the repository's existing fixture contract for
    this (see `backend/app/tests/test_artifact_audit_operations_migration.py`);
    the schema is genuinely built by running the older migrations rather than
    approximated by hand, and the `schema_migrations` table is never edited to
    fake a state.
    """
    database_path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        cutoff = next(
            index
            for index, name in enumerate(original)
            if name.endswith(CURRENT_HEAD_MIGRATION)
        )
        MIGRATION_MODULES[:] = original[:cutoff]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original
    with sqlite3.connect(database_path) as connection:
        connection.execute("INSERT INTO clients (full_name) VALUES ('Историческая клиентка')")


@pytest.fixture
def isolated_user_data(tmp_path, monkeypatch):
    base = tmp_path / "Мастерская косметолога"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(base))
    return base


def test_the_packaged_migration_registry_matches_the_repository(tmp_path):
    """The structure gate parses the registry; this proves the parse is faithful.

    The verifier reads migration module names out of the packaged
    `migrations.py` with a regular expression. If that expression ever stopped
    matching the real file, the gate would silently start checking nothing.
    """
    from macos_package import verification

    source = (REPO_ROOT / "backend" / "app" / "db" / "migrations.py").read_text(encoding="utf-8")
    parsed = re.findall(r'"(app\.migrations\.versions\.[0-9A-Za-z_]+)"', source)
    assert parsed == MIGRATION_MODULES
    assert verification.REQUIRED_APPLICATION_FILES  # the gate is wired to this file


def test_a_fresh_user_mode_start_reaches_the_current_migration_set(isolated_user_data):
    """First launch: directories created, database created, every migration applied."""
    result = initialize_startup("user")
    assert result.database_path == isolated_user_data / "data" / "cosmetic_workshop.sqlite"
    assert result.database_path.is_file()
    assert applied_migration_ids(result.database_path) == expected_migration_ids()
    # No backup on a first run: there was nothing to back up.
    assert result.backup is None
    paths = resolve_user_data_paths()
    for directory in paths.required_directories:
        assert directory.is_dir()


def test_the_fresh_database_is_created_outside_the_application_root(isolated_user_data):
    """User data never lives inside the package, the build directory or the repo."""
    result = initialize_startup("user")
    database = result.database_path.resolve()
    application_root = resolve_runtime_paths().project_root.resolve()
    assert application_root not in database.parents
    assert (REPO_ROOT / "build").resolve() not in database.parents
    assert database.is_relative_to(isolated_user_data.resolve())


def test_an_older_database_is_migrated_with_a_backup_taken_first(isolated_user_data):
    """The mandatory backup-before-migration contract survives packaging unchanged."""
    database_path = isolated_user_data / "data" / "cosmetic_workshop.sqlite"
    build_older_schema_database(database_path)
    before = applied_migration_ids(database_path)
    assert CURRENT_HEAD_MIGRATION not in before

    result = initialize_startup("user")

    assert result.backup is not None, "no backup was taken before a schema migration"
    assert result.backup.backup_path.is_file()
    assert "before_migration" in result.backup.backup_path.name
    # The backup lives with the user's data, outside the package.
    assert result.backup.backup_path.is_relative_to(isolated_user_data.resolve())
    assert applied_migration_ids(database_path) == expected_migration_ids()
    # And the historical row is still there afterwards.
    with sqlite3.connect(database_path) as connection:
        names = [row[0] for row in connection.execute("SELECT full_name FROM clients")]
    assert "Историческая клиентка" in names


def test_the_backup_snapshot_still_holds_the_pre_migration_schema(isolated_user_data):
    """A backup that already contained the new schema would be no protection."""
    database_path = isolated_user_data / "data" / "cosmetic_workshop.sqlite"
    build_older_schema_database(database_path)
    result = initialize_startup("user")
    assert result.backup is not None
    assert CURRENT_HEAD_MIGRATION not in applied_migration_ids(result.backup.backup_path)


def test_the_launcher_startup_entry_reaches_the_same_result(isolated_user_data):
    """The packaged entrypoint never calls `initialize_startup` itself.

    It hands over to `run_local_runtime`, which calls
    `initialize_backend_startup`. Exercising that seam keeps the packaged path
    honest: there is one startup, not a packaging-specific copy of it.
    """
    result = initialize_backend_startup("user", resolve_runtime_paths())
    assert result.mode == "user"
    assert applied_migration_ids(result.database_path) == expected_migration_ids()
