MIGRATION_ID = "0014_alerts"


def _add_column_if_missing(connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def upgrade(connection):
    _add_column_if_missing(connection, "ingredients", "minimum_stock", "TEXT")
    _add_column_if_missing(connection, "ingredients", "expiration_alert_days", "INTEGER")
    _add_column_if_missing(connection, "packaging_items", "minimum_stock", "TEXT")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_key TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            related_entity_type TEXT NOT NULL,
            related_entity_id INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            dismissed_at TEXT,
            CHECK (length(trim(alert_key)) > 0),
            CHECK (type IN ('low_ingredient_stock', 'low_packaging_stock', 'ingredient_expiration_soon', 'ingredient_expired', 'insufficient_materials_for_order', 'insufficient_packaging_for_order')),
            CHECK (severity IN ('info', 'warning', 'critical', 'blocking')),
            CHECK (status IN ('open', 'resolved', 'dismissed')),
            CHECK (related_entity_id > 0)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_alert_key ON alerts(alert_key);
        CREATE INDEX IF NOT EXISTS idx_alerts_status_type ON alerts(status, type, updated_at, id);
        """
    )
