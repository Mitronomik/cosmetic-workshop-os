from app.db.config import DatabaseConfig
from app.models.settings import AppSetting
from app.repositories.settings import SettingsRepository
from app.services.database import initialize_database


def read_app_settings(config: DatabaseConfig | None = None) -> list[AppSetting]:
    initialize_database(config)
    return SettingsRepository(config).list_settings()
