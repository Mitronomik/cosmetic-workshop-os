import json
import sqlite3

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.main import create_app
from app.tests.table_guards import FORBIDDEN_FUTURE_TABLES
from app.services.database import initialize_database
from app.services.onboarding import ONBOARDING_SETTING_KEY, ONBOARDING_STEPS, OnboardingService

FORBIDDEN_TABLES = FORBIDDEN_FUTURE_TABLES | {"onboarding_state"}


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "onboarding.sqlite")
    initialize_database(config)
    return config


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_default_onboarding_state_does_not_create_extra_tables(tmp_path):
    config = initialized_config(tmp_path)

    state = OnboardingService(config).get_state()

    assert state.has_started is False
    assert state.is_completed is False
    assert state.current_step == "welcome"
    assert state.completed_steps == ()
    assert not (FORBIDDEN_TABLES & table_names(config.path))


def test_onboarding_start_step_and_complete_are_persisted_in_app_settings(tmp_path):
    config = initialized_config(tmp_path)
    service = OnboardingService(config)

    started = service.start()
    after_step = service.complete_step("welcome")
    completed = service.complete()
    reloaded = OnboardingService(config).get_state()

    assert started.has_started is True
    assert after_step.completed_steps == ("welcome",)
    assert after_step.current_step == "data_location"
    assert completed.is_completed is True
    assert reloaded.completed_steps == ONBOARDING_STEPS
    with sqlite3.connect(config.path) as connection:
        row = connection.execute("SELECT value, value_type FROM app_settings WHERE key = ?", (ONBOARDING_SETTING_KEY,)).fetchone()
        audit_rows = connection.execute("SELECT action, summary FROM audit_logs ORDER BY id").fetchall()
    audit_actions = [row[0] for row in audit_rows]
    assert row[1] == "json"
    assert json.loads(row[0])["is_completed"] is True
    assert audit_actions == ["onboarding.started", "onboarding.step_completed", "onboarding.completed"]
    assert audit_rows[-1][1] == "Первичная настройка завершена пользователем."


def test_skip_default_state_closes_checklist_without_completing_all_steps(tmp_path):
    config = initialized_config(tmp_path)

    skipped = OnboardingService(config).skip()

    assert skipped.has_started is True
    assert skipped.is_completed is True
    assert skipped.current_step == "welcome"
    assert skipped.completed_steps == ()
    assert skipped.completed_steps != ONBOARDING_STEPS
    with sqlite3.connect(config.path) as connection:
        audit_actions = [row[0] for row in connection.execute("SELECT action FROM audit_logs ORDER BY id")]
    assert audit_actions == ["onboarding.skipped"]
    assert not (FORBIDDEN_TABLES & table_names(config.path))


def test_skip_after_welcome_preserves_only_actual_completed_steps(tmp_path):
    config = initialized_config(tmp_path)
    service = OnboardingService(config)

    service.complete_step("welcome")
    skipped = service.skip()

    assert skipped.has_started is True
    assert skipped.is_completed is True
    assert skipped.current_step == "data_location"
    assert skipped.completed_steps == ("welcome",)
    with sqlite3.connect(config.path) as connection:
        audit_actions = [row[0] for row in connection.execute("SELECT action FROM audit_logs ORDER BY id")]
    assert audit_actions == ["onboarding.step_completed", "onboarding.skipped"]


def test_complete_still_marks_all_steps_completed(tmp_path):
    config = initialized_config(tmp_path)

    completed = OnboardingService(config).complete()

    assert completed.has_started is True
    assert completed.is_completed is True
    assert completed.current_step == ONBOARDING_STEPS[-1]
    assert completed.completed_steps == ONBOARDING_STEPS


def test_get_returns_refreshed_steps_and_new_step_can_complete(tmp_path):
    config = initialized_config(tmp_path)
    service = OnboardingService(config)

    state = service.get_state()
    assert "first_ingredient_lot" in ONBOARDING_STEPS
    assert "first_packaging" in ONBOARDING_STEPS
    assert "backup_and_export" in ONBOARDING_STEPS
    assert "import_draft" in ONBOARDING_STEPS

    completed = service.complete_step("first_ingredient_lot")
    assert completed.has_started is True
    assert "first_ingredient_lot" in completed.completed_steps


def test_legacy_onboarding_state_is_mapped_without_crashing(tmp_path):
    config = initialized_config(tmp_path)
    legacy_payload = {
        "has_started": True,
        "is_completed": False,
        "current_step": "first_backup",
        "completed_steps": ["welcome", "first_backup", "unknown_old_step"],
        "dismissed_hints": ["old-hint"],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type) VALUES (?, ?, 'json')",
            (ONBOARDING_SETTING_KEY, json.dumps(legacy_payload)),
        )

    state = OnboardingService(config).get_state()

    assert state.is_completed is False
    assert state.current_step == "backup_and_export"
    assert state.completed_steps == ("welcome", "backup_and_export")


def test_unknown_current_step_falls_back_to_first_incomplete(tmp_path):
    config = initialized_config(tmp_path)
    payload = {
        "has_started": True,
        "is_completed": False,
        "current_step": "removed_step",
        "completed_steps": ["welcome", "data_location", "unknown_step"],
    }
    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type) VALUES (?, ?, 'json')",
            (ONBOARDING_SETTING_KEY, json.dumps(payload)),
        )

    state = OnboardingService(config).get_state()

    assert state.current_step == "first_ingredient"
    assert state.completed_steps == ("welcome", "data_location")


def test_completed_or_skipped_legacy_state_stays_closed(tmp_path):
    config = initialized_config(tmp_path)
    payload = {
        "has_started": True,
        "is_completed": True,
        "current_step": "first_backup",
        "completed_steps": ["welcome", "data_location", "first_backup"],
    }
    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type) VALUES (?, ?, 'json')",
            (ONBOARDING_SETTING_KEY, json.dumps(payload)),
        )

    state = OnboardingService(config).get_state()

    assert state.is_completed is True
    assert state.current_step == "backup_and_export"
    assert "backup_and_export" in state.completed_steps


def test_completing_all_refreshed_steps_marks_checklist_complete(tmp_path):
    config = initialized_config(tmp_path)
    service = OnboardingService(config)
    state = service.start()

    for step in ONBOARDING_STEPS:
        state = service.complete_step(step)

    assert state.is_completed is True
    assert state.current_step == ONBOARDING_STEPS[-1]
    assert state.completed_steps == ONBOARDING_STEPS


def test_onboarding_api_flow(monkeypatch, tmp_path):
    import pytest
    try:
        from fastapi.testclient import TestClient
    except RuntimeError as exc:
        pytest.skip(f"FastAPI TestClient dependency is unavailable: {exc}")

    database_path = tmp_path / "api-onboarding.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    client = TestClient(create_app())

    initial = client.get("/api/onboarding")
    assert initial.status_code == 200
    assert initial.json()["has_started"] is False

    started = client.post("/api/onboarding/start")
    assert started.status_code == 200
    assert started.json()["current_step"] == "welcome"

    step = client.post("/api/onboarding/complete-step", json={"step": "welcome"})
    assert step.status_code == 200
    assert step.json()["completed_steps"] == ["welcome"]
    assert step.json()["current_step"] == "data_location"

    invalid_step = client.post("/api/onboarding/complete-step", json={"step": "not-a-step"})
    assert invalid_step.status_code == 422

    skipped = client.post("/api/onboarding/skip")
    assert skipped.status_code == 200
    assert skipped.json()["is_completed"] is True
    assert skipped.json()["completed_steps"] == ["welcome"]

    completed = client.post("/api/onboarding/complete")
    assert completed.status_code == 200
    assert completed.json()["is_completed"] is True
    assert completed.json()["completed_steps"] == list(ONBOARDING_STEPS)
