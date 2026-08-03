"""Terminal publication failures, and the startup permission that depends on them.

Two findings from the second audit meet here.

**A post-rename failure at `completed` used to fall through to `_abort()`**, which
would attempt `completed → aborted` — an edge the accepted graph does not contain
— and let a `PhaseTransitionError` escape the launcher boundary. The existing
tests only covered a failure *before* `completed` was published, so the dangerous
half of the window was untested.

**Ordinary startup was permitted by a negative rule.** `phase not in
UNSAFE_STARTUP_PHASES` reads as if it means "safe" and does not: it admitted every
unresolved pre-replacement phase, and it admitted a terminal phase whose record
could not be flushed and may therefore revert.

The corrected behaviour, checked throughout this file:

1. a terminal record is **never** transitioned again — not to another phase, not
   to itself;
2. the phase reported is the phase actually on disk;
3. startup is permitted only from `completed`, `aborted` or `rolled_back`, and
   only once that record's durability has been re-proved;
4. when it cannot be, everything is preserved and the next start retries.
"""

from pathlib import Path

import pytest

from launcher.restore import durability
from launcher.restore.contracts import RestoreOutcome
from launcher.restore.engine import execute_restore
from launcher.restore.phases import (
    ALLOWED_TRANSITIONS,
    SAFE_TERMINAL_STARTUP_PHASES,
    TERMINAL_PHASES,
    RestorePhase,
)
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
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)


@pytest.fixture
def scenario(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        yield workspace, source, context
    finally:
        context.release()


def store_for(workspace) -> RestoreOperationStateStore:
    return RestoreOperationStateStore(
        RestoreWorkspace(
            restore_dir=workspace.restore_dir, database_path=workspace.database_path
        )
    )


def publish_phase(store, phase, *, safety_copy_filename=None):
    """Put a record on disk at an arbitrary phase, as a crash would leave it."""
    operation_id = new_operation_id()
    store.workspace.ensure_restore_dir()
    (store.workspace.restore_dir / operation_id).mkdir(parents=True, exist_ok=True)
    (store.workspace.restore_dir / operation_id / "candidate.sqlite").write_bytes(b"evidence")
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


class PostRenameFlushFault:
    """Make the flush *after* the rename fail, for one target phase.

    The rename still happens, so the new phase really is on disk — that is the
    window the corrected code has to survive. Togglable so a test can prove the
    retry on the next launcher start succeeds.
    """

    def __init__(self, phase, *, boundary: str = "flush_directory") -> None:
        self.phase = phase
        self.boundary = boundary
        self.active = True

    def install(self, monkeypatch) -> "PostRenameFlushFault":
        real_transition = RestoreOperationStateStore.transition
        real_boundary = getattr(durability, self.boundary)
        # Sticky on purpose. Arming only *during* the transition would let the
        # engine's immediate confirmation retry succeed, which is a different
        # scenario. This models a host whose flush keeps failing, so the retry
        # fails too and startup has to stay blocked until a later start.
        state = {"armed": False}

        def failing_boundary(*args, **kwargs):
            if state["armed"] and self.active:
                raise OSError(5, "injected post-rename flush failure")
            return real_boundary(*args, **kwargs)

        def guarded(store, record, target, **kwargs):
            if target is self.phase and self.active:
                state["armed"] = True
            return real_transition(store, record, target, **kwargs)

        monkeypatch.setattr(durability, self.boundary, failing_boundary)
        monkeypatch.setattr(RestoreOperationStateStore, "transition", guarded)
        return self


def record_attempted_transitions(monkeypatch):
    """Record every transition the production code attempts."""
    attempts: list[tuple[RestorePhase, RestorePhase]] = []
    real = RestoreOperationStateStore.transition

    def watched(self, record, target, **kwargs):
        attempts.append((record.phase, target))
        return real(self, record, target, **kwargs)

    monkeypatch.setattr(RestoreOperationStateStore, "transition", watched)
    return attempts


def assert_no_unauthorized(attempts):
    for current, target in attempts:
        assert target in ALLOWED_TRANSITIONS[current], (
            f"unauthorized transition attempted: {current.value} -> {target.value}"
        )


def assert_no_terminal_transition(attempts):
    for current, target in attempts:
        assert current not in TERMINAL_PHASES, (
            f"a terminal record was transitioned again: {current.value} -> {target.value}"
        )


# --------------------------------------------------------------------------
# The graph forbids the shortcut in the first place
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "current,target",
    [
        ("completed", "aborted"),
        ("completed", "rollback_in_progress"),
        ("completed", "completed"),
        ("aborted", "aborted"),
        ("rolled_back", "recovery_blocked"),
        ("recovery_blocked", "aborted"),
    ],
)
def test_no_terminal_phase_has_any_successor(current, target):
    """Including self-transitions, which the accepted graph does not define."""
    assert target not in ALLOWED_TRANSITIONS[RestorePhase(current)]


# --------------------------------------------------------------------------
# Post-rename failure at `completed`
# --------------------------------------------------------------------------

@pytest.mark.parametrize("boundary", ["flush_path", "flush_directory"])
def test_a_post_rename_completed_failure_never_attempts_an_unauthorized_transition(
    scenario, monkeypatch, boundary
):
    """The defect: `completed` visible on disk, then the flush fails."""
    workspace, source, context = scenario
    attempts = record_attempted_transitions(monkeypatch)
    PostRenameFlushFault(RestorePhase.COMPLETED, boundary=boundary).install(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert_no_unauthorized(attempts)
    assert_no_terminal_transition(attempts)
    # The record really is `completed`, and that is what gets reported.
    assert result.durable_phase is RestorePhase.COMPLETED
    assert store_for(workspace).read().phase is RestorePhase.COMPLETED
    # Never rolled back from a completed record.
    assert read_marker(workspace.database_path) == "workspace-B"


@pytest.mark.parametrize("boundary", ["flush_path", "flush_directory"])
def test_a_post_rename_completed_failure_blocks_startup_until_confirmed(
    scenario, monkeypatch, boundary
):
    """Durability is unproven, so startup waits even though the phase is safe."""
    workspace, source, context = scenario
    fault = PostRenameFlushFault(
        RestorePhase.COMPLETED, boundary=boundary
    ).install(monkeypatch)

    blocked = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert blocked.durable_phase is RestorePhase.COMPLETED
    assert blocked.normal_startup_allowed is False
    assert blocked.restore_succeeded is False, (
        "success may not be claimed while the record's durability is unproven"
    )

    # The next launcher start retries the confirmation, and it now succeeds.
    fault.active = False
    recovered = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert recovered.durable_phase is RestorePhase.COMPLETED
    assert recovered.normal_startup_allowed is True
    assert recovered.outcome is RestoreOutcome.COMPLETED


def test_a_durability_retry_that_keeps_failing_keeps_blocking(scenario, monkeypatch):
    workspace, source, context = scenario
    PostRenameFlushFault(RestorePhase.COMPLETED).install(monkeypatch)
    execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    # Confirmation still fails on the next start.
    monkeypatch.setattr(
        RestoreOperationStateStore,
        "confirm_record_durability",
        lambda _self: (_ for _ in ()).throw(RestoreStateError("still unprovable")),
    )
    attempts = record_attempted_transitions(monkeypatch)

    again = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert_no_unauthorized(attempts)
    assert_no_terminal_transition(attempts)
    assert again.durable_phase is RestorePhase.COMPLETED
    assert again.normal_startup_allowed is False


def test_a_completed_record_is_never_rolled_back(scenario, monkeypatch):
    """No rollback from a terminal success, whatever the publication did.

    The old code reached `_abort()` here. Rolling back would be even worse than
    the unauthorized transition: it would overwrite a database that had already
    been restored and verified.
    """
    workspace, source, context = scenario
    attempts: list[tuple[RestorePhase, RestorePhase]] = []
    real_transition = RestoreOperationStateStore.transition
    real_boundary = durability.flush_directory
    state = {"armed": False}

    def failing_boundary(*args, **kwargs):
        if state["armed"]:
            raise OSError(5, "injected post-rename flush failure")
        return real_boundary(*args, **kwargs)

    def guarded(self, record, target, **kwargs):
        attempts.append((record.phase, target))
        if target is RestorePhase.COMPLETED:
            state["armed"] = True
        return real_transition(self, record, target, **kwargs)

    monkeypatch.setattr(durability, "flush_directory", failing_boundary)
    monkeypatch.setattr(RestoreOperationStateStore, "transition", guarded)

    execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert not any(
        target is RestorePhase.ROLLBACK_IN_PROGRESS for _current, target in attempts
    ), "a completed record must never enter rollback"
    assert_no_terminal_transition(attempts)
    # The restored data stands: nothing rolled it back.
    assert read_marker(workspace.database_path) == "workspace-B"


# --------------------------------------------------------------------------
# The same rule for the other terminal phases
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "phase", [RestorePhase.ABORTED, RestorePhase.ROLLED_BACK, RestorePhase.COMPLETED]
)
def test_recovery_confirms_durability_before_allowing_startup(
    monkeypatch, tmp_path, phase
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store = store_for(workspace)
    publish_phase(store, phase)
    context = workspace.context()
    try:
        confirmations: list[int] = []
        real_confirm = RestoreOperationStateStore.confirm_record_durability

        def watched(self):
            confirmations.append(1)
            return real_confirm(self)

        monkeypatch.setattr(
            RestoreOperationStateStore, "confirm_record_durability", watched
        )
        attempts = record_attempted_transitions(monkeypatch)

        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert confirmations, f"{phase.value} was allowed to start without confirmation"
    assert result.normal_startup_allowed is True
    assert result.durable_phase is phase
    assert_no_terminal_transition(attempts)


@pytest.mark.parametrize(
    "phase", [RestorePhase.ABORTED, RestorePhase.ROLLED_BACK, RestorePhase.COMPLETED]
)
def test_a_terminal_phase_blocks_startup_when_confirmation_fails(
    monkeypatch, tmp_path, phase
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store = store_for(workspace)
    record = publish_phase(store, phase)
    context = workspace.context()
    try:
        monkeypatch.setattr(
            RestoreOperationStateStore,
            "confirm_record_durability",
            lambda _self: (_ for _ in ()).throw(RestoreStateError("unprovable")),
        )
        attempts = record_attempted_transitions(monkeypatch)

        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.normal_startup_allowed is False
    assert result.durable_phase is phase
    assert_no_terminal_transition(attempts)
    assert_no_unauthorized(attempts)
    # Evidence is preserved for the retry.
    assert (workspace.restore_dir / record.operation_id / "candidate.sqlite").exists()
    assert store.read().phase is phase


def test_recovery_blocked_never_transitions_and_never_starts(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    store = store_for(workspace)
    publish_phase(store, RestorePhase.RECOVERY_BLOCKED)
    context = workspace.context()
    try:
        attempts = record_attempted_transitions(monkeypatch)
        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.normal_startup_allowed is False
    assert result.blocks_browser is True
    assert attempts == []
    assert store.read().phase is RestorePhase.RECOVERY_BLOCKED


# --------------------------------------------------------------------------
# Every persisted phase, and exactly what startup it permits
# --------------------------------------------------------------------------

@pytest.mark.parametrize("phase", list(RestorePhase))
def test_unresolved_phases_never_fall_through_to_ordinary_startup(
    monkeypatch, tmp_path, phase
):
    """The finding: unresolved pre-replacement phases used to be treated as safe.

    Recovery may legitimately *resolve* a phase and then permit startup — an
    interrupted `prepared` becomes `aborted`, a `replacement_intent` rolls back.
    What must never happen is startup proceeding while the phase it started from
    is still the unresolved one.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")
    store = store_for(workspace)
    publish_phase(store, phase, safety_copy_filename=safety.filename)
    context = workspace.context()
    try:
        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    if result.normal_startup_allowed:
        assert result.durable_phase in SAFE_TERMINAL_STARTUP_PHASES, (
            f"startup was allowed from {result.durable_phase} after persisting {phase.value}"
        )
        assert store.read().phase in SAFE_TERMINAL_STARTUP_PHASES
    else:
        assert result.durable_phase is not None or phase is RestorePhase.RECOVERY_BLOCKED


# --------------------------------------------------------------------------
# Initial `prepared` publication ambiguity
# --------------------------------------------------------------------------

def test_an_ambiguous_prepared_publication_is_never_reported_as_no_record(
    scenario, monkeypatch
):
    """`create()` renamed, then its flush failed — a `prepared` record exists.

    Reporting `durable_phase=None` with startup allowed would leave a live
    operation unresolved while the launcher carried on.
    """
    workspace, source, context = scenario
    real_create = RestoreOperationStateStore.create

    def create_then_fail(self, operation_id, phase=RestorePhase.PREPARED):
        real_create(self, operation_id, phase)
        raise RestoreStateError("injected post-rename create failure", published=True)

    monkeypatch.setattr(RestoreOperationStateStore, "create", create_then_fail)
    attempts = record_attempted_transitions(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert_no_unauthorized(attempts)
    assert result.durable_phase is not None, "a visible prepared record was reported as none"
    # It is closed as `aborted`, which the graph authorizes from `prepared`.
    assert result.durable_phase is RestorePhase.ABORTED
    assert store_for(workspace).read().phase is RestorePhase.ABORTED
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_prepared_record_that_cannot_be_closed_blocks_startup(scenario, monkeypatch):
    workspace, source, context = scenario
    real_create = RestoreOperationStateStore.create
    real_transition = RestoreOperationStateStore.transition

    def create_then_fail(self, operation_id, phase=RestorePhase.PREPARED):
        real_create(self, operation_id, phase)
        raise RestoreStateError("injected post-rename create failure", published=True)

    def refuse_abort(self, record, target, **kwargs):
        if target is RestorePhase.ABORTED:
            raise RestoreStateError("abort cannot be published")
        return real_transition(self, record, target, **kwargs)

    monkeypatch.setattr(RestoreOperationStateStore, "create", create_then_fail)
    monkeypatch.setattr(RestoreOperationStateStore, "transition", refuse_abort)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.durable_phase is RestorePhase.PREPARED
    assert result.normal_startup_allowed is False, (
        "ordinary startup must never proceed while prepared remains persisted"
    )
    assert store_for(workspace).read().phase is RestorePhase.PREPARED


def test_a_create_failure_before_the_rename_leaves_no_record(scenario, monkeypatch):
    """The other half: nothing was published, so startup stays allowed."""
    workspace, source, context = scenario
    monkeypatch.setattr(
        RestoreOperationStateStore,
        "create",
        lambda _self, _oid, _phase=RestorePhase.PREPARED: (_ for _ in ()).throw(
            RestoreStateError("scratch creation failed", published=False)
        ),
    )

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.durable_phase is None
    assert result.normal_startup_allowed is True
    assert store_for(workspace).read() is None


def test_an_unreadable_record_after_an_ambiguous_create_blocks_startup(
    scenario, monkeypatch
):
    workspace, source, context = scenario
    real_create = RestoreOperationStateStore.create

    def create_then_corrupt(self, operation_id, phase=RestorePhase.PREPARED):
        real_create(self, operation_id, phase)
        self.record_path.write_text("{ truncated", encoding="utf-8")
        raise RestoreStateError("injected", published=True)

    monkeypatch.setattr(RestoreOperationStateStore, "create", create_then_corrupt)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
