MIGRATION_ID = "0013_production_batches"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS production_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL UNIQUE,
            recipe_version_id INTEGER,
            client_recipe_id INTEGER,
            final_batch_value TEXT NOT NULL,
            final_batch_unit TEXT NOT NULL,
            component_cost TEXT,
            packaging_cost TEXT,
            other_cost TEXT NOT NULL DEFAULT '0.00',
            total_cost TEXT,
            sale_price TEXT,
            tax TEXT,
            margin TEXT,
            margin_percent TEXT,
            produced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (recipe_version_id) REFERENCES recipe_versions(id),
            FOREIGN KEY (client_recipe_id) REFERENCES client_recipes(id),
            CHECK (order_id > 0),
            CHECK ((recipe_version_id IS NOT NULL AND client_recipe_id IS NULL) OR (recipe_version_id IS NULL AND client_recipe_id IS NOT NULL)),
            CHECK (final_batch_unit IN ('g', 'ml', 'pcs'))
        );

        CREATE TABLE IF NOT EXISTS production_batch_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            production_batch_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            ingredient_lot_id INTEGER NOT NULL,
            ingredient_name_snapshot TEXT NOT NULL,
            lot_code_snapshot TEXT NOT NULL DEFAULT '',
            required_quantity TEXT NOT NULL,
            consumed_quantity TEXT NOT NULL,
            unit TEXT NOT NULL,
            unit_cost_snapshot TEXT,
            total_cost_snapshot TEXT,
            expiration_date_snapshot TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (production_batch_id) REFERENCES production_batches(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
            FOREIGN KEY (ingredient_lot_id) REFERENCES ingredient_lots(id),
            CHECK (production_batch_id > 0),
            CHECK (ingredient_id > 0),
            CHECK (ingredient_lot_id > 0),
            CHECK (unit IN ('g', 'ml', 'pcs'))
        );

        CREATE TABLE IF NOT EXISTS production_batch_packaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            production_batch_id INTEGER NOT NULL,
            packaging_item_id INTEGER NOT NULL,
            packaging_name_snapshot TEXT NOT NULL,
            quantity TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'pcs',
            unit_cost_snapshot TEXT,
            total_cost_snapshot TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (production_batch_id) REFERENCES production_batches(id) ON DELETE CASCADE,
            FOREIGN KEY (packaging_item_id) REFERENCES packaging_items(id),
            CHECK (production_batch_id > 0),
            CHECK (packaging_item_id > 0),
            CHECK (unit = 'pcs')
        );

        CREATE INDEX IF NOT EXISTS idx_production_batch_ingredients_batch ON production_batch_ingredients(production_batch_id, id);
        CREATE INDEX IF NOT EXISTS idx_production_batch_packaging_batch ON production_batch_packaging(production_batch_id, id);
        """
    )
