"""Migration `0020` and the bounded CR-009 ledger it creates.

The risk this covers is not the shape of a new table; it is doing schema work to
the only copy of a real user's data. These tests prove the table is created
correctly on both a fresh and an existing database, that every accepted
constraint is actually enforced by SQLite rather than only by Python, that no
existing row or file is touched, and that the `before_migration` backup still
happens before `0020` runs.
"""

from pathlib import Path
import sqlite3

import pytest

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids, pending_migration_ids
from app.db.paths import USER_DATA_DIR_ENV
from app.services.database import initialize_database
from app.services.startup import initialize_startup

MIGRATION_ID = "0020_artifact_audit_operations"
PREVIOUS_MIGRATION_ID = "0019_production_batch_tax_rate_snapshots"
TABLE = "artifact_audit_operations"


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def applied(database_path: Path) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        return [row[0] for row in connection.execute("SELECT migration_id FROM schema_migrations")]


def table_names(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def build_pre_0020_database(database_path: Path) -> dict[str, object]:
    """A database at exactly the `0019` level, carrying representative data.

    The module list is truncated rather than the schema hand-written, so the
    starting point is genuinely the previously released schema instead of an
    approximation of it.
    """
    database_path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        cutoff = next(index for index, name in enumerate(original) if name.endswith(MIGRATION_ID))
        MIGRATION_MODULES[:] = original[:cutoff]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original
    with sqlite3.connect(database_path) as connection:
        connection.execute("INSERT INTO clients (full_name) VALUES ('Историческая клиентка')")
        connection.execute("INSERT INTO ingredients (name, category, default_unit) VALUES ('Масло', 'oil', 'g')")
        connection.execute(
            "INSERT INTO audit_logs (actor_type, action, entity_type, entity_id, summary)"
            " VALUES ('user', 'client.created', 'client', '1', 'Client created: Историческая клиентка')"
        )
    return snapshot(database_path)


def snapshot(database_path: Path) -> dict[str, object]:
    with sqlite3.connect(database_path) as connection:
        return {
            "clients": connection.execute("SELECT id, full_name FROM clients ORDER BY id").fetchall(),
            "ingredients": connection.execute("SELECT id, name FROM ingredients ORDER BY id").fetchall(),
            "audit_logs": connection.execute("SELECT id, action, summary FROM audit_logs ORDER BY id").fetchall(),
        }


def prepared_row(connection, operation_id="11111111-1111-4111-8111-111111111111", **overrides):
    values = {
        "operation_id": operation_id,
        "artifact_kind": "report_document",
        "primary_filename": "workshop-overview-20260731-101112.md",
        "companion_filename": "workshop-overview-20260731-101112.json",
        "status": "prepared",
        "audit_action": "report_document.created",
        "audit_log_id": None,
    }
    values.update(overrides)
    connection.execute(
        f"""
        INSERT INTO {TABLE}
            (operation_id, artifact_kind, primary_filename, companion_filename, status, audit_action, audit_log_id)
        VALUES (:operation_id, :artifact_kind, :primary_filename, :companion_filename, :status, :audit_action, :audit_log_id)
        """,
        values,
    )


# --------------------------------------------------------------------------
# Registration and ordering
# --------------------------------------------------------------------------

def test_migration_0020_is_registered_exactly_once_and_last():
    ids = expected_migration_ids()

    assert ids[-1] == MIGRATION_ID
    assert ids[-2] == PREVIOUS_MIGRATION_ID
    assert ids.count(MIGRATION_ID) == 1
    assert len(ids) == len(set(ids))


def test_fresh_empty_database_gets_the_ledger_table(tmp_path):
    database_path = tmp_path / "fresh.sqlite"

    initialize_database(DatabaseConfig(path=database_path))

    assert MIGRATION_ID in applied(database_path)
    assert TABLE in table_names(database_path)
    with connect(database_path) as connection:
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0


def test_a_database_at_0019_reports_exactly_one_pending_migration(tmp_path):
    database_path = tmp_path / "at-0019.sqlite"
    build_pre_0020_database(database_path)

    assert pending_migration_ids(DatabaseConfig(path=database_path)) == [MIGRATION_ID]


def test_upgrading_from_0019_preserves_every_existing_row_and_table(tmp_path):
    database_path = tmp_path / "upgrade.sqlite"
    before = build_pre_0020_database(database_path)
    tables_before = table_names(database_path)

    applied_now = initialize_database(DatabaseConfig(path=database_path))

    assert applied_now == [MIGRATION_ID]
    assert snapshot(database_path) == before
    assert tables_before < table_names(database_path)
    assert table_names(database_path) - tables_before == {TABLE}


def test_the_migration_applies_once_and_is_not_reapplied(tmp_path):
    database_path = tmp_path / "twice.sqlite"
    config = DatabaseConfig(path=database_path)
    build_pre_0020_database(database_path)

    initialize_database(config)
    initialize_database(config)

    assert applied(database_path).count(MIGRATION_ID) == 1
    assert pending_migration_ids(config) == []


def test_the_migration_creates_no_ledger_row_and_no_audit_log_row(tmp_path):
    """No legacy backfill: old artifacts stay unknown to the ledger.

    Existing documents were created before any operation was ever tracked. There
    is no honest way to reconstruct when or why they were made, so the migration
    invents nothing — it neither writes a ledger row for them nor an AuditLog
    event dated now for something that happened months ago.
    """
    database_path = tmp_path / "no-backfill.sqlite"
    documents_dir = tmp_path / "exports" / "report-documents"
    documents_dir.mkdir(parents=True)
    legacy_document = documents_dir / "workshop-overview-20250101-000000.md"
    legacy_sidecar = documents_dir / "workshop-overview-20250101-000000.json"
    legacy_document.write_text("# Старый документ\n", encoding="utf-8")
    legacy_sidecar.write_text('{"id": "workshop-overview-20250101-000000"}', encoding="utf-8")
    legacy_bytes = (legacy_document.read_bytes(), legacy_sidecar.read_bytes())
    build_pre_0020_database(database_path)
    audit_before = snapshot(database_path)["audit_logs"]

    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0
    assert snapshot(database_path)["audit_logs"] == audit_before
    assert (legacy_document.read_bytes(), legacy_sidecar.read_bytes()) == legacy_bytes


# --------------------------------------------------------------------------
# Schema and constraints
# --------------------------------------------------------------------------

def test_the_ledger_has_exactly_the_accepted_columns(tmp_path):
    database_path = tmp_path / "schema.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        columns = {row["name"]: row for row in connection.execute(f"PRAGMA table_info({TABLE})")}

    assert set(columns) == {
        "operation_id",
        "artifact_kind",
        "primary_filename",
        "companion_filename",
        "status",
        "audit_action",
        "audit_log_id",
        "created_at",
        "updated_at",
    }
    assert columns["operation_id"]["pk"] == 1
    for required in ("artifact_kind", "primary_filename", "status", "audit_action", "created_at", "updated_at"):
        assert columns[required]["notnull"] == 1, required
    for nullable in ("companion_filename", "audit_log_id"):
        assert columns[nullable]["notnull"] == 0, nullable


@pytest.mark.parametrize("status", ["prepared", "pending_audit", "abandoned"])
def test_the_accepted_unresolved_and_abandoned_statuses_are_allowed(tmp_path, status):
    database_path = tmp_path / f"status-{status}.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        prepared_row(connection, status=status)
        assert connection.execute(f"SELECT status FROM {TABLE}").fetchone()["status"] == status


@pytest.mark.parametrize("status", ["done", "PREPARED", "", "pending", "audited_maybe"])
def test_an_unknown_status_is_rejected_by_sqlite(tmp_path, status):
    database_path = tmp_path / "status-check.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, status=status)


@pytest.mark.parametrize("kind", ["report_document", "json_export", "manual_backup"])
def test_the_reserved_artifact_kinds_are_accepted(tmp_path, kind):
    database_path = tmp_path / f"kind-{kind}.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        prepared_row(connection, artifact_kind=kind, audit_action="report_document.created")
        assert connection.execute(f"SELECT artifact_kind FROM {TABLE}").fetchone()["artifact_kind"] == kind


@pytest.mark.parametrize("kind", ["database_backup", "", "REPORT_DOCUMENT", "anything"])
def test_an_unknown_artifact_kind_is_rejected_by_sqlite(tmp_path, kind):
    database_path = tmp_path / "kind-check.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, artifact_kind=kind)


@pytest.mark.parametrize("action", ["report_document.created", "export.created", "backup.created"])
def test_the_reserved_audit_actions_are_accepted(tmp_path, action):
    database_path = tmp_path / f"action-{action}.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        prepared_row(connection, audit_action=action)
        assert connection.execute(f"SELECT audit_action FROM {TABLE}").fetchone()["audit_action"] == action


@pytest.mark.parametrize("action", ["report_document.deleted", "client.created", "", "restore.created"])
def test_an_unknown_audit_action_is_rejected_by_sqlite(tmp_path, action):
    database_path = tmp_path / "action-check.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, audit_action=action)


def test_a_report_document_operation_must_record_its_companion_filename(tmp_path):
    database_path = tmp_path / "companion.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, companion_filename=None)
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, companion_filename="   ")


def test_an_empty_operation_id_or_primary_filename_is_rejected(tmp_path):
    database_path = tmp_path / "empty.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, operation_id="   ")
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, primary_filename="")


def test_an_audited_row_must_carry_an_audit_log_id_and_others_must_not(tmp_path):
    """The status and the AuditLog reference cannot disagree.

    Without this the ledger could claim an operation was audited while pointing
    at no event, or claim it is still pending while already holding one — either
    of which would make exactly-once finalization unprovable.
    """
    database_path = tmp_path / "audited.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        log_id = connection.execute(
            "INSERT INTO audit_logs (actor_type, action, entity_type, entity_id, summary)"
            " VALUES ('user', 'report_document.created', 'report_document', 'op', 'Report document created')"
        ).lastrowid

        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, operation_id="22222222-2222-4222-8222-222222222222", status="audited")
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, operation_id="33333333-3333-4333-8333-333333333333", status="prepared", audit_log_id=log_id)
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, operation_id="44444444-4444-4444-8444-444444444444", status="abandoned", audit_log_id=log_id)

        prepared_row(connection, operation_id="55555555-5555-4555-8555-555555555555", status="audited", audit_log_id=log_id)
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 1


def test_the_audit_log_reference_is_a_real_foreign_key(tmp_path):
    database_path = tmp_path / "fk.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, status="audited", audit_log_id=987654)


def test_only_one_active_operation_may_own_one_artifact_identity(tmp_path):
    database_path = tmp_path / "identity.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        prepared_row(connection, operation_id="11111111-1111-4111-8111-111111111111")
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, operation_id="22222222-2222-4222-8222-222222222222")
        # `pending_audit` is active too, so it collides with `prepared` as well.
        with pytest.raises(sqlite3.IntegrityError):
            prepared_row(connection, operation_id="33333333-3333-4333-8333-333333333333", status="pending_audit")
        # A different artifact kind is a different identity.
        prepared_row(connection, operation_id="44444444-4444-4444-8444-444444444444", artifact_kind="json_export")


def test_resolved_history_is_retained_and_does_not_block_reuse(tmp_path):
    """`audited` and `abandoned` rows stay, and stop reserving the identity.

    Retaining them is what makes repeated finalization idempotent and gives a
    later diagnosis something to read. Keeping them *out* of the active-identity
    index is what stops a resolved operation from permanently burning a filename
    the accepted identity rules allow to be reused.
    """
    database_path = tmp_path / "history.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        log_id = connection.execute(
            "INSERT INTO audit_logs (actor_type, action, entity_type, entity_id, summary)"
            " VALUES ('user', 'report_document.created', 'report_document', 'op', 'Report document created')"
        ).lastrowid
        prepared_row(connection, operation_id="11111111-1111-4111-8111-111111111111", status="audited", audit_log_id=log_id)
        prepared_row(connection, operation_id="22222222-2222-4222-8222-222222222222", status="abandoned")
        prepared_row(connection, operation_id="33333333-3333-4333-8333-333333333333", status="prepared")

        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 3


def test_the_active_identity_index_exists_and_is_partial(tmp_path):
    database_path = tmp_path / "index.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = 'idx_artifact_audit_operations_active_identity'"
        ).fetchone()

    assert sql is not None
    assert "UNIQUE" in sql["sql"]
    assert "WHERE" in sql["sql"]
    assert "'prepared'" in sql["sql"] and "'pending_audit'" in sql["sql"]


def test_timestamps_use_the_existing_sqlite_utc_convention(tmp_path):
    database_path = tmp_path / "timestamps.sqlite"
    initialize_database(DatabaseConfig(path=database_path))

    with connect(database_path) as connection:
        prepared_row(connection)
        row = connection.execute(f"SELECT created_at, updated_at FROM {TABLE}").fetchone()
        expected = connection.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]

    # Same `YYYY-MM-DD HH:MM:SS` shape as every other table, not a new ISO/offset
    # convention that later readers would have to special-case.
    assert len(row["created_at"]) == len(expected)
    assert row["created_at"][:10] == expected[:10]
    assert row["updated_at"] == row["created_at"]


# --------------------------------------------------------------------------
# Startup ordering
# --------------------------------------------------------------------------

def test_user_mode_startup_backs_up_before_applying_0020(monkeypatch, tmp_path):
    """The pre-migration backup still runs first, and does not know the ledger.

    The automatic `before_migration` backup is outside CR-009 entirely: it is not
    a user action, it is not audited, and it must not depend on a table that does
    not exist until the migration it is protecting has run.
    """
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    before = build_pre_0020_database(database_path)

    result = initialize_startup("user")

    assert result.applied_migrations == [MIGRATION_ID]
    assert result.backup is not None
    assert result.backup.reason == "before_migration"
    # The backup predates `0020`: no ledger table, and the data is intact.
    assert MIGRATION_ID not in applied(result.backup.backup_path)
    assert PREVIOUS_MIGRATION_ID in applied(result.backup.backup_path)
    assert TABLE not in table_names(result.backup.backup_path)
    assert snapshot(result.backup.backup_path) == before
    # The live database received the table and kept every existing value.
    assert TABLE in table_names(database_path)
    assert snapshot(database_path) == before


def test_the_startup_backup_creates_no_ledger_row_and_no_audit_event(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "user-data"
    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    build_pre_0020_database(database_path)
    audit_before = snapshot(database_path)["audit_logs"]

    initialize_startup("user")

    with connect(database_path) as connection:
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0
        actions = [row[0] for row in connection.execute("SELECT action FROM audit_logs ORDER BY id")]
    assert snapshot(database_path)["audit_logs"] == audit_before
    assert "backup.created" not in actions
    assert "report_document.created" not in actions
