"""The backend-liveness lock, and what survives a hard launcher crash.

The finding: `BackendProcessOwner` holds a `Popen` **in the launcher's memory**.
If the launcher dies hard — `SIGKILL`, panic, power loss — that handle is gone
while the uvicorn child keeps running and keeps the working database open. The
next launcher owns no process, so `stop_backend()` would report that nothing was
running, and Restore would replace a database underneath a live writer.

A PID file cannot fix it: PIDs are reused, so a recorded PID that is alive may
belong to something else. A listening port cannot either: a port describes a
socket, not who holds a database, and during Restore the port is free by design.

What does fix it is a lock **held by the backend process itself**. The kernel
releases an `fcntl.flock` when the holder dies, for any reason, with no cleanup
code of ours involved. So a held lock means a live backend, whoever started it.

The decisive test here is `test_a_backend_orphaned_by_a_hard_launcher_death...`,
which really does start a launcher-like helper, really does start a real backend
through it, really does `os._exit()` the helper, and then checks what a fresh
launcher concludes. Anything less would be testing the mock.

**Detection is not authority to kill.** An orphan this launcher never started is
never signalled — not by PID file, port, name or pattern. Restore refuses and
says so.
"""

from pathlib import Path
import os
import subprocess
import sys
import textwrap
import time

import pytest

from app.services.backend_liveness import (
    BACKEND_LIVENESS_LOCK_ENV,
    BackendLivenessError,
    acquire_backend_liveness_lock,
    holds_liveness_lock,
    release_backend_liveness_lock,
)

from launcher.restore.context import (
    LauncherLifecycleContext,
    RestoreLifecycleError,
    backend_liveness_lock_is_free,
)
from launcher.restore.contracts import (
    RECOVERY_BLOCKED_MESSAGE,
    RecoveryResult,
    RestoreOutcome,
)
from launcher.restore.engine import execute_restore
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
from launcher.restore.verification import wait_for_backend_ready
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def wait_until(predicate, *, timeout_seconds: float = 30.0, interval: float = 0.05) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


# --------------------------------------------------------------------------
# The lock module itself
# --------------------------------------------------------------------------

def test_no_lock_is_taken_when_the_launcher_did_not_assign_one(monkeypatch, tmp_path):
    """The ordinary test client and a direct import claim nothing."""
    monkeypatch.delenv(BACKEND_LIVENESS_LOCK_ENV, raising=False)

    assert acquire_backend_liveness_lock() is None
    assert holds_liveness_lock() is False


def test_the_lock_is_taken_when_the_launcher_assigns_one(monkeypatch, tmp_path):
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    monkeypatch.setenv(BACKEND_LIVENESS_LOCK_ENV, str(lock_path))
    try:
        assert acquire_backend_liveness_lock() == lock_path
        assert holds_liveness_lock() is True
        assert backend_liveness_lock_is_free(lock_path) is False
    finally:
        release_backend_liveness_lock()

    assert backend_liveness_lock_is_free(lock_path) is True


def test_a_second_holder_in_another_process_is_refused(monkeypatch, tmp_path):
    """flock is per open file description, so this needs a real second process."""
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    monkeypatch.setenv(BACKEND_LIVENESS_LOCK_ENV, str(lock_path))
    acquire_backend_liveness_lock()
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import fcntl, os, sys\n"
                "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
                "try:\n"
                "    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
                "except OSError:\n"
                "    print('refused')\n"
                "else:\n"
                "    print('acquired')\n",
                str(lock_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.stdout.strip() == "refused"
    finally:
        release_backend_liveness_lock()


def test_acquiring_twice_in_one_process_is_idempotent(monkeypatch, tmp_path):
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    monkeypatch.setenv(BACKEND_LIVENESS_LOCK_ENV, str(lock_path))
    try:
        assert acquire_backend_liveness_lock() == lock_path
        assert acquire_backend_liveness_lock() == lock_path
    finally:
        release_backend_liveness_lock()


def test_startup_fails_when_an_assigned_lock_cannot_be_taken(monkeypatch, tmp_path):
    """Two writers on one SQLite database is the thing being prevented."""
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl, os, sys, time\n"
            "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
            "fcntl.flock(fd, fcntl.LOCK_EX)\n"
            "print('held', flush=True)\n"
            "time.sleep(120)\n",
            str(lock_path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "held"
        monkeypatch.setenv(BACKEND_LIVENESS_LOCK_ENV, str(lock_path))

        with pytest.raises(BackendLivenessError):
            acquire_backend_liveness_lock()
    finally:
        holder.terminate()
        holder.wait(timeout=10)


# --------------------------------------------------------------------------
# A real backend child holds it
# --------------------------------------------------------------------------

def test_a_real_backend_child_holds_the_liveness_lock(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert context.no_backend_is_alive() is True

        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )
        wait_for_backend_ready(context.config.backend_url, process, timeout_seconds=90)

        assert context.no_backend_is_alive() is False, (
            "a running backend must hold the liveness lock"
        )
        assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is False
    finally:
        context.backend.stop()
        context.release()


def test_a_normal_stop_releases_the_liveness_lock(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )
        wait_for_backend_ready(context.config.backend_url, process, timeout_seconds=90)
        assert context.no_backend_is_alive() is False

        proof = context.backend.stop()
        assert proof.confirmed_stopped is True
        context.backend.wait_until_liveness_lock_released(
            context.backend_liveness_lock_path
        )

        assert context.no_backend_is_alive() is True, (
            "the lock must be free once the backend has exited"
        )
    finally:
        context.release()


def test_restore_proceeds_once_the_lock_is_free(monkeypatch, tmp_path):
    """The positive case, so the gate is not simply blocking everything."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )
        wait_for_backend_ready(context.config.backend_url, process, timeout_seconds=90)

        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.backend.stop()
        context.release()

    assert result.outcome is RestoreOutcome.COMPLETED
    assert read_marker(workspace.database_path) == "workspace-B"


# --------------------------------------------------------------------------
# The hard launcher death
# --------------------------------------------------------------------------

HELPER_LAUNCHER = textwrap.dedent(
    """
    import os, sys
    repository_root, user_data_dir, database_path, port, pid_file = sys.argv[1:6]
    sys.path.insert(0, repository_root)
    sys.path.insert(0, os.path.join(repository_root, "backend"))
    os.environ["COSMETIC_WORKSHOP_USER_DATA_DIR"] = user_data_dir
    os.environ.pop("COSMETIC_WORKSHOP_DB_PATH", None)

    from launcher.config import build_runtime_config, resolve_runtime_paths
    from launcher.restore.context import LauncherLifecycleContext
    from launcher.restore.verification import wait_for_backend_ready

    config = build_runtime_config(backend_port=int(port), open_browser=False)
    context = LauncherLifecycleContext.acquire(config, resolve_runtime_paths())
    process = context.backend.start(config, context.paths, database_path)
    wait_for_backend_ready(config.backend_url, process, timeout_seconds=120)

    # Reported through a file rather than a pipe. The backend inherits this
    # helper's standard streams, so a pipe would stay open after the helper dies
    # and any read of it in the parent would block on a process that is
    # deliberately being left running.
    with open(pid_file, "w") as handle:
        handle.write(str(process.pid))
        handle.flush()
        os.fsync(handle.fileno())

    # A hard launcher death: no atexit, no finally, no lock release, no child
    # cleanup. The uvicorn child is left running and still holding its liveness
    # lock, which is exactly the situation the next launcher has to notice.
    os._exit(0)
    """
)


@pytest.fixture
def orphaned_backend(monkeypatch, tmp_path):
    """A real backend orphaned by a helper launcher that died hard."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    pid_file = tmp_path / "orphan-backend.pid"
    helper_log = tmp_path / "helper.log"
    # Streams go to a file, never a pipe: the backend inherits them and is meant
    # to outlive the helper, so a pipe would keep a reader blocked forever.
    log_handle = open(helper_log, "w")
    helper = subprocess.Popen(
        [
            sys.executable,
            "-c",
            HELPER_LAUNCHER,
            str(REPOSITORY_ROOT),
            str(workspace.base_dir),
            str(workspace.database_path),
            str(port),
            str(pid_file),
        ],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    backend_pid = None
    try:
        helper.wait(timeout=180)
        log_handle.close()
        assert pid_file.exists(), (
            f"the helper launcher never reported a backend pid: {helper_log.read_text()[-2000:]}"
        )
        backend_pid = int(pid_file.read_text().strip())
        # The helper is gone; the backend it started is not.
        assert helper.poll() is not None, "the helper launcher must have exited"
        os.kill(backend_pid, 0)
        yield workspace, backend_pid
    finally:
        if not log_handle.closed:
            log_handle.close()
        # This test created the backend, so it may terminate that exact PID.
        if backend_pid is not None:
            try:
                os.kill(backend_pid, 15)
                wait_until(lambda: _pid_is_gone(backend_pid), timeout_seconds=15)
                if not _pid_is_gone(backend_pid):
                    os.kill(backend_pid, 9)
            except ProcessLookupError:
                pass
        if helper.poll() is None:
            helper.kill()
            helper.wait(timeout=10)


def _pid_is_gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def test_a_backend_orphaned_by_a_hard_launcher_death_is_still_detected(orphaned_backend):
    """The finding, end to end with real processes.

    A new launcher owns no process handle at all — the previous one died with it.
    The orphan is nonetheless detectable, because it still holds the lock.
    """
    workspace, backend_pid = orphaned_backend
    context = LauncherLifecycleContext.acquire(*_config_and_paths())
    try:
        assert context.backend.has_process is False, (
            "the new launcher owns no process, which is the whole problem"
        )
        assert context.no_backend_is_alive() is False, (
            "the orphaned backend must be detected through the held lock"
        )
        os.kill(backend_pid, 0)
    finally:
        context.release()


def test_restore_is_blocked_by_an_orphaned_backend(orphaned_backend, tmp_path):
    workspace, backend_pid = orphaned_backend
    source = make_source_backup(tmp_path, "workspace-B")
    context = LauncherLifecycleContext.acquire(*_config_and_paths())
    try:
        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ABORTED
    assert result.restore_succeeded is False
    # No replacement happened, and the orphan is untouched.
    assert read_marker(workspace.database_path) == "workspace-A"
    os.kill(backend_pid, 0)


def test_startup_recovery_is_blocked_by_an_orphaned_backend(orphaned_backend):
    """Recovery would replace the database from the safety copy; it must not.

    An orphan holding the liveness lock is an **expected** condition of this gate,
    so it is reported as a typed `RecoveryResult`, not raised. `run_local_runtime`
    branches on that result; a `RestoreLifecycleError` escaping instead would turn
    a designed refusal into an unhandled exception and a stack trace, and the
    launcher would print a traceback where it should print one fixed sentence.
    """
    workspace, backend_pid = orphaned_backend
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")
    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    operation_id = new_operation_id()
    store.workspace.create_operation_dir(operation_id)
    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=RestorePhase.REPLACEMENT_INTENT,
            created_at="2026-08-02T00:00:00+00:00",
            updated_at="2026-08-02T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety.filename,
        )
    )

    context = LauncherLifecycleContext.acquire(*_config_and_paths())
    try:
        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert isinstance(result, RecoveryResult)
    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.message == RECOVERY_BLOCKED_MESSAGE
    assert result.blocks_browser is True
    # The phase that is really on disk is reported; nothing was transitioned.
    assert result.durable_phase is RestorePhase.REPLACEMENT_INTENT

    # No rollback replacement occurred while the orphan was alive.
    assert read_marker(workspace.database_path) == "workspace-B"
    assert store.read().phase is RestorePhase.REPLACEMENT_INTENT
    os.kill(backend_pid, 0)


def test_an_orphan_is_never_killed_by_discovery(orphaned_backend, tmp_path):
    """Detection is not authority. The launcher refuses; it does not signal."""
    workspace, backend_pid = orphaned_backend
    source = make_source_backup(tmp_path, "workspace-B")
    context = LauncherLifecycleContext.acquire(*_config_and_paths())
    try:
        execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    # Still alive: this launcher did not start it, so it does not stop it.
    os.kill(backend_pid, 0)


def test_the_liveness_proof_uses_no_pid_port_or_pattern_lookup():
    """Mechanical check over the executable source, comments excluded."""
    from launcher.restore import context as context_module
    from launcher.tests.test_restore_context import executable_source

    code = executable_source(context_module)
    for forbidden in ("pkill", "pgrep", "killall", "lsof", "psutil", "getoutput"):
        assert forbidden not in code


def _config_and_paths():
    from launcher.config import build_runtime_config, resolve_runtime_paths
    from launcher.tests.restore_fixtures import free_port

    return (
        build_runtime_config(backend_port=free_port(), open_browser=False),
        resolve_runtime_paths(),
    )
