MIGRATION_ID = "0009_client_recipes"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS client_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            source_recipe_version_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            target_batch_size_value TEXT,
            target_batch_size_unit TEXT,
            personalization_notes TEXT NOT NULL DEFAULT '',
            allergy_notes TEXT NOT NULL DEFAULT '',
            preference_notes TEXT NOT NULL DEFAULT '',
            contraindication_notes TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (source_recipe_version_id) REFERENCES recipe_versions(id),
            CHECK (client_id > 0),
            CHECK (source_recipe_version_id > 0),
            CHECK (title <> ''),
            CHECK (status IN ('draft', 'active', 'archived')),
            CHECK (target_batch_size_value IS NULL OR target_batch_size_value <> ''),
            CHECK (target_batch_size_unit IS NULL OR target_batch_size_unit IN ('g', 'ml', 'pcs')),
            CHECK ((target_batch_size_value IS NULL AND target_batch_size_unit IS NULL) OR (target_batch_size_value IS NOT NULL AND target_batch_size_unit IS NOT NULL)),
            CHECK (is_active IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS client_recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_recipe_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            source_recipe_ingredient_id INTEGER,
            position INTEGER NOT NULL,
            phase TEXT NOT NULL DEFAULT '',
            amount_value TEXT NOT NULL,
            amount_unit TEXT NOT NULL,
            personalization_note TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_recipe_id) REFERENCES client_recipes(id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
            FOREIGN KEY (source_recipe_ingredient_id) REFERENCES recipe_ingredients(id),
            CHECK (client_recipe_id > 0),
            CHECK (ingredient_id > 0),
            CHECK (source_recipe_ingredient_id IS NULL OR source_recipe_ingredient_id > 0),
            CHECK (position > 0),
            CHECK (amount_value <> ''),
            CHECK (amount_unit IN ('g', 'ml', 'percent', 'pcs'))
        );

        CREATE INDEX IF NOT EXISTS idx_client_recipes_client
            ON client_recipes(client_id, is_active, status, id);
        CREATE INDEX IF NOT EXISTS idx_client_recipe_ingredients_recipe
            ON client_recipe_ingredients(client_recipe_id, position, id);
        """
    )
