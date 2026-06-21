MIGRATION_ID = "0006_packaging_stock_movements"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS packaging_stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            packaging_item_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'pcs',
            direction TEXT NOT NULL,
            occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reason TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'manual',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (packaging_item_id) REFERENCES packaging_items(id),
            CHECK (movement_type IN ('receipt', 'manual_adjustment_in', 'manual_adjustment_out', 'write_off', 'return_to_supplier')),
            CHECK (quantity <> ''),
            CHECK (unit = 'pcs'),
            CHECK (direction IN ('in', 'out'))
        );

        CREATE INDEX IF NOT EXISTS idx_packaging_stock_movements_item_created
            ON packaging_stock_movements(packaging_item_id, created_at, id);
        """
    )
