from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.db.migrations import expected_migration_ids

ALLOWED_INFRASTRUCTURE_TABLES = {"app_settings", "audit_logs", "schema_migrations", "sqlite_sequence"}
ALLOWED_CURRENT_TABLES = ALLOWED_INFRASTRUCTURE_TABLES | {
    "ingredients",
    "ingredient_lots",
    "stock_movements",
}
FORBIDDEN_FUTURE_TABLES = {
    "packaging_items",
    "recipes",
    "recipe_versions",
    "recipe_ingredients",
    "client_recipes",
    "client_recipe_ingredients",
    "clients",
    "client_wishes",
    "client_feedback",
    "orders",
    "production_batches",
    "import_sources",
    "import_drafts",
    "backup_records",
}
REQUIRED_INFRASTRUCTURE_TABLES = ("app_settings", "audit_logs", "schema_migrations")


class DatabaseRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def list_tables(self) -> list[str]:
        if not self.config.path.exists():
            return []
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
        database_exists = self.config.path.exists()
        tables = self.list_tables() if database_exists else []
        required_tables_present = all(table in tables for table in REQUIRED_INFRASTRUCTURE_TABLES)
        return {
            "status": "ok" if required_tables_present else "not_initialized",
            "database": "sqlite",
            "database_exists": database_exists,
            "required_tables_present": required_tables_present,
            "migrations_expected": expected_migration_ids(),
            "tables": tables,
        }
