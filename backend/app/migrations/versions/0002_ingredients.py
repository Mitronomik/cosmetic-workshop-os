MIGRATION_ID = "0002_ingredients"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            default_unit TEXT NOT NULL,
            density_g_per_ml TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            notes TEXT NOT NULL DEFAULT '',
            inci_name TEXT NOT NULL DEFAULT '',
            supplier_hint TEXT NOT NULL DEFAULT '',
            allergen_note TEXT NOT NULL DEFAULT '',
            usage_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (length(trim(name)) > 0),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_ingredients_active_name
            ON ingredients(is_active, name);
        CREATE INDEX IF NOT EXISTS idx_ingredients_category
            ON ingredients(category);
        """
    )
