from dataclasses import dataclass
from pathlib import Path
import os

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_PATH = REPOSITORY_ROOT / ".local" / "cosmetic_workshop.sqlite"
DATABASE_PATH_ENV = "COSMETIC_WORKSHOP_DB_PATH"


@dataclass(frozen=True)
class DatabaseConfig:
    path: Path

    @property
    def url(self) -> str:
        return f"sqlite:///{self.path}"


def get_database_config() -> DatabaseConfig:
    configured_path = os.environ.get(DATABASE_PATH_ENV)
    path = Path(configured_path) if configured_path else DEFAULT_DATABASE_PATH
    return DatabaseConfig(path=path)
