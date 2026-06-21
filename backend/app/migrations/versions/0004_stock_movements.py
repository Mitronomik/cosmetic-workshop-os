MIGRATION_ID = "0004_stock_movements"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_lot_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity TEXT NOT NULL,
            unit TEXT NOT NULL,
            direction TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            note TEXT NOT NULL DEFAULT '',
            reference_type TEXT,
            reference_id TEXT,
            source TEXT NOT NULL DEFAULT 'manual',
            correction_of_movement_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingredient_lot_id) REFERENCES ingredient_lots(id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
            FOREIGN KEY (correction_of_movement_id) REFERENCES stock_movements(id),
            CHECK (ingredient_lot_id > 0),
            CHECK (ingredient_id > 0),
            CHECK (movement_type IN ('receipt', 'manual_adjustment_in', 'manual_adjustment_out', 'write_off', 'return_to_supplier')),
            CHECK (direction IN ('in', 'out')),
            CHECK (unit IN ('g', 'ml', 'pcs')),
            CHECK (quantity <> '')
        );

        CREATE INDEX IF NOT EXISTS idx_stock_movements_lot_created
            ON stock_movements(ingredient_lot_id, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_stock_movements_ingredient_created
            ON stock_movements(ingredient_id, created_at, id);
        """
    )
