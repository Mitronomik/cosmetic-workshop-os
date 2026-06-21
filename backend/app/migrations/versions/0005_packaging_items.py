MIGRATION_ID = "0005_packaging_items"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS packaging_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'pcs',
            capacity_value TEXT,
            capacity_unit TEXT,
            material TEXT NOT NULL DEFAULT '',
            supplier_hint TEXT NOT NULL DEFAULT '',
            unit_cost TEXT,
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (name <> ''),
            CHECK (kind IN ('jar', 'bottle', 'tube', 'pump', 'cap', 'dropper', 'label', 'box', 'bag', 'other')),
            CHECK (unit = 'pcs'),
            CHECK (capacity_unit IS NULL OR capacity_unit IN ('ml', 'g')),
            CHECK ((capacity_value IS NULL AND capacity_unit IS NULL) OR (capacity_value IS NOT NULL AND capacity_unit IS NOT NULL)),
            CHECK (unit_cost IS NULL OR unit_cost <> ''),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_packaging_items_active_name
            ON packaging_items(is_active, name, id);
        """
    )
