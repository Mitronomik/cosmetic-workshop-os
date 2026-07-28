MIGRATION_ID = "0019_production_batch_tax_rate_snapshots"

SNAPSHOT_COLUMNS = ("tax_rate_percent_snapshot", "tax_rate_effective_at_snapshot")


def upgrade(connection):
    """Add the two nullable C2-II tax-rate snapshot columns.

    Additive `ALTER TABLE ... ADD COLUMN` only: no table rebuild, no default,
    and no backfill, so every existing production batch keeps all of its values
    and simply reads `NULL` for both snapshots. Rows produced before this
    migration never had a rate context, and inventing one would fabricate
    history.
    """
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(production_batches)").fetchall()}
    for column in SNAPSHOT_COLUMNS:
        if column not in existing:
            connection.execute(f"ALTER TABLE production_batches ADD COLUMN {column} TEXT")
