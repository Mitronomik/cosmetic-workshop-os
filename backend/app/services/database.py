from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.repositories.database import DatabaseRepository


def initialize_database(config: DatabaseConfig | None = None) -> list[str]:
    return apply_migrations(config)


def database_status(config: DatabaseConfig | None = None) -> dict[str, object]:
    initialize_database(config)
    return DatabaseRepository(config).status()
