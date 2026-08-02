"""Pre-import lock acquisition, and the proof that *this* child made it.

Two findings meet here, and they are the same finding seen from two ends.

**The lock was taken too late.** It was acquired in the FastAPI lifespan, which
runs after Python has imported uvicorn, `app.main`, every router and the database
layer. Everything before that is a window in which a launcher-managed backend
exists and holds nothing:

```text
launcher spawns the child
→ child is importing the application, holding no lock
→ launcher dies hard
→ the next launcher sees a free lock and begins destructive work
→ the delayed child finishes importing and opens the database underneath it
```

The existing hard-crash test waits for the backend to be *ready* before killing
the helper, so it never entered this window at all.

**Owning a handle did not prove the lock.** `Popen` says the launcher started a
process; it does not say the process took the lock. Health does not either — it
answers after the import this whole mechanism exists to gate.

So the child acquires the lock before importing anything from the application and
reports that over a one-run inherited pipe, and the launcher waits for that exact
report. The decisive test below really pauses a real child before its acquisition,
really `os._exit()`s its launcher, and then checks what the delayed child can do
once a new launcher owns the workspace.
"""

from pathlib import Path
import hashlib
import os
import subprocess
import sys
import textwrap
import time

import pytest

from launcher import runtime
from launcher.restore.backend_handshake import (
    BackendHandshakeError,
    new_backend_handshake,
)
from launcher.restore.context import LauncherLifecycleContext
from launcher.restore.contracts import RestoreOutcome
from launcher.restore.engine import execute_restore
from launcher.restore.verification import wait_for_backend_ready

from launcher.tests.restore_fixtures import (
    free_port,
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def fingerprint(path: Path) -> tuple[int, int, int, str]:
    """Content and stat identity, so "untouched" is a claim about bytes.

    Size and mtime alone would miss a same-size rewrite inside one filesystem
    timestamp tick, and "the delayed child quietly opened and migrated the
    database" is exactly a same-name, same-size-ish modification.
    """
    info = path.stat()
    return (
        info.st_size,
        info.st_dev,
        info.st_ino,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def wait_until(predicate, *, timeout_seconds: float = 60.0, interval: float = 0.05) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


class _FakeChild:
    """A process handle that never writes and can be declared dead on demand."""

    def __init__(self, exit_code=None) -> None:
        self._exit_code = exit_code
        self.terminated = False

    def poll(self):
        return self._exit_code

    def exit(self, code: int = 0) -> None:
        self._exit_code = code

    def send_signal(self, _signal):
        self.terminated = True
        self._exit_code = -15

    def wait(self, timeout=None):
        self._exit_code = self._exit_code if self._exit_code is not None else 0
        return self._exit_code

    def kill(self):
        self.terminated = True
        self._exit_code = -9


# --------------------------------------------------------------------------
# The handshake mechanism
# --------------------------------------------------------------------------

def test_the_handshake_accepts_this_start_s_own_report():
    handshake = new_backend_handshake()
    try:
        from app.launcher_backend_entrypoint import HANDSHAKE_ACQUIRED_PREFIX

        os.write(
            handshake.write_fd,
            f"{HANDSHAKE_ACQUIRED_PREFIX}{handshake.token}\n".encode("utf-8"),
        )
        handshake.close_child_end()

        assert handshake.await_acquisition(None, timeout_seconds=5) == handshake.token
    finally:
        handshake.close()


def test_a_token_from_a_different_start_is_refused():
    """Stale or replayed evidence cannot satisfy a new child start."""
    from app.launcher_backend_entrypoint import HANDSHAKE_ACQUIRED_PREFIX

    previous = new_backend_handshake()
    current = new_backend_handshake()
    try:
        assert previous.token != current.token
        # The payload a previous run's child would have written, replayed into
        # this run's pipe.
        os.write(
            current.write_fd,
            f"{HANDSHAKE_ACQUIRED_PREFIX}{previous.token}\n".encode("utf-8"),
        )
        current.close_child_end()

        with pytest.raises(BackendHandshakeError, match="different start"):
            current.await_acquisition(None, timeout_seconds=5)
    finally:
        previous.close()
        current.close()


def test_an_unrecognized_payload_is_refused():
    handshake = new_backend_handshake()
    try:
        os.write(handshake.write_fd, b"ready\n")
        handshake.close_child_end()

        with pytest.raises(BackendHandshakeError, match="unrecognized"):
            handshake.await_acquisition(None, timeout_seconds=5)
    finally:
        handshake.close()


def test_a_child_that_exits_before_reporting_is_a_failure():
    """Reported as soon as the exit is visible, not at the deadline.

    The write end is deliberately left open here, which is how a descriptor
    inherited further down a process tree behaves: the pipe never reaches EOF, so
    the exit itself is the only signal available. Without the liveness check
    inside the wait this would sit until the full bound expired, on a child that
    was already never going to write.
    """
    handshake = new_backend_handshake()
    child = _FakeChild(exit_code=None)
    try:
        child.exit(21)

        started = time.monotonic()
        with pytest.raises(BackendHandshakeError, match="exited before reporting"):
            handshake.await_acquisition(child, timeout_seconds=30)
        assert time.monotonic() - started < 10
    finally:
        handshake.close()


def test_a_closed_handshake_without_a_report_is_a_failure():
    """EOF is an answer: the child will never write now."""
    handshake = new_backend_handshake()
    try:
        handshake.close_child_end()

        with pytest.raises(BackendHandshakeError, match="closed the handshake"):
            handshake.await_acquisition(None, timeout_seconds=10)
    finally:
        handshake.close()


def test_a_silent_child_times_out():
    """Bounded, always. A wedged child may never hold Restore open."""
    handshake = new_backend_handshake()
    child = _FakeChild(exit_code=None)
    try:
        started = time.monotonic()
        with pytest.raises(BackendHandshakeError, match="within its bound"):
            handshake.await_acquisition(child, timeout_seconds=0.5)
        assert time.monotonic() - started < 30
    finally:
        handshake.close()


def test_the_handshake_uses_no_pid_port_or_pattern_evidence():
    from launcher.restore import backend_handshake as handshake_module
    from launcher.tests.test_restore_context import executable_source

    code = executable_source(handshake_module)
    for forbidden in ("pkill", "pgrep", "killall", "lsof", "psutil", "getoutput"):
        assert forbidden not in code
    # No PID-file authority and no port evidence: the token and the pipe are the
    # only things this module reads.
    assert "pid" not in code.lower()
    assert "socket" not in code


# --------------------------------------------------------------------------
# The entrypoint takes the lock before the application is imported
# --------------------------------------------------------------------------

def test_the_launcher_starts_the_pre_import_entrypoint_not_uvicorn():
    """The ordering is enforced by which module is executed."""
    import inspect

    assert runtime.BACKEND_ENTRYPOINT_MODULE == "app.launcher_backend_entrypoint"
    source = inspect.getsource(runtime.start_backend_process)
    assert "BACKEND_ENTRYPOINT_MODULE" in source
    assert '"uvicorn"' not in source


def test_the_entrypoint_imports_the_application_only_after_the_lock():
    """A structural check: no application import at module scope.

    `app.main` pulls in every router and the database layer. If it were imported
    while this module loaded, the lock would again be taken after the very work
    it is supposed to precede — and the check would be a comment rather than a
    property.
    """
    import ast
    import inspect

    from app import launcher_backend_entrypoint

    tree = ast.parse(inspect.getsource(launcher_backend_entrypoint))
    module_level_imports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            module_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module_level_imports.append(node.module or "")

    for name in module_level_imports:
        assert not name.startswith("app."), f"{name} must not be imported before the lock"
        assert name != "uvicorn", "uvicorn must not be imported before the lock"

    # And the serving function is the only place the application is named.
    serving = inspect.getsource(launcher_backend_entrypoint.run_backend)
    assert "uvicorn" in serving
    assert "app.main:app" in serving


def test_a_real_backend_child_reports_the_lock_before_health_answers(monkeypatch, tmp_path):
    """The handshake precedes health verification, with a real process."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert context.no_backend_is_alive() is True

        # `start` returns only once the child reported the lock, so the lock is
        # already held here — before any health request has been made.
        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )
        from launcher.restore.context import backend_liveness_lock_is_free

        assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is False, (
            "the handshake must not return before the child holds the lock"
        )

        wait_for_backend_ready(context.config.backend_url, process, timeout_seconds=90)
    finally:
        context.backend.stop()
        context.release()


def test_a_child_cannot_start_while_the_launcher_holds_the_lease(monkeypatch, tmp_path):
    """The lease and the child's own acquisition are the same lock."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.stop_backend()
        assert context.maintenance_lease.held is True

        with pytest.raises(BackendHandshakeError):
            context.backend.start(
                context.config, context.paths, workspace.database_path
            )
        assert context.backend.is_running is False
    finally:
        context.release()


# --------------------------------------------------------------------------
# The delayed pre-lock child after a hard launcher death
# --------------------------------------------------------------------------

# A backend child paused *before* its lock acquisition. It uses the production
# entrypoint's own functions, so nothing about the ordering is simulated: the only
# thing this wrapper adds is the pause, and the pause is what puts the child in
# the window the finding is about.
DELAYED_CHILD = textwrap.dedent(
    """
    import os, sys, time
    repository_root, backend_dir, release_file, report_file = sys.argv[1:5]
    sys.path.insert(0, repository_root)
    sys.path.insert(0, backend_dir)

    from app import launcher_backend_entrypoint as entrypoint
    from app.services.backend_liveness import BackendLivenessError

    # Paused here: the process exists, the launcher owns its handle, and it holds
    # nothing at all. This is the window.
    while not os.path.exists(release_file):
        time.sleep(0.02)

    try:
        entrypoint.acquire_lock_before_import()
    except BackendLivenessError:
        outcome = "refused"
    else:
        outcome = "acquired"

    # Reported before anything else could import the application, so the report
    # itself proves what had and had not been imported at that moment.
    with open(report_file, "w") as handle:
        handle.write(outcome + "\\n")
        handle.write(str("app.main" in sys.modules) + "\\n")
        handle.write(str("uvicorn" in sys.modules) + "\\n")
        handle.flush()
        os.fsync(handle.fileno())

    os._exit(0 if outcome == "acquired" else entrypoint.LOCK_REFUSED_EXIT_CODE)
    """
)

# A launcher-like helper that starts the delayed child and then dies hard. No
# atexit, no finally, no lock release, no child cleanup — the child is left in the
# pre-lock window with nobody owning it.
HELPER_LAUNCHER_WITH_DELAYED_CHILD = textwrap.dedent(
    """
    import os, subprocess, sys
    (
        repository_root,
        backend_dir,
        user_data_dir,
        database_path,
        child_script,
        release_file,
        report_file,
        pid_file,
    ) = sys.argv[1:9]
    sys.path.insert(0, repository_root)
    sys.path.insert(0, backend_dir)
    os.environ["COSMETIC_WORKSHOP_USER_DATA_DIR"] = user_data_dir
    os.environ.pop("COSMETIC_WORKSHOP_DB_PATH", None)

    from launcher.restore.workspace import RestoreWorkspace
    from pathlib import Path

    lock_path = RestoreWorkspace.for_database(Path(database_path)).backend_liveness_lock_path
    env = os.environ.copy()
    env["COSMETIC_WORKSHOP_BACKEND_LIVENESS_LOCK"] = str(lock_path)
    env["COSMETIC_WORKSHOP_DB_PATH"] = database_path
    env["PYTHONPATH"] = backend_dir

    child = subprocess.Popen(
        [sys.executable, "-c", child_script, repository_root, backend_dir, release_file, report_file],
        env=env,
    )
    with open(pid_file, "w") as handle:
        handle.write(str(child.pid))
        handle.flush()
        os.fsync(handle.fileno())

    # A hard launcher death, with the child still paused before its acquisition.
    os._exit(0)
    """
)


def test_a_delayed_pre_lock_child_cannot_start_after_a_new_launcher_owns_the_lease(
    monkeypatch, tmp_path
):
    """The finding, end to end, with real processes and real timing.

    A helper launcher starts a backend child that is paused *before* it acquires
    the liveness lock, then dies hard. A new launcher starts, takes the retained
    maintenance lease, and only then is the delayed child released. It must fail
    to acquire, must exit before importing the application, must not touch the
    database, and Restore must remain safe throughout.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    release_file = tmp_path / "release-the-child"
    report_file = tmp_path / "delayed-child-report.txt"
    pid_file = tmp_path / "delayed-child.pid"
    helper_log = tmp_path / "delayed-helper.log"

    log_handle = open(helper_log, "w")
    helper = subprocess.Popen(
        [
            sys.executable,
            "-c",
            HELPER_LAUNCHER_WITH_DELAYED_CHILD,
            str(REPOSITORY_ROOT),
            str(REPOSITORY_ROOT / "backend"),
            str(workspace.base_dir),
            str(workspace.database_path),
            DELAYED_CHILD,
            str(release_file),
            str(report_file),
            str(pid_file),
        ],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    child_pid = None
    context = None
    try:
        helper.wait(timeout=120)
        log_handle.close()
        assert pid_file.exists(), (
            f"the helper never reported a child pid: {helper_log.read_text()[-2000:]}"
        )
        child_pid = int(pid_file.read_text().strip())
        assert helper.poll() is not None, "the helper launcher must have died"
        os.kill(child_pid, 0)

        # The child is alive and holds nothing: this is the window the previous
        # hard-crash test never entered, because it waited for readiness first.
        from launcher.restore.context import backend_liveness_lock_is_free

        lock_path = workspace.restore_dir / "backend-liveness.lock"
        assert backend_liveness_lock_is_free(lock_path) is True, (
            "a child paused before acquisition holds nothing, which is the problem"
        )

        before = fingerprint(workspace.database_path)

        # A new launcher takes and *retains* the lease.
        context = LauncherLifecycleContext.acquire(
            *_config_and_paths()
        )
        context.stop_backend()
        assert context.maintenance_lease.held is True

        # Only now is the delayed child released.
        release_file.write_text("go")
        assert wait_until(lambda: report_file.exists(), timeout_seconds=90), (
            "the delayed child never reported"
        )
        assert wait_until(lambda: _pid_is_gone(child_pid), timeout_seconds=60), (
            "the delayed child must exit rather than continue"
        )

        outcome, imported_app_main, imported_uvicorn = (
            report_file.read_text().strip().splitlines()
        )
        assert outcome == "refused", (
            "the delayed child acquired the lock the new launcher was holding"
        )
        assert imported_app_main == "False", "the application was imported anyway"
        assert imported_uvicorn == "False", "uvicorn was imported anyway"

        # And it touched nothing on the way out.
        assert fingerprint(workspace.database_path) == before

        # Restore remains safe: the workspace is exclusively this launcher's.
        source = make_source_backup(tmp_path, "workspace-B")
        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
        assert result.outcome is RestoreOutcome.COMPLETED
        assert read_marker(workspace.database_path) == "workspace-B"
    finally:
        if not log_handle.closed:
            log_handle.close()
        if context is not None:
            context.release()
        # This test created the child, so it may signal that exact PID.
        if child_pid is not None and not _pid_is_gone(child_pid):
            try:
                os.kill(child_pid, 15)
                wait_until(lambda: _pid_is_gone(child_pid), timeout_seconds=15)
                if not _pid_is_gone(child_pid):
                    os.kill(child_pid, 9)
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


def _config_and_paths():
    from launcher.config import build_runtime_config, resolve_runtime_paths

    return (
        build_runtime_config(backend_port=free_port(), open_browser=False),
        resolve_runtime_paths(),
    )
