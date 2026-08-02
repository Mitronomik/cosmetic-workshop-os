"""CR-009 B3: manual-backup verification, exactly-once finalization, reconciliation.

Durable contract: ``docs/decisions/0013-file-backed-artifact-audit-semantics.md``
and ``docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md``.

The distinctive property under test is the one a report document and a JSON
export do not have: a manual backup is itself a SQLite database, so it can — and
must — carry proof of which operation created it. `PRAGMA quick_check = ok` is
necessary and nowhere near sufficient, and these tests pin that down from both
sides.
"""

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
import threading

import pytest

from app.db.config import DatabaseConfig
from app.domain.artifact_audit_operations import (
    ARTIFACT_KIND_JSON_EXPORT,
    ARTIFACT_KIND_MANUAL_BACKUP,
    ARTIFACT_KIND_REPORT_DOCUMENT,
    AUDIT_ACTION_BACKUP_CREATED,
    AUDIT_ACTION_EXPORT_CREATED,
    STATUS_ABANDONED,
    STATUS_AUDITED,
    STATUS_PENDING_AUDIT,
    STATUS_PREPARED,
    new_operation_id,
)
from app.repositories.artifact_audit_operations import ArtifactAuditOperationRepository
from app.services.backup import BackupPaths, reserve_backup_path
from app.services.backup_audit import (
    PENDING_AUDIT_MESSAGE,
    BackupAuditService,
    BackupAuditTrackingUnavailableError,
    reconcile_manual_backups,
)
from app.services.backup_creation import create_audited_backup
from app.services.database import initialize_database

FIXED_TIME = datetime(2026, 8, 1, 10, 15, 0, 123456, tzinfo=UTC)


# --------------------------------------------------------------------------
# fixtures and helpers
# --------------------------------------------------------------------------

@pytest.fixture
def workspace(tmp_path):
    """A migrated database plus its backup directory, wired as the API wires them."""
    database = tmp_path / "data" / "cosmetic_workshop.sqlite"
    database.parent.mkdir(parents=True)
    config = DatabaseConfig(path=database)
    initialize_database(config)
    connection = sqlite3.connect(database)
    try:
        connection.executemany(
            "INSERT INTO ingredients (name, category, default_unit, is_active) VALUES (?, 'base', 'g', 1)",
            [(f"row-{index}",) for index in range(5)],
        )
        connection.commit()
    finally:
        connection.close()
    return BackupPaths(database_path=database, backup_dir=tmp_path / "backups"), config


def audit_events(config: DatabaseConfig, action: str = AUDIT_ACTION_BACKUP_CREATED):
    connection = sqlite3.connect(config.path)
    try:
        return connection.execute(
            "SELECT id, entity_type, entity_id, summary, actor_type, metadata_json"
            " FROM audit_logs WHERE action = ? ORDER BY id",
            (action,),
        ).fetchall()
    finally:
        connection.close()


def create_one(workspace, reason="manual"):
    paths, config = workspace
    return create_audited_backup(paths, reason, config=config), paths, config


def embedded_operation(backup_path: Path, operation_id: str):
    connection = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
    try:
        return connection.execute(
            "SELECT artifact_kind, primary_filename, companion_filename, status, audit_action,"
            " audit_log_id FROM artifact_audit_operations WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
    finally:
        connection.close()


def rewrite_embedded(backup_path: Path, **columns):
    """Tamper with the embedded row inside one backup, to build a bad artifact.

    `ignore_check_constraints` is deliberate. Migration `0020` already refuses
    most of these combinations, and that is exactly why they have to be forced
    here: the point is to prove the *verifier* rejects a tampered snapshot on its
    own evidence, not to re-prove that the live schema would have refused to
    write it. A backup file is an ordinary file on the user's disk and can be
    edited by anything.
    """
    connection = sqlite3.connect(backup_path)
    try:
        connection.execute("PRAGMA ignore_check_constraints = ON")
        assignments = ", ".join(f"{name} = ?" for name in columns)
        connection.execute(
            f"UPDATE artifact_audit_operations SET {assignments}", tuple(columns.values())
        )
        connection.commit()
    finally:
        connection.close()


# --------------------------------------------------------------------------
# the accepted operation order and the embedded prepared row
# --------------------------------------------------------------------------

def test_a_recorded_backup_carries_its_own_prepared_ledger_row(workspace):
    """The heart of the accepted order.

    The snapshot is taken after the prepared row commits, so it contains that row
    in `prepared` with no `audit_log_id` — and no `backup.created` event for
    itself. That is what lets the artifact prove whose it is.
    """
    created, paths, config = create_one(workspace)

    assert created.audit_status == "recorded"
    assert created.audit_message is None

    row = embedded_operation(created.result.backup_path, created.operation_id)
    assert row == (
        ARTIFACT_KIND_MANUAL_BACKUP,
        created.result.backup_path.name,
        None,
        STATUS_PREPARED,
        AUDIT_ACTION_BACKUP_CREATED,
        None,
    )

    # The live ledger has moved on; the snapshot has not, and is never rewritten.
    live = ArtifactAuditOperationRepository(config).get_operation(created.operation_id)
    assert live.status == STATUS_AUDITED
    assert live.audit_log_id is not None

    snapshot = sqlite3.connect(f"file:{created.result.backup_path}?mode=ro", uri=True)
    try:
        assert (
            snapshot.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE action = ?", (AUDIT_ACTION_BACKUP_CREATED,)
            ).fetchone()[0]
            == 0
        )
    finally:
        snapshot.close()


def test_verification_never_modifies_the_backup(workspace):
    created, paths, config = create_one(workspace)
    service = BackupAuditService(paths.backup_dir, config)
    operation = ArtifactAuditOperationRepository(config).get_operation(created.operation_id)
    before = created.result.backup_path.read_bytes()

    for _ in range(3):
        assert service.verify(operation).outcome == "valid"

    assert created.result.backup_path.read_bytes() == before


# --------------------------------------------------------------------------
# `quick_check = ok` is not enough — embedded identity
# --------------------------------------------------------------------------

def test_an_unrelated_valid_sqlite_database_is_ambiguous(workspace, tmp_path):
    """The check no other artifact kind needs.

    A perfectly healthy database at the exact reserved path passes every
    structural test there is. It still cannot say which operation created it.
    """
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    # A different, complete, fully migrated application database.
    initialize_database(DatabaseConfig(path=reserved))

    service = BackupAuditService(paths.backup_dir, config)
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "embedded-operation-missing"
    finalization = service.finalize(operation_id, reconciled_after_failure=False)
    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert audit_events(config) == []


def test_an_empty_file_is_ambiguous_even_though_quick_check_passes(workspace):
    """CR-004 §7.8 produced exactly this from an aborted copy."""
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    reserved.touch()

    connection = sqlite3.connect(f"file:{reserved}?mode=ro", uri=True)
    try:
        assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    finally:
        connection.close()

    service = BackupAuditService(paths.backup_dir, config)
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    assert service.verify(operation).outcome == "ambiguous"


@pytest.mark.parametrize(
    ("columns", "expected_reason"),
    [
        ({"operation_id": "11111111-1111-4111-8111-111111111111"}, "embedded-operation-missing"),
        ({"artifact_kind": ARTIFACT_KIND_REPORT_DOCUMENT}, "embedded-artifact-kind-mismatch"),
        ({"audit_action": AUDIT_ACTION_EXPORT_CREATED}, "embedded-audit-action-mismatch"),
        ({"primary_filename": "20260801T101500123456Z-other-manual.sqlite"}, "embedded-filename-mismatch"),
        ({"companion_filename": "companion.sqlite"}, "embedded-companion-filename-present"),
        ({"status": STATUS_AUDITED}, "embedded-status-not-prepared"),
        ({"status": STATUS_PENDING_AUDIT}, "embedded-status-not-prepared"),
        ({"audit_log_id": 7}, "embedded-audit-log-id-present"),
    ],
)
def test_a_mismatched_embedded_operation_is_ambiguous(workspace, columns, expected_reason):
    """Every field of the embedded identity is load-bearing, one at a time."""
    created, paths, config = create_one(workspace)
    rewrite_embedded(created.result.backup_path, **columns)

    service = BackupAuditService(paths.backup_dir, config)
    operation = ArtifactAuditOperationRepository(config).get_operation(created.operation_id)
    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == expected_reason


def test_a_backup_missing_the_ledger_table_is_ambiguous(workspace):
    created, paths, config = create_one(workspace)
    connection = sqlite3.connect(created.result.backup_path)
    try:
        connection.execute("DROP TABLE artifact_audit_operations")
        connection.commit()
    finally:
        connection.close()

    service = BackupAuditService(paths.backup_dir, config)
    operation = ArtifactAuditOperationRepository(config).get_operation(created.operation_id)

    assert service.verify(operation).reason == "ledger-table-missing"


def test_a_missing_backup_is_definitely_absent_and_reconciles_to_abandoned(workspace):
    created, paths, config = create_one(workspace)
    created.result.backup_path.unlink()

    service = BackupAuditService(paths.backup_dir, config)
    repository = ArtifactAuditOperationRepository(config)
    repository.mark_pending_audit(created.operation_id)
    operation = repository.get_operation(created.operation_id)
    # Already audited by the create; re-open it so reconciliation has work to do.
    assert service.verify(operation).outcome in {"definitely_absent", "valid"}

    fresh_id = service.prepare_operation(primary_filename="20260801T101500123456Z-absent-manual.sqlite")
    assert service.verify(repository.get_operation(fresh_id)).outcome == "definitely_absent"

    service.reconcile()
    assert repository.get_operation(fresh_id).status == STATUS_ABANDONED


@pytest.mark.parametrize(
    "unsafe_name",
    ["../escape.sqlite", "sub/escape.sqlite", "not-a-generated-name.sqlite"],
)
def test_an_unsafe_or_ungrammatical_ledger_name_is_ambiguous(workspace, unsafe_name):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    repository = ArtifactAuditOperationRepository(config)
    operation_id = new_operation_id()
    # Written straight to the table so the repository's own write-side validation
    # cannot be what this test is relying on: the verifier must re-check on read.
    connection = sqlite3.connect(config.path)
    try:
        connection.execute(
            "INSERT INTO artifact_audit_operations"
            " (operation_id, artifact_kind, primary_filename, companion_filename, status, audit_action)"
            " VALUES (?, ?, ?, NULL, 'prepared', ?)",
            (operation_id, ARTIFACT_KIND_MANUAL_BACKUP, unsafe_name, AUDIT_ACTION_BACKUP_CREATED),
        )
        connection.commit()
    finally:
        connection.close()

    service = BackupAuditService(paths.backup_dir, config)
    verification = service.verify(repository.get_operation(operation_id))

    assert verification.outcome == "ambiguous"


def test_an_escaping_symlink_is_ambiguous(workspace, tmp_path):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside.sqlite"
    initialize_database(DatabaseConfig(path=outside))
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    reserved.symlink_to(outside)

    service = BackupAuditService(paths.backup_dir, config)
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "path-outside-backup-directory"


def test_a_directory_at_the_exact_path_is_ambiguous(workspace):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    reserved.mkdir()

    service = BackupAuditService(paths.backup_dir, config)
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    assert service.verify(operation).reason == "backup-not-regular-file"


# --------------------------------------------------------------------------
# exactly-once finalization
# --------------------------------------------------------------------------

def test_repeated_finalization_commits_exactly_one_event(workspace):
    created, paths, config = create_one(workspace)
    service = BackupAuditService(paths.backup_dir, config)
    first = audit_events(config)
    assert len(first) == 1

    for _ in range(5):
        repeated = service.finalize(created.operation_id, reconciled_after_failure=True)
        assert repeated.outcome == "recorded"
        # The existing audit ID is reused, never a second insert.
        assert repeated.audit_log_id == first[0][0]

    assert audit_events(config) == first


def test_concurrent_finalization_commits_exactly_one_event(workspace):
    """Twelve finalizers race for one operation; `BEGIN IMMEDIATE` orders them."""
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    created = create_audited_backup(paths, "manual", config=config)

    # Re-open the resolved operation so every thread has real work to attempt.
    repository = ArtifactAuditOperationRepository(config)
    connection = sqlite3.connect(config.path)
    try:
        connection.execute(
            "UPDATE artifact_audit_operations SET status = 'prepared', audit_log_id = NULL"
            " WHERE operation_id = ?",
            (created.operation_id,),
        )
        connection.execute("DELETE FROM audit_logs WHERE action = ?", (AUDIT_ACTION_BACKUP_CREATED,))
        connection.commit()
    finally:
        connection.close()

    start = threading.Barrier(12)
    results: list[int | None] = []
    lock = threading.Lock()

    def finalize() -> None:
        start.wait(timeout=30)
        outcome = BackupAuditService(paths.backup_dir, config).finalize(
            created.operation_id, reconciled_after_failure=False
        )
        with lock:
            results.append(outcome.audit_log_id if outcome.is_recorded else None)

    threads = [threading.Thread(target=finalize) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    events = audit_events(config)
    assert len(events) == 1
    committed = {value for value in results if value is not None}
    assert committed == {events[0][0]}
    assert repository.get_operation(created.operation_id).status == STATUS_AUDITED


def test_a_failed_audit_insert_rolls_back_the_ledger_transition(workspace, monkeypatch):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    from app.services.backup import backup_sqlite_database

    backup_sqlite_database(
        paths.database_path, paths.backup_dir, reason="manual", reserved_backup_path=reserved
    )

    def failing_create_log(**kwargs):
        raise sqlite3.OperationalError("audit insert failed")

    monkeypatch.setattr(service.audit_repository, "create_log", failing_create_log)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)
    # The artifact verified; only the Journal entry failed. That is a pending
    # success, not an invalid artifact.
    assert finalization.outcome == "audit_pending"
    assert finalization.artifact_is_authoritative is True
    assert audit_events(config) == []
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == (
        STATUS_PENDING_AUDIT
    )


def test_a_failed_ledger_transition_rolls_back_the_audit_insert(workspace, monkeypatch):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    from app.services.backup import backup_sqlite_database

    backup_sqlite_database(
        paths.database_path, paths.backup_dir, reason="manual", reserved_backup_path=reserved
    )

    monkeypatch.setattr(service.repository, "mark_audited", lambda *a, **k: False)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)
    assert finalization.outcome == "audit_pending"
    # The insert and the transition commit together or not at all.
    assert audit_events(config) == []
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == (
        STATUS_PENDING_AUDIT
    )


def test_the_audit_event_carries_only_the_two_allowed_metadata_keys(workspace):
    created, paths, config = create_one(workspace, reason="перед обновлением ../unsafe")
    (event_id, entity_type, entity_id, summary, actor_type, metadata_json) = audit_events(config)[0]

    assert entity_type == "backup_file"
    assert entity_id == created.operation_id
    assert summary == "Backup created"
    assert actor_type == "user"

    import json

    metadata = json.loads(metadata_json)
    assert set(metadata) == {"operation_id", "reconciled_after_failure"}
    assert metadata["operation_id"] == created.operation_id
    assert metadata["reconciled_after_failure"] is False

    # Nothing about the artifact itself may appear anywhere in the row.
    serialized = f"{entity_type}{entity_id}{summary}{actor_type}{metadata_json}"
    assert created.result.backup_path.name not in serialized
    assert str(created.result.backup_path) not in serialized
    assert "перед" not in serialized
    assert "unsafe" not in serialized
    assert ".sqlite" not in serialized


# --------------------------------------------------------------------------
# reconciliation
# --------------------------------------------------------------------------

def test_reconciliation_finalizes_a_valid_unresolved_backup_exactly_once(workspace, monkeypatch):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    reserved = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    operation_id = service.prepare_operation(primary_filename=reserved.name)
    from app.services.backup import backup_sqlite_database

    backup_sqlite_database(
        paths.database_path, paths.backup_dir, reason="manual", reserved_backup_path=reserved
    )

    first = service.reconcile()
    second = service.reconcile()

    assert (first.examined, first.audited) == (1, 1)
    assert (second.examined, second.audited) == (0, 0)
    events = audit_events(config)
    assert len(events) == 1
    import json

    assert json.loads(events[0][5])["reconciled_after_failure"] is True


def test_reconciliation_never_touches_other_artifact_kinds(workspace):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    repository = ArtifactAuditOperationRepository(config)
    foreign = new_operation_id()
    repository.prepare_operation(
        operation_id=foreign,
        artifact_kind=ARTIFACT_KIND_JSON_EXPORT,
        primary_filename="20260801T101500123456Z-cosmetic_workshop-export-manual.json",
        companion_filename=None,
        audit_action=AUDIT_ACTION_EXPORT_CREATED,
    )

    BackupAuditService(paths.backup_dir, config).reconcile()

    assert repository.get_operation(foreign).status == STATUS_PREPARED
    assert audit_events(config) == []


def test_one_broken_operation_does_not_block_the_others(workspace):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    repository = ArtifactAuditOperationRepository(config)
    from app.services.backup import backup_sqlite_database

    broken = service.prepare_operation(
        primary_filename="20260801T101500123456Z-cosmetic_workshop-broken.sqlite"
    )
    (paths.backup_dir / "20260801T101500123456Z-cosmetic_workshop-broken.sqlite").write_bytes(
        b"not a database at all"
    )
    good_path = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "good")
    good = service.prepare_operation(primary_filename=good_path.name)
    backup_sqlite_database(
        paths.database_path, paths.backup_dir, reason="good", reserved_backup_path=good_path
    )

    result = service.reconcile()

    assert result.examined == 2
    assert result.audited == 1
    assert repository.get_operation(good).status == STATUS_AUDITED
    # Ambiguous is neither audited nor abandoned: it stays counted.
    assert repository.get_operation(broken).status == STATUS_PENDING_AUDIT
    assert service.pending_count() == 1


def test_reconciliation_never_scans_the_backup_directory(workspace):
    """Only ledger filenames are inspected; a legacy backup is invisible to it."""
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    legacy = paths.backup_dir / "20260705T090000000000Z-cosmetic_workshop-before_update.sqlite"
    initialize_database(DatabaseConfig(path=legacy))
    before = legacy.read_bytes()

    result = BackupAuditService(paths.backup_dir, config).reconcile()

    assert result == type(result)()
    assert audit_events(config) == []
    assert legacy.read_bytes() == before


def test_the_startup_entry_point_resolves_its_directory_from_the_given_config(workspace):
    paths, config = workspace
    result = reconcile_manual_backups(config, paths.backup_dir)
    assert result.examined == 0


# --------------------------------------------------------------------------
# pending count and preparation failure
# --------------------------------------------------------------------------

def test_pending_count_counts_only_unresolved_manual_backups(workspace):
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    repository = ArtifactAuditOperationRepository(config)

    prepared = service.prepare_operation(primary_filename="20260801T101500123456Z-a-manual.sqlite")
    pending = service.prepare_operation(primary_filename="20260801T101500123456Z-b-manual.sqlite")
    repository.mark_pending_audit(pending)
    abandoned = service.prepare_operation(primary_filename="20260801T101500123456Z-c-manual.sqlite")
    repository.mark_abandoned(abandoned)
    repository.prepare_operation(
        operation_id=new_operation_id(),
        artifact_kind=ARTIFACT_KIND_JSON_EXPORT,
        primary_filename="20260801T101500123456Z-cosmetic_workshop-export-manual.json",
        companion_filename=None,
        audit_action=AUDIT_ACTION_EXPORT_CREATED,
    )

    assert service.pending_count() == 2
    assert repository.get_operation(prepared).status == STATUS_PREPARED


def test_pending_count_raises_rather_than_reporting_a_fabricated_zero(workspace, monkeypatch):
    """`0` is a claim, not a fallback: the UI clears a standing warning on it."""
    paths, config = workspace
    service = BackupAuditService(paths.backup_dir, config)

    def failing_count(*args, **kwargs):
        raise sqlite3.OperationalError("ledger unavailable")

    monkeypatch.setattr(service.repository, "count_unresolved", failing_count)

    with pytest.raises(sqlite3.Error):
        service.pending_count()


def test_preparation_failure_creates_no_backup_and_no_ledger_row(workspace, monkeypatch):
    paths, config = workspace
    service_module = __import__("app.services.backup_creation", fromlist=["x"])

    def failing_prepare(self, *, primary_filename):
        raise BackupAuditTrackingUnavailableError(BackupAuditTrackingUnavailableError.message)

    monkeypatch.setattr(BackupAuditService, "prepare_operation", failing_prepare)

    with pytest.raises(BackupAuditTrackingUnavailableError):
        service_module.create_audited_backup(paths, "manual", config=config)

    assert not paths.backup_dir.exists() or list(paths.backup_dir.iterdir()) == []
    assert audit_events(config) == []
    connection = sqlite3.connect(config.path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM artifact_audit_operations").fetchone()[0] == 0
    finally:
        connection.close()


def test_only_unresolved_manual_backup_identities_are_reported_as_active(workspace):
    """A `prepared` operation owns its name before that file exists."""
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    repository = ArtifactAuditOperationRepository(config)

    active = "20260801T101500123456Z-cosmetic_workshop-active.sqlite"
    resolved = "20260801T101500123456Z-cosmetic_workshop-resolved.sqlite"
    other_kind = "20260801T101500123456Z-cosmetic_workshop-export-manual.json"
    service.prepare_operation(primary_filename=active)
    repository.mark_abandoned(service.prepare_operation(primary_filename=resolved))
    repository.prepare_operation(
        operation_id=new_operation_id(),
        artifact_kind=ARTIFACT_KIND_JSON_EXPORT,
        primary_filename=other_kind,
        companion_filename=None,
        audit_action=AUDIT_ACTION_EXPORT_CREATED,
    )

    assert service.is_identity_active(active) is True
    assert not (paths.backup_dir / active).exists()
    # A resolved operation no longer owns its name, and another artifact kind
    # never did.
    assert service.is_identity_active(resolved) is False
    assert service.is_identity_active(other_kind) is False


def test_the_create_path_advances_past_an_occupied_identity(workspace):
    """End to end: an unresolved operation's name is not handed to a new backup.

    The occupying artifact is deliberately *ambiguous* rather than absent. An
    absent artifact is abandoned by the same request's pre-create reconciliation
    pass, which legitimately frees its name again; an ambiguous one stays
    unresolved, so its identity stays taken.
    """
    paths, config = workspace
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    service = BackupAuditService(paths.backup_dir, config)
    repository = ArtifactAuditOperationRepository(config)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return FIXED_TIME

    import app.services.backup_creation as module

    occupied = reserve_backup_path(paths.backup_dir, paths.database_path, FIXED_TIME, "manual")
    occupying = service.prepare_operation(primary_filename=occupied.name)
    # An unrelated but structurally valid database: ambiguous, never audited,
    # never deleted, and its identity stays owned.
    initialize_database(DatabaseConfig(path=occupied))

    original = module.datetime
    module.datetime = FrozenDatetime
    try:
        created = create_audited_backup(paths, "manual", config=config)
    finally:
        module.datetime = original

    assert created.result.backup_path.name != occupied.name
    assert created.result.backup_path.name.endswith("-manual-1.sqlite")
    assert created.audit_status == "recorded"
    # The occupying operation was neither audited nor abandoned.
    assert repository.get_operation(occupying).status == STATUS_PENDING_AUDIT
    assert service.pending_count() == 1


# --------------------------------------------------------------------------
# the pending path
# --------------------------------------------------------------------------

def test_a_failed_finalization_keeps_the_backup_and_reports_pending(workspace, monkeypatch):
    paths, config = workspace

    from app.services.backup_audit import BackupFinalization

    def failing_finalize(self, operation_id, *, reconciled_after_failure):
        # The artifact verified; only the AuditLog write failed.
        return BackupFinalization("audit_pending")

    monkeypatch.setattr(BackupAuditService, "finalize", failing_finalize)
    created = create_audited_backup(paths, "manual", config=config)

    assert created.audit_status == "pending"
    assert created.audit_message == PENDING_AUDIT_MESSAGE
    assert created.result.backup_path.exists()
    assert audit_events(config) == []

    monkeypatch.undo()
    # The backup is intact, so a later reconciliation finalizes it exactly once.
    BackupAuditService(paths.backup_dir, config).reconcile()
    assert len(audit_events(config)) == 1
