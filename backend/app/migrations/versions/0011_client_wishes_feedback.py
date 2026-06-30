MIGRATION_ID = "0011_client_wishes_feedback"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS client_wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            client_recipe_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'other',
            priority TEXT NOT NULL DEFAULT 'normal',
            status TEXT NOT NULL DEFAULT 'open',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (client_recipe_id) REFERENCES client_recipes(id),
            CHECK (client_id > 0),
            CHECK (client_recipe_id IS NULL OR client_recipe_id > 0),
            CHECK (length(trim(title)) > 0),
            CHECK (category IN ('texture', 'scent', 'packaging', 'ingredient', 'allergy', 'contraindication', 'effect', 'price', 'other')),
            CHECK (priority IN ('low', 'normal', 'high')),
            CHECK (status IN ('open', 'planned', 'resolved', 'archived')),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_client_wishes_client_active
            ON client_wishes(client_id, is_active, updated_at, id);
        CREATE INDEX IF NOT EXISTS idx_client_wishes_recipe
            ON client_wishes(client_recipe_id, id);

        CREATE TABLE IF NOT EXISTS client_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            client_recipe_id INTEGER,
            feedback_type TEXT NOT NULL DEFAULT 'note',
            sentiment TEXT NOT NULL DEFAULT 'neutral',
            rating INTEGER,
            text TEXT NOT NULL,
            follow_up_needed INTEGER NOT NULL DEFAULT 0,
            follow_up_note TEXT NOT NULL DEFAULT '',
            occurred_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (client_recipe_id) REFERENCES client_recipes(id),
            CHECK (client_id > 0),
            CHECK (client_recipe_id IS NULL OR client_recipe_id > 0),
            CHECK (feedback_type IN ('note', 'reaction', 'texture', 'scent', 'effect', 'packaging', 'request', 'other')),
            CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed')),
            CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
            CHECK (length(trim(text)) > 0),
            CHECK (follow_up_needed IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_client_feedback_client
            ON client_feedback(client_id, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_client_feedback_recipe
            ON client_feedback(client_recipe_id, id);
        """
    )
