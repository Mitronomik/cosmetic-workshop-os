MIGRATION_ID = "0001_infrastructure"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            value_type TEXT NOT NULL DEFAULT 'string',
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actor_type TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            summary TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
            ON audit_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
            ON audit_logs(entity_type, entity_id);
        """
    )
    defaults = [
        ("app.version", "0.1.0", "string", "Application version placeholder."),
        ("product.name", "Мастерская косметолога", "string", "Human-facing product name."),
        ("mode.local_first", "true", "boolean", "Local-first mode flag."),
        ("currency.default", "RUB", "string", "Default currency placeholder."),
        ("tax.default_rate", "0.06", "decimal_string", "Default tax rate placeholder."),
        ("units.default_system", "metric", "string", "Default unit system placeholder."),
    ]
    connection.executemany(
        """
        INSERT INTO app_settings (key, value, value_type, description)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO NOTHING
        """,
        defaults,
    )
