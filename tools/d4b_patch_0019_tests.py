from pathlib import Path

path = Path("backend/app/tests/test_production_batch_tax_snapshot_migration.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        'from app.services.startup import initialize_startup\n',
        'from app.services.startup import initialize_startup\nfrom app.services.update_safety import UpdateSafetyError\n',
    ),
    (
        '    with pytest.raises(RuntimeError, match="forced migration failure"):\n        initialize_startup("user")\n',
        '    with pytest.raises(UpdateSafetyError, match="staged-migration-failed"):\n        initialize_startup("user")\n',
    ),
    (
        '    # No user value was lost, and the migration was not recorded as applied.\n    assert snapshot(database_path) == before\n    assert MIGRATION_ID not in applied(database_path)\n',
        '    # D4-B runs the failing DDL only on the disposable stage. Canonical remains pre-0019.\n    assert snapshot(database_path) == before\n    assert not set(SNAPSHOT_COLUMNS) & set(columns(database_path))\n    assert MIGRATION_ID not in applied(database_path)\n',
    ),
    (
        'def test_recovery_from_a_real_one_column_partial_ddl_interruption(monkeypatch, tmp_path):\n    """Failure point: **between** the two `ALTER TABLE` statements.\n\n    The genuinely partial state: the first snapshot column exists, the second\n    does not, and the migration is unrecorded. Recovery must add only the\n    missing column — re-issuing the first would raise `duplicate column name`\n    and leave the user stuck on every subsequent start.\n    """\n',
        'def test_stage_interruption_between_alters_never_partially_mutates_canonical(monkeypatch, tmp_path):\n    """Failure between ALTERs remains isolated to the disposable migration stage.\n\n    The first ALTER may complete on the stage before the second raises, but canonical\n    must remain at the exact source schema. A later launch builds a fresh stage and\n    therefore executes both ALTERs normally.\n    """\n',
    ),
    (
        '    with pytest.raises(RuntimeError, match="between the two ALTER TABLE statements"):\n        initialize_startup("user")\n\n    # --- The interrupted state is exactly one column in, unrecorded.\n    live_columns = set(columns(database_path))\n    assert "tax_rate_percent_snapshot" in live_columns\n    assert "tax_rate_effective_at_snapshot" not in live_columns\n',
        '    with pytest.raises(UpdateSafetyError, match="staged-migration-failed"):\n        initialize_startup("user")\n\n    assert len(interrupted["wrapper"].add_column_statements) == 2\n    live_columns = set(columns(database_path))\n    assert not set(SNAPSHOT_COLUMNS) & live_columns\n',
    ),
    (
        '    # --- Recovery: only the missing column is added.\n',
        '    # --- Recovery starts from a fresh stage, so both columns are added there.\n',
    ),
    (
        '    issued = recorded["wrapper"].add_column_statements\n    assert len(issued) == 1, issued\n    assert "tax_rate_effective_at_snapshot" in issued[0]\n    assert "tax_rate_percent_snapshot" not in issued[0]\n',
        '    issued = recorded["wrapper"].add_column_statements\n    assert len(issued) == 2, issued\n    assert "tax_rate_percent_snapshot" in issued[0]\n    assert "tax_rate_effective_at_snapshot" in issued[1]\n',
    ),
]

for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"D4-B 0019 test patch anchor mismatch: {old[:80]!r}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
