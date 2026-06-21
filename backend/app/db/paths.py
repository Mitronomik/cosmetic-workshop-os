from dataclasses import dataclass
from pathlib import Path
import os
import platform

from app.db.config import DEFAULT_DATABASE_PATH

USER_DATA_DIR_ENV = "COSMETIC_WORKSHOP_USER_DATA_DIR"
USER_DOCUMENTS_DIRNAME = "Мастерская косметолога"
DATABASE_FILENAME = "cosmetic_workshop.sqlite"


@dataclass(frozen=True)
class UserDataPaths:
    base_dir: Path
    data_dir: Path
    database_path: Path
    backups_dir: Path
    exports_dir: Path
    attachments_dir: Path
    logs_dir: Path

    @property
    def required_directories(self) -> tuple[Path, ...]:
        return (
            self.base_dir,
            self.data_dir,
            self.backups_dir,
            self.exports_dir,
            self.attachments_dir,
            self.logs_dir,
        )


def default_user_data_base_dir(home: Path | None = None, system: str | None = None) -> Path:
    user_home = home or Path.home()
    current_system = system or platform.system()
    if current_system == "Windows":
        documents = user_home / "Documents"
    else:
        documents = user_home / "Documents"
    return documents / USER_DOCUMENTS_DIRNAME


def resolve_user_data_paths(base_dir: Path | None = None) -> UserDataPaths:
    configured_base_dir = os.environ.get(USER_DATA_DIR_ENV)
    resolved_base_dir = Path(configured_base_dir) if configured_base_dir else base_dir
    if resolved_base_dir is None:
        resolved_base_dir = default_user_data_base_dir()
    data_dir = resolved_base_dir / "data"
    return UserDataPaths(
        base_dir=resolved_base_dir,
        data_dir=data_dir,
        database_path=data_dir / DATABASE_FILENAME,
        backups_dir=resolved_base_dir / "backups",
        exports_dir=resolved_base_dir / "exports",
        attachments_dir=resolved_base_dir / "attachments",
        logs_dir=resolved_base_dir / "logs",
    )


def resolve_development_database_path() -> Path:
    return DEFAULT_DATABASE_PATH


def create_user_data_directories(paths: UserDataPaths) -> None:
    for directory in paths.required_directories:
        directory.mkdir(parents=True, exist_ok=True)
