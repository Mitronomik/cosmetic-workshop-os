import sqlite3
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.services.imports import UploadedFileData, apply_import_draft, create_import_draft, ImportApplyConflictError


def _create_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(DatabaseConfig(path=path))


def _count(path: Path, table: str) -> int:
    with sqlite3.connect(path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _draft(config: DatabaseConfig, target: str, content: bytes):
    return create_import_draft(UploadedFileData(filename=f"{target}.csv", content_type="text/csv", content=content), target, config=config)["draft"]


def test_apply_ingredients_transactionally_and_marks_source(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)
    draft = _draft(config, "ingredients", b"name,unit,density\nWater,ml,1\nOil,g,0.9\n")

    result = apply_import_draft(draft["id"], confirm_apply=True, backup_acknowledged=True, config=config)

    assert result["draft"]["status"] == "applied"
    assert result["apply_result"]["created_count"] == 2
    assert [r["label"] for r in result["apply_result"]["created_records"]] == ["Water", "Oil"]
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT status FROM import_sources WHERE id = ?", (draft["source_id"],)).fetchone()[0] == "applied"
        assert connection.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM ingredient_lots").fetchone()[0] == 0


def test_apply_supported_catalog_targets(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)
    cases = [
        ("clients", b"full_name,phone,email\nAnna,+1,anna@example.com\n", "clients"),
        ("recipe_templates", b"name,product_type,notes\nCream,day,note\n", "recipe_templates"),
        ("packaging_items", b"name,category,unit,cost,notes\nJar,jar,pcs,10,note\n", "packaging_items"),
    ]
    for target, content, table in cases:
        draft = _draft(config, target, content)
        result = apply_import_draft(draft["id"], confirm_apply=True, backup_acknowledged=True, config=config)
        assert result["apply_result"]["created_count"] == 1
        assert _count(db_path, table) == 1


def test_apply_requires_confirmation_backup_and_warning_flag(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)
    draft = _draft(config, "ingredients", b"name,unit,extra\nWater,g,x\n")

    with pytest.raises(ImportApplyConflictError) as missing_confirm:
        apply_import_draft(draft["id"], confirm_apply=False, backup_acknowledged=True, config=config)
    assert missing_confirm.value.issues[0]["code"] == "apply_confirmation_required"
    with pytest.raises(ImportApplyConflictError) as missing_backup:
        apply_import_draft(draft["id"], confirm_apply=True, backup_acknowledged=False, config=config)
    assert missing_backup.value.issues[0]["code"] == "backup_acknowledgement_required"
    with pytest.raises(ImportApplyConflictError) as warnings:
        apply_import_draft(draft["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    assert warnings.value.issues[0]["code"] == "warnings_not_allowed"

    result = apply_import_draft(draft["id"], confirm_apply=True, backup_acknowledged=True, allow_warnings=True, config=config)
    assert result["draft"]["status"] == "applied"


def test_apply_blocks_unsupported_cancelled_blocked_and_already_applied(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)

    unsupported = _draft(config, "ingredient_lots", b"ingredient_name,quantity,unit\nWater,10,g\n")
    with pytest.raises(ImportApplyConflictError) as unsupported_error:
        apply_import_draft(unsupported["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    assert unsupported_error.value.issues[0]["code"] == "apply_target_not_supported"

    blocked = _draft(config, "ingredients", b"unit\ng\n")
    with pytest.raises(ImportApplyConflictError) as blocked_error:
        apply_import_draft(blocked["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    assert blocked_error.value.issues[0]["code"] == "draft_not_ready"

    applied = _draft(config, "ingredients", b"name,unit\nWater,g\n")
    apply_import_draft(applied["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    with pytest.raises(ImportApplyConflictError) as already:
        apply_import_draft(applied["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    assert already.value.issues[0]["code"] == "draft_already_applied"


def test_apply_conflicts_insert_zero_rows_and_leave_draft_unapplied(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)
    first = _draft(config, "ingredients", b"name,unit\nWater,g\n")
    apply_import_draft(first["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    draft = _draft(config, "ingredients", b"name,unit\nOil,g\nWater,g\n")

    before = _count(db_path, "ingredients")
    with pytest.raises(ImportApplyConflictError) as conflict:
        apply_import_draft(draft["id"], confirm_apply=True, backup_acknowledged=True, config=config)

    assert conflict.value.issues[0]["code"] == "duplicate_domain_record"
    assert _count(db_path, "ingredients") == before
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT status FROM import_drafts WHERE id = ?", (draft["id"],)).fetchone()[0] == "draft"


def test_apply_duplicate_rows_and_packaging_stock_are_blocked(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)
    duplicate = _draft(config, "clients", b"full_name,email\nAnna,anna@example.com\nAnna,anna2@example.com\n")
    with pytest.raises(ImportApplyConflictError) as conflict:
        apply_import_draft(duplicate["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    assert conflict.value.issues[0]["code"] == "duplicate_domain_record"
    assert _count(db_path, "clients") == 0

    packaging = _draft(config, "packaging_items", b"name,unit,stock\nJar,pcs,5\n")
    with pytest.raises(ImportApplyConflictError) as stock_error:
        apply_import_draft(packaging["id"], confirm_apply=True, backup_acknowledged=True, config=config)
    assert stock_error.value.issues[0]["code"] == "apply_unsupported_field"
    assert _count(db_path, "packaging_items") == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_apply_api_response_and_missing_draft(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    client = TestClient(__import__("app.main", fromlist=["create_app"]).create_app())

    missing = client.post("/api/imports/drafts/999/apply", json={"confirm_apply": True, "backup_acknowledged": True})
    assert missing.status_code == 404

    created = client.post("/api/imports/drafts", files={"file": ("ingredients.csv", b"name,unit\nWater,g\n", "text/csv")}, data={"target_type": "ingredients"}).json()
    response = client.post(f"/api/imports/drafts/{created['draft']['id']}/apply", json={"confirm_apply": True, "backup_acknowledged": True})
    assert response.status_code == 200
    body = response.json()
    assert body["draft"]["status"] == "applied"
    assert body["apply_result"]["created_records"][0]["label"] == "Water"
