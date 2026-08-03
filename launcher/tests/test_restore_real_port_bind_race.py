"""The real post-probe / pre-bind race, with real processes and a real bind.

The sixth-audit finding `P1-1`, and the finding `P2-1` about how it was evidenced.

## What was actually broken

`assert_port_available()` binds a probe, closes it and returns. It establishes
availability at an instant and reserves nothing. Uvicorn then performed the real
bind *after* the child had already reported a successful start:

```text
parent probes the port          ← free
parent spawns the child
child takes the liveness lock
child reports "started"         ← the launcher believes the backend is up
another program takes the port  ← the real race, and nothing was watching it
child imports uvicorn
uvicorn tries to bind           ← EADDRINUSE
child exits
```

The launcher saw a child that started and then died. `wait_for_backend_ready()`
classifies that as `BackendVerificationError`, and during rollback recovery a
verification failure ends the operation at terminal `recovery_blocked` — a
support-only state, reached because another program held a socket.

## What was wrong with the previous evidence

The fifth correction's late-collision test monkeypatched
`BackendProcessOwner.start` and raised `BackendPortUnavailableError` directly. That
proves the *routing* — that such an exception becomes a retryable refusal — and
nothing at all about whether the product can ever produce one from a real bind.
It could not: the real bind happened after the handshake, so the real race never
reached that routing.

Those synthetic tests remain, correctly labelled as exception-routing unit tests,
in `launcher/tests/test_restore_retryable_port_collision.py`. **This** module is
the regression proof, and it uses:

```text
the real parent           launcher.runtime / BackendProcessOwner
the real child entrypoint python -m app.launcher_backend_entrypoint
the real handshake        the one-run inherited pipe and token
the real configured port  the same port the config names
the real bind             socket.bind() inside the child
the real process exit     observed through the owned handle
```

Nothing here monkeypatches `BackendProcessOwner.start`, raises
`BackendPortUnavailableError` by hand, or reads uvicorn's output. The only
test-only coordination is *when* the competing socket holder binds: it is armed to
take the port during the parent's early probe, which is exactly the window the
defect lived in. The production child startup path and the production bind run
untouched.
"""

from pathlib import Path
import hashlib
import socket
import subprocess
import sys

import pytest

from launcher import runtime
from launcher.config import build_runtime_config, resolve_runtime_paths
from launcher.restore import engine as engine_module
from launcher.restore.backend_handshake import (
    BackendHandshakeError,
    BackendSocketUnavailableError,
    new_backend_handshake,
)
from launcher.restore.context import backend_liveness_lock_is_free
from launcher.restore.contracts import (
    BACKEND_PORT_UNAVAILABLE_MESSAGE,
    RECOVERY_BLOCKED_MESSAGE,
    RestoreOutcome,
)
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
from launcher.restore.verification import (
    RetryableBackendStartError,
    verify_restored_backend,
)
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    free_port,
    make_workspace,
    migrating_startup,
    read_marker,
    request_for,
    make_source_backup,
)


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def can_bind(host: str, port: int) -> bool:
    """Whether the exact configured address is bindable right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


class CompetingListener:
    """A real listening socket on the exact configured port.

    Not a stand-in for anything: it is an ordinary program holding a port, which
    is what the user actually hits. It holds **no** canonical liveness lock, so
    it is an *unrelated* collision rather than an orphaned backend.
    """

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None

    def bind(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(8)
        self._socket = server

    def release(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    @property
    def holding(self) -> bool:
        return self._socket is not None


class ArmedAtTheProbe:
    """Take the port during the parent's early probe — the exact defect window.

    The production probe still runs, for real, and still passes: the wrapper calls
    it first and only then binds the competing listener. What follows is entirely
    production code — `Popen`, the real entrypoint, the real lock, the real
    `bind()`, the real handshake — reaching a port that is genuinely taken.

    This is test-only *coordination*, not a substitute for any production step.
    Without it the window is a few milliseconds wide and the test would be a
    coin flip.
    """

    def __init__(self, monkeypatch, host: str, port: int) -> None:
        self.listener = CompetingListener(host, port)
        self.probes = 0
        self.armed = True
        real_probe = runtime.assert_port_available

        def probe_then_take(probe_host, probe_port):
            real_probe(probe_host, probe_port)
            self.probes += 1
            if self.armed and not self.listener.holding:
                self.listener.bind()

        monkeypatch.setattr(runtime, "assert_port_available", probe_then_take)

    def disarm(self) -> None:
        """The user closed the other program.

        Disarming rather than undoing the patch: `monkeypatch.undo()` would also
        revert the isolated-workspace environment this test depends on, and the
        production probe should keep running for the second launch anyway.
        """
        self.armed = False
        self.release()

    def release(self) -> None:
        self.listener.release()


def publish_rollback_in_progress(workspace):
    """A durable `rollback_in_progress` with a real verified safety copy."""
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")
    launcher_workspace = RestoreWorkspace.for_database(workspace.database_path)
    store = RestoreOperationStateStore(launcher_workspace)
    operation_id = new_operation_id()
    launcher_workspace.create_operation_dir(operation_id)
    candidate = launcher_workspace.restore_dir / operation_id / "candidate.sqlite"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    build_workspace_database(candidate, "workspace-B")
    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=RestorePhase.ROLLBACK_IN_PROGRESS,
            created_at="2026-08-03T00:00:00+00:00",
            updated_at="2026-08-03T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety.filename,
        )
    )
    return store, operation_id, candidate


def real_verification_services(database_path):
    """The production verifier; only the startup migration is stubbed."""
    from launcher.restore.engine import RestoreServices

    return RestoreServices(
        verify_backend=verify_restored_backend,
        initialize_startup=migrating_startup(database_path),
    )


# --------------------------------------------------------------------------
# 1. A successful handshake proves the lock *and* the real socket
# --------------------------------------------------------------------------

def test_readiness_proves_both_the_liveness_lock_and_the_listening_socket(
    monkeypatch, tmp_path
):
    """The conjunction, observed the moment `start` returns.

    Both facts are checked from *outside* the child: the canonical lock cannot be
    taken, and the exact configured port cannot be bound. Neither was true of the
    old handshake, which returned with the port still free.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is True
        assert can_bind(context.config.host, context.config.backend_port) is True

        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )

        # `start` returned, so `ready:` arrived. Both halves must already hold.
        assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is False, (
            "readiness returned before the child held the canonical lock"
        )
        assert can_bind(context.config.host, context.config.backend_port) is False, (
            "readiness returned before the child owned the listening socket"
        )
        assert process.poll() is None
    finally:
        context.backend.stop()
        context.release()

    # And teardown gives both back.
    assert can_bind(workspace.context and context.config.host, context.config.backend_port) is True
    assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is True


def test_the_backend_serves_through_the_socket_it_proved_it_owned(monkeypatch, tmp_path):
    """One socket, from the ownership proof through to serving requests.

    If uvicorn were binding a second time, the port would be free between the
    handshake and that bind — and a request would fail until it landed. Here the
    same socket carries the readiness proof and then the traffic.
    """
    from launcher.restore.verification import wait_for_backend_ready

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        process = context.backend.start(
            context.config, context.paths, workspace.database_path
        )
        # Occupied from the instant readiness returned, with no gap to observe.
        assert can_bind(context.config.host, context.config.backend_port) is False

        payload = wait_for_backend_ready(
            context.config.backend_url, process, timeout_seconds=90
        )
        assert isinstance(payload, dict) and payload.get("status")
    finally:
        context.backend.stop()
        context.release()


# --------------------------------------------------------------------------
# 2. The real post-probe / pre-bind collision
# --------------------------------------------------------------------------

def test_a_real_bind_collision_is_refused_through_the_real_child(monkeypatch, tmp_path):
    """The whole defect, reproduced with production code on both sides.

    The parent's real probe passes, a real program then takes the exact port, and
    the real child reaches its real `bind()`. What comes back is the ordinary
    port-collision error — not a started-then-died backend.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        with pytest.raises(runtime.BackendPortUnavailableError, match="уже занят"):
            context.backend.start(
                context.config, context.paths, workspace.database_path
            )

        assert armed.probes >= 1, "the production probe did not run"
        # No child survived, and the launcher is not tracking one.
        assert context.backend.is_running is False
        # The child released the canonical lock by exiting.
        assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is True
    finally:
        armed.release()
        context.backend.stop()
        context.release()

    # And with the competing listener gone, the port is free again.
    assert can_bind(context.config.host, context.config.backend_port) is True


def test_the_refusal_is_a_runtime_launch_error_with_the_unchanged_message(
    monkeypatch, tmp_path
):
    """The ordinary contract is preserved, not replaced by a new one."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        with pytest.raises(runtime.RuntimeLaunchError) as raised:
            context.backend.start(
                context.config, context.paths, workspace.database_path
            )
    finally:
        armed.release()
        context.backend.stop()
        context.release()

    assert isinstance(raised.value, runtime.BackendPortUnavailableError)
    message = str(raised.value)
    assert "Порт" in message and "уже занят" in message
    # Nothing technical reaches the sentence a user would see.
    for forbidden in ("Traceback", "EADDRINUSE", "errno", "/", "uvicorn"):
        assert forbidden not in message


def test_no_readiness_is_accepted_and_the_report_is_the_typed_refusal(
    monkeypatch, tmp_path
):
    """Straight at the handshake: the child wrote `port-unavailable`, not `ready`.

    Driven through `start_backend_process` and the real entrypoint, so the
    payload under inspection is the one the production child actually produced.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    port = free_port()
    config = build_runtime_config(backend_port=port, open_browser=False)
    paths = resolve_runtime_paths()

    competing = CompetingListener(config.host, port)
    competing.bind()
    handshake = new_backend_handshake()
    process = None
    try:
        # The early probe is bypassed *only* here, because this test is about what
        # the child reports; `start_backend_process` would otherwise refuse before
        # spawning. The child, its lock, its bind and its handshake are all real.
        monkeypatch.setattr(runtime, "assert_port_available", lambda _h, _p: None)
        process = runtime.start_backend_process(
            config, paths, workspace.database_path, handshake=handshake
        )
        handshake.close_child_end()

        with pytest.raises(BackendSocketUnavailableError):
            handshake.await_acquisition(process, timeout_seconds=60)

        # A refusal, not a handshake failure: those are different answers.
        assert process.wait(timeout=30) != 0
    finally:
        handshake.close()
        if process is not None:
            runtime.terminate_process(process)
        competing.release()


def test_a_refused_child_exits_and_leaves_nothing_behind(monkeypatch, tmp_path):
    """No process, no lock, no socket — after a real refusal."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        with pytest.raises(runtime.BackendPortUnavailableError):
            context.backend.start(
                context.config, context.paths, workspace.database_path
            )
        assert context.backend.has_process is False
        assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is True
    finally:
        armed.release()
        context.release()

    assert can_bind(context.config.host, context.config.backend_port) is True


# --------------------------------------------------------------------------
# 3. No application import on a refused bind
# --------------------------------------------------------------------------

def test_a_refused_bind_imports_no_application_module(tmp_path):
    """The refusal happens before `app.main`, the routers and the database layer.

    Asserted inside the refusing process itself, because "nothing was imported"
    is a claim about *its* `sys.modules`. The child runs the real entrypoint
    `main()` against a really occupied port.
    """
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    port = free_port()

    competing = CompetingListener("127.0.0.1", port)
    competing.bind()
    try:
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json, os, sys\n"
                "from app.launcher_backend_entrypoint import main\n"
                "code = main(['--host', '127.0.0.1', '--port', sys.argv[1]])\n"
                "leaked = sorted(\n"
                "    name for name in sys.modules\n"
                "    if name == 'uvicorn' or name.startswith('uvicorn.')\n"
                "    or name == 'app.main' or name.startswith('app.db')\n"
                "    or name.startswith('app.routers') or name.startswith('app.models')\n"
                ")\n"
                "print(json.dumps({'code': code, 'leaked': leaked}))\n",
                str(port),
            ],
            cwd=str(resolve_runtime_paths().backend_dir),
            env={
                **_child_environment(lock_path),
            },
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        competing.release()

    import json

    payload = json.loads(probe.stdout.strip().splitlines()[-1])
    from app import launcher_backend_entrypoint as entrypoint

    assert payload["code"] == entrypoint.PORT_UNAVAILABLE_EXIT_CODE
    assert payload["leaked"] == [], (
        f"the child imported application modules after a refused bind: {payload['leaked']}"
    )


def _child_environment(lock_path: Path) -> dict:
    """A minimal environment for a real entrypoint subprocess.

    The database path is deliberately **not** set: a child that refuses its bind
    must never reach the database layer, so it has no legitimate use for one, and
    omitting it means the repository fallback cannot be touched either.
    """
    import os

    from app.services.backend_liveness import BACKEND_LIVENESS_LOCK_ENV

    paths = resolve_runtime_paths()
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(paths.backend_dir),
        BACKEND_LIVENESS_LOCK_ENV: str(lock_path),
    }
    return environment


# --------------------------------------------------------------------------
# 4. Rollback recovery stays retryable through the real child path
# --------------------------------------------------------------------------

def test_rollback_recovery_defers_on_a_real_bind_collision(monkeypatch, tmp_path):
    """The finding, end to end: a busy socket must not reach `recovery_blocked`.

    A durable `rollback_in_progress`, the production recovery path, the production
    verifier, and a real competing listener taking the exact port after the real
    probe. The rollback replacement runs under the lease; only its verification
    cannot start.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, candidate = publish_rollback_in_progress(workspace)
    context = workspace.context()
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        result = recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
        lease_after = context.maintenance_lease.held
        child_running = context.backend.is_running
    finally:
        armed.release()
        context.release()

    # Deferred, not blocked.
    assert result.normal_startup_allowed is False
    assert result.outcome is None
    assert result.message == BACKEND_PORT_UNAVAILABLE_MESSAGE
    assert result.message != RECOVERY_BLOCKED_MESSAGE
    assert result.durable_phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert store.read().operation_id == operation_id
    # Every artifact retained while the operation is still open.
    assert workspace.safety_copies() != []
    assert candidate.exists()
    # The lease came back and no child was leaked.
    assert lease_after is True
    assert child_running is False
    assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is True


def test_rollback_recovery_completes_after_the_real_port_is_released(
    monkeypatch, tmp_path
):
    """Close the other program, reopen, and the same operation finishes.

    The second run starts **real** verification backends through the ordinary
    owned-backend path, so this is the whole round trip rather than a claim about
    one half of it.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, _candidate = publish_rollback_in_progress(workspace)
    context = workspace.context()
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        deferred = recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
    finally:
        context.release()

    assert deferred.normal_startup_allowed is False
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS

    # The user closed the other program.
    armed.disarm()
    assert can_bind(context.config.host, context.config.backend_port) is True

    context = workspace.context(backend_port=context.config.backend_port)
    try:
        completed = recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
    finally:
        context.release()

    assert completed.normal_startup_allowed is True
    assert completed.outcome is RestoreOutcome.ROLLED_BACK
    assert store.read().phase is RestorePhase.ROLLED_BACK
    assert store.read().operation_id == operation_id
    assert read_marker(workspace.database_path) == "workspace-A"


# --------------------------------------------------------------------------
# 5. Forward verification stays retryable
# --------------------------------------------------------------------------

def test_forward_verification_defers_on_a_real_bind_collision(monkeypatch, tmp_path):
    """The forward path too: a busy socket never triggers a rollback.

    Driven through the real engine to `verification_in_progress`, with the real
    verifier and a real competing listener. Rolling back here would undo a restore
    that may be perfectly good, over another program holding a socket.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    rollbacks: list[str] = []
    real_rollback = engine_module.perform_rollback

    def watched_rollback(*args, **kwargs):  # pragma: no cover - must not be called
        rollbacks.append("entered")
        return real_rollback(*args, **kwargs)

    monkeypatch.setattr(engine_module, "perform_rollback", watched_rollback)
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        with pytest.raises(RetryableBackendStartError):
            engine_module.execute_restore(
                request_for(source),
                context,
                services=real_verification_services(workspace.database_path),
            )
        lease_after = context.maintenance_lease.held
        child_running = context.backend.is_running
    finally:
        armed.release()
        context.release()

    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert rollbacks == [], "a busy socket triggered a rollback"
    assert store.read().phase is RestorePhase.VERIFICATION_IN_PROGRESS
    assert lease_after is True
    assert child_running is False
    assert workspace.safety_copies() != []


# --------------------------------------------------------------------------
# 6. Ordinary startup keeps its ordinary contract
# --------------------------------------------------------------------------

def test_ordinary_startup_late_collision_keeps_the_ordinary_contract(
    monkeypatch, tmp_path, capsys
):
    """No Restore record, a real late collision, the existing launch error."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert store.has_record() is False
    database_before = digest(workspace.database_path)

    browsers: list[str] = []
    monkeypatch.setattr(
        runtime, "open_runtime_browser", lambda _config: browsers.append("opened")
    )
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)
    port = free_port()
    armed = ArmedAtTheProbe(monkeypatch, "127.0.0.1", port)
    try:
        with pytest.raises(runtime.RuntimeLaunchError, match="уже занят"):
            runtime.run_local_runtime(
                build_runtime_config(backend_port=port, open_browser=True),
                resolve_runtime_paths(),
            )
    finally:
        armed.release()

    assert browsers == [], "the browser opened despite a refused backend"
    # No Restore operation was invented and nothing on disk moved.
    assert store.has_record() is False
    assert digest(workspace.database_path) == database_before
    printed = capsys.readouterr().out
    assert "Traceback" not in printed
    assert "BackendSocketUnavailableError" not in printed


# --------------------------------------------------------------------------
# 7-8. What must stay non-retryable
# --------------------------------------------------------------------------

def test_a_child_refused_the_liveness_lock_is_not_a_port_collision(
    monkeypatch, tmp_path
):
    """A held lock is evidence about the workspace; it keeps its own answer."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        # The launcher's own lease holds the canonical lock, so the child cannot.
        context.stop_backend()
        assert context.maintenance_lease.held is True

        with pytest.raises(BackendHandshakeError):
            runtime.start_owned_backend_process(
                context.config, context.paths, workspace.database_path
            )
    finally:
        context.release()


def test_a_socket_error_that_is_not_a_collision_is_not_reported_as_one():
    """Only `EADDRINUSE` becomes a port refusal.

    An unusable host is a configuration problem, not a program to close. Reported
    as an ordinary `OSError` from the bind helper, which `main()` turns into its
    own exit code rather than into a structured port refusal.
    """
    from app.launcher_backend_entrypoint import (
        ConfiguredPortUnavailableError,
        bind_configured_socket,
    )

    with pytest.raises(OSError) as raised:
        bind_configured_socket("203.0.113.1", free_port())

    assert not isinstance(raised.value, ConfiguredPortUnavailableError)


def test_a_port_unavailable_report_from_another_start_is_refused(monkeypatch):
    """A refusal is only this start's refusal when it carries this start's token.

    Otherwise a previous run's message could decide a later run's classification —
    the same replay the `ready:` path has always refused.
    """
    import os

    from app.launcher_backend_entrypoint import HANDSHAKE_PORT_UNAVAILABLE_PREFIX

    previous = new_backend_handshake()
    current = new_backend_handshake()
    try:
        os.write(
            current.write_fd,
            f"{HANDSHAKE_PORT_UNAVAILABLE_PREFIX}{previous.token}\n".encode("utf-8"),
        )
        current.close_child_end()
        with pytest.raises(BackendHandshakeError, match="different start"):
            current.await_acquisition(None, timeout_seconds=5)
    finally:
        previous.close()
        current.close()


def test_the_two_structured_results_are_distinct_types():
    """A refusal is not a handshake failure, and neither is a verification failure."""
    from launcher.restore.verification import BackendVerificationError

    assert not issubclass(BackendSocketUnavailableError, BackendHandshakeError)
    assert not issubclass(BackendHandshakeError, BackendSocketUnavailableError)
    assert not issubclass(RetryableBackendStartError, BackendVerificationError)
    assert issubclass(runtime.BackendPortUnavailableError, runtime.RuntimeLaunchError)


# --------------------------------------------------------------------------
# 10. Descriptors and sockets
# --------------------------------------------------------------------------

def test_no_socket_survives_a_successful_child_teardown(monkeypatch, tmp_path):
    """After a normal stop, the port and the lock are both available again."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.backend.start(context.config, context.paths, workspace.database_path)
        assert can_bind(context.config.host, context.config.backend_port) is False

        proof = context.backend.stop()
        assert proof.confirmed_stopped is True
        context.backend.wait_until_liveness_lock_released(
            context.backend_liveness_lock_path
        )
    finally:
        context.release()

    assert can_bind(context.config.host, context.config.backend_port) is True
    assert backend_liveness_lock_is_free(context.backend_liveness_lock_path) is True


def test_the_handshake_descriptors_are_closed_after_a_refusal(monkeypatch, tmp_path):
    """A refused start closes its pipe; nothing accumulates across attempts.

    Repeated deliberately: a descriptor leak only shows up as a pattern, and a
    launcher that refuses several times in a row is an ordinary thing for a user
    to do while they hunt for the program holding the port.
    """
    import os

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    armed = ArmedAtTheProbe(
        monkeypatch, context.config.host, context.config.backend_port
    )
    try:
        before = len(os.listdir(f"/dev/fd/{os.getpid()}")) if _has_dev_fd() else None
        for _ in range(3):
            with pytest.raises(runtime.BackendPortUnavailableError):
                context.backend.start(
                    context.config, context.paths, workspace.database_path
                )
        after = len(os.listdir(f"/dev/fd/{os.getpid()}")) if _has_dev_fd() else None
    finally:
        armed.release()
        context.release()

    if before is not None and after is not None:
        assert after <= before + 1, (
            f"handshake descriptors accumulated across refusals: {before} → {after}"
        )


def _has_dev_fd() -> bool:
    import os

    return Path(f"/dev/fd/{os.getpid()}").is_dir()


# --------------------------------------------------------------------------
# The shape itself
# --------------------------------------------------------------------------

def test_this_module_uses_the_production_child_rather_than_a_stub():
    """`P2-1`, stated as a test: the regression proof may not be synthetic.

    The previous evidence monkeypatched `BackendProcessOwner.start` and raised
    `BackendPortUnavailableError` by hand, which proves exception routing and
    nothing about whether a real bind can produce one.
    """
    import inspect
    import io
    import tokenize

    # Comments and string literals removed: this module *documents* the synthetic
    # approach it replaces, so a plain substring check would trip on its own
    # explanation.
    kept: list[str] = []
    stream = io.StringIO(inspect.getsource(sys.modules[__name__])).readline
    for token in tokenize.generate_tokens(stream):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    source = " ".join(kept)

    assert "BackendProcessOwner . start" not in source, (
        "the real-race module must not stub the owned-backend start"
    )
    assert "raise runtime . BackendPortUnavailableError" not in source, (
        "the real-race module must not raise the port error by hand"
    )
    for forbidden in ("pkill", "pgrep", "killall", "lsof"):
        assert forbidden not in source
