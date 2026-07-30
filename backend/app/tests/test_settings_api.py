import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app
from app.repositories.audit import AuditLogRepository
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
    assert set(saved.json()) == {"profile", "is_configured", "updated_at", "message"}

    journal = client.get("/api/audit-logs").json()
    event = next(item for item in journal["items"] if item["action"] == "workshop_profile.updated")
    assert event == {
        "id": event["id"],
        "created_at": event["created_at"],
        "action": "workshop_profile.updated",
        "action_label": "Профиль мастерской изменён",
        "entity_type": "app_setting",
        "entity_label": "Настройка приложения",
        "display_summary": "Профиль мастерской обновлён",
        "actor_type": "user",
        "actor_label": "Пользователь",
    }
    assert {"value": "workshop_profile.updated", "label": "Профиль мастерской изменён"} in journal["filter_options"]["actions"]
    assert {"value": "app_setting", "label": "Настройка приложения"} in journal["filter_options"]["entity_types"]
    serialized_journal = client.get("/api/audit-logs").text
    for forbidden in ("Workshop profile updated", "Мастерская", "Мария", "Телефон", "Уход", "metadata_json", "entity_id"):
        assert forbidden not in serialized_journal

    status_response = client.get("/api/settings/status")
    editable = {item["id"] for group in status_response.json()["setting_groups"] for item in group["items"] if item["status"] == "editable_now"}
    assert editable == {"workshop_name", "master_name", "workshop_contact_text", "workshop_note", "default_tax_rate"}


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_workshop_profile_api_rejects_invalid_values(monkeypatch, tmp_path):
    db = tmp_path / "settings-profile-api-invalid.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    client = TestClient(create_app())

    assert client.put("/api/settings/workshop-profile", json={"workshop_name": "я" * 121}).status_code == 422
    assert client.put("/api/settings/workshop-profile", json={"workshop_name": "bad\u0000"}).status_code == 422


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_workshop_profile_api_returns_safe_persistence_failure_and_rolls_back(monkeypatch, tmp_path):
    db = tmp_path / "settings-profile-api-failure.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    client = TestClient(create_app())
    saved = client.put("/api/settings/workshop-profile", json={"workshop_name": "Исходная"}).json()

    def fail_profile_audit(self, **_kwargs):
        raise sqlite3.OperationalError("forced audit failure")

    monkeypatch.setattr(AuditLogRepository, "create_log", fail_profile_audit)
    failed = client.put("/api/settings/workshop-profile", json={"workshop_name": "Новая"})

    assert failed.status_code == 500
    assert failed.json() == {
        "detail": {
            "code": "workshop_profile_not_saved",
            "message": "Не удалось сохранить профиль мастерской. Предыдущие данные сохранены без изменений.",
            "next_action": "Повторите сохранение. Если ошибка повторяется, проверьте, что локальное приложение работает.",
        }
    }
    loaded = client.get("/api/settings/workshop-profile").json()
    assert loaded["profile"] == saved["profile"]
    assert loaded["updated_at"] == saved["updated_at"]
    with sqlite3.connect(db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action = 'workshop_profile.updated'"
        ).fetchone()[0] == 1
