"""End-to-end Restore attempts, and a deterministic fault at every boundary.

The happy path is one test. The rest of this file is the failure surface, because
that is where the accepted phase machine earns its keep: a fault injected before
`replacement_intent` must end at `aborted` with the working database untouched,
and a fault at or after it must end at `rolled_back` — including when the
replacement call itself failed, since a persisted `replacement_intent` is treated
as though replacement may have occurred.

The backend child is stubbed out here. Migrations still run for real against the
exact restored path; the real uvicorn boundary is covered by
`test_restore_backend_verification.py` and by the exact-head smoke runner.
"""

from pathlib import Path
from types import SimpleNamespace
import hashlib

import pytest

from launcher.restore.contracts import RestoreFailure, RestoreOutcome
from launcher.restore.engine import execute_restore
from launcher.restore.phases import RestorePhase
from launcher.restore.state import (
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.workspace import RestoreWorkspace

from launcher.tests.restore_fixtures import (
    failing_startup,
    failing_verifier,
    make_source_backup,
    make_workspace,
    migrating_startup,
    read_marker,
    request_for,
    stub_services,
)


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def store_for(workspace_fixture) -> RestoreOperationStateStore:
    return RestoreOperationStateStore(
        RestoreWorkspace(
            restore_dir=workspace_fixture.restore_dir,
            database_path=workspace_fixture.database_path,
        )
    )


@pytest.fixture
def scenario(monkeypatch, tmp_path):
    """Workspace A on disk, backup B selected as the Restore source.

    The context is a real one, acquired through the production classmethod, so
    every test here also exercises canonical path derivation and the held lock.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        yield workspace, source, context
    finally:
        context.release()


def run(workspace, source, context, **service_overrides):
    return execute_restore(
        request_for(source),
        context,
        services=stub_services(workspace.database_path, **service_overrides),
    )


def fail_transition_at(monkeypatch, phase: RestorePhase) -> None:
    """Make exactly one durable phase publication fail."""
    real = RestoreOperationStateStore.transition

    def guarded(self, record, target, **kwargs):
        if target is phase:
            raise RestoreStateError(f"injected publication failure at {target.value}")
        return real(self, record, target, **kwargs)

    monkeypatch.setattr(RestoreOperationStateStore, "transition", guarded)


# --------------------------------------------------------------------------
# The accepted happy path
# --------------------------------------------------------------------------

def test_a_complete_restore_reaches_durable_completed(scenario):
    workspace, source, context = scenario

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.COMPLETED
    assert result.durable_phase is RestorePhase.COMPLETED
    assert result.restore_succeeded is True
    assert result.failure is None
    assert read_marker(workspace.database_path) == "workspace-B"
    assert store_for(workspace).read().phase is RestorePhase.COMPLETED


def test_a_successful_restore_retains_a_verified_safety_copy(scenario):
    workspace, source, context = scenario

    result = run(workspace, source, context)

    copies = workspace.safety_copies()
    assert len(copies) == 1
    assert copies[0].name == result.safety_copy_filename
    # It holds the *previous* workspace, which is what makes it a recovery point.
    assert read_marker(copies[0]) == "workspace-A"


def test_a_successful_restore_leaves_the_source_byte_identical(scenario):
    workspace, source, context = scenario
    before = digest(source)

    run(workspace, source, context)

    assert digest(source) == before


def test_a_successful_restore_cleans_only_its_own_staging(scenario):
    workspace, source, context = scenario

    result = run(workspace, source, context)

    assert not (workspace.restore_dir / result.operation_id).exists()
    assert workspace.safety_copies()
    assert (workspace.restore_dir / "operation.json").exists()


def test_an_older_supported_schema_is_migrated_on_the_restored_copy(monkeypatch, tmp_path):
    import sqlite3

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    older = make_source_backup(tmp_path, "workspace-B-old", up_to="0018_demo_data_tracking")
    before = digest(older)

    context = workspace.context()
    try:
        result = run(workspace, older, context)
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.COMPLETED
    connection = sqlite3.connect(f"file:{workspace.database_path}?mode=ro", uri=True)
    try:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    finally:
        connection.close()
    assert "artifact_audit_operations" in tables
    # The selected source itself was never migrated.
    assert digest(older) == before


# --------------------------------------------------------------------------
# Failures before the replacement boundary — abort, database untouched
# --------------------------------------------------------------------------

def test_a_rejected_source_aborts_without_creating_an_operation(scenario, tmp_path):
    workspace, _source, context = scenario
    missing = tmp_path / "not-there.sqlite"

    result = execute_restore(
        request_for(missing),
        context,
        services=stub_services(workspace.database_path),
    )

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.SOURCE_REJECTED
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read() is None


def test_an_invalid_candidate_aborts_and_retains_the_working_database(monkeypatch, tmp_path):
    import sqlite3

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    connection = sqlite3.connect(source)
    try:
        connection.execute("DROP TABLE schema_migrations")
        connection.commit()
    finally:
        connection.close()
    before = digest(source)

    context = workspace.context()
    try:
        result = run(workspace, source, context)
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.CANDIDATE_INVALID
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read().phase is RestorePhase.ABORTED
    assert digest(source) == before
    assert workspace.safety_copies() == []


def test_a_newer_schema_is_rejected_before_the_working_database_changes(monkeypatch, tmp_path):
    import sqlite3

    from app.db.migrations import expected_migration_ids

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    connection = sqlite3.connect(source)
    try:
        connection.execute(
            "INSERT INTO schema_migrations (migration_id) VALUES ('0021_from_the_future')"
        )
        connection.commit()
    finally:
        connection.close()
    assert "0021_from_the_future" not in expected_migration_ids()

    context = workspace.context()
    try:
        result = run(workspace, source, context)
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.UNSUPPORTED_SCHEMA
    assert read_marker(workspace.database_path) == "workspace-A"


def test_insufficient_disk_space_aborts_before_staging(scenario, monkeypatch):
    import shutil

    workspace, source, context = scenario
    monkeypatch.setattr(
        shutil, "disk_usage", lambda _p: shutil._ntuple_diskusage(total=1, used=0, free=1)
    )

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.INSUFFICIENT_DISK_SPACE
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read() is None
    assert workspace.safety_copies() == []


def test_a_failing_safety_copy_aborts_before_replacement_intent(scenario, monkeypatch):
    from app.services import backup as backup_module

    workspace, source, context = scenario

    def refuse(**_kwargs):
        raise backup_module.BackupError("engine refused")

    monkeypatch.setattr(backup_module, "backup_sqlite_database", refuse)

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.SAFETY_COPY_FAILED
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read().phase is RestorePhase.ABORTED


def test_unsafe_target_journal_state_stops_before_replacement(scenario, monkeypatch):
    from launcher.restore import engine as engine_module
    from launcher.restore.replacement import JournalSafetyError

    workspace, source, context = scenario
    monkeypatch.setattr(
        engine_module,
        "quiesce_target_journal",
        lambda _p: (_ for _ in ()).throw(JournalSafetyError("unaccountable sidecar")),
    )

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.REPLACEMENT_FAILED
    assert read_marker(workspace.database_path) == "workspace-A"
    # The safety copy was already verified by then and is retained.
    assert len(workspace.safety_copies()) == 1


def test_a_failure_to_publish_replacement_intent_aborts(scenario, monkeypatch):
    """The boundary was never entered, so nothing is ambiguous."""
    workspace, source, context = scenario
    fail_transition_at(monkeypatch, RestorePhase.REPLACEMENT_INTENT)

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.REPLACEMENT_FAILED
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read().phase is RestorePhase.ABORTED


# --------------------------------------------------------------------------
# Failures at or after the replacement boundary — rollback
# --------------------------------------------------------------------------

def assert_rolled_back(result, workspace, source_digest=None, source=None):
    assert result.outcome is RestoreOutcome.ROLLED_BACK
    assert result.durable_phase is RestorePhase.ROLLED_BACK
    assert result.restore_succeeded is False, "rolled_back is never a successful Restore"
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read().phase is RestorePhase.ROLLED_BACK
    assert workspace.safety_copies(), "the safety copy is retained after rollback"
    if source is not None and source_digest is not None:
        assert digest(source) == source_digest


def test_a_failing_replacement_call_rolls_back(scenario, monkeypatch):
    """A persisted intent is ambiguous even when the rename demonstrably failed."""
    from launcher.restore import engine as engine_module
    from launcher.restore.replacement import ReplacementError

    workspace, source, context = scenario
    before = digest(source)
    calls = {"n": 0}
    real = engine_module.commit_replacement

    def fail_first(artifact, target, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ReplacementError("injected replacement failure")
        return real(artifact, target, **kwargs)

    monkeypatch.setattr(engine_module, "commit_replacement", fail_first)

    result = run(workspace, source, context)

    assert result.failure is RestoreFailure.REPLACEMENT_FAILED
    assert_rolled_back(result, workspace, before, source)


@pytest.mark.parametrize(
    "phase",
    [RestorePhase.REPLACEMENT_COMMITTED, RestorePhase.VERIFICATION_IN_PROGRESS],
)
def test_a_failure_to_publish_a_post_replacement_phase_rolls_back(scenario, monkeypatch, phase):
    workspace, source, context = scenario
    before = digest(source)
    fail_transition_at(monkeypatch, phase)

    result = run(workspace, source, context)

    assert_rolled_back(result, workspace, before, source)


def test_a_migration_failure_during_restored_startup_rolls_back(scenario):
    workspace, source, context = scenario
    before = digest(source)

    result = run(workspace, source, context, startup=failing_startup(workspace.database_path))

    assert_rolled_back(result, workspace, before, source)


def test_a_startup_resolving_a_different_database_rolls_back(scenario, tmp_path):
    """Database-path continuity is a hard requirement, not a warning."""
    workspace, source, context = scenario
    calls = {"n": 0}
    healthy = migrating_startup(workspace.database_path)

    def wrong_path_startup(mode, paths):
        calls["n"] += 1
        if calls["n"] == 1:
            return SimpleNamespace(database_path=tmp_path / "somewhere-else.sqlite")
        return healthy(mode, paths)

    result = run(workspace, source, context, startup=wrong_path_startup)

    assert_rolled_back(result, workspace)


@pytest.mark.parametrize(
    "boundary",
    [
        "first backend start",
        "health check",
        "representative read",
        "first backend stop",
        "second backend start",
        "second verification",
    ],
)
def test_every_backend_verification_boundary_rolls_back(scenario, boundary):
    """Each named verification boundary ends at the same accepted outcome."""
    workspace, source, context = scenario
    before = digest(source)

    result = run(workspace, source, context, verify=failing_verifier(boundary))

    assert result.failure is RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK
    assert_rolled_back(result, workspace, before, source)


def test_a_failure_to_publish_completed_rolls_back(scenario, monkeypatch):
    """The durable state still says `verification_in_progress`.

    Rolling back now is the same decision the next startup would make from that
    phase, taken while this process is still here to make it cleanly.
    """
    workspace, source, context = scenario
    fail_transition_at(monkeypatch, RestorePhase.COMPLETED)

    result = run(workspace, source, context)

    assert_rolled_back(result, workspace)


def test_after_completed_is_published_nothing_rolls_back(scenario):
    """The last boundary: once `completed` is durable, the restore stands."""
    workspace, source, context = scenario

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.COMPLETED
    assert read_marker(workspace.database_path) == "workspace-B"
    assert store_for(workspace).read().phase is RestorePhase.COMPLETED


# --------------------------------------------------------------------------
# recovery_blocked
# --------------------------------------------------------------------------

def test_an_unverifiable_rollback_becomes_recovery_blocked(scenario, monkeypatch):
    from launcher.restore import engine as engine_module
    from launcher.restore.safety_copy import SafetyCopyError

    workspace, source, context = scenario
    monkeypatch.setattr(
        engine_module,
        "verify_safety_copy",
        lambda _p: (_ for _ in ()).throw(SafetyCopyError("cannot verify")),
    )

    result = run(workspace, source, context, verify=failing_verifier("verification"))

    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.failure is RestoreFailure.RECOVERY_BLOCKED
    assert store_for(workspace).read().phase is RestorePhase.RECOVERY_BLOCKED


def test_recovery_blocked_preserves_every_piece_of_evidence(scenario, monkeypatch):
    from launcher.restore import engine as engine_module
    from launcher.restore.safety_copy import SafetyCopyError

    workspace, source, context = scenario
    monkeypatch.setattr(
        engine_module,
        "verify_safety_copy",
        lambda _p: (_ for _ in ()).throw(SafetyCopyError("cannot verify")),
    )

    result = run(workspace, source, context, verify=failing_verifier("verification"))

    assert (workspace.restore_dir / result.operation_id / "candidate.sqlite").exists()
    assert (workspace.restore_dir / "operation.json").exists()
    assert workspace.safety_copies(), "the safety copy is never silently deleted"
    assert source.exists()


# --------------------------------------------------------------------------
# Locking
# --------------------------------------------------------------------------

def test_restore_is_refused_without_a_held_lifecycle_lock(scenario):
    """A bare engine call cannot bypass the gate.

    Releasing the lock leaves a context that still *looks* complete — canonical
    paths, workspace, backend owner — and the engine still refuses, because
    authority is the held lock rather than the presence of the object.
    """
    workspace, source, context = scenario
    context.release()

    result = run(workspace, source, context)

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.LAUNCHER_ALREADY_RUNNING
    assert result.durable_phase is None
    assert read_marker(workspace.database_path) == "workspace-A"
    assert store_for(workspace).read() is None


def test_a_competing_launcher_process_cannot_take_the_lock(scenario):
    """flock is per open file description, so this needs a real second process."""
    import subprocess
    import sys

    workspace, _source, _context = scenario
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import fcntl,os,sys\n"
            "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
            "try:\n"
            "    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
            "except OSError:\n"
            "    print('refused')\n"
            "else:\n"
            "    print('acquired')\n",
            str(workspace.restore_dir / "launcher.lock"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.stdout.strip() == "refused"
    assert read_marker(workspace.database_path) == "workspace-A"
