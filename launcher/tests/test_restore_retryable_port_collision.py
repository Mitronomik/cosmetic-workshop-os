"""A busy port is an environment problem. It may never end a Restore.

The fifth-audit finding `P1-1`. The fourth correction correctly moved Restore
recovery ahead of the port check, because a real orphan holds the canonical
`backend-liveness.lock` *and* the configured port. But recovery **writes**: it
closes pre-replacement operations out to `aborted`, enters `rollback_in_progress`,
replaces the working database from the safety copy and runs migrations. Doing all
of that first and only then discovering that an unrelated program owns the port
meant this:

```text
recover_incomplete_restore()
→ publish rollback_in_progress
→ replace the working database from the safety copy
→ run startup and migrations
→ start the verification backend
→ assert_port_available() fails
→ a verification exception
→ recovery_blocked          ← terminal, support-only, over a busy socket
```

The port said nothing about the database. Nothing was verified, because nothing
was started. Yet a recoverable operation became one that only a support procedure
can clear, and the user's actual problem — another program holding a port — is
one they fix in ten seconds.

Two separate defences, because they answer two different moments:

```text
before any write   the launcher checks the port between the non-mutating
                   preflight and the state-mutating recovery, so an occupied
                   port refuses with the Restore history byte-identical

after that check   the port can still be taken before the child binds it; no
                   momentary probe can close that race, so the late collision is
                   *classified* as retryable and the durable phase is left alone
```

Every port holder here is a real socket bound by this test, and the canonical
lock is deliberately left free — that is what makes these collisions *unrelated*.
The same-port orphan, which holds both, is covered in
`launcher/tests/test_restore_same_port_orphan.py` and must keep its own answer.

## What this module does and does not prove

The "before any write" half above is proved here end to end, through the real
launcher boundary.

The **late**-collision tests in this module are, deliberately, *exception-routing
unit tests*. They intercept the owned-backend start and hand the engine a
`BackendPortUnavailableError`, which proves one narrow and useful thing: given
that condition, the engine defers instead of publishing `recovery_blocked`.

They do **not** prove that the product can produce that condition from a real
socket. The sixth audit found that it could not: the child reported success
before uvicorn bound, so a genuine post-probe collision arrived as a
started-then-died child and was classified as a verification failure. That gap is
closed by the child owning the real listening socket before it reports readiness,
and the regression proof for it — real parent, real child entrypoint, real
handshake, real bind, real process exit — lives in
`launcher/tests/test_restore_real_port_bind_race.py`.

Keep both. One says the routing is right; the other says the routing is
reachable.
"""

from pathlib import Path
import hashlib
import socket

import pytest

from launcher import runtime
from launcher.config import build_runtime_config, resolve_runtime_paths
from launcher.restore import engine as engine_module
from launcher.restore.contracts import (
    BACKEND_PORT_UNAVAILABLE_MESSAGE,
    RECOVERY_BLOCKED_MESSAGE,
    RestoreFailure,
    USER_SAFE_MESSAGES,
)
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import (
    prepare_restore_startup_recovery,
    recover_incomplete_restore,
)
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
from launcher.restore.verification import RetryableBackendStartError
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    free_port,
    make_workspace,
    migrating_startup,
    read_marker,
    stub_services,
)

UNSAFE_PRE_ROLLBACK_PHASES = [
    RestorePhase.REPLACEMENT_INTENT,
    RestorePhase.REPLACEMENT_COMMITTED,
    RestorePhase.VERIFICATION_IN_PROGRESS,
]


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class OccupiedPort:
    """A real listening socket on a real port, holding **no** canonical lock.

    An unrelated program, modelled as one. It binds and listens so the launcher's
    own bind probe fails exactly as it would against any other process, and it is
    closable mid-test so "the user closed it and reopened the application" is a
    thing this module can actually perform rather than simulate.
    """

    def __init__(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(1)
        self.port = self._socket.getsockname()[1]

    def release(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "OccupiedPort":
        return self

    def __exit__(self, *_exception) -> None:
        self.release()


def publish_phase(workspace, phase: RestorePhase, *, with_safety_copy: bool = True):
    """A durable record at one exact phase, with the artifacts that phase implies."""
    launcher_workspace = RestoreWorkspace.for_database(workspace.database_path)
    store = RestoreOperationStateStore(launcher_workspace)
    operation_id = new_operation_id()
    launcher_workspace.create_operation_dir(operation_id)

    safety_filename = None
    if with_safety_copy:
        safety = create_verified_safety_copy(
            workspace.database_path, workspace.backup_dir
        )
        safety_filename = safety.filename
        # The replacement already happened for every phase past the boundary, so
        # the working database carries the *restored* marker and the safety copy
        # carries the previous one. That is what makes a rollback observable.
        build_workspace_database(workspace.database_path, "workspace-B")

    candidate = launcher_workspace.restore_dir / operation_id / "candidate.sqlite"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    build_workspace_database(candidate, "workspace-B")

    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=phase,
            created_at="2026-08-03T00:00:00+00:00",
            updated_at="2026-08-03T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety_filename,
        )
    )
    return store, operation_id, candidate


def guard_the_boundary(monkeypatch) -> dict:
    """Fail loudly on any backend start, and record browser opens."""
    watched = {"browser": [], "backends": []}

    def refuse_to_start(*_args, **_kwargs):  # pragma: no cover - must not be called
        watched["backends"].append("started")
        raise AssertionError("no backend may start while the port is occupied")

    monkeypatch.setattr(runtime, "start_backend_process", refuse_to_start)
    monkeypatch.setattr(runtime, "start_owned_backend_process", refuse_to_start)
    monkeypatch.setattr(
        runtime, "open_runtime_browser", lambda _config: watched["browser"].append("opened")
    )
    return watched


def evidence_of(workspace, store, candidate: Path) -> dict:
    """Everything that must survive a refused run, as comparable values."""
    return {
        "record": store.record_path.read_bytes(),
        "database": digest(workspace.database_path),
        "safety_copies": sorted(path.name for path in workspace.safety_copies()),
        "staged_candidate": candidate.exists() and digest(candidate),
    }


# --------------------------------------------------------------------------
# 1-2. The port is checked before anything is written
# --------------------------------------------------------------------------

@pytest.mark.parametrize("phase", UNSAFE_PRE_ROLLBACK_PHASES)
def test_an_occupied_port_leaves_an_unsafe_record_byte_identical(
    monkeypatch, tmp_path, phase
):
    """The three phases the matrix resolves through rollback, all left alone.

    Each of these would have entered `rollback_in_progress` and replaced the
    working database before the port was ever consulted. Now the run refuses
    first, and the operation is exactly where the interruption left it.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, candidate = publish_phase(workspace, phase)
    before = evidence_of(workspace, store, candidate)
    watched = guard_the_boundary(monkeypatch)

    with OccupiedPort() as occupied:
        config = build_runtime_config(backend_port=occupied.port, open_browser=True)
        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    assert evidence_of(workspace, store, candidate) == before
    assert store.read().phase is phase
    assert store.read().operation_id == operation_id
    # The restored candidate is still in place: no rollback replacement ran.
    assert read_marker(workspace.database_path) == "workspace-B"
    assert watched["browser"] == []
    assert watched["backends"] == []


def test_an_occupied_port_leaves_rollback_in_progress_byte_identical(
    monkeypatch, tmp_path
):
    """`rollback_in_progress` is the one the old ordering damaged worst.

    It is the phase that *replaces the working database* on the way to being
    resolved. Refusing before that write is what keeps a busy port from touching
    the user's data at all.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    before = evidence_of(workspace, store, candidate)
    watched = guard_the_boundary(monkeypatch)

    with OccupiedPort() as occupied:
        config = build_runtime_config(backend_port=occupied.port, open_browser=True)
        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    assert evidence_of(workspace, store, candidate) == before
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert store.read().operation_id == operation_id
    assert read_marker(workspace.database_path) == "workspace-B"
    assert watched["browser"] == []
    assert watched["backends"] == []


@pytest.mark.parametrize(
    "phase",
    [
        RestorePhase.PREPARED,
        RestorePhase.SOURCE_STAGED,
        RestorePhase.CANDIDATE_VALIDATED,
        RestorePhase.SAFETY_COPY_VERIFIED,
    ],
)
def test_an_occupied_port_does_not_close_out_a_pre_replacement_operation(
    monkeypatch, tmp_path, phase
):
    """`prepared → aborted` is a write, and a busy socket may not cause it.

    These four phases replaced nothing, so closing them out is harmless to the
    *data* — but it still rewrites Restore history during a run that cannot
    start, and a user who closes the other program has a right to find their
    operation where they left it.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, candidate = publish_phase(
        workspace, phase, with_safety_copy=False
    )
    before = evidence_of(workspace, store, candidate)
    watched = guard_the_boundary(monkeypatch)

    with OccupiedPort() as occupied:
        config = build_runtime_config(backend_port=occupied.port, open_browser=True)
        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    assert evidence_of(workspace, store, candidate) == before
    assert store.read().phase is phase, "the operation was closed out over a busy port"
    assert store.read().operation_id == operation_id
    assert read_marker(workspace.database_path) == "workspace-A"
    assert watched["browser"] == []
    assert watched["backends"] == []


def test_the_preflight_itself_writes_nothing(monkeypatch, tmp_path):
    """The non-mutating half, held to that claim directly.

    Everything it does — authority, the owned-child stop, the retained lease, the
    record read — is either a lock or a read. If it wrote, the port check that
    now sits after it would be protecting nothing.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    before = evidence_of(workspace, store, candidate)

    context = workspace.context()
    try:
        preflight = prepare_restore_startup_recovery(context)

        assert preflight.blocked_result is None
        assert preflight.has_record is True
        assert preflight.durable_phase is RestorePhase.ROLLBACK_IN_PROGRESS
        assert preflight.record.operation_id == operation_id
        # Exclusion really was established: the lease is held from here on.
        assert context.maintenance_lease.held is True
    finally:
        context.release()

    assert evidence_of(workspace, store, candidate) == before


# --------------------------------------------------------------------------
# 3. The next launch continues from the same durable phase
# --------------------------------------------------------------------------

def test_recovery_completes_once_the_port_is_released(monkeypatch, tmp_path):
    """Close the other program, reopen the application, recovery finishes.

    The whole point of refusing without writing: the operation is still
    resumable, and resuming it is the ordinary path rather than a support
    procedure.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, _candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    guard_the_boundary(monkeypatch)

    occupied = OccupiedPort()
    try:
        config = build_runtime_config(backend_port=occupied.port, open_browser=False)
        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())
        assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS
    finally:
        occupied.release()

    # The user closed it. The next start resolves the same operation, from the
    # same durable phase, through the ordinary recovery matrix.
    context = workspace.context()
    try:
        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.normal_startup_allowed is True
    assert result.durable_phase is RestorePhase.ROLLED_BACK
    assert store.read().phase is RestorePhase.ROLLED_BACK
    assert store.read().operation_id == operation_id
    # The previous workspace is authoritative again.
    assert read_marker(workspace.database_path) == "workspace-A"


@pytest.mark.parametrize("phase", UNSAFE_PRE_ROLLBACK_PHASES)
def test_an_unsafe_phase_still_recovers_normally_on_the_next_launch(
    monkeypatch, tmp_path, phase
):
    """Deferring is not cancelling: the matrix still governs, one launch later."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, _operation_id, _candidate = publish_phase(workspace, phase)
    guard_the_boundary(monkeypatch)

    with OccupiedPort() as occupied:
        with pytest.raises(runtime.RuntimeLaunchError):
            runtime.run_local_runtime(
                build_runtime_config(backend_port=occupied.port, open_browser=False),
                resolve_runtime_paths(),
            )
    assert store.read().phase is phase

    context = workspace.context()
    try:
        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.durable_phase is RestorePhase.ROLLED_BACK
    assert read_marker(workspace.database_path) == "workspace-A"


# --------------------------------------------------------------------------
# 4. A collision that appears after the port check
# --------------------------------------------------------------------------

def real_verification_services(database_path):
    """The **production** verifier, with only the startup migration stubbed.

    The classification under test lives inside `verify_restored_backend`, so a
    stub verifier would prove nothing about it. Startup is stubbed only because
    it would otherwise resolve the repository database rather than this isolated
    workspace; it still migrates the exact restored path for real.
    """
    from launcher.restore.engine import RestoreServices
    from launcher.restore.verification import verify_restored_backend

    return RestoreServices(
        verify_backend=verify_restored_backend,
        initialize_startup=migrating_startup(database_path),
    )


class StolenPort:
    """A **synthetic** stand-in for the late collision, at the owned-backend start.

    This intercepts `BackendProcessOwner.start` and raises the condition a real
    bind refusal produces. It is an exception-routing fixture, not a reproduction
    of the race: no child is spawned, no socket is bound and nothing about the
    production startup path is exercised.

    That distinction is the sixth audit's `P2-1`. Described as proof of the real
    race, this fixture was overstating what it demonstrates — and it kept
    demonstrating it while the product could not actually reach the routing,
    because uvicorn bound only after the child had already reported success. The
    real regression proof is
    `launcher/tests/test_restore_real_port_bind_race.py`.

    What it *does* prove, and what it is kept for: given the condition, the engine
    and startup recovery defer instead of publishing `recovery_blocked`.

    `disarm()` is the user closing the other program: the next child starts for
    real, through the ordinary owned-backend path.
    """

    def __init__(self, monkeypatch) -> None:
        from launcher.restore.context import BackendProcessOwner

        self.holders: list[OccupiedPort] = []
        self.armed = True
        real_start = BackendProcessOwner.start
        stealer = self

        def start(owner_self, config, paths, database_path):
            if not stealer.armed:
                return real_start(owner_self, config, paths, database_path)
            occupied = OccupiedPort()
            stealer.holders.append(occupied)
            # Exactly what `assert_port_available` raises inside
            # `start_backend_process` when the bind fails.
            raise runtime.BackendPortUnavailableError(
                f"Порт {occupied.port} уже занят. "
                "Закройте другое окно приложения или выберите свободный порт."
            )

        monkeypatch.setattr(BackendProcessOwner, "start", start)

    def disarm(self) -> None:
        self.armed = False
        self.release()

    def release(self) -> None:
        for holder in self.holders:
            holder.release()
        self.holders = []


def test_a_late_port_collision_is_retryable_and_publishes_nothing(monkeypatch, tmp_path):
    """The classification that keeps a busy socket from ending the operation.

    An **exception-routing** test: the condition is injected at the owned-backend
    start rather than produced by a real bind. What it establishes is that the
    engine, given that condition, defers — the rollback replacement has already
    run under the lease, so the previous workspace is back on disk; only its
    *verification* could not start; the durable phase stays
    `rollback_in_progress`, which is safely repeatable, and the next launch
    finishes it.

    That the product can actually *reach* this routing from a real socket is the
    separate question the sixth audit raised, and it is proved against real
    processes in `launcher/tests/test_restore_real_port_bind_race.py`.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    stolen = StolenPort(monkeypatch)

    context = workspace.context()
    try:
        result = recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
        lease_after = context.maintenance_lease.held
        child_running = context.backend.is_running
    finally:
        stolen.release()
        context.release()

    assert result.normal_startup_allowed is False
    # Not blocked. Deferred.
    assert result.outcome is None
    assert result.message == BACKEND_PORT_UNAVAILABLE_MESSAGE
    assert result.durable_phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert store.read().operation_id == operation_id
    # Evidence intact.
    assert workspace.safety_copies() != []
    assert candidate.exists()
    # The lease came back and no child was leaked.
    assert lease_after is True
    assert child_running is False
    # The rollback replacement did run — it precedes verification — so the
    # previous workspace is already authoritative again.
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_late_collision_completes_recovery_on_the_next_launch(monkeypatch, tmp_path):
    """Deferred, then finished, with no support procedure in between.

    The second run starts **real** verification backends through the ordinary
    owned-backend path, so this is the whole round trip: the collision defers,
    the user closes the other program, and the same operation completes.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, operation_id, _candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    stolen = StolenPort(monkeypatch)

    context = workspace.context()
    try:
        deferred = recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
    finally:
        context.release()

    assert deferred.normal_startup_allowed is False
    assert deferred.message == BACKEND_PORT_UNAVAILABLE_MESSAGE
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS

    # The user closed the other program.
    stolen.disarm()

    context = workspace.context()
    try:
        result = recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.normal_startup_allowed is True
    assert result.durable_phase is RestorePhase.ROLLED_BACK
    assert store.read().phase is RestorePhase.ROLLED_BACK
    assert store.read().operation_id == operation_id
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_late_collision_reaches_the_launcher_as_a_message_not_a_traceback(
    monkeypatch, tmp_path, capsys
):
    """The product boundary returns an exit code and one fixed sentence."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, _operation_id, _candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    watched = guard_the_boundary(monkeypatch)
    stolen = StolenPort(monkeypatch)

    try:
        exit_code = runtime.run_local_runtime(
            build_runtime_config(backend_port=free_port(), open_browser=True),
            resolve_runtime_paths(),
        )
    finally:
        stolen.release()

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert watched["browser"] == []

    printed = capsys.readouterr().out
    assert BACKEND_PORT_UNAVAILABLE_MESSAGE in printed
    # It is a retry instruction, not the support sentence: nothing is stuck.
    assert RECOVERY_BLOCKED_MESSAGE not in printed
    assert "Traceback" not in printed
    assert "RetryableBackendStartError" not in printed
    assert "BackendPortUnavailableError" not in printed
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS


# --------------------------------------------------------------------------
# 5. Real verification failures stay non-retryable
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "failure",
    [
        "representative read failed",
        "the backend exited during startup",
        "the child could not acquire the liveness lock",
        "the handshake token was refused",
    ],
)
def test_an_actual_verification_failure_is_still_not_retryable(
    monkeypatch, tmp_path, failure
):
    """The new branch must catch a busy port and nothing else.

    Each of these is evidence *about the workspace*, so each keeps the accepted
    consequence: an unverifiable rollback ends at `recovery_blocked` with every
    artifact preserved. Widening the retryable branch to "anything that went
    wrong while starting a backend" would quietly make a broken database look
    like a busy port.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, _operation_id, _candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )

    def always_fails(_config, _paths, _database_path):
        raise RuntimeError(failure)

    context = workspace.context()
    try:
        result = recover_incomplete_restore(
            context,
            services=stub_services(workspace.database_path, verify=always_fails),
        )
    finally:
        context.release()

    assert result.normal_startup_allowed is False
    assert result.message == RECOVERY_BLOCKED_MESSAGE
    assert result.message != BACKEND_PORT_UNAVAILABLE_MESSAGE
    assert store.read().phase is RestorePhase.RECOVERY_BLOCKED
    assert workspace.safety_copies() != []


def test_a_verification_error_is_not_a_retryable_start_error():
    """The two types are unrelated by construction, not by convention."""
    from launcher.restore.verification import BackendVerificationError

    assert not issubclass(RetryableBackendStartError, BackendVerificationError)
    assert not issubclass(BackendVerificationError, RetryableBackendStartError)
    # And the port error the launcher raises is still an ordinary launch error,
    # so every existing `except RuntimeLaunchError` is unchanged.
    assert issubclass(runtime.BackendPortUnavailableError, runtime.RuntimeLaunchError)


def test_only_an_occupied_port_produces_the_retryable_classification(monkeypatch, tmp_path):
    """Straight at the classifier: one input maps to retryable, others do not."""
    from launcher.restore import verification as verification_module

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    config = build_runtime_config(backend_port=free_port(), open_browser=False)

    def start_raising(exception):
        def start(self, _config, _paths, _database_path):
            raise exception

        return start

    port_error = runtime.BackendPortUnavailableError("Порт 1 уже занят.")
    other_errors = [
        RuntimeError("the child exited during startup"),
        OSError("the liveness lock could not be taken"),
        ValueError("the handshake token was refused"),
    ]

    monkeypatch.setattr(
        "launcher.restore.context.BackendProcessOwner.start", start_raising(port_error)
    )
    with pytest.raises(RetryableBackendStartError):
        verification_module._run_one_verification_cycle(
            config, resolve_runtime_paths(), workspace.database_path, "http://127.0.0.1:1", 0
        )

    for error in other_errors:
        monkeypatch.setattr(
            "launcher.restore.context.BackendProcessOwner.start", start_raising(error)
        )
        with pytest.raises(verification_module.BackendVerificationError):
            verification_module._run_one_verification_cycle(
                config, resolve_runtime_paths(), workspace.database_path,
                "http://127.0.0.1:1", 0,
            )


# --------------------------------------------------------------------------
# The message
# --------------------------------------------------------------------------

def test_the_retry_message_says_retry_rather_than_contact_support():
    """A user closes a program. They are not sent to support, and nothing is lost."""
    assert BACKEND_PORT_UNAVAILABLE_MESSAGE == USER_SAFE_MESSAGES[
        RestoreFailure.BACKEND_PORT_UNAVAILABLE
    ]
    assert "поддержк" not in BACKEND_PORT_UNAVAILABLE_MESSAGE
    assert "не завершилось" not in BACKEND_PORT_UNAVAILABLE_MESSAGE
    assert "сохранены" in BACKEND_PORT_UNAVAILABLE_MESSAGE
    # Fixed and path-free, like every other category.
    for forbidden in ("/", "\\", "sqlite", "Traceback", "SELECT"):
        assert forbidden not in BACKEND_PORT_UNAVAILABLE_MESSAGE
    # And it is never confused with the terminal one.
    assert BACKEND_PORT_UNAVAILABLE_MESSAGE != RECOVERY_BLOCKED_MESSAGE


def test_the_retryable_category_is_never_written_into_the_record(monkeypatch, tmp_path):
    """A category chooses a sentence. It is not a phase and not a persisted flag."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store, _operation_id, _candidate = publish_phase(
        workspace, RestorePhase.ROLLBACK_IN_PROGRESS
    )
    stolen = StolenPort(monkeypatch)

    context = workspace.context()
    try:
        recover_incomplete_restore(
            context, services=real_verification_services(workspace.database_path)
        )
    finally:
        stolen.release()
        context.release()

    raw = store.record_path.read_text(encoding="utf-8")
    for forbidden in ("backend_port_unavailable", "retryable", "port", "deferred"):
        assert forbidden not in raw, f"{forbidden} leaked into the durable record"
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS


def test_the_phase_vocabulary_is_unchanged_by_this_correction():
    """No new phase. The retryable condition is a result category, not a state."""
    assert [phase.value for phase in RestorePhase] == [
        "prepared",
        "source_staged",
        "candidate_validated",
        "safety_copy_verified",
        "replacement_intent",
        "replacement_committed",
        "verification_in_progress",
        "completed",
        "aborted",
        "rollback_in_progress",
        "rolled_back",
        "recovery_blocked",
    ]


def test_the_engine_defers_rather_than_rolling_back_on_a_busy_port(monkeypatch, tmp_path):
    """The forward path too: a busy port never triggers a rollback.

    Rolling back here would undo a restore that may be perfectly good, over
    another program holding a socket. Nothing was verified, so nothing about the
    restored database was learned, and the durable phase is left for the accepted
    matrix to resolve on a launch that can actually run.
    """
    from launcher.restore.contracts import RestoreRequest
    from launcher.tests.restore_fixtures import make_source_backup, request_for

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    rollbacks: list[str] = []
    real_rollback = engine_module.perform_rollback

    def watched_rollback(*args, **kwargs):  # pragma: no cover - must not be called
        rollbacks.append("entered")
        return real_rollback(*args, **kwargs)

    monkeypatch.setattr(engine_module, "perform_rollback", watched_rollback)

    def refuse_on_a_busy_port(_config, _paths, _database_path):
        raise RetryableBackendStartError("the configured port was occupied")

    try:
        with pytest.raises(RetryableBackendStartError):
            engine_module.execute_restore(
                request_for(source),
                context,
                services=stub_services(
                    workspace.database_path,
                    verify=lambda *_a: (_ for _ in ()).throw(
                        RetryableBackendStartError("the configured port was occupied")
                    ),
                ),
            )
        lease_after = context.maintenance_lease.held
    finally:
        context.release()

    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert rollbacks == [], "a busy port triggered a rollback"
    assert store.read().phase is RestorePhase.VERIFICATION_IN_PROGRESS
    assert lease_after is True
    assert workspace.safety_copies() != []
