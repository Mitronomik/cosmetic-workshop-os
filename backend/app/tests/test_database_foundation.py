import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.config import (
    DATABASE_PATH_ENV,
    DEFAULT_DATABASE_PATH,
    REPOSITORY_ROOT,
    DatabaseConfig,
    get_database_config,
)
from app.db.migrations import apply_migrations, current_migrations, expected_migration_ids
from app.main import create_app
from app.repositories.database import ALLOWED_CURRENT_TABLES, FORBIDDEN_FUTURE_TABLES, DatabaseRepository
from app.repositories.settings import SettingsNotInitializedError
from app.services.backup import BackupSourceMissingError, backup_sqlite_database
from app.services.database import database_status, initialize_database
from app.services.settings import read_app_settings

from app.db.paths import (
    USER_DATA_DIR_ENV,
    create_user_data_directories,
    default_user_data_base_dir,
    resolve_development_database_path,
    resolve_user_data_paths,
)
from app.services.startup import initialize_startup, startup_database_config

FORBIDDEN_PR6_BUSINESS_TABLES = FORBIDDEN_FUTURE_TABLES


def assert_no_forbidden_pr6_business_tables(tables):
    assert not FORBIDDEN_PR6_BUSINESS_TABLES & tables


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    return {row[0] for row in rows}


def test_default_database_path_is_repository_root_local_path(monkeypatch):
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    config = get_database_config()

    assert config.path == DEFAULT_DATABASE_PATH
    assert config.path == REPOSITORY_ROOT / ".local" / "cosmetic_workshop.sqlite"
    assert config.path.is_absolute()


def test_database_path_env_override_still_works(monkeypatch, tmp_path):
    override_path = tmp_path / "override.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(override_path))

    config = get_database_config()

    assert config.path == override_path


def test_database_initialization_creates_infrastructure_tables(tmp_path):
    config = DatabaseConfig(path=tmp_path / "test.sqlite")

    applied = initialize_database(config)

    assert applied == expected_migration_ids()
    tables = table_names(config.path)
    assert "app_settings" in tables
    assert "audit_logs" in tables
    assert "schema_migrations" in tables


def test_database_status_does_not_initialize_missing_database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "missing.sqlite")

    status = database_status(config)

    assert status["status"] == "not_initialized"
    assert status["database_exists"] is False
    assert status["required_tables_present"] is False
    assert status["tables"] == []
    assert not config.path.exists()


def test_read_app_settings_does_not_initialize_missing_database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "missing-settings.sqlite")

    with pytest.raises(SettingsNotInitializedError):
        read_app_settings(config)

    assert not config.path.exists()


def test_migrations_apply_to_temporary_sqlite_database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "migration-test.sqlite")

    first_apply = apply_migrations(config)
    second_apply = apply_migrations(config)

    assert first_apply == expected_migration_ids()
    assert second_apply == []
    assert current_migrations(config) == set(expected_migration_ids())


def test_database_contains_only_allowed_current_tables(tmp_path):
    config = DatabaseConfig(path=tmp_path / "scope-test.sqlite")
    initialize_database(config)

    tables = table_names(config.path)

    assert tables <= ALLOWED_CURRENT_TABLES
    assert_no_forbidden_pr6_business_tables(tables)


def test_settings_read_returns_seeded_app_configuration_after_explicit_init(tmp_path):
    config = DatabaseConfig(path=tmp_path / "settings-test.sqlite")
    initialize_database(config)

    settings = {setting.key: setting for setting in read_app_settings(config)}

    assert settings["product.name"].value == "Мастерская косметолога"
    assert settings["mode.local_first"].value == "true"
    assert settings["tax.default_rate"].value == "0.06"


def test_database_status_reports_required_tables_after_explicit_init(tmp_path):
    config = DatabaseConfig(path=tmp_path / "status-test.sqlite")
    initialize_database(config)

    status = DatabaseRepository(config).status()

    assert status["status"] == "ok"
    assert status["database"] == "sqlite"
    assert status["database_exists"] is True
    assert status["required_tables_present"] is True
    assert "app_settings" in status["tables"]
    assert "audit_logs" in status["tables"]


def test_database_status_endpoint_does_not_initialize_test_database(monkeypatch, tmp_path):
    database_path = tmp_path / "api-uninitialized-database.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    client = TestClient(create_app())

    response = client.get("/api/database/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_initialized"
    assert body["database_exists"] is False
    assert body["required_tables_present"] is False
    assert body["tables"] == []
    assert not database_path.exists()


def test_settings_endpoint_requires_explicit_database_initialization(monkeypatch, tmp_path):
    database_path = tmp_path / "api-uninitialized-settings.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    client = TestClient(create_app())

    response = client.get("/api/settings")

    assert response.status_code == 409
    assert "not initialized" in response.json()["detail"]
    assert not database_path.exists()


def test_settings_endpoint_reads_explicitly_initialized_test_database(monkeypatch, tmp_path):
    database_path = tmp_path / "api-settings.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    client = TestClient(create_app())

    response = client.get("/api/settings")

    assert response.status_code == 200
    body = response.json()
    settings = {setting["key"]: setting for setting in body["settings"]}
    assert settings["product.name"]["value"] == "Мастерская косметолога"
    assert settings["mode.local_first"]["value"] == "true"


def test_database_status_endpoint_reads_explicitly_initialized_test_database(monkeypatch, tmp_path):
    database_path = tmp_path / "api-database.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    client = TestClient(create_app())

    response = client.get("/api/database/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "sqlite"
    assert body["database_exists"] is True
    assert body["required_tables_present"] is True
    assert "app_settings" in body["tables"]
    assert "audit_logs" in body["tables"]


def test_development_database_path_remains_stable(monkeypatch):
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    assert resolve_development_database_path() == REPOSITORY_ROOT / ".local" / "cosmetic_workshop.sqlite"
    assert get_database_config().path == resolve_development_database_path()


def test_user_data_default_path_uses_documents_folder_without_creating_it(monkeypatch, tmp_path):
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    paths = resolve_user_data_paths()

    assert paths.base_dir == fake_home / "Documents" / "Мастерская косметолога"
    assert paths.data_dir == paths.base_dir / "data"
    assert paths.database_path == paths.data_dir / "cosmetic_workshop.sqlite"
    assert paths.backups_dir == paths.base_dir / "backups"
    assert paths.exports_dir == paths.base_dir / "exports"
    assert paths.attachments_dir == paths.base_dir / "attachments"
    assert paths.logs_dir == paths.base_dir / "logs"
    assert not paths.base_dir.exists()


def test_user_data_directory_env_override(monkeypatch, tmp_path):
    override_dir = tmp_path / "custom-user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(override_dir))

    paths = resolve_user_data_paths()

    assert paths.base_dir == override_dir
    assert paths.database_path == override_dir / "data" / "cosmetic_workshop.sqlite"
    assert not override_dir.exists()


def test_database_path_env_override_takes_precedence_for_development_config(monkeypatch, tmp_path):
    override_path = tmp_path / "explicit-db.sqlite"
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(override_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    config = startup_database_config("development")

    assert config.path == override_path
    assert not override_path.exists()
    assert not user_data_dir.exists()


def test_user_mode_database_path_uses_user_data_directory(monkeypatch, tmp_path):
    override_path = tmp_path / "explicit-db.sqlite"
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(override_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    config = startup_database_config("user")

    assert config.path == user_data_dir / "data" / "cosmetic_workshop.sqlite"
    assert not config.path.exists()


def test_default_user_data_base_dir_is_cross_platform_documents_folder(tmp_path):
    assert default_user_data_base_dir(tmp_path, "Darwin") == tmp_path / "Documents" / "Мастерская косметолога"
    assert default_user_data_base_dir(tmp_path, "Windows") == tmp_path / "Documents" / "Мастерская косметолога"
    assert default_user_data_base_dir(tmp_path, "Linux") == tmp_path / "Documents" / "Мастерская косметолога"


def test_directory_creation_helper_creates_expected_user_data_folders(tmp_path):
    paths = resolve_user_data_paths(tmp_path / "Мастерская косметолога")

    create_user_data_directories(paths)

    assert all(directory.is_dir() for directory in paths.required_directories)
    assert not paths.database_path.exists()


def test_explicit_user_startup_initialization_creates_directories_and_applies_migrations(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    result = initialize_startup("user")

    assert result.mode == "user"
    assert result.user_data_paths is not None
    assert result.database_path == user_data_dir / "data" / "cosmetic_workshop.sqlite"
    assert result.applied_migrations == expected_migration_ids()
    assert all(directory.is_dir() for directory in result.user_data_paths.required_directories)
    tables = table_names(result.database_path)
    assert tables <= ALLOWED_CURRENT_TABLES
    assert_no_forbidden_pr6_business_tables(tables)


def test_explicit_development_startup_initialization_respects_database_path_override(monkeypatch, tmp_path):
    database_path = tmp_path / "development.sqlite"
    user_data_dir = tmp_path / "unused-user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    result = initialize_startup("development")

    assert result.mode == "development"
    assert result.user_data_paths is None
    assert result.database_path == database_path
    assert result.applied_migrations == expected_migration_ids()
    assert not user_data_dir.exists()
    tables = table_names(database_path)
    assert tables <= ALLOWED_CURRENT_TABLES
    assert_no_forbidden_pr6_business_tables(tables)


def test_status_endpoint_still_does_not_apply_migrations_when_user_data_env_exists(monkeypatch, tmp_path):
    database_path = tmp_path / "api-status.sqlite"
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    client = TestClient(create_app())

    response = client.get("/api/database/status")

    assert response.status_code == 200
    assert response.json()["status"] == "not_initialized"
    assert not database_path.exists()
    assert not user_data_dir.exists()


def test_startup_database_config_rejects_unsupported_mode(monkeypatch, tmp_path):
    database_path = tmp_path / "should-not-exist.sqlite"
    user_data_dir = tmp_path / "should-not-exist-user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    with pytest.raises(ValueError, match="Unsupported startup mode 'production'"):
        startup_database_config("production")

    assert not database_path.exists()
    assert not user_data_dir.exists()


def test_initialize_startup_rejects_unsupported_mode_without_side_effects(monkeypatch, tmp_path):
    database_path = tmp_path / "should-not-exist.sqlite"
    user_data_dir = tmp_path / "should-not-exist-user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    with pytest.raises(ValueError, match="Allowed modes: development, user"):
        initialize_startup("production")

    assert not database_path.exists()
    assert not user_data_dir.exists()


def test_backup_fails_clearly_when_source_database_is_missing(tmp_path):
    source = tmp_path / "missing.sqlite"
    backup_dir = tmp_path / "backups"

    with pytest.raises(BackupSourceMissingError, match="SQLite database file does not exist"):
        backup_sqlite_database(source, backup_dir, reason="before_migration")

    assert not backup_dir.exists()


def test_backup_creates_copy_with_matching_file_content(tmp_path):
    source = tmp_path / "source.sqlite"
    backup_dir = tmp_path / "backups"
    source.write_bytes(b"sqlite bytes for backup test")

    result = backup_sqlite_database(source, backup_dir, reason="before_migration")

    assert result.source_path == source
    assert result.reason == "before_migration"
    assert result.backup_path.parent == backup_dir
    assert result.size_bytes == source.stat().st_size
    assert result.backup_path.read_bytes() == source.read_bytes()
    assert source.read_bytes() == b"sqlite bytes for backup test"


def test_backup_filename_does_not_overwrite_existing_backup(tmp_path):
    source = tmp_path / "source.sqlite"
    backup_dir = tmp_path / "backups"
    source.write_bytes(b"first")

    first = backup_sqlite_database(source, backup_dir, reason="manual")
    source.write_bytes(b"second")
    second = backup_sqlite_database(source, backup_dir, reason="manual")

    assert first.backup_path != second.backup_path
    assert first.backup_path.read_bytes() == b"first"
    assert second.backup_path.read_bytes() == b"second"


def test_backup_directory_is_created_only_through_explicit_backup_call(tmp_path):
    source = tmp_path / "source.sqlite"
    backup_dir = tmp_path / "backups"
    source.write_bytes(b"database")

    assert not backup_dir.exists()

    backup_sqlite_database(source, backup_dir, reason="manual")

    assert backup_dir.is_dir()


def test_user_mode_startup_creates_backup_before_migration_for_existing_database(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    database_path.parent.mkdir(parents=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE legacy_marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO legacy_marker (value) VALUES ('before migration')")

    result = initialize_startup("user")

    assert result.backup is not None
    assert result.backup.reason == "before_migration"
    assert result.backup.backup_path.parent == user_data_dir / "backups"
    with sqlite3.connect(result.backup.backup_path) as backup_connection:
        marker = backup_connection.execute("SELECT value FROM legacy_marker").fetchone()[0]
        backup_tables = table_names(result.backup.backup_path)
    assert marker == "before migration"
    assert "app_settings" not in backup_tables
    assert result.applied_migrations == expected_migration_ids()
    tables = table_names(database_path)
    assert tables <= (ALLOWED_CURRENT_TABLES | {"legacy_marker"})
    assert_no_forbidden_pr6_business_tables(tables)


def test_brand_new_user_mode_startup_does_not_create_unnecessary_backup(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    result = initialize_startup("user")

    assert result.backup is None
    assert result.applied_migrations == expected_migration_ids()
    assert (user_data_dir / "backups").is_dir()
    assert list((user_data_dir / "backups").iterdir()) == []


def test_ordinary_status_and_settings_reads_do_not_create_backups(monkeypatch, tmp_path):
    database_path = tmp_path / "api-status.sqlite"
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    client = TestClient(create_app())

    status_response = client.get("/api/database/status")
    settings_response = client.get("/api/settings")

    assert status_response.status_code == 200
    assert settings_response.status_code == 409
    assert not database_path.exists()
    assert not user_data_dir.exists()
    assert not (user_data_dir / "backups").exists()
