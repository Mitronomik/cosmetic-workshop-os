MIGRATION_ID = "0016_import_drafts"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS import_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            content_type TEXT NOT NULL DEFAULT '',
            file_extension TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            content_hash TEXT NOT NULL,
            target_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'uploaded',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (length(trim(original_filename)) > 0),
            CHECK (file_extension IN ('csv', 'xlsx')),
            CHECK (file_size_bytes >= 0),
            CHECK (length(trim(content_hash)) > 0),
            CHECK (target_type IN ('ingredients', 'packaging_items', 'clients', 'recipe_templates', 'ingredient_lots', 'orders')),
            CHECK (status IN ('uploaded', 'parsed', 'failed', 'cancelled'))
        );

        CREATE TABLE IF NOT EXISTS import_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES import_sources(id),
            target_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            row_count INTEGER NOT NULL DEFAULT 0,
            valid_row_count INTEGER NOT NULL DEFAULT 0,
            invalid_row_count INTEGER NOT NULL DEFAULT 0,
            warning_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            headers_json TEXT NOT NULL DEFAULT '[]',
            summary_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (target_type IN ('ingredients', 'packaging_items', 'clients', 'recipe_templates', 'ingredient_lots', 'orders')),
            CHECK (status IN ('draft', 'failed', 'cancelled')),
            CHECK (row_count >= 0),
            CHECK (valid_row_count >= 0),
            CHECK (invalid_row_count >= 0),
            CHECK (warning_count >= 0),
            CHECK (error_count >= 0)
        );

        CREATE TABLE IF NOT EXISTS import_draft_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL REFERENCES import_drafts(id),
            row_number INTEGER NOT NULL,
            raw_values_json TEXT NOT NULL DEFAULT '{}',
            normalized_values_json TEXT NOT NULL DEFAULT '{}',
            issues_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (row_number > 0),
            CHECK (status IN ('valid', 'warning', 'error'))
        );

        CREATE INDEX IF NOT EXISTS idx_import_sources_status_target ON import_sources(status, target_type, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_import_drafts_status_target ON import_drafts(status, target_type, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_import_draft_rows_draft_row ON import_draft_rows(draft_id, row_number, id);
        """
    )
