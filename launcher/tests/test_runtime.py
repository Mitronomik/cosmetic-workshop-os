import socket
import sqlite3
from pathlib import Path

import pytest

from launcher.config import build_runtime_config, resolve_runtime_paths, RuntimeConfigError
from launcher import runtime
from launcher.runtime import RuntimeLaunchError, initialize_backend_startup
from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations

# The single shared table guard, so the launcher's expectation of the migrated
# schema cannot drift away from the backend's own. The previous local copy was
# frozen at roughly the `0011` schema and had gone stale: every table added by
# `0012`–`0020` broke this assertion for reasons unrelated to the launcher, and
# its local "forbidden" list still named `orders`, `production_batches`,
# `import_sources` and `import_drafts` — all of which are ordinary tables today.
#
# `assert_only_current_tables` stays a bounded check: an unexpected table still
# fails it. It is now bounded by the list the backend actually maintains.
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables


def table_names(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def test_runtime_config_defaults_are_localhost_user_mode():
    config = build_runtime_config(open_browser=False)

    assert config.host == "127.0.0.1"
    assert config.backend_port == 8000
    assert config.backend_url == "http://127.0.0.1:8000"
    assert config.frontend_url == "http://127.0.0.1:5173"
    assert config.mode == "user"
    assert config.open_browser is False


def test_runtime_config_rejects_non_localhost_host():
    with pytest.raises(RuntimeConfigError, match="127.0.0.1 only"):
        build_runtime_config(host="0.0.0.0")


def test_runtime_config_rejects_invalid_port():
    with pytest.raises(RuntimeConfigError, match="port"):
        build_runtime_config(backend_port=70000)


def test_launcher_startup_respects_user_data_override(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(user_data_dir))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)

    result = initialize_backend_startup("user", resolve_runtime_paths())

    assert result.mode == "user"
    assert result.database_path == user_data_dir / "data" / "cosmetic_workshop.sqlite"
    assert result.database_path.exists()
    assert not (fake_home / "Documents" / "Мастерская косметолога").exists()
    tables = table_names(result.database_path)
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    # The launcher must have migrated all the way to the current head, including
    # the CR-009 ledger — that is what startup reconciliation depends on.
    assert "artifact_audit_operations" in tables


def build_supported_older_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-1]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def test_launcher_startup_creates_backup_before_migration(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    build_supported_older_database(database_path)
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(user_data_dir))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE legacy_marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO legacy_marker (value) VALUES ('before')")

    result = initialize_backend_startup("user", resolve_runtime_paths())

    assert result.backup is not None
    assert result.backup.backup_path.parent == user_data_dir / "backups"
    with sqlite3.connect(result.backup.backup_path) as connection:
        assert connection.execute("SELECT value FROM legacy_marker").fetchone()[0] == "before"


def test_run_local_runtime_checks_port_before_user_data_startup(monkeypatch, tmp_path):
    """An occupied port still stops the run before any startup or migration.

    The port check now runs *after* Restore recovery rather than first, because
    an orphaned backend holds the port as well as the canonical lock and the
    ordering used to turn that case into a traceback. What the check protects is
    unchanged: no startup, no migration, no database, no backend, no browser.

    Recovery does take the launcher's lifecycle authority on the way, so the
    Restore directory and its lock file exist afterwards. Those are the
    launcher's own coordination files, created before any verdict and carrying no
    user data; the user database is the thing that must not appear, and it does
    not.
    """
    user_data_dir = tmp_path / "user-data"
    fake_home = tmp_path / "home"
    startup_called = False
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(user_data_dir))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)

    def fail_if_startup_is_called(mode, paths):
        nonlocal startup_called
        startup_called = True
        raise AssertionError("startup must not run when the backend port is already occupied")

    monkeypatch.setattr(runtime, "initialize_backend_startup", fail_if_startup_is_called)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied_socket:
        occupied_socket.bind(("127.0.0.1", 0))
        occupied_socket.listen(1)
        occupied_port = occupied_socket.getsockname()[1]
        config = build_runtime_config(backend_port=occupied_port, open_browser=False)

        with pytest.raises(RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    assert startup_called is False
    assert not (user_data_dir / "data").exists(), "no user database was created"
    assert not (user_data_dir / "backups").exists(), "no backup was taken"
    assert not (fake_home / "Documents" / "Мастерская косметолога").exists()
