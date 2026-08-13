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
from app.db.migrations import MIGRATION_MODULES, apply_migrations, current_migrations, expected_migration_ids
from app.main import create_app
from app.repositories.database import DatabaseRepository
from app.repositories.settings import SettingsNotInitializedError
import app.services.backup as backup_service
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
from app.tests.table_guards import (
    CURRENT_ALLOWED_TABLES,
    assert_no_forbidden_future_tables,
    assert_only_current_tables,
)


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

    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)


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
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)


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
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)


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


def _seed_source_database(path, values):
    """A real SQLite source with identifiable committed rows.

    ADR 0015 replaced the raw file copy with the SQLite Online Backup API, so a
    backup source must now actually be a database. These tests previously used a
    few literal bytes, which only ever worked because the old implementation
    copied bytes it did not understand.
    """
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS marker (value TEXT NOT NULL)")
        connection.execute("DELETE FROM marker")
        connection.executemany("INSERT INTO marker (value) VALUES (?)", [(value,) for value in values])
    return path


def _marker_values(path):
    """Read one database independently, without its source WAL or journal."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return [row[0] for row in connection.execute("SELECT value FROM marker ORDER BY value")]
    finally:
        connection.close()


def test_backup_creates_copy_with_matching_file_content(tmp_path):
    """The backup reproduces the source's committed content.

    The node ID is preserved from before ADR 0015 because the subject is
    unchanged; only the definition of "matching" moved. A raw file copy promised
    matching *bytes* and, as CR-004 measured, could still omit every committed
    row. The Online Backup API promises matching *committed state*, which is the
    property a backup is actually for, and does not promise byte equality.
    """
    source = _seed_source_database(tmp_path / "source.sqlite", ["alpha", "beta"])
    backup_dir = tmp_path / "backups"

    result = backup_sqlite_database(source, backup_dir, reason="before_migration")

    assert result.source_path == source
    assert result.reason == "before_migration"
    assert result.backup_path.parent == backup_dir
    assert result.size_bytes == result.backup_path.stat().st_size
    # The committed source state, opened independently. Byte-for-byte equality
    # with the source file is deliberately not asserted: ADR 0015 accepts a
    # transactionally consistent snapshot, not a file-level clone.
    assert _marker_values(result.backup_path) == ["alpha", "beta"]
    assert _marker_values(source) == ["alpha", "beta"]
    connection = sqlite3.connect(f"file:{result.backup_path}?mode=ro", uri=True)
    try:
        assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    finally:
        connection.close()


def test_backup_never_uses_a_raw_file_copy_for_database_contents():
    """No file-copy machinery may be reachable from the backup service.

    CR-004 classified the raw main-file copy as the defect itself, so this is a
    structural guard rather than a style check: reintroducing `shutil.copy2`
    would silently restore silent omission of committed data under WAL, and a
    green `quick_check` would not reveal it.

    The module's own prose is allowed to name `shutil` — explaining why it is
    gone is the point — so this inspects the parsed imports and the module
    namespace rather than the text.
    """
    import ast

    tree = ast.parse(Path(backup_service.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "shutil" not in imported
    assert not hasattr(backup_service, "shutil")
    assert "sqlite3" in imported


def test_backup_filename_does_not_overwrite_existing_backup(tmp_path):
    source = _seed_source_database(tmp_path / "source.sqlite", ["first"])
    backup_dir = tmp_path / "backups"

    first = backup_sqlite_database(source, backup_dir, reason="manual")
    _seed_source_database(source, ["second"])
    second = backup_sqlite_database(source, backup_dir, reason="manual")

    assert first.backup_path != second.backup_path
    assert _marker_values(first.backup_path) == ["first"]
    assert _marker_values(second.backup_path) == ["second"]


def test_backup_directory_is_created_only_through_explicit_backup_call(tmp_path):
    source = _seed_source_database(tmp_path / "source.sqlite", ["database"])
    backup_dir = tmp_path / "backups"

    assert not backup_dir.exists()

    backup_sqlite_database(source, backup_dir, reason="manual")

    assert backup_dir.is_dir()


def build_supported_older_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-1]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def test_user_mode_startup_creates_backup_before_migration_for_existing_database(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    build_supported_older_database(database_path)
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
    assert "artifact_audit_operations" not in backup_tables
    assert result.applied_migrations == [expected_migration_ids()[-1]]
    tables = table_names(database_path)
    assert tables <= (CURRENT_ALLOWED_TABLES | {"legacy_marker"})
    assert_no_forbidden_future_tables(tables)


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
