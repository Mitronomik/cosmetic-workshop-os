import sqlite3

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
from app.repositories.database import ALLOWED_INFRASTRUCTURE_TABLES, DatabaseRepository
from app.repositories.settings import SettingsNotInitializedError
from app.services.database import database_status, initialize_database
from app.services.settings import read_app_settings


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

    assert applied == ["0001_infrastructure"]
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


def test_database_contains_only_allowed_infrastructure_tables(tmp_path):
    config = DatabaseConfig(path=tmp_path / "scope-test.sqlite")
    initialize_database(config)

    tables = table_names(config.path)

    assert tables <= ALLOWED_INFRASTRUCTURE_TABLES
    assert not {
        "recipes",
        "recipe_versions",
        "recipe_ingredients",
        "client_recipes",
        "ingredients",
        "ingredient_lots",
        "packaging_items",
        "stock_movements",
        "clients",
        "orders",
        "production_batches",
        "import_sources",
        "import_drafts",
        "backup_records",
    } & tables


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
