from app.db.config import DatabaseConfig
from app.db.connection import session
from app.db.migrations import expected_migration_ids

ALLOWED_INFRASTRUCTURE_TABLES = {"app_settings", "audit_logs", "schema_migrations", "sqlite_sequence"}


class DatabaseRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config

    def list_tables(self) -> list[str]:
        with session(self.config) as connection:
            rows = connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def status(self) -> dict[str, object]:
        tables = self.list_tables()
        return {
            "status": "ok",
            "database": "sqlite",
            "required_tables_present": all(
                table in tables for table in ("app_settings", "audit_logs", "schema_migrations")
            ),
            "migrations_expected": expected_migration_ids(),
            "tables": tables,
        }
