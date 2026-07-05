from pathlib import Path

import pytest
from pydantic import ValidationError

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app
from app.schemas.backups import BackupCreateRequest
from app.services.backup import list_backup_files


def test_missing_backup_dir_returns_empty_list_without_creating_dir(tmp_path):
    backup_dir = tmp_path / "missing-backups"

    assert list_backup_files(backup_dir) == []
    assert not backup_dir.exists()


def test_existing_backup_files_are_listed_newest_first_and_ignore_non_backups(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    older = backup_dir / "20260705T090000000000Z-cosmetic_workshop-manual.sqlite"
    newer = backup_dir / "20260705T100000000000Z-cosmetic_workshop-before_update.sqlite"
    ignored = backup_dir / "notes.txt"
    older.write_bytes(b"old")
    newer.write_bytes(b"newer")
    ignored.write_text("not a sqlite backup", encoding="utf-8")

    backups = list_backup_files(backup_dir)

    assert [backup.filename for backup in backups] == [newer.name, older.name]
    assert backups[0].reason == "before_update"
    assert backups[0].size_bytes == len(b"newer")


def test_malformed_backup_filename_does_not_crash_listing(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    malformed = backup_dir / "manual-copy.sqlite"
    malformed.write_bytes(b"sqlite bytes")

    backups = list_backup_files(backup_dir)

    assert len(backups) == 1
    assert backups[0].filename == malformed.name
    assert backups[0].created_at is not None
    assert backups[0].reason is None


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_status_is_read_only_and_reports_paths(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "cosmetic_workshop.sqlite"
    user_data_dir = tmp_path / "user-data"
    backup_dir = user_data_dir / "backups"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    client = TestClient(create_app())
    response = client.get("/api/backups/status")

    assert response.status_code == 200
    body = response.json()
    assert body["database_path"] == str(db_path)
    assert body["database_exists"] is False
    assert body["database_size_bytes"] is None
    assert body["backup_dir"] == str(backup_dir)
    assert body["backup_dir_exists"] is False
    assert body["backup_count"] == 0
    assert body["latest_backup"] is None
    assert not db_path.exists()
    assert not backup_dir.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_list_returns_empty_for_missing_dir_without_creating_it(tmp_path, monkeypatch):
    db_path = tmp_path / "dev.sqlite"
    backup_dir = tmp_path / "backups"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.get("/api/backups")

    assert response.status_code == 200
    assert response.json() == {"backups": [], "backup_dir": str(backup_dir)}
    assert not backup_dir.exists()
    assert not db_path.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_backup_creates_unique_backup_without_modifying_source(tmp_path, monkeypatch):
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    original_content = b"SQLite database bytes"
    db_path.write_bytes(original_content)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    first = client.post("/api/backups", json={"reason": "before_large_edit"})
    second = client.post("/api/backups", json={"reason": "before_large_edit"})

    assert first.status_code == 201
    assert second.status_code == 201
    first_backup = first.json()["backup"]
    second_backup = second.json()["backup"]
    assert first.json()["message"] == "Резервная копия создана."
    assert first.json()["database_path"] == str(db_path)
    assert first_backup["filename"] != second_backup["filename"]
    assert "before_large_edit" in first_backup["filename"]
    assert Path(first_backup["path"]).read_bytes() == original_content
    assert Path(second_backup["path"]).read_bytes() == original_content
    assert first_backup["size_bytes"] == len(original_content)
    assert second_backup["size_bytes"] == len(original_content)
    assert db_path.exists()
    assert db_path.read_bytes() == original_content

    listed = client.get("/api/backups").json()["backups"]
    assert [item["filename"] for item in listed] == [second_backup["filename"], first_backup["filename"]]


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_backup_with_missing_database_returns_safe_error_without_backup(tmp_path, monkeypatch):
    db_path = tmp_path / "missing.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 404
    assert response.json()["detail"] == "База данных не найдена. Сначала запустите приложение и создайте рабочую базу."
    assert not (tmp_path / "backups").exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters(tmp_path, monkeypatch):
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    db_path.write_bytes(b"db")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    empty = client.post("/api/backups", json={"reason": "   "})
    unsafe = client.post("/api/backups", json={"reason": "before/update ../unsafe"})

    assert empty.status_code == 201
    assert "manual" in empty.json()["backup"]["filename"]
    assert unsafe.status_code == 201
    unsafe_path = Path(unsafe.json()["backup"]["path"])
    assert unsafe_path.parent == tmp_path / "backups"
    assert "before_update_unsafe" in unsafe_path.name


def test_backup_reason_rejects_too_long_values():
    with pytest.raises(ValidationError):
        BackupCreateRequest(reason="x" * 81)
