"""What happens when the launcher cannot record what it is about to do.

The defect this file exists for: a failure to publish `rollback_in_progress`
left the durable record at `replacement_intent`, `replacement_committed` or
`verification_in_progress` — and the code then tried to transition **straight to
`recovery_blocked`**, which the accepted graph does not authorize. That raises
`PhaseTransitionError` out of the launcher boundary, and worse, it would have
reported a phase that is not on disk.

The corrected rule has three parts, and every test here checks all three:

1. **No unauthorized transition is ever attempted.** Only
   `rollback_in_progress → recovery_blocked` is in the graph, so any other
   starting phase reports rather than forces.
2. **The reported phase is the phase actually on disk.** Never the one this run
   intended to write.
3. **Ordinary startup is blocked while anything is uncertain**, so the next
   launcher start resolves the same real phase through the same matrix.
"""

from pathlib import Path

import pytest

from launcher.restore import state as state_module
from launcher.restore.contracts import RestoreOutcome
from launcher.restore.engine import RestoreServices, execute_restore, perform_rollback
from launcher.restore.phases import (
    ALLOWED_TRANSITIONS,
    PhaseTransitionError,
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
    failing_verifier,
    make_source_backup,
    make_workspace,
    migrating_startup,
    read_marker,
    request_for,
    stub_services,
)

UNSAFE_START_PHASES = [
    RestorePhase.REPLACEMENT_INTENT,
    RestorePhase.REPLACEMENT_COMMITTED,
    RestorePhase.VERIFICATION_IN_PROGRESS,
]


@pytest.fixture
def crashed(monkeypatch, tmp_path):
    """Workspace holding B, with a verified safety copy holding A."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")
    store = RestoreOperationStateStore(
        RestoreWorkspace(
            restore_dir=workspace.restore_dir, database_path=workspace.database_path
        )
    )
    context = workspace.context()
    try:
        yield workspace, context, store, safety
    finally:
        context.release()


def publish_crash_state(store, phase, safety_copy_filename=None):
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


class TransitionFault:
    """A togglable publication fault for one target phase.

    Togglable rather than `monkeypatch.undo()`, because undo would also roll back
    the environment overrides that point the resolvers at the isolated workspace —
    and the whole point of the retry tests is that the *same* workspace is
    resolved again on the next start.
    """

    def __init__(self, phase, *, published: bool = False) -> None:
        self.phase = phase
        self.published = published
        self.active = True

    def install(self, monkeypatch) -> "TransitionFault":
        real = RestoreOperationStateStore.transition

        def guarded(store, record, target, **kwargs):
            if self.active and target is self.phase:
                raise RestoreStateError(
                    f"injected publication failure at {target.value}",
                    published=self.published,
                )
            return real(store, record, target, **kwargs)

        monkeypatch.setattr(RestoreOperationStateStore, "transition", guarded)
        return self


def refuse_transition_to(monkeypatch, phase, *, published: bool = False) -> TransitionFault:
    """Make exactly one target phase unpublishable."""
    return TransitionFault(phase, published=published).install(monkeypatch)


def forbid_unauthorized_transitions(monkeypatch):
    """Fail loudly if any production call attempts an edge outside the graph.

    `require_allowed_transition` already refuses them, but it refuses by raising
    from deep inside the store. This records the attempt so a test can assert the
    engine never even tried, rather than only that the store caught it.
    """
    attempts: list[tuple[RestorePhase, RestorePhase]] = []
    real = RestoreOperationStateStore.transition

    def watched(self, record, target, **kwargs):
        if target not in ALLOWED_TRANSITIONS[record.phase]:
            attempts.append((record.phase, target))
        return real(self, record, target, **kwargs)

    monkeypatch.setattr(RestoreOperationStateStore, "transition", watched)
    return attempts


# --------------------------------------------------------------------------
# The graph itself
# --------------------------------------------------------------------------

def test_recovery_blocked_is_reachable_only_from_rollback_in_progress():
    """The edge whose absence caused the defect."""
    sources = [
        phase
        for phase, targets in ALLOWED_TRANSITIONS.items()
        if RestorePhase.RECOVERY_BLOCKED in targets
    ]

    assert sources == [RestorePhase.ROLLBACK_IN_PROGRESS]


@pytest.mark.parametrize("phase", UNSAFE_START_PHASES)
def test_the_forbidden_shortcut_is_still_refused_by_the_store(phase, tmp_path):
    store = RestoreOperationStateStore(
        RestoreWorkspace(restore_dir=tmp_path / "restore", database_path=tmp_path / "db.sqlite")
    )
    record = publish_crash_state(store, phase)

    with pytest.raises(PhaseTransitionError):
        store.transition(record, RestorePhase.RECOVERY_BLOCKED)


# --------------------------------------------------------------------------
# Failure to publish `rollback_in_progress`
# --------------------------------------------------------------------------

@pytest.mark.parametrize("phase", UNSAFE_START_PHASES)
def test_a_failed_rollback_request_reports_the_actual_durable_phase(
    crashed, monkeypatch, phase
):
    workspace, context, store, safety = crashed
    publish_crash_state(store, phase, safety.filename)
    attempts = forbid_unauthorized_transitions(monkeypatch)
    refuse_transition_to(monkeypatch, RestorePhase.ROLLBACK_IN_PROGRESS)

    result = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert attempts == [], f"an unauthorized transition was attempted: {attempts}"
    assert result.normal_startup_allowed is False
    # The phase reported is the one really on disk, not the one this run wanted.
    assert result.durable_phase is phase
    assert store.read().phase is phase
    assert safety.path.exists(), "evidence is preserved"


@pytest.mark.parametrize("phase", UNSAFE_START_PHASES)
def test_a_failed_rollback_request_never_starts_a_backend_or_browser(
    crashed, monkeypatch, phase
):
    workspace, context, store, safety = crashed
    publish_crash_state(store, phase, safety.filename)
    started: list[object] = []
    refuse_transition_to(monkeypatch, RestorePhase.ROLLBACK_IN_PROGRESS)

    result = recover_incomplete_restore(
        context,
        services=RestoreServices(
            verify_backend=lambda *_a: started.append(_a),
            initialize_startup=migrating_startup(workspace.database_path),
        ),
    )

    assert result.normal_startup_allowed is False
    assert result.blocks_browser is True
    assert started == []


@pytest.mark.parametrize("phase", UNSAFE_START_PHASES)
def test_the_next_launcher_start_retries_recovery_from_the_real_phase(
    crashed, monkeypatch, phase
):
    """A failed rollback request is resumable, not a dead end."""
    workspace, context, store, safety = crashed
    publish_crash_state(store, phase, safety.filename)
    fault = refuse_transition_to(monkeypatch, RestorePhase.ROLLBACK_IN_PROGRESS)

    first = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )
    assert first.normal_startup_allowed is False
    assert first.durable_phase is phase

    # The next start has no injected fault and resolves the same real phase.
    fault.active = False
    second = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert second.outcome is RestoreOutcome.ROLLED_BACK
    assert store.read().phase is RestorePhase.ROLLED_BACK
    assert read_marker(workspace.database_path) == "workspace-A"


def test_an_engine_side_failed_rollback_request_reports_honestly(monkeypatch, tmp_path):
    """The same rule on the execute path, not only on the recovery path."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        attempts = forbid_unauthorized_transitions(monkeypatch)
        refuse_transition_to(monkeypatch, RestorePhase.ROLLBACK_IN_PROGRESS)

        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(
                workspace.database_path, verify=failing_verifier("verification refused")
            ),
        )
    finally:
        context.release()

    assert attempts == []
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.normal_startup_allowed is False
    # `verification_in_progress` is what really remains on disk.
    assert result.durable_phase is RestorePhase.VERIFICATION_IN_PROGRESS


# --------------------------------------------------------------------------
# Failure to publish the terminal rollback phases
# --------------------------------------------------------------------------

def test_a_failed_recovery_blocked_publication_keeps_rollback_in_progress(
    crashed, monkeypatch
):
    """The durable phase stays resumable rather than being claimed."""
    workspace, context, store, safety = crashed
    publish_crash_state(store, RestorePhase.ROLLBACK_IN_PROGRESS, safety.filename)
    attempts = forbid_unauthorized_transitions(monkeypatch)
    refuse_transition_to(monkeypatch, RestorePhase.RECOVERY_BLOCKED)

    result = recover_incomplete_restore(
        context,
        services=RestoreServices(
            verify_backend=failing_verifier("always fails", only_first=False),
            initialize_startup=migrating_startup(workspace.database_path),
        ),
    )

    assert attempts == []
    assert result.normal_startup_allowed is False
    assert result.durable_phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS
    assert safety.path.exists()


def test_a_failed_rolled_back_publication_does_not_claim_success(crashed, monkeypatch):
    """A rollback that worked but could not be recorded is not `rolled_back`."""
    workspace, context, store, safety = crashed
    publish_crash_state(store, RestorePhase.ROLLBACK_IN_PROGRESS, safety.filename)
    attempts = forbid_unauthorized_transitions(monkeypatch)
    refuse_transition_to(monkeypatch, RestorePhase.ROLLED_BACK)

    result = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert attempts == []
    assert result.outcome is not RestoreOutcome.ROLLED_BACK
    assert result.normal_startup_allowed is False
    assert store.read().phase is RestorePhase.RECOVERY_BLOCKED


def test_no_unhandled_exception_escapes_any_publication_failure(crashed, monkeypatch):
    """Every injected failure produces a typed result, never a raised phase error."""
    workspace, context, store, safety = crashed
    fault = TransitionFault(RestorePhase.ROLLBACK_IN_PROGRESS).install(monkeypatch)

    for phase in (
        RestorePhase.ROLLBACK_IN_PROGRESS,
        RestorePhase.ROLLED_BACK,
        RestorePhase.RECOVERY_BLOCKED,
        RestorePhase.ABORTED,
    ):
        fault.active = False
        publish_crash_state(store, RestorePhase.REPLACEMENT_INTENT, safety.filename)
        fault.phase = phase
        fault.active = True

        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )

        assert isinstance(result.normal_startup_allowed, bool)
        assert result.durable_phase in set(RestorePhase) | {None}


def test_perform_rollback_refuses_to_run_from_the_wrong_phase(crashed):
    """The precondition is asserted rather than assumed."""
    from launcher.restore.engine import RestoreEngineError

    workspace, context, store, safety = crashed
    record = publish_crash_state(store, RestorePhase.REPLACEMENT_INTENT, safety.filename)

    with pytest.raises(RestoreEngineError):
        perform_rollback(
            store,
            record,
            context.workspace,
            context,
            stub_services(workspace.database_path),
        )


# --------------------------------------------------------------------------
# Production code respects the graph
# --------------------------------------------------------------------------

def test_production_modules_never_bypass_the_transition_graph():
    """`publish` skips the graph, so only `state.py` itself may call it.

    Everything else goes through `transition`, which calls
    `require_allowed_transition`. That is what makes the graph a runtime
    guarantee rather than a convention.
    """
    import inspect

    from launcher.restore import engine, recovery

    for module in (engine, recovery):
        source = inspect.getsource(module)
        assert ".publish(" not in source, (
            f"{module.__name__} bypasses the transition graph via publish()"
        )
        assert "store.publish" not in source


def test_the_state_store_validates_every_transition():
    import inspect

    body = inspect.getsource(state_module.RestoreOperationStateStore.transition)

    assert "require_allowed_transition" in body
