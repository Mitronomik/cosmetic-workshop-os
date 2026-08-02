"""The complete startup recovery matrix of ADR 0016 § 7.5.

All twelve phases, each with the one behaviour the accepted table requires. The
parameterized test is the matrix itself: if a phase were dropped, renamed or
allowed to fall through to ordinary startup, it fails here.

Crash states are constructed by publishing a record directly, which is how a
crashed operation actually looks on disk — a durable record left at whatever
phase the process died in.
"""

from pathlib import Path
import hashlib

import pytest

from launcher.restore.contracts import RestoreOutcome
from launcher.restore.engine import RestoreServices
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import (
    RestoreOperationRecord,
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    make_workspace,
    migrating_startup,
    read_marker,
    stub_services,
)

# The accepted matrix, as data. `True` means ordinary startup may continue.
STARTUP_ALLOWED = {
    "prepared": True,
    "source_staged": True,
    "candidate_validated": True,
    "safety_copy_verified": True,
    "replacement_intent": True,  # after a successful rollback
    "replacement_committed": True,  # after a successful rollback
    "verification_in_progress": True,  # after a successful rollback
    "completed": True,
    "aborted": True,
    "rollback_in_progress": True,  # after a successful rollback
    "rolled_back": True,
    "recovery_blocked": False,
}

ROLLS_BACK = {
    "replacement_intent",
    "replacement_committed",
    "verification_in_progress",
    "rollback_in_progress",
}

BECOMES_ABORTED = {"prepared", "source_staged", "candidate_validated", "safety_copy_verified"}


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def crashed(monkeypatch, tmp_path):
    """A workspace that looks like a Restore crashed part-way through.

    The working database holds workspace **B** (the restored candidate) and the
    verified safety copy holds workspace **A** (the previous workspace), so a
    rollback is observable rather than a no-op.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")

    launcher_workspace = RestoreWorkspace(
        restore_dir=workspace.restore_dir, database_path=workspace.database_path
    )
    store = RestoreOperationStateStore(launcher_workspace)
    context = workspace.context()
    try:
        yield workspace, context, store, safety
    finally:
        context.release()


def publish_crash_state(store, phase: RestorePhase, *, safety_copy_filename=None, operation_id=None):
    operation_id = operation_id or new_operation_id()
    store.workspace.ensure_restore_dir()
    operation_dir = store.workspace.restore_dir / operation_id
    operation_dir.mkdir(parents=True, exist_ok=True)
    (operation_dir / "candidate.sqlite").write_bytes(b"staged evidence")
    return store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=phase,
            created_at="2026-08-02T00:00:00+00:00",
            updated_at="2026-08-02T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety_copy_filename,
        )
    )


def recover(workspace, context, **kwargs):
    services = kwargs.pop("services", None) or stub_services(workspace.database_path)
    return recover_incomplete_restore(context, services=services, **kwargs)


# --------------------------------------------------------------------------
# The matrix
# --------------------------------------------------------------------------

@pytest.mark.parametrize("phase_value", list(STARTUP_ALLOWED))
def test_every_persisted_phase_gets_its_required_startup_behaviour(crashed, phase_value):
    workspace, context, store, safety = crashed
    phase = RestorePhase(phase_value)
    publish_crash_state(store, phase, safety_copy_filename=safety.filename)

    result = recover(workspace, context)

    assert result.normal_startup_allowed is STARTUP_ALLOWED[phase_value], phase_value

    if phase_value in BECOMES_ABORTED:
        assert result.durable_phase is RestorePhase.ABORTED
        assert store.read().phase is RestorePhase.ABORTED
        # Never replaced, never rolled back: the working database is as the
        # crash left it.
        assert read_marker(workspace.database_path) == "workspace-B"
    elif phase_value in ROLLS_BACK:
        assert result.outcome is RestoreOutcome.ROLLED_BACK
        assert store.read().phase is RestorePhase.ROLLED_BACK
        assert read_marker(workspace.database_path) == "workspace-A"
    elif phase_value == "recovery_blocked":
        assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
        assert store.read().phase is RestorePhase.RECOVERY_BLOCKED
    else:
        assert result.durable_phase is RestorePhase(phase_value)

    # The safety copy is never silently deleted, in any phase.
    assert safety.path.exists()


def test_no_phase_is_missing_from_the_matrix():
    assert set(STARTUP_ALLOWED) == {phase.value for phase in RestorePhase}


# --------------------------------------------------------------------------
# The individual behaviours the matrix names
# --------------------------------------------------------------------------

def test_no_operation_allows_ordinary_startup_untouched(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")

    context = workspace.context()
    try:
        result = recover(workspace, context)
    finally:
        context.release()

    assert result.no_operation is True
    assert result.normal_startup_allowed is True
    assert read_marker(workspace.database_path) == "workspace-A"


def test_an_aborted_phase_cleans_only_owned_staging(crashed):
    workspace, context, store, safety = crashed
    record = publish_crash_state(
        store, RestorePhase.SOURCE_STAGED, safety_copy_filename=safety.filename
    )

    recover(workspace, context)

    assert not (workspace.restore_dir / record.operation_id).exists()
    assert safety.path.exists()


def test_a_completed_phase_retains_the_safety_copy_and_continues(crashed):
    workspace, context, store, safety = crashed
    record = publish_crash_state(
        store, RestorePhase.COMPLETED, safety_copy_filename=safety.filename
    )

    result = recover(workspace, context)

    assert result.normal_startup_allowed is True
    assert result.outcome is RestoreOutcome.COMPLETED
    assert store.read().phase is RestorePhase.COMPLETED
    assert safety.path.exists()
    assert not (workspace.restore_dir / record.operation_id).exists()
    # Never rolled back: the restored workspace stays authoritative.
    assert read_marker(workspace.database_path) == "workspace-B"


def test_replacement_intent_always_rolls_back_even_when_nothing_changed(monkeypatch, tmp_path):
    """The ambiguous crash window is resolved conservatively, never by guessing.

    Here the working database still holds the *previous* workspace, so the
    replacement demonstrably never happened — and the launcher still rolls back,
    because it is forbidden from inspecting the file to find that out.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    launcher_workspace = RestoreWorkspace(
        restore_dir=workspace.restore_dir, database_path=workspace.database_path
    )
    store = RestoreOperationStateStore(launcher_workspace)
    publish_crash_state(
        store, RestorePhase.REPLACEMENT_INTENT, safety_copy_filename=safety.filename
    )

    context = workspace.context()
    try:
        result = recover(workspace, context)
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ROLLED_BACK
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_rolled_back_result_is_never_reported_as_success(crashed):
    workspace, context, store, safety = crashed
    publish_crash_state(
        store, RestorePhase.VERIFICATION_IN_PROGRESS, safety_copy_filename=safety.filename
    )

    result = recover(workspace, context)

    assert result.outcome is RestoreOutcome.ROLLED_BACK
    assert result.outcome is not RestoreOutcome.COMPLETED
    assert "не завершилось" in result.message


def test_an_interrupted_rollback_safely_repeats(crashed):
    """A crash inside `rollback_in_progress` continues from the same phase."""
    workspace, context, store, safety = crashed
    publish_crash_state(
        store, RestorePhase.ROLLBACK_IN_PROGRESS, safety_copy_filename=safety.filename
    )

    first = recover(workspace, context)
    assert first.outcome is RestoreOutcome.ROLLED_BACK
    assert read_marker(workspace.database_path) == "workspace-A"

    # Re-publishing the same crash state and recovering again is idempotent.
    publish_crash_state(
        store, RestorePhase.ROLLBACK_IN_PROGRESS, safety_copy_filename=safety.filename
    )
    second = recover(workspace, context)

    assert second.outcome is RestoreOutcome.ROLLED_BACK
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_rollback_without_a_recorded_safety_copy_blocks_recovery(crashed):
    """Nothing provably safe to restore, so nothing is guessed at."""
    workspace, context, store, _safety = crashed
    publish_crash_state(store, RestorePhase.REPLACEMENT_COMMITTED, safety_copy_filename=None)

    result = recover(workspace, context)

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert store.read().phase is RestorePhase.RECOVERY_BLOCKED


def test_a_rollback_that_cannot_be_verified_blocks_recovery(crashed):
    workspace, context, store, safety = crashed
    publish_crash_state(
        store, RestorePhase.REPLACEMENT_INTENT, safety_copy_filename=safety.filename
    )

    def always_fails(_config, _paths, _database_path):
        raise RuntimeError("the recovered workspace does not start")

    result = recover(
        workspace,
        context,
        services=RestoreServices(
            verify_backend=always_fails,
            initialize_startup=migrating_startup(workspace.database_path),
        ),
    )

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED


def test_recovery_blocked_preserves_evidence_and_never_starts(crashed):
    workspace, context, store, safety = crashed
    record = publish_crash_state(
        store, RestorePhase.RECOVERY_BLOCKED, safety_copy_filename=safety.filename
    )

    result = recover(workspace, context)

    assert result.normal_startup_allowed is False
    assert result.blocks_browser is True
    assert (workspace.restore_dir / record.operation_id / "candidate.sqlite").exists()
    assert (workspace.restore_dir / "operation.json").exists()
    assert safety.path.exists()


def test_an_unreadable_record_blocks_startup_rather_than_being_ignored(crashed):
    """"There is no operation" and "I cannot read the operation" are different."""
    workspace, context, store, _safety = crashed
    store.workspace.ensure_restore_dir()
    store.record_path.write_text("{ truncated", encoding="utf-8")

    result = recover(workspace, context)

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED


def test_a_failure_to_close_out_an_aborted_operation_blocks_startup(crashed, monkeypatch):
    workspace, context, store, safety = crashed
    publish_crash_state(store, RestorePhase.PREPARED, safety_copy_filename=safety.filename)

    def refuse(self, record, target, **kwargs):
        raise RestoreStateError("injected publication failure")

    monkeypatch.setattr(RestoreOperationStateStore, "transition", refuse)

    result = recover(workspace, context)

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED


# --------------------------------------------------------------------------
# The launcher gate
# --------------------------------------------------------------------------

def test_run_local_runtime_refuses_to_start_from_recovery_blocked(monkeypatch, tmp_path):
    """No backend child, and no browser."""
    import socket
    import subprocess

    from launcher import runtime
    from launcher.config import build_runtime_config, resolve_runtime_paths

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    store = RestoreOperationStateStore(
        RestoreWorkspace(
            restore_dir=workspace.restore_dir, database_path=workspace.database_path
        )
    )
    publish_crash_state(
        store, RestorePhase.RECOVERY_BLOCKED, safety_copy_filename=safety.filename
    )

    started: list[object] = []
    browsers: list[object] = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: started.append(a) or (_ for _ in ()).throw(
            AssertionError("no backend may start from recovery_blocked")
        )
    )
    monkeypatch.setattr(
        runtime,
        "open_runtime_browser",
        lambda _config: browsers.append(_config),
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]

    exit_code = runtime.run_local_runtime(
        build_runtime_config(backend_port=free_port, open_browser=True),
        resolve_runtime_paths(),
    )

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert started == []
    assert browsers == [], "the browser must not open from recovery_blocked"


def test_run_local_runtime_recovers_an_interrupted_replacement_before_startup(
    monkeypatch, tmp_path
):
    """The gate runs before startup migrations, the backend child and the browser."""
    import socket
    import subprocess

    from launcher import runtime
    from launcher.config import build_runtime_config, resolve_runtime_paths
    from launcher.tests.test_runtime_database_continuity import RecordedPopen

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")
    store = RestoreOperationStateStore(
        RestoreWorkspace(
            restore_dir=workspace.restore_dir, database_path=workspace.database_path
        )
    )
    publish_crash_state(
        store, RestorePhase.REPLACEMENT_INTENT, safety_copy_filename=safety.filename
    )

    RecordedPopen.instances = []
    monkeypatch.setattr(subprocess, "Popen", RecordedPopen)
    monkeypatch.setattr(runtime, "open_runtime_browser", lambda _config: None)
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)
    # The child is a stand-in that serves nothing, so the real bounded backend
    # verification could not pass against it. Substituting the verifier keeps
    # this test on what it is actually about: that the gate runs, rolls back and
    # only then lets ordinary startup continue. The real verifier has its own
    # tests and its own smoke.
    monkeypatch.setattr(
        runtime,
        "resolve_restore_recovery",
        lambda context: recover_incomplete_restore(
            context, services=stub_services(context.database_path)
        ),
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]

    runtime.run_local_runtime(
        build_runtime_config(backend_port=free_port, open_browser=False),
        resolve_runtime_paths(),
    )

    assert store.read().phase is RestorePhase.ROLLED_BACK
    assert read_marker(workspace.database_path) == "workspace-A"
    # Ordinary startup then continued against the recovered previous workspace.
    assert len(RecordedPopen.instances) == 1
