MIGRATION_ID = "0003_ingredient_lots"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingredient_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER NOT NULL,
            lot_code TEXT NOT NULL DEFAULT '',
            supplier_name TEXT NOT NULL DEFAULT '',
            purchased_at TEXT,
            expires_at TEXT,
            unit TEXT NOT NULL,
            unit_cost TEXT,
            total_cost TEXT,
            density_g_per_ml TEXT,
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
            CHECK (ingredient_id > 0),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_ingredient_lots_active
            ON ingredient_lots(is_active, id);
        CREATE INDEX IF NOT EXISTS idx_ingredient_lots_ingredient_active
            ON ingredient_lots(ingredient_id, is_active, id);
        CREATE INDEX IF NOT EXISTS idx_ingredient_lots_expires_at
            ON ingredient_lots(expires_at);
        """
    )
