"""Read-only inspection of a candidate database's migration lineage.

Durable contract:
``docs/decisions/0016-launcher-assisted-restore.md`` § 3 (`CR-010`) and
``docs/backup-and-restore.md`` § 3.

`C4-I` has to answer one question about a **staged Restore candidate**: is this
file a `cosmetic-workshop-os` workspace whose recorded migration history is an
exact ordered prefix of the chain this application knows? Everything here exists
to answer that **without writing to the candidate**.

That rules out the obvious reuse. `app.db.migrations.applied_migration_ids`
calls `_ensure_migration_table`, which issues `CREATE TABLE IF NOT EXISTS` —
correct for a database the application owns and about to migrate, and exactly
wrong for a candidate that must stay byte-identical to what the user chose. A
read-only connection would make that call fail rather than mutate, but a failure
is not the same answer as "this file has no migration history", and the
distinction decides whether the candidate is rejected or silently repaired.

So this module reads, classifies and reports. It never creates the migration
table, never inserts a row, never runs a migration, and never repairs anything.
It is not a second migration registry: the expected chain still comes from
``app.db.migrations.MIGRATION_MODULES`` through `expected_migration_ids()`, so a
new migration added there is picked up here with no second list to update.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import sqlite3

from app.db.migrations import MIGRATION_TABLE, expected_migration_ids

# The two columns `_ensure_migration_table` creates. A candidate whose migration
# table has some other shape is not one this application wrote, and reading
# `migration_id` out of it would be a guess rather than a fact.
EXPECTED_MIGRATION_TABLE_COLUMNS: tuple[str, ...] = ("migration_id", "applied_at")

# The tables each migration adds, keyed by migration ID. This is the minimum
# required-table mapping for a supported known migration prefix: a candidate that
# records `0007_recipes` must actually contain the recipe tables, or its history
# is describing a schema the file does not have.
#
# `0017_import_apply_status` and `0019_production_batch_tax_rate_snapshots` are
# deliberately mapped to no *new* table. `0017` rebuilds `import_sources` and
# `import_drafts` through `*_new` scratch tables that are renamed over the
# originals, and `0019` only adds columns. Neither leaves a table behind that
# `0016` had not already required.
REQUIRED_TABLES_BY_MIGRATION: dict[str, frozenset[str]] = {
    "0001_infrastructure": frozenset({"app_settings", "audit_logs"}),
    "0002_ingredients": frozenset({"ingredients"}),
    "0003_ingredient_lots": frozenset({"ingredient_lots"}),
    "0004_stock_movements": frozenset({"stock_movements"}),
    "0005_packaging_items": frozenset({"packaging_items"}),
    "0006_packaging_stock_movements": frozenset({"packaging_stock_movements"}),
    "0007_recipes": frozenset({"recipe_templates", "recipe_versions", "recipe_ingredients"}),
    "0008_clients": frozenset({"clients"}),
    "0009_client_recipes": frozenset({"client_recipes", "client_recipe_ingredients"}),
    "0010_catalog": frozenset(
        {
            "catalog_categories",
            "catalog_tags",
            "ingredient_catalog_tags",
            "packaging_item_catalog_tags",
            "recipe_template_catalog_tags",
        }
    ),
    "0011_client_wishes_feedback": frozenset({"client_wishes", "client_feedback"}),
    "0012_orders": frozenset({"orders"}),
    "0013_production_batches": frozenset(
        {"production_batches", "production_batch_ingredients", "production_batch_packaging"}
    ),
    "0014_alerts": frozenset({"alerts"}),
    "0015_purchase_suggestions": frozenset({"purchase_suggestions"}),
    "0016_import_drafts": frozenset({"import_sources", "import_drafts", "import_draft_rows"}),
    "0017_import_apply_status": frozenset(),
    "0018_demo_data_tracking": frozenset({"demo_data_sessions", "demo_data_records"}),
    "0019_production_batch_tax_rate_snapshots": frozenset(),
    "0020_artifact_audit_operations": frozenset({"artifact_audit_operations"}),
}

# What makes a file recognizably *this* application's workspace rather than an
# arbitrary healthy SQLite database. `0001` is the floor of every supported
# prefix, so these three always have to be present.
WORKSPACE_IDENTITY_TABLES: frozenset[str] = frozenset(
    {MIGRATION_TABLE, "app_settings", "audit_logs"}
)

LineageStatus = Literal["known_prefix", "rejected"]

LineageRejection = Literal[
    "migration-table-missing",
    "migration-table-shape-unexpected",
    "migration-history-empty",
    "migration-history-unreadable",
    "duplicate-migration-id",
    "unknown-migration-id",
    "reordered-migration-id",
    "skipped-migration-id",
    "schema-newer-than-application",
]


@dataclass(frozen=True)
class MigrationLineage:
    """The verdict on one candidate's recorded migration history.

    `applied_ids` is populated only for an accepted `known_prefix`. A rejected
    lineage deliberately does not hand its caller a list to reason further about:
    the reason code is the complete answer, and the launcher's job is to reject,
    not to work around what it found.
    """

    status: LineageStatus
    rejection: LineageRejection | None = None
    applied_ids: tuple[str, ...] = ()

    @property
    def is_known_prefix(self) -> bool:
        return self.status == "known_prefix"

    @property
    def is_current_head(self) -> bool:
        """Whether the candidate already sits at the application's head schema.

        `False` for an accepted older prefix, which is exactly the case that will
        take the ordinary `before_migration` backup during restored startup.
        """
        return self.is_known_prefix and list(self.applied_ids) == expected_migration_ids()


def _rejected(reason: LineageRejection) -> MigrationLineage:
    return MigrationLineage(status="rejected", rejection=reason)


def migration_table_exists(connection: sqlite3.Connection) -> bool:
    """Whether the migration-history table is present, without creating it."""
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (MIGRATION_TABLE,),
    ).fetchone()
    return row is not None


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _migration_table_shape_matches(connection: sqlite3.Connection) -> bool:
    columns = tuple(
        row[1] for row in connection.execute(f"PRAGMA table_info({MIGRATION_TABLE})").fetchall()
    )
    return columns == EXPECTED_MIGRATION_TABLE_COLUMNS


def read_recorded_migration_ids(connection: sqlite3.Connection) -> list[str]:
    """Every recorded migration ID, in the order the table stores them.

    `rowid` order, not `migration_id` order. The point of this read is to notice
    a *reordered* history, and sorting the rows here would erase the very
    evidence the caller is looking for.
    """
    rows = connection.execute(
        f"SELECT migration_id FROM {MIGRATION_TABLE} ORDER BY rowid"
    ).fetchall()
    return [row[0] for row in rows]


def classify_recorded_migration_ids(recorded: list[str]) -> MigrationLineage:
    """Classify a recorded history against the application's migration chain.

    Accepted only when `recorded` is an exact ordered prefix of the expected
    chain — same IDs, same order, starting at the first, with nothing missing in
    between. Every other shape gets its own reason code, because the launcher's
    user-safe categories differ: a newer schema is a *supported file this
    application is too old for*, while an unknown ID is a file it does not
    recognize at all.
    """
    if not recorded:
        return _rejected("migration-history-empty")
    if len(set(recorded)) != len(recorded):
        return _rejected("duplicate-migration-id")

    expected = expected_migration_ids()
    expected_positions = {migration_id: index for index, migration_id in enumerate(expected)}

    unknown = [migration_id for migration_id in recorded if migration_id not in expected_positions]
    if unknown:
        # A history that contains the complete known chain *plus* extra IDs is a
        # database written by a later version of this application. Anything else
        # is simply not a history this application produced. The distinction
        # matters to the user-facing category and to nothing else — both are
        # rejected before the working database is touched.
        if set(expected).issubset(set(recorded)):
            return _rejected("schema-newer-than-application")
        return _rejected("unknown-migration-id")

    positions = [expected_positions[migration_id] for migration_id in recorded]
    if positions != sorted(positions):
        return _rejected("reordered-migration-id")
    if positions != list(range(len(positions))):
        return _rejected("skipped-migration-id")

    return MigrationLineage(status="known_prefix", applied_ids=tuple(recorded))


def inspect_migration_lineage(connection: sqlite3.Connection) -> MigrationLineage:
    """Read and classify one candidate's lineage through a read-only connection.

    The connection is the caller's, and it is expected to be opened
    `mode=ro`. Nothing here writes, so passing a writable connection would not
    change the outcome — but the read-only open is what makes that a property of
    the file rather than a promise of this function.
    """
    try:
        if not migration_table_exists(connection):
            return _rejected("migration-table-missing")
        if not _migration_table_shape_matches(connection):
            return _rejected("migration-table-shape-unexpected")
        recorded = read_recorded_migration_ids(connection)
    except sqlite3.Error:
        return _rejected("migration-history-unreadable")
    return classify_recorded_migration_ids(recorded)


def required_tables_for_prefix(applied_ids: tuple[str, ...] | list[str]) -> frozenset[str]:
    """The tables a database recording exactly `applied_ids` must contain.

    Union of the identity tables and everything each recorded migration creates.
    Unknown IDs contribute nothing, because `classify_recorded_migration_ids`
    has already rejected any history that contains one.
    """
    required = set(WORKSPACE_IDENTITY_TABLES)
    for migration_id in applied_ids:
        required |= REQUIRED_TABLES_BY_MIGRATION.get(migration_id, frozenset())
    return frozenset(required)


def missing_required_tables(
    connection: sqlite3.Connection, applied_ids: tuple[str, ...] | list[str]
) -> frozenset[str]:
    """Which required tables the candidate does not actually have.

    A recorded history is a claim; this is the check that the file backs the
    claim up. An empty result means every table the recorded prefix promises is
    present.
    """
    present = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    return frozenset(required_tables_for_prefix(applied_ids) - present)
