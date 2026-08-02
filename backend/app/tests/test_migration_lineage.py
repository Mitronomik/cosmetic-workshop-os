"""The read-only migration-lineage helper.

Backend-owned and independently tested, because the launcher orchestration
depends on it and must not carry a second copy of the migration chain.

The property that matters most is the one in the last section: nothing here
creates the migration table, inserts a row or runs a migration. That is exactly
why `applied_migration_ids` could not be reused — it calls
`CREATE TABLE IF NOT EXISTS` on a file the Restore contract requires to stay
untouched.
"""

from pathlib import Path
import hashlib
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.db.migration_lineage import (
    EXPECTED_MIGRATION_TABLE_COLUMNS,
    REQUIRED_TABLES_BY_MIGRATION,
    WORKSPACE_IDENTITY_TABLES,
    classify_recorded_migration_ids,
    inspect_migration_lineage,
    migration_table_exists,
    missing_required_tables,
    required_tables_for_prefix,
)
from app.db.migrations import MIGRATION_MODULES, MIGRATION_TABLE, apply_migrations, expected_migration_ids


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def migrated_database(path: Path, up_to: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        if up_to is not None:
            cutoff = next(i for i, name in enumerate(original) if name.endswith(up_to))
            MIGRATION_MODULES[:] = original[: cutoff + 1]
        apply_migrations(DatabaseConfig(path=path))
    finally:
        MIGRATION_MODULES[:] = original
    return path


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

def test_the_complete_current_chain_is_a_known_prefix_at_head():
    lineage = classify_recorded_migration_ids(expected_migration_ids())

    assert lineage.is_known_prefix
    assert lineage.is_current_head


def test_a_shorter_ordered_prefix_is_known_but_not_head():
    lineage = classify_recorded_migration_ids(expected_migration_ids()[:10])

    assert lineage.is_known_prefix
    assert not lineage.is_current_head


@pytest.mark.parametrize(
    "recorded,reason",
    [
        ([], "migration-history-empty"),
        (["0001_infrastructure", "0001_infrastructure"], "duplicate-migration-id"),
        (["0001_infrastructure", "0002_invented"], "unknown-migration-id"),
        (["0002_ingredients", "0001_infrastructure"], "reordered-migration-id"),
        (["0001_infrastructure", "0003_ingredient_lots"], "skipped-migration-id"),
        (["0002_ingredients"], "skipped-migration-id"),
    ],
)
def test_every_malformed_history_shape_has_its_own_reason(recorded, reason):
    lineage = classify_recorded_migration_ids(recorded)

    assert not lineage.is_known_prefix
    assert lineage.rejection == reason


def test_a_superset_of_the_known_chain_is_reported_as_newer():
    """The complete chain plus extras is a database from a later version."""
    lineage = classify_recorded_migration_ids(expected_migration_ids() + ["0021_future"])

    assert lineage.rejection == "schema-newer-than-application"


def test_a_partial_chain_with_an_extra_is_merely_unknown():
    """Distinct from `newer`, because the user-facing category differs."""
    lineage = classify_recorded_migration_ids(expected_migration_ids()[:5] + ["9999_alien"])

    assert lineage.rejection == "unknown-migration-id"


def test_a_rejected_lineage_hands_back_no_ids_to_work_around():
    lineage = classify_recorded_migration_ids(["0002_ingredients"])

    assert lineage.applied_ids == ()


# --------------------------------------------------------------------------
# Inspection through a read-only connection
# --------------------------------------------------------------------------

def test_a_migrated_database_inspects_as_the_current_head(tmp_path):
    database = migrated_database(tmp_path / "head.sqlite")

    connection = read_only(database)
    try:
        lineage = inspect_migration_lineage(connection)
    finally:
        connection.close()

    assert lineage.is_current_head
    assert list(lineage.applied_ids) == expected_migration_ids()


def test_an_older_database_inspects_as_an_older_prefix(tmp_path):
    database = migrated_database(tmp_path / "older.sqlite", up_to="0012_orders")

    connection = read_only(database)
    try:
        lineage = inspect_migration_lineage(connection)
    finally:
        connection.close()

    assert lineage.is_known_prefix
    assert not lineage.is_current_head
    assert lineage.applied_ids[-1] == "0012_orders"


def test_a_database_without_the_migration_table_is_rejected(tmp_path):
    foreign = tmp_path / "foreign.sqlite"
    connection = sqlite3.connect(foreign)
    try:
        connection.execute("CREATE TABLE notes (x INTEGER)")
        connection.commit()
    finally:
        connection.close()

    connection = read_only(foreign)
    try:
        assert migration_table_exists(connection) is False
        assert inspect_migration_lineage(connection).rejection == "migration-table-missing"
    finally:
        connection.close()


def test_an_unexpected_migration_table_shape_is_rejected(tmp_path):
    odd = tmp_path / "odd.sqlite"
    connection = sqlite3.connect(odd)
    try:
        connection.execute(f"CREATE TABLE {MIGRATION_TABLE} (migration_id TEXT)")
        connection.commit()
    finally:
        connection.close()

    connection = read_only(odd)
    try:
        assert inspect_migration_lineage(connection).rejection == "migration-table-shape-unexpected"
    finally:
        connection.close()


def test_the_expected_migration_table_columns_match_what_migrations_creates(tmp_path):
    database = migrated_database(tmp_path / "shape.sqlite")

    connection = read_only(database)
    try:
        columns = tuple(
            row[1] for row in connection.execute(f"PRAGMA table_info({MIGRATION_TABLE})")
        )
    finally:
        connection.close()

    assert columns == EXPECTED_MIGRATION_TABLE_COLUMNS


# --------------------------------------------------------------------------
# The required-table mapping
# --------------------------------------------------------------------------

def test_the_mapping_covers_every_migration_in_the_chain():
    assert set(REQUIRED_TABLES_BY_MIGRATION) == set(expected_migration_ids())


def test_the_head_prefix_requires_every_table_the_migrations_create(tmp_path):
    database = migrated_database(tmp_path / "head.sqlite")
    required = required_tables_for_prefix(expected_migration_ids())

    connection = read_only(database)
    try:
        present = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        assert missing_required_tables(connection, expected_migration_ids()) == frozenset()
    finally:
        connection.close()

    # Every required table really exists, and the identity tables are included.
    assert required <= present
    assert WORKSPACE_IDENTITY_TABLES <= required


@pytest.mark.parametrize(
    "up_to",
    ["0001_infrastructure", "0007_recipes", "0013_production_batches", "0018_demo_data_tracking"],
)
def test_each_supported_older_prefix_maps_to_tables_that_really_exist(tmp_path, up_to):
    database = migrated_database(tmp_path / f"{up_to}.sqlite", up_to=up_to)
    prefix = expected_migration_ids()[: expected_migration_ids().index(up_to) + 1]

    connection = read_only(database)
    try:
        assert missing_required_tables(connection, prefix) == frozenset()
    finally:
        connection.close()


def test_a_dropped_required_table_is_reported(tmp_path):
    database = migrated_database(tmp_path / "damaged.sqlite")
    connection = sqlite3.connect(database)
    try:
        connection.execute("DROP TABLE purchase_suggestions")
        connection.commit()
    finally:
        connection.close()

    connection = read_only(database)
    try:
        missing = missing_required_tables(connection, expected_migration_ids())
    finally:
        connection.close()

    assert missing == frozenset({"purchase_suggestions"})


def test_an_older_prefix_does_not_require_a_later_migrations_table(tmp_path):
    prefix = expected_migration_ids()[: expected_migration_ids().index("0018_demo_data_tracking") + 1]

    required = required_tables_for_prefix(prefix)

    assert "artifact_audit_operations" not in required
    assert "demo_data_sessions" in required


def test_column_only_migrations_add_no_required_table():
    """`0017` rebuilds existing tables and `0019` only adds columns."""
    assert REQUIRED_TABLES_BY_MIGRATION["0017_import_apply_status"] == frozenset()
    assert REQUIRED_TABLES_BY_MIGRATION["0019_production_batch_tax_rate_snapshots"] == frozenset()


# --------------------------------------------------------------------------
# Nothing here writes
# --------------------------------------------------------------------------

def test_inspection_never_creates_the_migration_table(tmp_path):
    foreign = tmp_path / "foreign.sqlite"
    connection = sqlite3.connect(foreign)
    try:
        connection.execute("CREATE TABLE notes (x INTEGER)")
        connection.commit()
    finally:
        connection.close()
    before = digest(foreign)

    connection = read_only(foreign)
    try:
        inspect_migration_lineage(connection)
    finally:
        connection.close()

    assert digest(foreign) == before


def test_inspection_leaves_a_migrated_database_byte_identical(tmp_path):
    database = migrated_database(tmp_path / "head.sqlite")
    before = digest(database)

    connection = read_only(database)
    try:
        inspect_migration_lineage(connection)
        missing_required_tables(connection, expected_migration_ids())
    finally:
        connection.close()

    assert digest(database) == before


def test_inspection_does_not_migrate_an_older_database(tmp_path):
    database = migrated_database(tmp_path / "older.sqlite", up_to="0010_catalog")
    before = digest(database)

    connection = read_only(database)
    try:
        lineage = inspect_migration_lineage(connection)
    finally:
        connection.close()

    assert lineage.applied_ids[-1] == "0010_catalog"
    assert digest(database) == before
