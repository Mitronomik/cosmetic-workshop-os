import sqlite3
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app


def _create_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(DatabaseConfig(path=path))


def _counts(path: Path) -> dict[str, int]:
    tables = ["ingredients", "clients", "recipe_templates", "orders", "stock_movements", "backup_records", "exports"]
    counts = {}
    with sqlite3.connect(path) as connection:
        for table in tables:
            exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
            if exists:
                counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_targets_endpoint_returns_supported_targets(tmp_path, monkeypatch):
    monkeypatch.setenv(DATABASE_PATH_ENV, str(tmp_path / "db.sqlite"))
    client = TestClient(create_app())

    response = client.get("/api/imports/targets")

    assert response.status_code == 200
    targets = response.json()["targets"]
    assert {target["type"] for target in targets} >= {"ingredients", "clients", "orders"}
    assert next(target for target in targets if target["type"] == "ingredients")["required_columns"] == ["name"]


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_create_list_detail_and_cancel_import_draft_without_domain_mutation(tmp_path, monkeypatch):
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    user_dir = tmp_path / "user-data"
    _create_database(db_path)
    before_counts = _counts(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_dir))
    client = TestClient(create_app())

    response = client.post(
        "/api/imports/drafts",
        files={"file": ("ingredients.csv", b"name,unit\nWater,ml\nOil,g\n", "text/csv")},
        data={"target_type": "ingredients"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "Данные ещё не внесены в систему" in body["message"]
    draft = body["draft"]
    assert draft["row_count"] == 2
    assert draft["valid_row_count"] == 2
    assert len(body["preview_rows"]) == 2
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM import_sources").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM import_drafts").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM import_draft_rows").fetchone()[0] == 2
    assert _counts(db_path) == before_counts
    assert not (user_dir / "backups").exists()
    assert not (user_dir / "exports").exists()

    listing = client.get("/api/imports/drafts").json()
    assert listing["drafts"][0]["id"] == draft["id"]
    detail = client.get(f"/api/imports/drafts/{draft['id']}", params={"limit": 1, "offset": 1}).json()
    assert detail["source"]["original_filename"] == "ingredients.csv"
    assert "content_hash" not in detail["source"]
    assert detail["limit"] == 1 and detail["offset"] == 1
    assert len(detail["preview_rows"]) == 1

    cancelled = client.post(f"/api/imports/drafts/{draft['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["draft"]["status"] == "cancelled"
    assert "Рабочие данные не изменены" in cancelled.json()["message"]
    assert _counts(db_path) == before_counts


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_missing_required_columns_and_row_errors_create_draft_with_issues(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    client = TestClient(create_app())

    response = client.post(
        "/api/imports/drafts",
        files={"file": ("lots.csv", b"quantity,unit,purchase_date\nnot-number,kg,05.07.2026\n", "text/csv")},
        data={"target_type": "ingredient_lots"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["draft"]["error_count"] >= 4
    assert {issue["code"] for issue in body["issues"]} >= {"missing_required_column"}
    row_codes = {issue["code"] for issue in body["preview_rows"][0]["issues"]}
    assert {"invalid_decimal", "invalid_unit", "invalid_date"} <= row_codes


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_unsupported_and_too_large_uploads_return_safe_errors(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    client = TestClient(create_app())

    unsupported = client.post("/api/imports/drafts", files={"file": ("bad.txt", b"name\nA\n", "text/plain")}, data={"target_type": "ingredients"})
    assert unsupported.status_code == 415
    assert unsupported.json()["detail"] == "Поддерживаются только CSV и XLSX файлы."

    too_large = client.post("/api/imports/drafts", files={"file": ("big.csv", b"x" * (5 * 1024 * 1024 + 1), "text/csv")}, data={"target_type": "ingredients"})
    assert too_large.status_code == 413
    assert too_large.json()["detail"] == "Файл слишком большой для черновика импорта."


def test_service_create_detail_list_and_cancel_import_draft_without_domain_mutation(tmp_path):
    from app.services.imports import UploadedFileData, cancel_import_draft, create_import_draft, get_import_draft, list_import_drafts

    db_path = tmp_path / "service.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)
    before_counts = _counts(db_path)

    created = create_import_draft(
        UploadedFileData(filename="ingredients.csv", content_type="text/csv", content=b"name,unit\nWater,ml\n"),
        "ingredients",
        config=config,
    )

    draft_id = created["draft"]["id"]
    assert created["draft"]["row_count"] == 1
    assert created["preview_rows"][0]["normalized_values"] == {"name": "Water", "unit": "ml"}
    listed = list_import_drafts(config=config)
    assert listed["drafts"][0]["id"] == draft_id
    detail = get_import_draft(draft_id, config=config)
    assert detail is not None
    assert detail["source"]["original_filename"] == "ingredients.csv"
    assert "content_hash" not in detail["source"]
    cancelled = cancel_import_draft(draft_id, config=config)
    assert cancelled is not None
    assert cancelled["draft"]["status"] == "cancelled"
    assert _counts(db_path) == before_counts


def test_service_readiness_states_and_issue_counts(tmp_path):
    from app.services.imports import UploadedFileData, cancel_import_draft, create_import_draft, get_import_draft, list_import_drafts

    db_path = tmp_path / "readiness.sqlite"
    _create_database(db_path)
    config = DatabaseConfig(path=db_path)

    ready = create_import_draft(UploadedFileData(filename="ingredients.csv", content_type="text/csv", content=b"name,unit\nWater,g\n"), "ingredients", config=config)
    assert ready["draft"]["apply_readiness"]["status"] == "ready"
    assert ready["draft"]["apply_readiness"]["can_apply"] is True

    warned = create_import_draft(UploadedFileData(filename="ingredients.csv", content_type="text/csv", content=b"name,unit,extra\nWater,g,x\n"), "ingredients", config=config)
    assert warned["draft"]["apply_readiness"]["status"] == "ready_with_warnings"
    assert warned["draft"]["summary"]["issue_counts_by_code"]["unknown_column"] == 1

    blocked = create_import_draft(UploadedFileData(filename="ingredients.csv", content_type="text/csv", content=b"unit\ng\n"), "ingredients", config=config)
    assert blocked["draft"]["apply_readiness"]["status"] == "blocked"
    assert blocked["draft"]["apply_readiness"]["can_apply"] is False

    empty = create_import_draft(UploadedFileData(filename="ingredients.csv", content_type="text/csv", content=b"name,unit\n"), "ingredients", config=config)
    assert empty["draft"]["apply_readiness"]["status"] == "blocked"

    cancelled = cancel_import_draft(ready["draft"]["id"], config=config)
    assert cancelled["draft"]["apply_readiness"]["status"] == "cancelled"

    detail = get_import_draft(warned["draft"]["id"], config=config)
    assert detail["draft"]["apply_readiness"]["warning_count"] == warned["draft"]["warning_count"]
    listing = list_import_drafts(config=config)
    assert all("apply_readiness" in draft for draft in listing["drafts"])


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_no_import_apply_endpoint_exists(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_database(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    client = TestClient(create_app())

    response = client.post("/api/imports/drafts/1/apply", json={"confirm": True})

    assert response.status_code == 404
