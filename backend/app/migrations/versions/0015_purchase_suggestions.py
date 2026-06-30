MIGRATION_ID = "0015_purchase_suggestions"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS purchase_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_key TEXT NOT NULL UNIQUE,
            item_type TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            item_name_snapshot TEXT NOT NULL,
            recommended_quantity TEXT NOT NULL,
            unit TEXT NOT NULL,
            reason TEXT NOT NULL,
            source_entity_type TEXT NOT NULL,
            source_entity_id INTEGER,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            CHECK (length(trim(suggestion_key)) > 0),
            CHECK (item_type IN ('ingredient', 'packaging')),
            CHECK (item_id > 0),
            CHECK (length(trim(item_name_snapshot)) > 0),
            CHECK (CAST(recommended_quantity AS NUMERIC) > 0),
            CHECK (length(trim(unit)) > 0),
            CHECK (reason IN ('below_minimum_stock', 'insufficient_for_order', 'predicted_shortage', 'expiration_replacement', 'manual')),
            CHECK (length(trim(source_entity_type)) > 0),
            CHECK (source_entity_id IS NULL OR source_entity_id > 0),
            CHECK (length(trim(message)) > 0),
            CHECK (status IN ('open', 'purchased', 'dismissed', 'archived'))
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_purchase_suggestions_key ON purchase_suggestions(suggestion_key);
        CREATE INDEX IF NOT EXISTS idx_purchase_suggestions_status_reason ON purchase_suggestions(status, reason, updated_at, id);
        CREATE INDEX IF NOT EXISTS idx_purchase_suggestions_item ON purchase_suggestions(item_type, item_id, status);
        """
    )
