MIGRATION_ID = "0012_orders"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            recipe_version_id INTEGER,
            client_recipe_id INTEGER,
            product_name TEXT NOT NULL,
            target_batch_size_value TEXT NOT NULL,
            target_batch_size_unit TEXT NOT NULL,
            packaging_item_id INTEGER,
            packaging_quantity TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            sale_price TEXT,
            ordered_at TEXT,
            planned_production_at TEXT,
            produced_at TEXT,
            delivered_at TEXT,
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (recipe_version_id) REFERENCES recipe_versions(id),
            FOREIGN KEY (client_recipe_id) REFERENCES client_recipes(id),
            FOREIGN KEY (packaging_item_id) REFERENCES packaging_items(id),
            CHECK (client_id > 0),
            CHECK ((recipe_version_id IS NOT NULL AND client_recipe_id IS NULL) OR (recipe_version_id IS NULL AND client_recipe_id IS NOT NULL)),
            CHECK (recipe_version_id IS NULL OR recipe_version_id > 0),
            CHECK (client_recipe_id IS NULL OR client_recipe_id > 0),
            CHECK (length(trim(target_batch_size_value)) > 0),
            CHECK (target_batch_size_unit IN ('g', 'ml', 'pcs')),
            CHECK (packaging_item_id IS NULL OR packaging_item_id > 0),
            CHECK (packaging_quantity IS NULL OR length(trim(packaging_quantity)) > 0),
            CHECK (status IN ('new', 'waiting_for_materials', 'ready_to_produce', 'in_progress', 'produced', 'delivered', 'cancelled', 'archived')),
            CHECK (is_active IN (0, 1))
        );
        CREATE INDEX IF NOT EXISTS idx_orders_client_active ON orders(client_id, is_active, updated_at, id);
        CREATE INDEX IF NOT EXISTS idx_orders_status_active ON orders(status, is_active, updated_at, id);
        CREATE INDEX IF NOT EXISTS idx_orders_recipe_version ON orders(recipe_version_id, id);
        CREATE INDEX IF NOT EXISTS idx_orders_client_recipe ON orders(client_recipe_id, id);
        CREATE INDEX IF NOT EXISTS idx_orders_packaging_item ON orders(packaging_item_id, id);
        """
    )
