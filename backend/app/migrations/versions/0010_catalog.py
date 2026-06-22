MIGRATION_ID = "0010_catalog"


def _column_exists(connection, table: str, column: str) -> bool:
    return any(
        row["name"] == column
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    )


def upgrade(connection):
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS catalog_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            parent_id INTEGER,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_system INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES catalog_categories(id),
            UNIQUE(scope, slug),
            CHECK (scope IN ('ingredient', 'packaging', 'recipe')),
            CHECK (length(trim(name)) > 0),
            CHECK (slug <> ''),
            CHECK (is_system IN (0, 1)),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_catalog_categories_scope_active_sort
            ON catalog_categories(scope, is_active, sort_order, name, id);

        CREATE TABLE IF NOT EXISTS catalog_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(scope, slug),
            CHECK (scope IN ('ingredient', 'packaging', 'recipe')),
            CHECK (length(trim(name)) > 0),
            CHECK (slug <> ''),
            CHECK (is_active IN (0, 1))
        );

        CREATE INDEX IF NOT EXISTS idx_catalog_tags_scope_active_name
            ON catalog_tags(scope, is_active, name, id);

        CREATE TABLE IF NOT EXISTS ingredient_catalog_tags (
            ingredient_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ingredient_id, tag_id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
            FOREIGN KEY (tag_id) REFERENCES catalog_tags(id)
        );

        CREATE TABLE IF NOT EXISTS packaging_item_catalog_tags (
            packaging_item_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (packaging_item_id, tag_id),
            FOREIGN KEY (packaging_item_id) REFERENCES packaging_items(id),
            FOREIGN KEY (tag_id) REFERENCES catalog_tags(id)
        );

        CREATE TABLE IF NOT EXISTS recipe_template_catalog_tags (
            recipe_template_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (recipe_template_id, tag_id),
            FOREIGN KEY (recipe_template_id) REFERENCES recipe_templates(id),
            FOREIGN KEY (tag_id) REFERENCES catalog_tags(id)
        );
        """)
    for table in ("ingredients", "packaging_items", "recipe_templates"):
        if not _column_exists(connection, table, "catalog_category_id"):
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN catalog_category_id INTEGER"
            )
