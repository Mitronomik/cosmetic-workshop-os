import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app
from app.services.database import initialize_database


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_settings_status_endpoint_returns_response_shape_and_is_read_only(monkeypatch, tmp_path):
    db = tmp_path / "settings-api.sqlite"
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    initialize_database(DatabaseConfig(path=db))
    with sqlite3.connect(db) as con:
        before = {row[0]: con.execute(f"SELECT COUNT(*) FROM {row[0]}").fetchone()[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}

    response = TestClient(create_app()).get("/api/settings/status")

    assert response.status_code == 200
    body = response.json()
    assert body["generated_at"]
    assert body["app"]["local_first"] is True
    assert body["app"]["internet_required"] is False
    assert body["local_data"]["user_data_separate_from_code"] is True
    assert body["capabilities"]
    assert body["setting_groups"]
    assert body["editable_settings_available"] is True
    assert all(capability["mutates_from_settings"] is False for capability in body["capabilities"])
    assert not user_data_dir.exists()
    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert after == before


def test_settings_status_route_is_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert ("/api/settings/status", ("GET",)) in routes


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_workshop_profile_api_get_put_and_status(monkeypatch, tmp_path):
    db = tmp_path / "settings-profile-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    client = TestClient(create_app())

    default = client.get("/api/settings/workshop-profile")
    assert default.status_code == 200
    assert default.json()["is_configured"] is False

    saved = client.put("/api/settings/workshop-profile", json={"workshop_name": "  Мастерская  ", "master_name": "Мария", "workshop_contact_text": "Телефон", "workshop_note": "Уход"})
    assert saved.status_code == 200
    assert saved.json()["profile"]["workshop_name"] == "Мастерская"
    assert saved.json()["updated_at"] is not None

    loaded = client.get("/api/settings/workshop-profile")
    assert loaded.json()["profile"] == saved.json()["profile"]
    assert loaded.json()["updated_at"] == saved.json()["updated_at"]

    status_response = client.get("/api/settings/status")
    editable = {item["id"] for group in status_response.json()["setting_groups"] for item in group["items"] if item["status"] == "editable_now"}
    assert editable == {"workshop_name", "master_name", "workshop_contact_text", "workshop_note"}


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_workshop_profile_api_rejects_invalid_values(monkeypatch, tmp_path):
    db = tmp_path / "settings-profile-api-invalid.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    client = TestClient(create_app())

    assert client.put("/api/settings/workshop-profile", json={"workshop_name": "я" * 121}).status_code == 422
    assert client.put("/api/settings/workshop-profile", json={"workshop_name": "bad\u0000"}).status_code == 422
