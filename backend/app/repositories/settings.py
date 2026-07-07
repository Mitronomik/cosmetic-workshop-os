from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.models.settings import AppSetting


class SettingsNotInitializedError(RuntimeError):
    pass


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

    def get_setting(self, key: str) -> AppSetting | None:
        if not self.config.path.exists():
            raise SettingsNotInitializedError("Database settings are not initialized yet.")
        with session(self.config) as connection:
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

    def upsert_setting(self, key: str, value: str, value_type: str, description: str) -> None:
        if not self.config.path.exists():
            raise SettingsNotInitializedError("Database settings are not initialized yet.")
        with session(self.config) as connection:
            try:
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
            except Exception as exc:
                raise SettingsNotInitializedError("Database settings are not initialized yet.") from exc
