import sqlite3

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
    assert "Профиль мастерской уже можно редактировать" in response.message


def test_settings_status_capabilities_are_navigation_only():
    response = SettingsService().build_status()
    capabilities = {capability.id: capability for capability in response.capabilities}

    assert EXPECTED_CAPABILITIES <= capabilities.keys()
    assert all(capability.mutates_from_settings is False for capability in response.capabilities)
    assert capabilities["backups"].route == "/backups"
    assert capabilities["settings"].route == "/settings"
    assert "редактировать только профиль мастерской" in capabilities["settings"].description


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
from app.services.settings import WorkshopProfileSettingsService, WorkshopProfileValidationError


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


def test_workshop_profile_allows_empty_and_preserves_unrelated_settings(tmp_path):
    config = DatabaseConfig(path=tmp_path / "settings-profile-empty.sqlite")
    initialize_database(config)
    repo = SettingsRepository(config)
    before = repo.get_setting("product.name")

    response = WorkshopProfileSettingsService(config).update_profile(WorkshopProfileUpdateRequest())

    assert response.is_configured is False
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
        before = {row[0]: con.execute(f"SELECT COUNT(*) FROM {row[0]}").fetchone()[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'app_settings'")}

    WorkshopProfileSettingsService(config).update_profile(WorkshopProfileUpdateRequest(workshop_name="Мастерская"))

    after_files = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert after_files == before_files
    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert after == before


def test_settings_status_marks_only_workshop_profile_editable():
    response = SettingsService().build_status()
    editable = {item.id for group in response.setting_groups for item in group.items if item.status == "editable_now"}
    assert editable == {"workshop_name", "master_name", "workshop_contact_text", "workshop_note"}
    calculation_group = next(group for group in response.setting_groups if group.id == "calculation_sensitive_candidates")
    assert all(item.status == "requires_backend_rules" for item in calculation_group.items)
