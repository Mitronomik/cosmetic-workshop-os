import json
import sqlite3

import pytest

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.paths import USER_DATA_DIR_ENV
from app.services.database import initialize_database
from app.services.settings import SettingsService


EXPECTED_CAPABILITIES = {"backups", "exports", "imports", "report_documents", "reports", "demo_data", "help", "settings"}


def test_settings_status_response_builds_local_first_status(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    response = SettingsService().build_status()

    assert response.generated_at
    assert response.app.product_name == "Мастерская косметолога"
    assert response.app.repository_name == "cosmetic-workshop-os"
    assert response.app.mode == "Локальное приложение"
    assert response.app.local_first is True
    assert response.app.internet_required is False
    assert response.local_data.user_data_separate_from_code is True
    assert response.local_data.user_data_path_available is True
    assert response.local_data.user_data_path_display == str(user_data_dir)
    assert response.local_data.backup_before_migration_required is True
    assert "отдельно от кода" in response.local_data.message
    assert response.editable_settings_available is True
    assert "Профиль мастерской и налоговую ставку для расчётов уже можно редактировать" in response.message


def test_settings_status_capabilities_are_navigation_only():
    response = SettingsService().build_status()
    capabilities = {capability.id: capability for capability in response.capabilities}

    assert EXPECTED_CAPABILITIES <= capabilities.keys()
    assert all(capability.mutates_from_settings is False for capability in response.capabilities)
    assert capabilities["backups"].route == "/backups"
    assert capabilities["settings"].route == "/settings"
    assert "редактировать профиль мастерской и налоговую ставку для расчётов" in capabilities["settings"].description
    assert "остальные расчетные настройки остаются закрыты" in capabilities["settings"].description


def test_settings_decision_matrix_contains_required_groups_and_profile_items_are_editable():
    response = SettingsService().build_status()
    groups = {group.id: group for group in response.setting_groups}

    assert {"safe_mvp_candidates", "calculation_sensitive_candidates", "v2_v3_only", "not_mvp"} <= groups.keys()
    safe_ids = {item.id for item in groups["safe_mvp_candidates"].items}
    calculation_ids = {item.id for item in groups["calculation_sensitive_candidates"].items}
    v2_ids = {item.id for item in groups["v2_v3_only"].items}
    not_mvp_ids = {item.id for item in groups["not_mvp"].items}

    assert {"workshop_name", "master_name", "workshop_contact_text", "workshop_note", "default_report_document_format", "backup_reminder_hint", "hide_demo_hints_after_onboarding"} <= safe_ids
    assert {"currency_display", "default_tax_rate", "target_margin", "default_low_stock_threshold", "expiry_warning_days", "default_measurement_units"} <= calculation_ids
    assert {"document_templates", "labels", "certificates", "docx_export", "email_sending", "external_integrations", "cloud_sync"} <= v2_ids
    assert {"roles_multi_user", "full_accounting", "advanced_analytics", "template_marketplace"} <= not_mvp_ids


def test_calculation_sensitive_settings_require_backend_service_and_history_flags_are_explicit():
    response = SettingsService().build_status()
    calculation_group = next(group for group in response.setting_groups if group.id == "calculation_sensitive_candidates")

    assert all(item.requires_backend_service is True for item in calculation_group.items)
    history_sensitive = {item.id for item in calculation_group.items if item.affects_historical_data}
    assert {"currency_display", "default_tax_rate", "target_margin", "default_measurement_units"} <= history_sensitive
    assert not {"default_low_stock_threshold", "expiry_warning_days"} & history_sensitive


def test_settings_service_does_not_create_files_or_mutate_database(monkeypatch, tmp_path):
    db = tmp_path / "data" / "cosmetic_workshop.sqlite"
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    db.parent.mkdir(parents=True)
    initialize_database(DatabaseConfig(path=db))
    with sqlite3.connect(db) as con:
        before = {row[0]: con.execute(f"SELECT COUNT(*) FROM {row[0]}").fetchone()[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}

    SettingsService().build_status()

    assert not user_data_dir.exists()
    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert after == before

from app.repositories.settings import SettingsRepository
from app.schemas.settings import WorkshopProfileUpdateRequest
from app.services.settings import (
    WORKSHOP_PROFILE_KEY,
    WorkshopProfilePersistenceError,
    WorkshopProfileSettingsService,
    WorkshopProfileValidationError,
)


def workshop_profile_audit_rows(config: DatabaseConfig) -> list[sqlite3.Row]:
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT actor_type, action, entity_type, entity_id, summary, metadata_json
            FROM audit_logs
            WHERE action = 'workshop_profile.updated'
            ORDER BY id
            """
        ).fetchall()


def workshop_profile_setting_row(config: DatabaseConfig) -> sqlite3.Row | None:
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT value, updated_at FROM app_settings WHERE key = ?",
            (WORKSHOP_PROFILE_KEY,),
        ).fetchone()


def test_workshop_profile_defaults_and_update_are_persisted(monkeypatch, tmp_path):
    db = tmp_path / "settings-profile.sqlite"
    initialize_database(DatabaseConfig(path=db))
    service = WorkshopProfileSettingsService(DatabaseConfig(path=db))

    default = service.get_profile()
    assert default.profile.workshop_name == ""
    assert default.is_configured is False

    updated = service.update_profile(WorkshopProfileUpdateRequest(workshop_name="  Мастерская  ", master_name=" Мария ", workshop_contact_text=" Телефон ", workshop_note=" Заметка "))
    assert updated.is_configured is True
    assert updated.updated_at is not None
    assert updated.profile.workshop_name == "Мастерская"
    assert updated.profile.master_name == "Мария"

    loaded = service.get_profile()
    assert loaded.profile == updated.profile
    assert loaded.updated_at == updated.updated_at
    assert len(workshop_profile_audit_rows(DatabaseConfig(path=db))) == 1


def test_workshop_profile_allows_empty_and_preserves_unrelated_settings(tmp_path):
    config = DatabaseConfig(path=tmp_path / "settings-profile-empty.sqlite")
    initialize_database(config)
    repo = SettingsRepository(config)
    before = repo.get_setting("product.name")

    response = WorkshopProfileSettingsService(config).update_profile(WorkshopProfileUpdateRequest())

    assert response.is_configured is False
    assert response.updated_at is None
    assert response.message == "Профиль мастерской уже сохранён без изменений."
    assert workshop_profile_setting_row(config) is None
    assert workshop_profile_audit_rows(config) == []
    assert repo.get_setting("product.name") == before


def test_workshop_profile_rejects_limits_and_control_characters(tmp_path):
    config = DatabaseConfig(path=tmp_path / "settings-profile-invalid.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)

    invalid_cases = [
        WorkshopProfileUpdateRequest(workshop_name="я" * 121),
        WorkshopProfileUpdateRequest(master_name="я" * 121),
        WorkshopProfileUpdateRequest(workshop_contact_text="я" * 501),
        WorkshopProfileUpdateRequest(workshop_note="я" * 501),
        WorkshopProfileUpdateRequest(workshop_name="bad\x00value"),
    ]
    for request in invalid_cases:
        try:
            service.update_profile(request)
        except WorkshopProfileValidationError:
            pass
        else:
            raise AssertionError("invalid workshop profile was accepted")


def test_workshop_profile_update_does_not_create_files_or_mutate_business_tables(tmp_path):
    db = tmp_path / "data" / "profile.sqlite"
    db.parent.mkdir()
    config = DatabaseConfig(path=db)
    initialize_database(config)
    before_files = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    with sqlite3.connect(db) as con:
        before = {row[0]: con.execute(f"SELECT COUNT(*) FROM {row[0]}").fetchone()[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT IN ('app_settings', 'audit_logs')")}

    WorkshopProfileSettingsService(config).update_profile(WorkshopProfileUpdateRequest(workshop_name="Мастерская"))

    after_files = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert after_files == before_files
    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert after == before


def test_workshop_profile_real_change_uses_one_connection_and_transaction(tmp_path, monkeypatch):
    config = DatabaseConfig(path=tmp_path / "profile-one-transaction.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)
    seen: dict[str, object] = {}
    original_upsert = service.repository.upsert_setting
    original_create_log = service.audit_repository.create_log

    def tracked_upsert(*args, connection=None, **kwargs):
        assert connection is not None
        seen["upsert_connection"] = connection
        original_upsert(*args, connection=connection, **kwargs)
        seen["upsert_in_transaction"] = connection.in_transaction

    def tracked_create_log(*args, connection=None, **kwargs):
        assert connection is not None
        seen["audit_connection"] = connection
        seen["audit_in_transaction"] = connection.in_transaction
        original_create_log(*args, connection=connection, **kwargs)

    monkeypatch.setattr(service.repository, "upsert_setting", tracked_upsert)
    monkeypatch.setattr(service.audit_repository, "create_log", tracked_create_log)

    response = service.update_profile(WorkshopProfileUpdateRequest(workshop_name="Тестовая мастерская"))

    assert response.profile.workshop_name == "Тестовая мастерская"
    assert seen["upsert_connection"] is seen["audit_connection"]
    assert seen["upsert_in_transaction"] is True
    assert seen["audit_in_transaction"] is True
    assert len(workshop_profile_audit_rows(config)) == 1


def test_workshop_profile_audit_failure_rolls_back_value_timestamp_and_event(tmp_path, monkeypatch):
    config = DatabaseConfig(path=tmp_path / "profile-audit-rollback.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)
    service.update_profile(WorkshopProfileUpdateRequest(workshop_name="До изменения"))
    before = dict(workshop_profile_setting_row(config))

    def fail_audit(**_kwargs):
        raise sqlite3.OperationalError("forced workshop-profile audit failure")

    monkeypatch.setattr(service.audit_repository, "create_log", fail_audit)

    with pytest.raises(WorkshopProfilePersistenceError):
        service.update_profile(WorkshopProfileUpdateRequest(workshop_name="После изменения"))

    assert dict(workshop_profile_setting_row(config)) == before
    assert len(workshop_profile_audit_rows(config)) == 1


def test_workshop_profile_persistence_failure_commits_no_audit(tmp_path, monkeypatch):
    config = DatabaseConfig(path=tmp_path / "profile-setting-rollback.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)

    def fail_upsert(*_args, **_kwargs):
        raise sqlite3.OperationalError("forced workshop-profile persistence failure")

    monkeypatch.setattr(service.repository, "upsert_setting", fail_upsert)

    with pytest.raises(WorkshopProfilePersistenceError):
        service.update_profile(WorkshopProfileUpdateRequest(workshop_name="Не сохранится"))

    assert workshop_profile_setting_row(config) is None
    assert workshop_profile_audit_rows(config) == []


def test_workshop_profile_canonical_noop_writes_nothing_and_preserves_timestamp(tmp_path, monkeypatch):
    config = DatabaseConfig(path=tmp_path / "profile-noop.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)
    saved = service.update_profile(
        WorkshopProfileUpdateRequest(
            workshop_name="Студия 1",
            master_name="Мария",
            workshop_contact_text="Телефон",
            workshop_note="Заметка",
        )
    )

    monkeypatch.setattr(
        service.repository,
        "upsert_setting",
        lambda *_args, **_kwargs: pytest.fail("canonical no-op must not upsert"),
    )
    monkeypatch.setattr(
        service.audit_repository,
        "create_log",
        lambda *_args, **_kwargs: pytest.fail("canonical no-op must not audit"),
    )

    for _ in range(2):
        repeated = service.update_profile(
            WorkshopProfileUpdateRequest(
                workshop_name="  Студия １  ",
                master_name=" Мария ",
                workshop_contact_text=" Телефон ",
                workshop_note=" Заметка ",
            )
        )
        assert repeated.profile == saved.profile
        assert repeated.updated_at == saved.updated_at
        assert repeated.message == "Профиль мастерской уже сохранён без изменений."

    assert len(workshop_profile_audit_rows(config)) == 1


def test_workshop_profile_configured_to_empty_persists_row_and_audits_once(tmp_path):
    config = DatabaseConfig(path=tmp_path / "profile-to-empty.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)
    service.update_profile(WorkshopProfileUpdateRequest(workshop_name="Мастерская", workshop_note="Заметка"))
    before_count = len(workshop_profile_audit_rows(config))

    emptied = service.update_profile(WorkshopProfileUpdateRequest())

    stored = workshop_profile_setting_row(config)
    assert emptied.is_configured is False
    assert stored is not None
    assert json.loads(stored["value"]) == {
        "workshop_name": "",
        "master_name": "",
        "workshop_contact_text": "",
        "workshop_note": "",
    }
    assert len(workshop_profile_audit_rows(config)) == before_count + 1
    metadata = json.loads(workshop_profile_audit_rows(config)[-1]["metadata_json"])
    assert metadata == {
        "setting_key": "workshop_profile",
        "changed_fields": ["workshop_name", "workshop_note"],
        "changed_field_count": 2,
        "previous_configured": True,
        "new_configured": False,
    }
    empty_timestamp = stored["updated_at"]
    repeated = service.update_profile(WorkshopProfileUpdateRequest())
    assert repeated.message == "Профиль мастерской уже сохранён без изменений."
    assert workshop_profile_setting_row(config)["updated_at"] == empty_timestamp
    assert len(workshop_profile_audit_rows(config)) == before_count + 1


def test_workshop_profile_audit_contract_is_exact_bounded_and_value_free(tmp_path):
    config = DatabaseConfig(path=tmp_path / "profile-safe-audit.sqlite")
    initialize_database(config)
    profile_values = {
        "workshop_name": "Секретная мастерская",
        "master_name": "Секретный мастер",
        "workshop_contact_text": "Телефон +7 000 и secret@example.com",
        "workshop_note": "Секретная заметка и адрес",
    }

    WorkshopProfileSettingsService(config).update_profile(WorkshopProfileUpdateRequest(**profile_values))

    row = workshop_profile_audit_rows(config)[0]
    assert (row["action"], row["entity_type"], row["entity_id"], row["actor_type"], row["summary"]) == (
        "workshop_profile.updated",
        "app_setting",
        "workshop_profile",
        "user",
        "Workshop profile updated",
    )
    metadata = json.loads(row["metadata_json"])
    assert metadata == {
        "setting_key": "workshop_profile",
        "changed_fields": ["master_name", "workshop_contact_text", "workshop_name", "workshop_note"],
        "changed_field_count": 4,
        "previous_configured": False,
        "new_configured": True,
    }
    persisted_audit = row["summary"] + row["metadata_json"]
    assert all(value not in persisted_audit for value in profile_values.values())


def test_workshop_profile_get_and_validation_create_no_audit(tmp_path):
    config = DatabaseConfig(path=tmp_path / "profile-read-validation.sqlite")
    initialize_database(config)
    service = WorkshopProfileSettingsService(config)

    service.get_profile()
    with pytest.raises(WorkshopProfileValidationError):
        service.update_profile(WorkshopProfileUpdateRequest(workshop_note="x" * 501))

    assert workshop_profile_setting_row(config) is None
    assert workshop_profile_audit_rows(config) == []


def test_settings_status_marks_only_workshop_profile_editable():
    """C1-I adds exactly one newly editable setting: `default_tax_rate`."""
    response = SettingsService().build_status()
    editable = {item.id for group in response.setting_groups for item in group.items if item.status == "editable_now"}
    assert editable == {"workshop_name", "master_name", "workshop_contact_text", "workshop_note", "default_tax_rate"}
    calculation_group = next(group for group in response.setting_groups if group.id == "calculation_sensitive_candidates")
    assert {item.id for item in calculation_group.items if item.status != "requires_backend_rules"} == {"default_tax_rate"}
