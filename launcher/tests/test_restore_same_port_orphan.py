"""A real orphan holds the lock **and** the port. Both facts, one verdict.

The fourth-audit finding `P1-2`: `run_local_runtime()` checked the configured
port before it acquired the lifecycle context and before startup recovery ran.

That ordering was wrong about the most likely real case. A backend orphaned by a
hard launcher crash is a *running backend*: it holds the canonical
`backend-liveness.lock` for its whole lifetime, and it is still listening on the
configured port. So the port check fired first and raised `RuntimeLaunchError`
about a busy port — an exception, a traceback, and a message telling the user to
close another window — while the typed blocked `RecoveryResult` built for exactly
this situation never ran at all.

```text
before:  assert_port_available()  → RuntimeLaunchError  (traceback, wrong story)
after:   acquire lifecycle → resolve recovery → RESTORE_BLOCKED_EXIT_CODE
                                              → then assert_port_available()
```

The orphan here is a **separate process** that takes the real canonical lock and
binds and listens on the real configured port, then stays alive for the whole
test. Nothing less reproduces it: `flock` is per open file description, and a
port held by this process would not be the same fact.

Nothing in this module discovers, matches or signals anything but the exact PID
it created itself. The orphan is never killed by the launcher — that is the
point — and the fixture's own cleanup terminates only the `Popen` handle it owns.

The regression at the end is the other half of the rule: an unrelated program on
the configured port, with the canonical lock free, is an ordinary collision and
must still be reported as one. Recovery is not a licence to reinterpret every
busy port as a Restore problem.
"""

from pathlib import Path
import hashlib
import os
import socket
import subprocess
import sys

import pytest

from launcher import runtime
from launcher.restore.contracts import RECOVERY_BLOCKED_MESSAGE
from launcher.restore.phases import RestorePhase
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.config import build_runtime_config, resolve_runtime_paths
from launcher.tests.restore_fixtures import (
    build_workspace_database,
    free_port,
    make_workspace,
    read_marker,
)

# An orphan-shaped process: it takes the canonical liveness lock *and* listens on
# the configured port, exactly as a real crashed-launcher backend would, then
# waits. It prints once both are held so the test never races its own fixture.
ORPHAN = (
    "import fcntl, os, socket, sys, time\n"
    "lock_path, port = sys.argv[1], int(sys.argv[2])\n"
    "fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)\n"
    "fcntl.flock(fd, fcntl.LOCK_EX)\n"
    "server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
    "server.bind(('127.0.0.1', port))\n"
    "server.listen(8)\n"
    "print('held', flush=True)\n"
    "time.sleep(300)\n"
)


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def same_port_orphan(monkeypatch, tmp_path):
    """An isolated workspace whose canonical lock *and* port are held elsewhere.

    Yields `(workspace, port, orphan_pid)`. The teardown signals the exact
    `Popen` this fixture created and nothing else — no port lookup, no name
    match, no pattern.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    lock_path = workspace.restore_dir / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    port = free_port()

    orphan = subprocess.Popen(
        [sys.executable, "-c", ORPHAN, str(lock_path), str(port)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert orphan.stdout.readline().strip() == "held"
        yield workspace, port, orphan.pid
    finally:
        orphan.terminate()
        orphan.wait(timeout=10)


def unsafe_record(workspace) -> tuple[RestoreOperationStateStore, str]:
    """A durable `replacement_intent`: an interrupted, unrecovered Restore."""
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")
    launcher_workspace = RestoreWorkspace.for_database(workspace.database_path)
    store = RestoreOperationStateStore(launcher_workspace)
    operation_id = new_operation_id()
    launcher_workspace.create_operation_dir(operation_id)
    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=RestorePhase.REPLACEMENT_INTENT,
            created_at="2026-08-03T00:00:00+00:00",
            updated_at="2026-08-03T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety.filename,
        )
    )
    return store, operation_id


def guard_against_starting_a_backend(monkeypatch) -> list[str]:
    """Make every backend start path fail loudly, and record browser opens."""
    opened: list[str] = []

    def refuse_to_start(*_args, **_kwargs):  # pragma: no cover - must not be called
        raise AssertionError("a second backend must never start while startup is blocked")

    monkeypatch.setattr(runtime, "start_backend_process", refuse_to_start)
    monkeypatch.setattr(runtime, "start_owned_backend_process", refuse_to_start)
    monkeypatch.setattr(
        runtime, "open_runtime_browser", lambda _config: opened.append("opened")
    )
    return opened


def assert_orphan_still_alive(pid: int) -> None:
    """Signal 0 asks the kernel whether the PID exists; it changes nothing.

    An orphan is never killed. This launcher did not start it, so it has
    detection but no authority, and signalling a process it cannot account for
    would be a second failure mode rather than a safety measure.
    """
    os.kill(pid, 0)


# --------------------------------------------------------------------------
# The typed blocked result, through the real public boundary
# --------------------------------------------------------------------------

def test_a_same_port_orphan_with_an_unsafe_record_blocks_startup(
    same_port_orphan, monkeypatch, capsys
):
    """The case the old ordering could not reach: lock and port held together."""
    workspace, port, orphan_pid = same_port_orphan
    store, operation_id = unsafe_record(workspace)
    record_before = store.record_path.read_bytes()
    database_before = digest(workspace.database_path)

    opened = guard_against_starting_a_backend(monkeypatch)
    config = build_runtime_config(backend_port=port, open_browser=True)

    exit_code = runtime.run_local_runtime(config, resolve_runtime_paths())

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert opened == [], "the browser must stay closed while startup is blocked"

    printed = capsys.readouterr().out
    assert RECOVERY_BLOCKED_MESSAGE in printed
    # The old behaviour, named so it cannot come back quietly: the user was told
    # about a busy port, which is true and beside the point.
    assert "Порт" not in printed, "a same-port orphan was reported as a port collision"
    assert "Traceback" not in printed
    assert "RuntimeLaunchError" not in printed
    assert "RestoreLifecycleError" not in printed
    assert "MaintenanceLeaseError" not in printed

    # Nothing on disk moved, and the operation record is byte-identical.
    assert store.record_path.read_bytes() == record_before
    assert digest(workspace.database_path) == database_before
    assert store.read().operation_id == operation_id
    assert read_marker(workspace.database_path) == "workspace-B"
    assert_orphan_still_alive(orphan_pid)


def test_a_same_port_orphan_with_no_record_at_all_blocks_startup(
    same_port_orphan, monkeypatch, capsys
):
    """No Restore was ever attempted; the orphan alone is reason to refuse.

    Ordinary startup would put a second writer on one SQLite database, and the
    port being busy is a consequence of that rather than the reason to stop.
    """
    workspace, port, orphan_pid = same_port_orphan
    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert store.has_record() is False
    database_before = digest(workspace.database_path)

    opened = guard_against_starting_a_backend(monkeypatch)
    config = build_runtime_config(backend_port=port, open_browser=True)

    exit_code = runtime.run_local_runtime(config, resolve_runtime_paths())

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert opened == []

    printed = capsys.readouterr().out
    assert RECOVERY_BLOCKED_MESSAGE in printed
    assert "Порт" not in printed
    assert "Traceback" not in printed

    # And nothing was created on the way to saying so.
    assert store.has_record() is False
    assert digest(workspace.database_path) == database_before
    assert read_marker(workspace.database_path) == "workspace-A"
    assert_orphan_still_alive(orphan_pid)


@pytest.mark.parametrize("with_record", [True, False])
def test_no_exception_escapes_the_public_boundary_for_a_same_port_orphan(
    same_port_orphan, monkeypatch, with_record
):
    """`run_local_runtime` returns a code. It does not raise, for either shape."""
    from launcher.restore.context import RestoreLifecycleError

    workspace, port, _orphan_pid = same_port_orphan
    if with_record:
        unsafe_record(workspace)

    guard_against_starting_a_backend(monkeypatch)
    config = build_runtime_config(backend_port=port, open_browser=False)

    try:
        exit_code = runtime.run_local_runtime(config, resolve_runtime_paths())
    except runtime.RuntimeLaunchError as exc:  # pragma: no cover - the defect
        pytest.fail(f"the port check pre-empted startup recovery: {exc}")
    except RestoreLifecycleError as exc:  # pragma: no cover - a different defect
        pytest.fail(f"a lifecycle error escaped the launcher boundary: {exc}")

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE


def test_recovery_is_resolved_before_the_port_is_ever_checked(
    same_port_orphan, monkeypatch
):
    """The ordering itself, observed rather than inferred from the outcome."""
    workspace, port, _orphan_pid = same_port_orphan
    unsafe_record(workspace)

    order: list[str] = []
    real_recovery = runtime.resolve_restore_recovery
    real_port_check = runtime.assert_port_available

    def watched_recovery(context):
        order.append("recovery")
        return real_recovery(context)

    def watched_port_check(host, port_number):
        order.append("port")
        return real_port_check(host, port_number)

    monkeypatch.setattr(runtime, "resolve_restore_recovery", watched_recovery)
    monkeypatch.setattr(runtime, "assert_port_available", watched_port_check)
    guard_against_starting_a_backend(monkeypatch)

    exit_code = runtime.run_local_runtime(
        build_runtime_config(backend_port=port, open_browser=False),
        resolve_runtime_paths(),
    )

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    # The port was never even looked at: the verdict was already binding.
    assert order == ["recovery"]


# --------------------------------------------------------------------------
# The other half of the rule
# --------------------------------------------------------------------------

def test_an_unrelated_process_on_the_port_is_still_an_ordinary_collision(
    monkeypatch, tmp_path
):
    """A busy port with a free canonical lock is not a Restore problem.

    This is the case the reordering must not swallow. Some other program — not a
    backend, holding no lock — is using the configured port. Recovery allows
    startup, the port check then fails with its own unchanged message, and no
    backend or browser follows.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    opened = guard_against_starting_a_backend(monkeypatch)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        config = build_runtime_config(
            backend_port=occupied.getsockname()[1], open_browser=True
        )

        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    assert opened == [], "the browser must not open on a port collision"
    # The canonical lock was free throughout, so nothing was reported as blocked
    # recovery and no operation record was invented.
    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert store.has_record() is False
    assert read_marker(workspace.database_path) == "workspace-A"


def test_an_occupied_port_does_not_prevent_recovery_from_running(monkeypatch, tmp_path):
    """Recovery still resolves an interrupted Restore, then the port check fails.

    The two are independent, and in this order. A safe terminal record is closed
    out normally even though the run cannot continue, so the next start with a
    free port begins from a resolved workspace rather than replaying the same
    interrupted operation.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    launcher_workspace = RestoreWorkspace.for_database(workspace.database_path)
    store = RestoreOperationStateStore(launcher_workspace)
    operation_id = new_operation_id()
    launcher_workspace.create_operation_dir(operation_id)
    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=RestorePhase.PREPARED,
            created_at="2026-08-03T00:00:00+00:00",
            updated_at="2026-08-03T00:00:00+00:00",
        )
    )
    guard_against_starting_a_backend(monkeypatch)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        config = build_runtime_config(
            backend_port=occupied.getsockname()[1], open_browser=False
        )

        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    # `prepared` replaced nothing, so recovery closed it out and left the working
    # database alone — the accepted behaviour, reached before the port check.
    assert store.read().phase is RestorePhase.ABORTED
    assert read_marker(workspace.database_path) == "workspace-A"


def test_the_orphan_is_detected_but_never_signalled(same_port_orphan, monkeypatch):
    """Detection is not authority, and the launcher has only the first.

    Proved twice: the orphan is still alive after a full blocked run, and the
    launcher module contains none of the discover-and-kill shortcuts that would
    make killing it possible in the first place.
    """
    from launcher.tests.test_restore_context import executable_source

    workspace, port, orphan_pid = same_port_orphan
    unsafe_record(workspace)
    guard_against_starting_a_backend(monkeypatch)

    exit_code = runtime.run_local_runtime(
        build_runtime_config(backend_port=port, open_browser=False),
        resolve_runtime_paths(),
    )

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert_orphan_still_alive(orphan_pid)

    code = executable_source(runtime)
    for forbidden in ("pkill", "pgrep", "killall", "lsof", "psutil", "os.kill"):
        assert forbidden not in code, f"{forbidden} must never appear in the launcher"
