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
                    SELECT key, value, value_type, description
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
            )
            for row in rows
        ]
