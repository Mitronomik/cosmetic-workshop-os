from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import UserDataPaths, create_user_data_directories, resolve_user_data_paths
from app.services.database import initialize_database

StartupMode = Literal["development", "user"]


@dataclass(frozen=True)
class StartupInitializationResult:
    mode: StartupMode
    database_path: Path
    user_data_paths: UserDataPaths | None
    applied_migrations: list[str]


def startup_database_config(mode: StartupMode = "development") -> DatabaseConfig:
    if mode == "user":
        return DatabaseConfig(path=resolve_user_data_paths().database_path)
    return get_database_config()


def initialize_startup(mode: StartupMode = "development") -> StartupInitializationResult:
    user_data_paths = resolve_user_data_paths() if mode == "user" else None
    if user_data_paths is not None:
        create_user_data_directories(user_data_paths)
        config = DatabaseConfig(path=user_data_paths.database_path)
    else:
        config = get_database_config()
    applied_migrations = initialize_database(config)
    return StartupInitializationResult(
        mode=mode,
        database_path=config.path,
        user_data_paths=user_data_paths,
        applied_migrations=applied_migrations,
    )
