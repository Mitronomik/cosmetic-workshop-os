MIGRATION_ID = "0007_recipes"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS recipe_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            product_type TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (name <> ''),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_recipe_templates_active_name
            ON recipe_templates(is_active, name, id);

        CREATE TABLE IF NOT EXISTS recipe_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_template_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            title TEXT NOT NULL DEFAULT '',
            target_batch_size_value TEXT,
            target_batch_size_unit TEXT,
            notes TEXT NOT NULL DEFAULT '',
            change_note TEXT NOT NULL DEFAULT '',
            created_from_version_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_template_id) REFERENCES recipe_templates(id),
            FOREIGN KEY (created_from_version_id) REFERENCES recipe_versions(id),
            UNIQUE (recipe_template_id, version_number),
            CHECK (version_number > 0),
            CHECK (status IN ('draft', 'active', 'archived')),
            CHECK (target_batch_size_unit IS NULL OR target_batch_size_unit IN ('g', 'ml', 'pcs')),
            CHECK ((target_batch_size_value IS NULL AND target_batch_size_unit IS NULL) OR (target_batch_size_value IS NOT NULL AND target_batch_size_unit IS NOT NULL))
        );

        CREATE INDEX IF NOT EXISTS idx_recipe_versions_template_version
            ON recipe_versions(recipe_template_id, version_number, id);

        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_version_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            phase TEXT NOT NULL DEFAULT '',
            amount_value TEXT NOT NULL,
            amount_unit TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_version_id) REFERENCES recipe_versions(id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
            CHECK (position > 0),
            CHECK (amount_value <> ''),
            CHECK (amount_unit IN ('g', 'ml', 'percent', 'pcs'))
        );

        CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_version_position
            ON recipe_ingredients(recipe_version_id, position, id);
        """
    )
