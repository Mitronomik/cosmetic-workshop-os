import socket
import sqlite3
from pathlib import Path

import pytest

from launcher.config import build_runtime_config, resolve_runtime_paths, RuntimeConfigError
from launcher import runtime
from launcher.runtime import RuntimeLaunchError, initialize_backend_startup

FORBIDDEN_TABLES = {
    "recipes", "recipe_versions",
    "recipe_ingredients", "client_recipes", "client_recipe_ingredients", "clients",
    "client_wishes", "client_feedback", "orders", "production_batches", "import_sources",
    "import_drafts", "backup_records",
}
ALLOWED_TABLES = {"schema_migrations", "app_settings", "audit_logs", "ingredients", "ingredient_lots", "stock_movements", "packaging_items", "packaging_stock_movements", "sqlite_sequence"}


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
    assert tables <= ALLOWED_TABLES
    assert not FORBIDDEN_TABLES & tables


def test_launcher_startup_creates_backup_before_migration(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    database_path.parent.mkdir(parents=True)
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
    assert not user_data_dir.exists()
    assert not (fake_home / "Documents" / "Мастерская косметолога").exists()
