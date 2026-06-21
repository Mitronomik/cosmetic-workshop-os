from app.db.config import DatabaseConfig
from app.db.connection import session
from app.models.settings import AppSetting


class SettingsRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config

    def list_settings(self) -> list[AppSetting]:
        with session(self.config) as connection:
            rows = connection.execute(
                """
                SELECT key, value, value_type, description
                FROM app_settings
                ORDER BY key
                """
            ).fetchall()
        return [
            AppSetting(
                key=row["key"],
                value=row["value"],
                value_type=row["value_type"],
                description=row["description"],
            )
            for row in rows
        ]
