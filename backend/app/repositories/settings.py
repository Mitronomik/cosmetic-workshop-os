import sqlite3
from contextlib import nullcontext

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.models.settings import AppSetting


class SettingsNotInitializedError(RuntimeError):
    pass


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    """Reuse a caller-owned connection, or open and commit an own session."""
    return nullcontext(connection) if connection is not None else session(config)


class SettingsRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def list_settings(self) -> list[AppSetting]:
        if not self.config.path.exists():
            raise SettingsNotInitializedError("Database settings are not initialized yet.")
        with session(self.config) as connection:
            try:
                rows = connection.execute(
                    """
                    SELECT key, value, value_type, description, updated_at
                    FROM app_settings
                    ORDER BY key
                    """
                ).fetchall()
            except Exception as exc:
                raise SettingsNotInitializedError("Database settings are not initialized yet.") from exc
        return [
            AppSetting(
                key=row["key"],
                value=row["value"],
                value_type=row["value_type"],
                description=row["description"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_setting(self, key: str, connection: sqlite3.Connection | None = None) -> AppSetting | None:
        if connection is None and not self.config.path.exists():
            raise SettingsNotInitializedError("Database settings are not initialized yet.")
        with _connection_scope(self.config, connection) as connection:
            try:
                row = connection.execute(
                    """
                    SELECT key, value, value_type, description, updated_at
                    FROM app_settings
                    WHERE key = ?
                    """,
                    (key,),
                ).fetchone()
            except Exception as exc:
                raise SettingsNotInitializedError("Database settings are not initialized yet.") from exc
        if row is None:
            return None
        return AppSetting(key=row["key"], value=row["value"], value_type=row["value_type"], description=row["description"], updated_at=row["updated_at"])

    def upsert_setting(
        self,
        key: str,
        value: str,
        value_type: str,
        description: str,
        connection: sqlite3.Connection | None = None,
        updated_at: str | None = None,
    ) -> None:
        """Insert or update one settings row.

        ``updated_at`` is optional: when omitted the column keeps its existing
        ``CURRENT_TIMESTAMP`` behavior, and when supplied the caller owns the
        stored ``YYYY-MM-DD HH:MM:SS`` UTC value.
        """
        if connection is None and not self.config.path.exists():
            raise SettingsNotInitializedError("Database settings are not initialized yet.")
        with _connection_scope(self.config, connection) as connection:
            try:
                if updated_at is None:
                    connection.execute(
                        """
                        INSERT INTO app_settings (key, value, value_type, description)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET
                            value = excluded.value,
                            value_type = excluded.value_type,
                            description = excluded.description,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (key, value, value_type, description),
                    )
                else:
                    connection.execute(
                        """
                        INSERT INTO app_settings (key, value, value_type, description, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET
                            value = excluded.value,
                            value_type = excluded.value_type,
                            description = excluded.description,
                            updated_at = excluded.updated_at
                        """,
                        (key, value, value_type, description, updated_at),
                    )
            except Exception as exc:
                raise SettingsNotInitializedError("Database settings are not initialized yet.") from exc

    def delete_setting(self, key: str, connection: sqlite3.Connection | None = None) -> bool:
        """Delete exactly one settings row by key and report whether it existed."""
        if connection is None and not self.config.path.exists():
            raise SettingsNotInitializedError("Database settings are not initialized yet.")
        with _connection_scope(self.config, connection) as connection:
            try:
                cursor = connection.execute("DELETE FROM app_settings WHERE key = ?", (key,))
            except Exception as exc:
                raise SettingsNotInitializedError("Database settings are not initialized yet.") from exc
            return cursor.rowcount > 0
