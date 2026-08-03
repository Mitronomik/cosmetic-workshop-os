"""The launcher lifecycle context: canonical paths and backend-stop proof.

Two independent review findings live here.

**A caller may supply only the selected source.** Every destructive or
application-owned path is derived from the launcher's own resolvers, so a caller
cannot take the lock for one workspace and replace a database in another. The
tests here try to do exactly that and are refused.

**The backend must be provably stopped, by handle.** A held lock does not prove
it — the backend never takes that lock — and a free port proves less than
nothing, because during Restore the port is free by design. So the proof is
process ownership, and one test in this file starts a **real uvicorn child** and
watches the engine kill that exact PID before the working database is touched.
That test is deliberately not a mock: it is the only thing that shows the
ordering actually holds against a real process.
"""

from pathlib import Path
import os
import signal
import subprocess
import time

import pytest

from launcher.config import build_runtime_config, resolve_runtime_paths
from launcher.restore.context import (
    BackendProcessOwner,
    BackendStopProof,
    LauncherLifecycleContext,
    RestoreLifecycleError,
)
from launcher.restore.contracts import RestoreFailure, RestoreOutcome
from launcher.restore.engine import execute_restore
from launcher.restore.instance_lock import LauncherAlreadyRunningError
from launcher.restore.workspace import resolve_restore_dir

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    free_port,
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)


# --------------------------------------------------------------------------
# Canonical path derivation
# --------------------------------------------------------------------------

def test_every_destructive_path_is_derived_from_the_launcher_resolvers(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert context.database_path == workspace.database_path
        assert context.backup_dir == workspace.backup_dir
        assert context.workspace.restore_dir == workspace.restore_dir
        assert context.lock.lock_path == context.workspace.lock_path
    finally:
        context.release()


def test_the_request_carries_only_the_selected_source():
    """The complete caller-supplied surface, as a type-level fact."""
    from launcher.restore.contracts import RestoreRequest

    assert set(RestoreRequest.__dataclass_fields__) == {"selected_source"}


def test_a_caller_cannot_supply_a_foreign_database_target(monkeypatch, tmp_path):
    """There is no parameter to pass one through."""
    import inspect

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    signature = inspect.signature(execute_restore)

    assert set(signature.parameters) == {"request", "context", "services"}
    context = workspace.context()
    try:
        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.COMPLETED
    assert read_marker(workspace.database_path) == "workspace-B"


def test_a_tampered_database_path_is_rejected_before_staging(monkeypatch, tmp_path):
    """Mutating the context after construction must not redirect the boundary."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    elsewhere = build_workspace_database(tmp_path / "elsewhere" / "victim.sqlite", "victim")
    context = workspace.context()
    try:
        context.database_path = elsewhere

        result = execute_restore(
            request_for(source), context, services=stub_services(elsewhere)
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.durable_phase is None
    # Neither database was touched.
    assert read_marker(elsewhere) == "victim"
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_tampered_backup_directory_is_rejected(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.backup_dir = tmp_path / "somewhere-else"

        with pytest.raises(RestoreLifecycleError, match="backup directory"):
            context.require_authority()
    finally:
        context.release()


def test_a_tampered_restore_directory_is_rejected(monkeypatch, tmp_path):
    from launcher.restore.workspace import RestoreWorkspace

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.workspace = RestoreWorkspace(
            restore_dir=tmp_path / "foreign-restore", database_path=workspace.database_path
        )

        with pytest.raises(RestoreLifecycleError, match="operation directory"):
            context.require_authority()
    finally:
        context.release()


def test_the_lock_cannot_guard_one_database_while_another_is_replaced(monkeypatch, tmp_path):
    """The lock path and the target must come from one database identity."""
    from launcher.restore.instance_lock import LauncherInstanceLock

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.lock = LauncherInstanceLock(tmp_path / "unrelated.lock")

        with pytest.raises(RestoreLifecycleError, match="lock"):
            context.require_authority()
    finally:
        context.release()


def test_development_mode_stays_isolated_from_the_user_documents_directory(
    monkeypatch, tmp_path
):
    """A developer run must never resolve into the real Documents directory."""
    development_database = tmp_path / "development" / "workshop.sqlite"
    monkeypatch.setenv("COSMETIC_WORKSHOP_DB_PATH", str(development_database))
    monkeypatch.delenv("COSMETIC_WORKSHOP_USER_DATA_DIR", raising=False)
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    build_workspace_database(development_database, "development")

    config = build_runtime_config(
        backend_port=free_port(), mode="development", open_browser=False
    )
    context = LauncherLifecycleContext.acquire(config, resolve_runtime_paths())
    try:
        assert context.database_path == development_database
        assert context.workspace.restore_dir == development_database.parent / "restore"
        assert context.backup_dir == development_database.parent / "backups"
        assert resolve_restore_dir(development_database) == development_database.parent / "restore"
    finally:
        context.release()

    assert not (fake_home / "Documents").exists()


def test_user_mode_uses_the_expected_user_data_layout(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert context.database_path == workspace.base_dir / "data" / "cosmetic_workshop.sqlite"
        assert context.backup_dir == workspace.base_dir / "backups"
        assert context.workspace.restore_dir == workspace.base_dir / "restore"
    finally:
        context.release()


# --------------------------------------------------------------------------
# Authority
# --------------------------------------------------------------------------

def test_restore_without_a_held_lock_is_refused(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    context.release()

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.failure is RestoreFailure.LAUNCHER_ALREADY_RUNNING
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_second_context_cannot_be_acquired_while_one_is_held(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        with pytest.raises(LauncherAlreadyRunningError):
            workspace.context()
    finally:
        context.release()


# --------------------------------------------------------------------------
# Backend process ownership
# --------------------------------------------------------------------------

def test_an_owner_with_no_process_proves_nothing_was_running():
    proof = BackendProcessOwner().stop()

    assert proof.confirmed_stopped is True
    assert proof.was_running is False
    assert proof.pid is None


def test_an_owner_refuses_to_lose_track_of_a_live_child():
    owner = BackendProcessOwner()
    first = subprocess.Popen(["sleep", "30"])
    try:
        owner.adopt(first)
        second = subprocess.Popen(["sleep", "30"])
        try:
            with pytest.raises(RestoreLifecycleError):
                owner.adopt(second)
        finally:
            second.kill()
            second.wait(timeout=10)
    finally:
        owner.stop()


def test_stopping_terminates_exactly_the_recorded_process():
    owner = BackendProcessOwner()
    child = subprocess.Popen(["sleep", "30"])
    bystander = subprocess.Popen(["sleep", "30"])
    try:
        owner.adopt(child)

        proof = owner.stop(timeout_seconds=10.0)

        assert proof.confirmed_stopped is True
        assert proof.was_running is True
        assert proof.pid == child.pid
        assert child.poll() is not None
        # The bystander is untouched: nothing here discovers processes by name.
        assert bystander.poll() is None
    finally:
        bystander.kill()
        bystander.wait(timeout=10)


def test_a_wedged_child_is_killed_on_the_same_handle():
    """Escalation stays on the owned handle; no PID is looked up by port or name."""
    owner = BackendProcessOwner()
    # Ignores SIGTERM, so graceful shutdown must time out and escalate.
    child = subprocess.Popen(
        ["python3", "-c", "import signal, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\ntime.sleep(60)"]
    )
    try:
        # Give the child time to install the handler.
        time.sleep(0.5)
        owner.adopt(child)

        proof = owner.stop(timeout_seconds=1.0)

        assert proof.confirmed_stopped is True
        assert proof.pid == child.pid
        assert child.poll() is not None
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


def executable_source(module) -> str:
    """A module's source with comments and string literals removed.

    Needed because the module *documents* the forbidden shortcuts in prose. The
    check below is about what the code does, so the prose has to go — otherwise
    explaining why `pkill` is absent would trip the test that proves it is.
    """
    import inspect
    import io
    import tokenize

    source = inspect.getsource(module)
    kept: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept)


def test_the_owner_never_discovers_processes_by_port_or_pattern():
    """A mechanical check against the forbidden shortcuts.

    Killing a process this launcher did not start is not a safety measure; it is
    a second failure mode. Ownership is the only accepted way to find the process
    to stop.
    """
    from launcher.restore import context as context_module

    code = executable_source(context_module)
    for forbidden in ("pkill", "lsof", "killall", "psutil", "pgrep", "getoutput"):
        assert forbidden not in code, f"{forbidden} must never be used to find a process"


def test_backend_stop_proof_is_required_before_the_working_database_is_touched(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        with pytest.raises(RestoreLifecycleError, match="backend-stop proof"):
            context.require_backend_stopped()
    finally:
        context.release()


def test_a_backend_that_starts_again_invalidates_the_proof(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.stop_backend()
        context.backend.adopt(subprocess.Popen(["sleep", "30"]))

        with pytest.raises(RestoreLifecycleError, match="running again"):
            context.require_backend_stopped()
    finally:
        context.backend.stop()
        context.release()


# --------------------------------------------------------------------------
# Real backend process integration
# --------------------------------------------------------------------------

def test_restore_stops_a_real_backend_child_before_touching_the_database(
    monkeypatch, tmp_path
):
    """The ordering, proved against an actual uvicorn process.

    A real child is started against workspace A and handed to the launcher's
    process owner. Restore must terminate *that PID* before the journal is
    settled and before the replacement boundary — not merely observe a free port.
    """
    from launcher.restore import engine as engine_module
    from launcher.restore.verification import wait_for_backend_ready

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )
        wait_for_backend_ready(context.config.backend_url, process, timeout_seconds=60)
        backend_pid = process.pid
        assert process.poll() is None, "the real backend must be running before Restore"

        alive_at_journal_settlement: list[bool] = []
        real_quiesce = engine_module.quiesce_target_journal

        def watched_quiesce(path):
            alive_at_journal_settlement.append(process.poll() is None)
            return real_quiesce(path)

        monkeypatch.setattr(engine_module, "quiesce_target_journal", watched_quiesce)

        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )

        assert result.outcome is RestoreOutcome.COMPLETED
        assert alive_at_journal_settlement == [False], (
            "journal settlement ran while the original backend was still alive"
        )
        assert process.poll() is not None, "the original backend survived Restore"
        assert read_marker(workspace.database_path) == "workspace-B"
        # The exact recorded PID is the one that was stopped.
        with pytest.raises(OSError):
            os.kill(backend_pid, 0)
    finally:
        context.backend.stop()
        context.release()


def test_the_launcher_owns_the_backend_child_it_starts(monkeypatch, tmp_path):
    """`run_local_runtime` starts its child *through* the owner, not beside it.

    Starting through `context.backend.start` is stronger than spawning and then
    adopting: the owner's start waits for the child's own lock-acquisition
    handshake, so there is no window in which the launcher holds a handle to a
    process it cannot yet prove took the liveness lock. The maintenance lease is
    released immediately before, because the child is the one process allowed to
    hold that lock next.
    """
    import inspect

    from launcher import runtime

    body = inspect.getsource(runtime._run_locked_runtime)
    assert "context.backend.start(runtime_config, runtime_paths, startup.database_path)" in body
    assert "context.release_maintenance_lease()" in body
