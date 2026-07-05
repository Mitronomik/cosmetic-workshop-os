import json
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app
from app.schemas.exports import ExportCreateRequest
from app.services.export import create_json_export, list_export_files


def _create_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(DatabaseConfig(path=path))


def test_missing_export_dir_returns_empty_list_without_creating_dir(tmp_path):
    export_dir = tmp_path / "missing-exports"

    assert list_export_files(export_dir) == []
    assert not export_dir.exists()


def test_existing_export_files_are_listed_newest_first_and_ignore_non_json(tmp_path):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    older = export_dir / "20260705T090000000000Z-cosmetic_workshop-export-manual.json"
    newer = export_dir / "20260705T100000000000Z-cosmetic_workshop-export-before_update.json"
    ignored = export_dir / "notes.txt"
    older.write_text('{"older": true}', encoding="utf-8")
    newer.write_text('{"newer": true}', encoding="utf-8")
    ignored.write_text("not an export", encoding="utf-8")

    exports = list_export_files(export_dir)

    assert [export.filename for export in exports] == [newer.name, older.name]
    assert exports[0].reason == "before_update"
    assert exports[0].size_bytes == len('{"newer": true}'.encode("utf-8"))


def test_malformed_export_filename_does_not_crash_listing(tmp_path):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    malformed = export_dir / "manual-export.json"
    malformed.write_text("{}", encoding="utf-8")

    exports = list_export_files(export_dir)

    assert len(exports) == 1
    assert exports[0].filename == malformed.name
    assert exports[0].created_at is not None
    assert exports[0].reason is None


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_export_status_is_read_only_and_reports_paths(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "cosmetic_workshop.sqlite"
    user_data_dir = tmp_path / "user-data"
    export_dir = user_data_dir / "exports"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    client = TestClient(create_app())
    response = client.get("/api/exports/status")

    assert response.status_code == 200
    body = response.json()
    assert body["database_path"] == str(db_path)
    assert body["database_exists"] is False
    assert body["database_size_bytes"] is None
    assert body["export_dir"] == str(export_dir)
    assert body["export_dir_exists"] is False
    assert body["export_count"] == 0
    assert body["latest_export"] is None
    assert not db_path.exists()
    assert not export_dir.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_export_list_returns_empty_for_missing_dir_without_creating_it(tmp_path, monkeypatch):
    db_path = tmp_path / "dev.sqlite"
    export_dir = tmp_path / "exports"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.get("/api/exports")

    assert response.status_code == 200
    assert response.json() == {"exports": [], "export_dir": str(export_dir)}
    assert not export_dir.exists()
    assert not db_path.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_export_creates_json_snapshot_without_modifying_source(tmp_path, monkeypatch):
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    _create_database(db_path)
    before_bytes = db_path.read_bytes()
    before_mtime = db_path.stat().st_mtime_ns
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    first = client.post("/api/exports", json={"reason": "before_large_edit"})
    second = client.post("/api/exports", json={"reason": "before_large_edit"})

    assert first.status_code == 201
    assert second.status_code == 201
    first_export = first.json()["export"]
    second_export = second.json()["export"]
    assert first.json()["message"] == "Экспорт создан."
    assert first.json()["database_path"] == str(db_path)
    assert first.json()["export_dir"] == str(tmp_path / "exports")
    assert first_export["filename"] != second_export["filename"]
    assert "before_large_edit" in first_export["filename"]

    export_payload = json.loads(Path(first_export["path"]).read_text(encoding="utf-8"))
    assert set(export_payload) == {"manifest", "data"}
    manifest = export_payload["manifest"]
    assert manifest["export_schema_version"] == 1
    assert manifest["reason"] == "before_large_edit"
    assert manifest["source"] == "cosmetic-workshop-os"
    assert manifest["database_filename"] == db_path.name
    assert manifest["database_location_kind"] == "development"
    assert "database_path" not in manifest
    assert manifest["tables"] == first.json()["entity_counts"]
    for table_name, rows in export_payload["data"].items():
        assert manifest["tables"][table_name] == len(rows)
    assert "schema_migrations" not in export_payload["data"]
    assert "alembic_version" not in export_payload["data"]
    assert db_path.exists()
    assert db_path.read_bytes() == before_bytes
    assert db_path.stat().st_mtime_ns == before_mtime

    listed = client.get("/api/exports").json()["exports"]
    assert [item["filename"] for item in listed] == [second_export["filename"], first_export["filename"]]


def test_export_includes_catalog_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    _create_database(db_path)
    with sqlite3.connect(db_path) as connection:
        ingredient_id = connection.execute(
            """
            INSERT INTO ingredients (name, category, default_unit)
            VALUES ('Масло ши', 'oil', 'g')
            """
        ).lastrowid
        packaging_item_id = connection.execute(
            """
            INSERT INTO packaging_items (name, kind, unit)
            VALUES ('Баночка 30 мл', 'jar', 'pcs')
            """
        ).lastrowid
        recipe_template_id = connection.execute(
            """
            INSERT INTO recipe_templates (name, product_type)
            VALUES ('Базовый крем', 'cream')
            """
        ).lastrowid
        ingredient_tag_id = connection.execute(
            """
            INSERT INTO catalog_tags (scope, name, slug)
            VALUES ('ingredient', 'Любимые масла', 'favorite-oils')
            """
        ).lastrowid
        packaging_tag_id = connection.execute(
            """
            INSERT INTO catalog_tags (scope, name, slug)
            VALUES ('packaging', 'Подарочная тара', 'gift-packaging')
            """
        ).lastrowid
        recipe_tag_id = connection.execute(
            """
            INSERT INTO catalog_tags (scope, name, slug)
            VALUES ('recipe', 'Базовые рецепты', 'base-recipes')
            """
        ).lastrowid
        connection.execute(
            """
            INSERT INTO catalog_categories (scope, name, slug)
            VALUES ('ingredient', 'Масла', 'oils')
            """
        )
        connection.execute(
            "INSERT INTO ingredient_catalog_tags (ingredient_id, tag_id) VALUES (?, ?)",
            (ingredient_id, ingredient_tag_id),
        )
        connection.execute(
            "INSERT INTO packaging_item_catalog_tags (packaging_item_id, tag_id) VALUES (?, ?)",
            (packaging_item_id, packaging_tag_id),
        )
        connection.execute(
            "INSERT INTO recipe_template_catalog_tags (recipe_template_id, tag_id) VALUES (?, ?)",
            (recipe_template_id, recipe_tag_id),
        )

    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    result = create_json_export(db_path, tmp_path / "exports", reason="catalog_check")
    payload = json.loads(result.export_path.read_text(encoding="utf-8"))

    expected_counts = {
        "catalog_categories": 1,
        "catalog_tags": 3,
        "ingredient_catalog_tags": 1,
        "packaging_item_catalog_tags": 1,
        "recipe_template_catalog_tags": 1,
    }
    for table_name, expected_count in expected_counts.items():
        assert table_name in payload["data"]
        assert table_name in payload["manifest"]["tables"]
        assert payload["manifest"]["tables"][table_name] == len(payload["data"][table_name])
        assert payload["manifest"]["tables"][table_name] == expected_count
    assert payload["manifest"]["database_filename"] == db_path.name
    assert payload["manifest"]["database_location_kind"] == "development"
    assert "database_path" not in payload["manifest"]


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_export_with_missing_database_returns_safe_error_without_export(tmp_path, monkeypatch):
    db_path = tmp_path / "missing.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 404
    assert response.json()["detail"] == "База данных не найдена. Сначала запустите приложение и создайте рабочую базу."
    assert not (tmp_path / "exports").exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_export_with_database_path_directory_returns_safe_error(tmp_path, monkeypatch):
    db_path = tmp_path / "not-a-file.sqlite"
    db_path.mkdir()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 409
    assert "SQLite database path is not a file" in response.json()["detail"]
    assert not (tmp_path / "exports").exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_export_reason_defaults_empty_and_sanitizes_unsafe_characters(tmp_path, monkeypatch):
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    _create_database(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    empty = client.post("/api/exports", json={"reason": "   "})
    unsafe = client.post("/api/exports", json={"reason": "before/import ../unsafe"})

    assert empty.status_code == 201
    empty_payload = json.loads(Path(empty.json()["export"]["path"]).read_text(encoding="utf-8"))
    assert "manual" in empty.json()["export"]["filename"]
    assert empty_payload["manifest"]["reason"] == "manual"
    assert unsafe.status_code == 201
    unsafe_path = Path(unsafe.json()["export"]["path"])
    unsafe_payload = json.loads(unsafe_path.read_text(encoding="utf-8"))
    assert unsafe_path.parent == tmp_path / "exports"
    assert "before_import_unsafe" in unsafe_path.name
    assert unsafe_payload["manifest"]["reason"] == "before/import ../unsafe"


def test_export_reason_rejects_too_long_values():
    with pytest.raises(ValidationError):
        ExportCreateRequest(reason="x" * 81)
