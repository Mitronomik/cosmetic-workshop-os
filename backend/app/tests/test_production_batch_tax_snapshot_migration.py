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

    # `0019` is no longer the tail of the list: CR-009 B1 appends
    # `0020_artifact_audit_operations` after it. What this test has always been
    # about is `0019`'s *position* — still immediately after `0018`, still
    # registered exactly once — so it is pinned relative to its neighbour rather
    # than to the end of a list that is expected to keep growing.
    assert ids.index(MIGRATION_ID) == ids.index(PREVIOUS_MIGRATION_ID) + 1
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
    # The point is that the backup predates `0019`, which is what makes it a
    # genuine pre-migration copy. Asserting it directly rather than through the
    # last element of an ID-sorted list, because `build_pre_c2_ii_database`
    # removes only `0019` and later migrations legitimately sort after it.
    assert MIGRATION_ID not in applied(result.backup.backup_path)
    assert PREVIOUS_MIGRATION_ID in applied(result.backup.backup_path)
    # The live database received the columns and kept every existing value.
    assert set(SNAPSHOT_COLUMNS) <= set(columns(database_path))
    assert snapshot(database_path) == before


def test_a_failed_0019_destroys_neither_the_user_database_nor_the_backup(monkeypatch, tmp_path):
    """Failure point: **after both** `ALTER TABLE` statements, before recording.

    This is the "complete DDL executed but migration ID unrecorded" state, not a
    partial one — the interruption happens once `upgrade()` has fully returned.
    The genuinely partial one-column state is covered separately by
    `test_recovery_from_a_real_one_column_partial_ddl_interruption`.

    Python's `sqlite3` runs DDL outside the implicit transaction, so the columns
    survive the rollback while the `schema_migrations` insert — ordinary DML —
    does not. That is why `0019` is idempotent: the failed run leaves the two
    nullable columns, no row loses a value, the backup is still there, and the
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


class InterruptBetweenAlterStatements:
    """Let the first `ADD COLUMN` through, then fail on the second.

    Wrapping the connection rather than rewriting the migration means the real
    `upgrade()` runs, so the interrupted schema is the one a genuine crash
    between the two statements would leave behind.
    """

    def __init__(self, connection):
        self._connection = connection
        self.add_column_statements = []

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def execute(self, sql, *args):
        if "ADD COLUMN" in sql:
            self.add_column_statements.append(sql)
            if len(self.add_column_statements) > 1:
                raise RuntimeError("forced failure between the two ALTER TABLE statements")
        return self._connection.execute(sql, *args)


class RecordingConnection:
    """Record the `ADD COLUMN` statements a migration actually issues."""

    def __init__(self, connection):
        self._connection = connection
        self.add_column_statements = []

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def execute(self, sql, *args):
        if "ADD COLUMN" in sql:
            self.add_column_statements.append(sql)
        return self._connection.execute(sql, *args)


def test_recovery_from_a_real_one_column_partial_ddl_interruption(monkeypatch, tmp_path):
    """Failure point: **between** the two `ALTER TABLE` statements.

    The genuinely partial state: the first snapshot column exists, the second
    does not, and the migration is unrecorded. Recovery must add only the
    missing column — re-issuing the first would raise `duplicate column name`
    and leave the user stuck on every subsequent start.
    """
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    before = build_pre_c2_ii_database(database_path)

    import app.migrations.versions as versions_package

    migration = __import__(f"{versions_package.__name__}.{MIGRATION_ID}", fromlist=["upgrade"])
    original_upgrade = migration.upgrade
    interrupted = {}

    def interrupted_upgrade(connection):
        wrapper = InterruptBetweenAlterStatements(connection)
        interrupted["wrapper"] = wrapper
        return original_upgrade(wrapper)

    monkeypatch.setattr(migration, "upgrade", interrupted_upgrade)

    with pytest.raises(RuntimeError, match="between the two ALTER TABLE statements"):
        initialize_startup("user")

    # --- The interrupted state is exactly one column in, unrecorded.
    live_columns = set(columns(database_path))
    assert "tax_rate_percent_snapshot" in live_columns
    assert "tax_rate_effective_at_snapshot" not in live_columns
    assert MIGRATION_ID not in applied(database_path)
    assert pending_migration_ids(DatabaseConfig(path=database_path)) == [MIGRATION_ID]
    assert snapshot(database_path) == before
    # The pre-migration backup predates the DDL and holds neither column.
    backups = sorted((user_data_dir / "backups").iterdir())
    assert len(backups) == 1
    assert not set(SNAPSHOT_COLUMNS) & set(columns(backups[0]))
    assert snapshot(backups[0]) == before

    # --- Recovery: only the missing column is added.
    recorded = {}

    def recording_upgrade(connection):
        wrapper = RecordingConnection(connection)
        recorded["wrapper"] = wrapper
        return original_upgrade(wrapper)

    monkeypatch.setattr(migration, "upgrade", recording_upgrade)
    recovered = initialize_startup("user")

    issued = recorded["wrapper"].add_column_statements
    assert len(issued) == 1, issued
    assert "tax_rate_effective_at_snapshot" in issued[0]
    assert "tax_rate_percent_snapshot" not in issued[0]

    assert recovered.applied_migrations == [MIGRATION_ID]
    assert recovered.backup is not None and recovered.backup.reason == "before_migration"
    assert set(SNAPSHOT_COLUMNS) <= set(columns(database_path))
    assert applied(database_path).count(MIGRATION_ID) == 1
    assert snapshot(database_path) == before
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(f"SELECT {', '.join(SNAPSHOT_COLUMNS)} FROM production_batches WHERE id = 1").fetchone() == (None, None)
    assert len(sorted((user_data_dir / "backups").iterdir())) == 2

    # --- A further startup applies nothing and creates no new migration backup.
    settled = initialize_startup("user")
    assert settled.applied_migrations == []
    assert settled.backup is None
    assert len(sorted((user_data_dir / "backups").iterdir())) == 2
    assert snapshot(database_path) == before


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
