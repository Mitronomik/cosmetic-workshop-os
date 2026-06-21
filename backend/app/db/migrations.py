from importlib import import_module

from app.db.config import DatabaseConfig
from app.db.connection import session

MIGRATION_MODULES = ["app.migrations.versions.0001_infrastructure"]
MIGRATION_TABLE = "schema_migrations"


def _ensure_migration_table(connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def applied_migration_ids(connection) -> set[str]:
    _ensure_migration_table(connection)
    rows = connection.execute(f"SELECT migration_id FROM {MIGRATION_TABLE}").fetchall()
    return {row["migration_id"] for row in rows}


def pending_migration_ids(config: DatabaseConfig | None = None) -> list[str]:
    expected = expected_migration_ids()
    if config is not None and not config.path.exists():
        return expected
    if config is None:
        from app.db.config import get_database_config

        resolved_config = get_database_config()
        if not resolved_config.path.exists():
            return expected
        config = resolved_config
    with session(config) as connection:
        table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (MIGRATION_TABLE,),
        ).fetchone()
        if table_exists is None:
            return expected
        existing = applied_migration_ids(connection)
    return [migration_id for migration_id in expected if migration_id not in existing]


def apply_migrations(config: DatabaseConfig | None = None) -> list[str]:
    applied: list[str] = []
    with session(config) as connection:
        _ensure_migration_table(connection)
        existing = applied_migration_ids(connection)
        for module_name in MIGRATION_MODULES:
            migration = import_module(module_name)
            migration_id = migration.MIGRATION_ID
            if migration_id in existing:
                continue
            migration.upgrade(connection)
            connection.execute(
                f"INSERT INTO {MIGRATION_TABLE} (migration_id) VALUES (?)",
                (migration_id,),
            )
            applied.append(migration_id)
    return applied


def current_migrations(config: DatabaseConfig | None = None) -> set[str]:
    with session(config) as connection:
        return applied_migration_ids(connection)


def expected_migration_ids() -> list[str]:
    return [import_module(module_name).MIGRATION_ID for module_name in MIGRATION_MODULES]
