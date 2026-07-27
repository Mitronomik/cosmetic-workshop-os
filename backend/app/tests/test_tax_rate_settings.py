"""Focused service/domain coverage for the C1 tax-rate setting.

API behavior and transaction boundaries live in `test_tax_rate_settings_api.py`.
"""

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from app.db.config import DatabaseConfig
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.tax_rate import canonical_tax_rate_percent, parse_tax_rate_percent
from app.repositories.settings import SettingsRepository
from app.services.database import initialize_database
from app.services.tax_rate_settings import (
    CHANGE_MESSAGE,
    CLEAR_MESSAGE,
    CONFIGURE_MESSAGE,
    DEFAULT_TAX_RATE_KEY,
    NOOP_CLEAR_MESSAGE,
    NOOP_SAVE_MESSAGE,
    TaxRateSettingPersistenceError,
    TaxRateSettingsService,
)

LEGACY_KEY = "tax.default_rate"


class FixedClock:
    """Deterministic UTC clock, so no test needs `sleep()` for timestamps."""

    def __init__(self, start: datetime | None = None) -> None:
        self.current = start or datetime(2026, 7, 27, 10, 0, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current = self.current + timedelta(seconds=seconds)


@pytest.fixture
def config(tmp_path):
    database_config = DatabaseConfig(path=tmp_path / "tax-rate-settings.sqlite")
    initialize_database(database_config)
    return database_config


def service(config: DatabaseConfig, clock: FixedClock | None = None) -> TaxRateSettingsService:
    return TaxRateSettingsService(config, now=clock or FixedClock())


def legacy_row(config: DatabaseConfig) -> tuple:
    with sqlite3.connect(config.path) as connection:
        return connection.execute(
            "SELECT key, value, value_type, description, updated_at FROM app_settings WHERE key = ?",
            (LEGACY_KEY,),
        ).fetchone()


def audit_rows(config: DatabaseConfig) -> list[sqlite3.Row]:
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT action, entity_type, entity_id, summary, metadata_json, created_at FROM audit_logs WHERE action = 'tax_rate_setting_changed' ORDER BY id"
        ).fetchall()


def stored_row(config: DatabaseConfig) -> sqlite3.Row | None:
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT value, updated_at FROM app_settings WHERE key = ?", (DEFAULT_TAX_RATE_KEY,)
        ).fetchone()


def test_initial_state_is_unconfigured_and_ignores_the_legacy_placeholder(config):
    response = service(config).get_tax_rate()

    assert response.is_configured is False
    assert response.tax_rate_percent is None
    assert response.effective_at is None
    assert legacy_row(config)[1] == "0.06"
    assert stored_row(config) is None


@pytest.mark.parametrize("requested", ["6", "6.0", "6.00", " 6 "])
def test_equivalent_inputs_persist_and_return_the_canonical_two_decimal_form(config, requested):
    response = service(config).update_tax_rate(requested)

    assert response.tax_rate_percent == "6.00"
    assert response.is_configured is True
    assert stored_row(config)["value"] == "6.00"


@pytest.mark.parametrize(("requested", "canonical"), [("0", "0.00"), ("100", "100.00"), ("0.5", "0.50"), ("99.99", "99.99")])
def test_boundary_and_fractional_values_are_configured_values(config, requested, canonical):
    response = service(config).update_tax_rate(requested)

    assert response.tax_rate_percent == canonical
    assert response.is_configured is True
    assert stored_row(config)["value"] == canonical


def test_configured_zero_is_a_real_value_and_not_missing(config):
    response = service(config).update_tax_rate("0")

    assert response.is_configured is True
    assert response.tax_rate_percent == "0.00"
    assert response.effective_at is not None
    assert service(config).get_tax_rate().is_configured is True


@pytest.mark.parametrize(
    ("requested", "code"),
    [
        ("-1", DomainIssueCode.TAX_RATE_OUT_OF_RANGE),
        ("-0.01", DomainIssueCode.TAX_RATE_OUT_OF_RANGE),
        ("100.01", DomainIssueCode.TAX_RATE_OUT_OF_RANGE),
        ("101", DomainIssueCode.TAX_RATE_OUT_OF_RANGE),
        ("6.005", DomainIssueCode.TAX_RATE_PRECISION_EXCEEDED),
        ("0.001", DomainIssueCode.TAX_RATE_PRECISION_EXCEEDED),
        ("6e1", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("1E2", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("   ", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("NaN", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("Infinity", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("-Infinity", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("6,5", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("шесть", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("6%", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("6.", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("+6", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
        ("6 6", DomainIssueCode.INVALID_TAX_RATE_FORMAT),
    ],
)
def test_invalid_strings_are_rejected_with_structured_codes(config, requested, code):
    with pytest.raises(DomainValidationError) as failure:
        service(config).update_tax_rate(requested)

    assert failure.value.issue.code == code
    assert failure.value.issue.field == "tax_rate_percent"
    assert failure.value.issue.message
    assert stored_row(config) is None
    assert audit_rows(config) == []


@pytest.mark.parametrize("requested", [6, 6.0, 0, True, False, float("nan"), float("inf"), [], {}, ("6",)])
def test_non_string_payloads_are_rejected_as_type_errors(config, requested):
    with pytest.raises(DomainValidationError) as failure:
        service(config).update_tax_rate(requested)

    assert failure.value.issue.code == DomainIssueCode.INVALID_TAX_RATE_TYPE
    assert stored_row(config) is None
    assert audit_rows(config) == []


def test_rejected_precision_never_becomes_a_rounded_value(config):
    service(config).update_tax_rate("6.00")

    with pytest.raises(DomainValidationError):
        service(config).update_tax_rate("6.005")

    assert stored_row(config)["value"] == "6.00"
    assert len(audit_rows(config)) == 1


def test_quantize_percentage_is_not_used_for_validation():
    with pytest.raises(DomainValidationError):
        parse_tax_rate_percent("6.005")
    assert canonical_tax_rate_percent(parse_tax_rate_percent("6.5")) == "6.50"


def test_first_configuration_is_audited_exactly_once_with_safe_metadata(config):
    clock = FixedClock()
    response = service(config, clock).update_tax_rate("6")

    rows = audit_rows(config)
    assert len(rows) == 1
    assert rows[0]["action"] == "tax_rate_setting_changed"
    assert rows[0]["entity_type"] == "app_setting"
    assert rows[0]["entity_id"] == DEFAULT_TAX_RATE_KEY
    assert rows[0]["summary"] == "Настроена налоговая ставка для расчётов."
    metadata = json.loads(rows[0]["metadata_json"])
    assert metadata == {
        "setting_key": DEFAULT_TAX_RATE_KEY,
        "previous_configured": False,
        "new_configured": True,
        "previous_rate_percent": None,
        "new_rate_percent": "6.00",
        "previous_effective_at": None,
        "new_effective_at": response.effective_at,
        "source": "settings",
    }
    assert response.message == CONFIGURE_MESSAGE


def test_real_change_is_audited_exactly_once_with_previous_and_new_values(config):
    clock = FixedClock()
    first = service(config, clock).update_tax_rate("6")
    clock.advance(60)
    second = service(config, clock).update_tax_rate("7.5")

    rows = audit_rows(config)
    assert len(rows) == 2
    assert rows[1]["summary"] == "Изменена налоговая ставка для расчётов."
    metadata = json.loads(rows[1]["metadata_json"])
    assert metadata["previous_rate_percent"] == "6.00"
    assert metadata["new_rate_percent"] == "7.50"
    assert metadata["previous_effective_at"] == first.effective_at
    assert metadata["new_effective_at"] == second.effective_at
    assert metadata["previous_configured"] is True
    assert metadata["new_configured"] is True
    assert second.message == CHANGE_MESSAGE


def test_audit_metadata_contains_no_payload_or_unrelated_fields(config):
    service(config).update_tax_rate("6")

    metadata = json.loads(audit_rows(config)[0]["metadata_json"])
    assert set(metadata) == {
        "setting_key",
        "previous_configured",
        "new_configured",
        "previous_rate_percent",
        "new_rate_percent",
        "previous_effective_at",
        "new_effective_at",
        "source",
    }


def test_get_is_not_audited(config):
    service(config).get_tax_rate()
    service(config).update_tax_rate("6")
    service(config).get_tax_rate()

    assert len(audit_rows(config)) == 1


@pytest.mark.parametrize(("stored", "requested"), [("6", "6"), ("6", "6.0"), ("6.00", "6"), ("0", "0"), ("100", "100.00")])
def test_noop_save_writes_nothing_and_preserves_the_effective_timestamp(config, stored, requested):
    clock = FixedClock()
    first = service(config, clock).update_tax_rate(stored)
    before = stored_row(config)["updated_at"]
    clock.advance(3600)

    response = service(config, clock).update_tax_rate(requested)

    assert response.message == NOOP_SAVE_MESSAGE
    assert response.effective_at == first.effective_at
    assert stored_row(config)["updated_at"] == before
    assert len(audit_rows(config)) == 1


def test_successful_clear_deletes_only_the_tax_rate_row_and_returns_null_fields(config):
    clock = FixedClock()
    configured = service(config, clock).update_tax_rate("6")
    with sqlite3.connect(config.path) as connection:
        before_keys = {row[0] for row in connection.execute("SELECT key FROM app_settings")}

    response = service(config, clock).update_tax_rate(None)

    assert response.is_configured is False
    assert response.tax_rate_percent is None
    assert response.effective_at is None
    assert response.message == CLEAR_MESSAGE
    assert stored_row(config) is None
    with sqlite3.connect(config.path) as connection:
        after_keys = {row[0] for row in connection.execute("SELECT key FROM app_settings")}
    assert before_keys - after_keys == {DEFAULT_TAX_RATE_KEY}
    rows = audit_rows(config)
    assert len(rows) == 2
    assert rows[1]["summary"] == "Налоговая ставка для расчётов очищена."
    metadata = json.loads(rows[1]["metadata_json"])
    assert metadata["previous_effective_at"] == configured.effective_at
    assert metadata["new_effective_at"] is None
    assert metadata["previous_rate_percent"] == "6.00"
    assert metadata["new_rate_percent"] is None
    assert metadata["previous_configured"] is True
    assert metadata["new_configured"] is False
    assert rows[1]["created_at"]


def test_noop_clear_performs_no_delete_and_no_audit(config):
    response = service(config).update_tax_rate(None)

    assert response.message == NOOP_CLEAR_MESSAGE
    assert response.is_configured is False
    assert response.effective_at is None
    assert audit_rows(config) == []
    assert legacy_row(config)[1] == "0.06"


def test_legacy_placeholder_row_is_unchanged_by_configure_change_and_clear(config):
    before = legacy_row(config)
    clock = FixedClock()
    tax_service = service(config, clock)

    tax_service.update_tax_rate("6")
    assert legacy_row(config) == before
    clock.advance(5)
    tax_service.update_tax_rate("7")
    assert legacy_row(config) == before
    tax_service.update_tax_rate(None)
    assert legacy_row(config) == before


def test_legacy_placeholder_is_never_read_as_a_configured_rate(config):
    response = service(config).get_tax_rate()

    assert response.tax_rate_percent is None
    assert response.is_configured is False


def test_rapid_successive_changes_receive_strictly_increasing_effective_times(config):
    clock = FixedClock()
    tax_service = service(config, clock)

    first = tax_service.update_tax_rate("1")
    second = tax_service.update_tax_rate("2")
    third = tax_service.update_tax_rate("3")

    assert first.effective_at < second.effective_at < third.effective_at
    stored = [json.loads(row["metadata_json"])["new_effective_at"] for row in audit_rows(config)]
    assert stored == [first.effective_at, second.effective_at, third.effective_at]


def test_stored_timestamp_stays_sqlite_utc_text_while_the_api_form_is_iso(config):
    clock = FixedClock(datetime(2026, 7, 27, 10, 28, 54, tzinfo=UTC))
    response = service(config, clock).update_tax_rate("6")

    assert stored_row(config)["updated_at"] == "2026-07-27 10:28:54"
    assert response.effective_at == "2026-07-27T10:28:54Z"


def test_persistence_survives_new_service_and_repository_instances(config):
    clock = FixedClock()
    saved = service(config, clock).update_tax_rate("6.25")

    reloaded = TaxRateSettingsService(config).get_tax_rate()

    assert reloaded.tax_rate_percent == "6.25"
    assert reloaded.effective_at == saved.effective_at
    assert SettingsRepository(config).get_setting(DEFAULT_TAX_RATE_KEY).value == "6.25"


def test_repository_delete_setting_reports_whether_a_row_existed(config):
    repository = SettingsRepository(config)
    repository.upsert_setting("temporary.key", "value", "string", "temporary")

    assert repository.delete_setting("temporary.key") is True
    assert repository.delete_setting("temporary.key") is False
    assert repository.get_setting("temporary.key") is None
    assert legacy_row(config)[1] == "0.06"


def test_repository_upsert_keeps_current_timestamp_behavior_without_explicit_value(config):
    repository = SettingsRepository(config)
    repository.upsert_setting("workshop_profile", "{}", "json", "profile")

    stored = repository.get_setting("workshop_profile")
    assert stored is not None
    assert stored.updated_at


def _failing_audit_service(config: DatabaseConfig, clock: FixedClock) -> TaxRateSettingsService:
    tax_service = TaxRateSettingsService(config, now=clock)

    def explode(**_kwargs):
        raise sqlite3.OperationalError("forced audit failure")

    tax_service.audit_repository.create_log = explode  # type: ignore[method-assign]
    return tax_service


def test_forced_audit_failure_rolls_back_the_first_configuration(config):
    clock = FixedClock()

    with pytest.raises(TaxRateSettingPersistenceError):
        _failing_audit_service(config, clock).update_tax_rate("6")

    assert stored_row(config) is None
    assert audit_rows(config) == []
    assert service(config).get_tax_rate().is_configured is False


def test_forced_audit_failure_rolls_back_a_change_and_preserves_value_and_timestamp(config):
    clock = FixedClock()
    first = service(config, clock).update_tax_rate("6")
    before = stored_row(config)
    clock.advance(120)

    with pytest.raises(TaxRateSettingPersistenceError):
        _failing_audit_service(config, clock).update_tax_rate("9.99")

    after = stored_row(config)
    assert after["value"] == before["value"] == "6.00"
    assert after["updated_at"] == before["updated_at"]
    assert len(audit_rows(config)) == 1
    assert service(config).get_tax_rate().effective_at == first.effective_at


def test_forced_audit_failure_rolls_back_clear_and_leaves_no_partial_audit(config):
    clock = FixedClock()
    service(config, clock).update_tax_rate("6")
    before = stored_row(config)

    with pytest.raises(TaxRateSettingPersistenceError):
        _failing_audit_service(config, clock).update_tax_rate(None)

    after = stored_row(config)
    assert after is not None
    assert after["value"] == before["value"]
    assert after["updated_at"] == before["updated_at"]
    assert len(audit_rows(config)) == 1
    assert legacy_row(config)[1] == "0.06"
