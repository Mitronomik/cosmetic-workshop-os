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
    assert body["editable_settings_available"] is False
    assert all(item["editable_in_pr95"] is False for group in body["setting_groups"] for item in group["items"])
    assert all(capability["mutates_from_settings"] is False for capability in body["capabilities"])
    assert not user_data_dir.exists()
    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert after == before


def test_settings_status_route_is_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert ("/api/settings/status", ("GET",)) in routes
