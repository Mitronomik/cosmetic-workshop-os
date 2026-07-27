"""Backend-owned workshop tax-rate setting (`default_tax_rate`).

C1 stores and edits the setting only. It calculates no tax, no margin, and never
touches historical production, orders, stock, or reports. The legacy seeded
`tax.default_rate` placeholder row is a different key and is never read, written,
deleted, or interpreted here.
"""

import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Callable, Final

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.tax_rate import canonical_tax_rate_percent, parse_tax_rate_percent
from app.models.settings import AppSetting
from app.repositories.audit import AuditLogRepository
from app.repositories.settings import SettingsNotInitializedError, SettingsRepository
from app.schemas.tax_rate_settings import TaxRateSettingResponse

DEFAULT_TAX_RATE_KEY: Final = "default_tax_rate"
TAX_RATE_VALUE_TYPE: Final = "decimal_string"
TAX_RATE_DESCRIPTION: Final = "Workshop tax rate percentage for internal tax and margin estimates."

TAX_RATE_AUDIT_ACTION: Final = "tax_rate_setting_changed"
TAX_RATE_AUDIT_ENTITY_TYPE: Final = "app_setting"
TAX_RATE_AUDIT_SOURCE: Final = "settings"

CONFIGURED_MESSAGE: Final = "Налоговая ставка для расчётов настроена."
UNCONFIGURED_MESSAGE: Final = "Налоговая ставка для расчётов пока не настроена."
CONFIGURE_MESSAGE: Final = "Налоговая ставка для расчётов сохранена."
CHANGE_MESSAGE: Final = "Налоговая ставка для расчётов изменена."
NOOP_SAVE_MESSAGE: Final = "Налоговая ставка уже сохранена без изменений."
CLEAR_MESSAGE: Final = "Налоговая ставка для расчётов очищена."
NOOP_CLEAR_MESSAGE: Final = "Налоговая ставка уже не настроена."

CONFIGURE_AUDIT_SUMMARY: Final = "Настроена налоговая ставка для расчётов."
CHANGE_AUDIT_SUMMARY: Final = "Изменена налоговая ставка для расчётов."
CLEAR_AUDIT_SUMMARY: Final = "Налоговая ставка для расчётов очищена."

STORAGE_TIMESTAMP_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
API_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"


class TaxRateSettingPersistenceError(RuntimeError):
    """The setting could not be saved atomically with its audit record."""


class TaxRateSettingsService:
    def __init__(self, config: DatabaseConfig | None = None, *, now: Callable[[], datetime] | None = None) -> None:
        self.config = config or get_database_config()
        self.repository = SettingsRepository(self.config)
        self.audit_repository = AuditLogRepository(self.config)
        self._now = now or (lambda: datetime.now(UTC))

    def get_tax_rate(self) -> TaxRateSettingResponse:
        """Read the current setting. Never audited and never writes."""
        return self._state_response(self.repository.get_setting(DEFAULT_TAX_RATE_KEY))

    def update_tax_rate(self, requested: object) -> TaxRateSettingResponse:
        """Configure/change the rate, or clear it when `requested` is `None`.

        Validation happens before any transaction opens, so a rejected request
        writes nothing and creates no audit record.
        """
        if requested is None:
            return self._clear()
        return self._configure(canonical_tax_rate_percent(parse_tax_rate_percent(requested)))

    def _configure(self, canonical: str) -> TaxRateSettingResponse:
        return self._atomic(lambda connection: self._apply_configure(connection, canonical))

    def _clear(self) -> TaxRateSettingResponse:
        return self._atomic(self._apply_clear)

    def _apply_configure(self, connection: sqlite3.Connection, canonical: str) -> TaxRateSettingResponse:
        previous = self.repository.get_setting(DEFAULT_TAX_RATE_KEY, connection)
        previous_percent = _stored_percent(previous)
        if previous is not None and previous_percent == canonical:
            return self._response(previous_percent, _api_timestamp(previous.updated_at), NOOP_SAVE_MESSAGE)
        effective_at = self._next_storage_timestamp(previous.updated_at if previous else None)
        self.repository.upsert_setting(
            DEFAULT_TAX_RATE_KEY,
            canonical,
            TAX_RATE_VALUE_TYPE,
            TAX_RATE_DESCRIPTION,
            connection=connection,
            updated_at=effective_at,
        )
        stored = self.repository.get_setting(DEFAULT_TAX_RATE_KEY, connection)
        new_effective_at = _api_timestamp(stored.updated_at if stored else effective_at)
        self._write_audit(
            connection,
            CONFIGURE_AUDIT_SUMMARY if previous is None else CHANGE_AUDIT_SUMMARY,
            previous_percent=previous_percent,
            new_percent=canonical,
            previous_effective_at=_api_timestamp(previous.updated_at) if previous else None,
            new_effective_at=new_effective_at,
        )
        return self._response(canonical, new_effective_at, CONFIGURE_MESSAGE if previous is None else CHANGE_MESSAGE)

    def _apply_clear(self, connection: sqlite3.Connection) -> TaxRateSettingResponse:
        previous = self.repository.get_setting(DEFAULT_TAX_RATE_KEY, connection)
        if previous is None:
            return self._response(None, None, NOOP_CLEAR_MESSAGE)
        self.repository.delete_setting(DEFAULT_TAX_RATE_KEY, connection)
        self._write_audit(
            connection,
            CLEAR_AUDIT_SUMMARY,
            previous_percent=_stored_percent(previous),
            new_percent=None,
            previous_effective_at=_api_timestamp(previous.updated_at),
            new_effective_at=None,
        )
        return self._response(None, None, CLEAR_MESSAGE)

    def _write_audit(
        self,
        connection: sqlite3.Connection,
        summary: str,
        *,
        previous_percent: str | None,
        new_percent: str | None,
        previous_effective_at: str | None,
        new_effective_at: str | None,
    ) -> None:
        self.audit_repository.create_log(
            action=TAX_RATE_AUDIT_ACTION,
            entity_type=TAX_RATE_AUDIT_ENTITY_TYPE,
            entity_id=DEFAULT_TAX_RATE_KEY,
            summary=summary,
            actor_type="user",
            metadata={
                "setting_key": DEFAULT_TAX_RATE_KEY,
                "previous_configured": previous_percent is not None,
                "new_configured": new_percent is not None,
                "previous_rate_percent": previous_percent,
                "new_rate_percent": new_percent,
                "previous_effective_at": previous_effective_at,
                "new_effective_at": new_effective_at,
                "source": TAX_RATE_AUDIT_SOURCE,
            },
            connection=connection,
        )

    def _next_storage_timestamp(self, previous_stored: str | None) -> str:
        """Return a stored UTC timestamp strictly later than the previous one.

        SQLite `CURRENT_TIMESTAMP` has second precision, so two real changes
        inside the same second would otherwise share a timestamp. This logical
        tie-break keeps effective times strictly increasing without sleeping; the
        setting still becomes effective immediately.
        """
        current = self._now().astimezone(UTC).replace(tzinfo=None, microsecond=0)
        previous = _parse_storage_timestamp(previous_stored)
        if previous is not None and current <= previous:
            current = previous + timedelta(seconds=1)
        return current.strftime(STORAGE_TIMESTAMP_FORMAT)

    def _atomic(self, operation: Callable[[sqlite3.Connection], TaxRateSettingResponse]) -> TaxRateSettingResponse:
        """Run one operation in a single transaction.

        The setting write and its `AuditLog` insert share this transaction, so a
        failed audit insert rolls the setting change back and leaves the previous
        value, timestamp, and row presence exactly as they were.
        """
        try:
            with session(self.config) as connection:
                return operation(connection)
        except SettingsNotInitializedError:
            raise
        except Exception as failure:
            raise TaxRateSettingPersistenceError(
                "Не удалось сохранить налоговую ставку вместе с записью в истории действий."
            ) from failure

    def _state_response(self, setting: AppSetting | None) -> TaxRateSettingResponse:
        if setting is None:
            return self._response(None, None, UNCONFIGURED_MESSAGE)
        return self._response(_stored_percent(setting), _api_timestamp(setting.updated_at), CONFIGURED_MESSAGE)

    def _response(self, percent: str | None, effective_at: str | None, message: str) -> TaxRateSettingResponse:
        return TaxRateSettingResponse(
            tax_rate_percent=percent,
            is_configured=percent is not None,
            effective_at=effective_at,
            message=message,
        )


def _stored_percent(setting: AppSetting | None) -> str | None:
    """Return the canonical stored percentage without inventing a value."""
    if setting is None:
        return None
    text = (setting.value or "").strip()
    if not text:
        return text
    try:
        return canonical_tax_rate_percent(parse_tax_rate_percent(text))
    except Exception:
        return text


def _parse_storage_timestamp(stored: str | None) -> datetime | None:
    if not stored:
        return None
    text = stored.strip().replace("T", " ").removesuffix("Z")
    try:
        return datetime.strptime(text, STORAGE_TIMESTAMP_FORMAT)
    except ValueError:
        try:
            return datetime.fromisoformat(text).replace(tzinfo=None, microsecond=0)
        except ValueError:
            return None


def _api_timestamp(stored: str | None) -> str | None:
    """Normalize the stored SQLite UTC text into the ISO-8601 UTC API form."""
    parsed = _parse_storage_timestamp(stored)
    return parsed.strftime(API_TIMESTAMP_FORMAT) if parsed else None
