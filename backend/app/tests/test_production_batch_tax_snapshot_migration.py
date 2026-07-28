"""Migration `0019` and its backup-before-migration contract.

`C2-II` adds two nullable columns to an existing local user database. The risk
is not the schema change; it is doing it to a real user's only copy of their
data. These tests prove the existing user-mode startup flow still creates a
`before_migration` backup first, that the backup holds the pre-migration state,
that a failed migration destroys neither, and that no real user path is ever
touched.
"""

from pathlib import Path
import sqlite3

import pytest

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids, pending_migration_ids
from app.db.paths import USER_DATA_DIR_ENV
from app.services.database import initialize_database
from app.services.startup import initialize_startup

MIGRATION_ID = "0019_production_batch_tax_rate_snapshots"
SNAPSHOT_COLUMNS = ("tax_rate_percent_snapshot", "tax_rate_effective_at_snapshot")
PREVIOUS_MIGRATION_ID = "0018_demo_data_tracking"


def columns(database_path: Path, table: str = "production_batches") -> dict[str, sqlite3.Row]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        return {row["name"]: row for row in connection.execute(f"PRAGMA table_info({table})")}


def applied(database_path: Path) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        return [row[0] for row in connection.execute("SELECT migration_id FROM schema_migrations ORDER BY migration_id")]


def build_pre_c2_ii_database(database_path: Path) -> dict[str, object]:
    """Create a database at exactly the 0018 level, with representative data.

    The migration list is truncated rather than the schema hand-written, so the
    starting point is genuinely the previous release's schema.
    """
    database_path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = [name for name in original if not name.endswith(MIGRATION_ID)]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original
    with sqlite3.connect(database_path) as connection:
        connection.execute("INSERT INTO clients (full_name) VALUES ('Историческая клиентка')")
        connection.execute("INSERT INTO recipe_templates (name) VALUES ('Историческая база')")
        connection.execute("INSERT INTO recipe_versions (recipe_template_id, version_number, title) VALUES (1, 1, 'v1')")
        connection.execute("INSERT INTO packaging_items (name, kind, unit, unit_cost) VALUES ('Банка', 'jar', 'pcs', '10.00')")
        connection.execute(
            "INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, packaging_item_id, packaging_quantity, status, sale_price)"
            " VALUES (1, 1, 'Исторический крем', '50', 'g', 1, '1', 'produced', '200.00')"
        )
        connection.execute(
            "INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, component_cost, packaging_cost, other_cost, total_cost, sale_price, notes)"
            " VALUES (1, 1, '50', 'g', '100.00', '10.00', '0.00', '110.00', '200.00', 'историческая партия')"
        )
    return snapshot(database_path)


def snapshot(database_path: Path) -> dict[str, object]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        return {
            "batches": [dict(row) for row in connection.execute("SELECT id, order_id, component_cost, packaging_cost, other_cost, total_cost, sale_price, tax, margin, margin_percent, notes FROM production_batches ORDER BY id")],
            "orders": [dict(row) for row in connection.execute("SELECT * FROM orders ORDER BY id")],
            "clients": [dict(row) for row in connection.execute("SELECT * FROM clients ORDER BY id")],
            "packaging_items": [dict(row) for row in connection.execute("SELECT * FROM packaging_items ORDER BY id")],
        }


def test_fresh_database_gets_both_columns_nullable_and_without_defaults(tmp_path):
    database_path = tmp_path / "fresh.sqlite"

    initialize_database(DatabaseConfig(path=database_path))

    table = columns(database_path)
    for column in SNAPSHOT_COLUMNS:
        assert column in table
        assert table[column]["type"] == "TEXT"
        assert table[column]["notnull"] == 0
        assert table[column]["dflt_value"] is None
    assert MIGRATION_ID in applied(database_path)


def test_migration_0019_is_registered_last_in_the_existing_ordering():
    ids = expected_migration_ids()

    assert ids[-1] == MIGRATION_ID
    assert ids[-2] == PREVIOUS_MIGRATION_ID
    assert ids.count(MIGRATION_ID) == 1


def test_a_database_at_0018_reports_exactly_one_pending_migration(tmp_path):
    database_path = tmp_path / "existing.sqlite"
    build_pre_c2_ii_database(database_path)

    assert pending_migration_ids(DatabaseConfig(path=database_path)) == [MIGRATION_ID]


def test_upgrading_from_0018_adds_the_columns_and_preserves_every_existing_value(tmp_path):
    database_path = tmp_path / "existing.sqlite"
    before = build_pre_c2_ii_database(database_path)
    assert not set(SNAPSHOT_COLUMNS) & set(columns(database_path))

    initialize_database(DatabaseConfig(path=database_path))

    after = snapshot(database_path)
    assert after == before
    assert set(SNAPSHOT_COLUMNS) <= set(columns(database_path))
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(f"SELECT {', '.join(SNAPSHOT_COLUMNS)} FROM production_batches WHERE id = 1").fetchone()
    assert row == (None, None)


def test_the_migration_applies_once_and_is_not_reapplied(tmp_path):
    database_path = tmp_path / "existing.sqlite"
    build_pre_c2_ii_database(database_path)
    config = DatabaseConfig(path=database_path)

    first = apply_migrations(config)
    second = apply_migrations(config)

    assert first == [MIGRATION_ID]
    assert second == []
    assert applied(database_path).count(MIGRATION_ID) == 1
    assert pending_migration_ids(config) == []


def test_no_extra_snapshot_columns_and_no_new_table_are_introduced(tmp_path):
    database_path = tmp_path / "fresh.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    table = set(columns(database_path))
    with sqlite3.connect(database_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert not {"sale_price_snapshot", "total_cost_snapshot", "tax_amount_snapshot", "margin_amount_snapshot", "taxable_amount_snapshot"} & table
    assert not {"tax_rate_history", "tax_rate_versions", "tax_periods", "scheduled_tax_rates"} & tables


def test_user_mode_startup_backs_up_before_applying_0019(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    before = build_pre_c2_ii_database(database_path)

    result = initialize_startup("user")

    assert result.applied_migrations == [MIGRATION_ID]
    assert result.backup is not None
    assert result.backup.reason == "before_migration"
    assert result.backup.backup_path.parent == user_data_dir / "backups"
    # The backup is the pre-migration state: no new columns, all data intact.
    assert not set(SNAPSHOT_COLUMNS) & set(columns(result.backup.backup_path))
    assert snapshot(result.backup.backup_path) == before
    assert applied(result.backup.backup_path)[-1] == PREVIOUS_MIGRATION_ID
    # The live database received the columns and kept every existing value.
    assert set(SNAPSHOT_COLUMNS) <= set(columns(database_path))
    assert snapshot(database_path) == before


def test_a_failed_0019_destroys_neither_the_user_database_nor_the_backup(monkeypatch, tmp_path):
    """A mid-migration failure must leave the user's data and backup intact.

    Python's `sqlite3` runs DDL outside the implicit transaction, so an
    `ALTER TABLE ADD COLUMN` that has already executed survives the rollback
    while the `schema_migrations` insert — ordinary DML — does not. That is why
    `0019` is written idempotently: the failed run leaves a harmless extra
    nullable column, no row loses a value, the backup is still there, and the
    next startup completes the migration exactly once.
    """
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    before = build_pre_c2_ii_database(database_path)

    import app.migrations.versions as versions_package

    migration = __import__(f"{versions_package.__name__}.{MIGRATION_ID}", fromlist=["upgrade"])
    original_upgrade = migration.upgrade

    def failing_upgrade(connection):
        original_upgrade(connection)
        raise RuntimeError("forced migration failure after the column was added")

    monkeypatch.setattr(migration, "upgrade", failing_upgrade)

    with pytest.raises(RuntimeError, match="forced migration failure"):
        initialize_startup("user")

    backups = sorted((user_data_dir / "backups").iterdir())
    assert len(backups) == 1
    assert snapshot(backups[0]) == before
    assert not set(SNAPSHOT_COLUMNS) & set(columns(backups[0]))
    # No user value was lost, and the migration was not recorded as applied.
    assert snapshot(database_path) == before
    assert MIGRATION_ID not in applied(database_path)
    assert pending_migration_ids(DatabaseConfig(path=database_path)) == [MIGRATION_ID]

    # Recovery: the next startup backs up again, completes it once, keeps data.
    monkeypatch.setattr(migration, "upgrade", original_upgrade)
    recovered = initialize_startup("user")

    assert recovered.applied_migrations == [MIGRATION_ID]
    assert recovered.backup is not None and recovered.backup.reason == "before_migration"
    assert snapshot(database_path) == before
    assert applied(database_path).count(MIGRATION_ID) == 1
    assert len(sorted((user_data_dir / "backups").iterdir())) == 2


def test_a_brand_new_user_database_creates_no_pointless_pre_migration_backup(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    result = initialize_startup("user")

    assert result.backup is None
    assert result.applied_migrations == expected_migration_ids()
    assert list((user_data_dir / "backups").iterdir()) == []


def test_a_fully_migrated_user_database_starts_up_without_another_backup(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    build_pre_c2_ii_database(user_data_dir / "data" / "cosmetic_workshop.sqlite")
    initialize_startup("user")

    repeated = initialize_startup("user")

    assert repeated.applied_migrations == []
    assert repeated.backup is None
    assert len(list((user_data_dir / "backups").iterdir())) == 1


def test_development_mode_initialization_never_touches_a_real_user_path(monkeypatch, tmp_path):
    database_path = tmp_path / "development.sqlite"
    user_data_dir = tmp_path / "unused-user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    result = initialize_startup("development")

    assert result.user_data_paths is None
    assert result.database_path == database_path
    assert result.backup is None
    assert not user_data_dir.exists()
    assert set(SNAPSHOT_COLUMNS) <= set(columns(database_path))
    assert not (Path.home() / "Library" / "Application Support" / "Мастерская косметолога").exists() or database_path.is_relative_to(tmp_path)
