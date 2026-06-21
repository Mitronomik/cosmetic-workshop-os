from app.db.config import DatabaseConfig
from app.models.settings import AppSetting
from app.repositories.settings import SettingsRepository


def read_app_settings(config: DatabaseConfig | None = None) -> list[AppSetting]:
    return SettingsRepository(config).list_settings()
