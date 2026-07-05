MIGRATION_ID = "0017_import_apply_status"


def _rebuild_import_sources(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS import_sources_new (
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
            CHECK (status IN ('uploaded', 'parsed', 'failed', 'cancelled', 'applied'))
        );
        INSERT INTO import_sources_new (id, original_filename, content_type, file_extension, file_size_bytes, content_hash, target_type, status, created_at, updated_at)
            SELECT id, original_filename, content_type, file_extension, file_size_bytes, content_hash, target_type, status, created_at, updated_at FROM import_sources;
        DROP TABLE import_sources;
        ALTER TABLE import_sources_new RENAME TO import_sources;
        CREATE INDEX IF NOT EXISTS idx_import_sources_status_target ON import_sources(status, target_type, created_at, id);
        """
    )


def _rebuild_import_drafts(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS import_drafts_new (
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
            CHECK (status IN ('draft', 'failed', 'cancelled', 'applied')),
            CHECK (row_count >= 0),
            CHECK (valid_row_count >= 0),
            CHECK (invalid_row_count >= 0),
            CHECK (warning_count >= 0),
            CHECK (error_count >= 0)
        );
        INSERT INTO import_drafts_new (id, source_id, target_type, status, row_count, valid_row_count, invalid_row_count, warning_count, error_count, headers_json, summary_json, created_at, updated_at)
            SELECT id, source_id, target_type, status, row_count, valid_row_count, invalid_row_count, warning_count, error_count, headers_json, summary_json, created_at, updated_at FROM import_drafts;
        DROP TABLE import_drafts;
        ALTER TABLE import_drafts_new RENAME TO import_drafts;
        CREATE INDEX IF NOT EXISTS idx_import_drafts_status_target ON import_drafts(status, target_type, created_at, id);
        """
    )


def upgrade(connection):
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        _rebuild_import_sources(connection)
        _rebuild_import_drafts(connection)
    finally:
        connection.execute("PRAGMA foreign_keys = ON")
