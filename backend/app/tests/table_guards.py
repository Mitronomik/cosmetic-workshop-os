CURRENT_ALLOWED_TABLES = {
    "schema_migrations",
    "app_settings",
    "audit_logs",
    "ingredients",
    "ingredient_lots",
    "stock_movements",
    "packaging_items",
    "packaging_stock_movements",
    "recipe_templates",
    "recipe_versions",
    "recipe_ingredients",
    "clients",
    "sqlite_sequence",
}

FORBIDDEN_FUTURE_TABLES = {
    "recipes",
    "client_recipes",
    "client_recipe_ingredients",
    "client_wishes",
    "client_feedback",
    "orders",
    "production_batches",
    "import_sources",
    "import_drafts",
    "backup_records",
}


def assert_only_current_tables(tables: set[str]) -> None:
    assert tables <= CURRENT_ALLOWED_TABLES


def assert_no_forbidden_future_tables(tables: set[str]) -> None:
    assert not FORBIDDEN_FUTURE_TABLES & tables
