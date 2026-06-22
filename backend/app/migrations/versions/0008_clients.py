MIGRATION_ID = "0008_clients"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            birthday TEXT,
            skin_notes TEXT NOT NULL DEFAULT '',
            allergy_notes TEXT NOT NULL DEFAULT '',
            preference_notes TEXT NOT NULL DEFAULT '',
            contraindication_notes TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (full_name <> ''),
            CHECK (birthday IS NULL OR birthday <> ''),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_clients_active_name
            ON clients(is_active, full_name, id);
        """
    )
