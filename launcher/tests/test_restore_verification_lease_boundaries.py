"""Where the maintenance lease is released, and how narrowly.

The fourth-audit finding `P1-1`: the lease was released around the **whole**
startup-plus-verification block rather than around each exact owned-backend
lifetime. That left two windows in which nothing held the canonical
backend-liveness lock while Restore was still active:

```text
maintenance lease held
→ release lease
→ services.startup / migrations        ← window A: no backend runs, nothing holds
→ verification backend cycle 1           the lock, and the restored database is
→ backend stops                          being migrated underneath
→                                      ← window B: cycle 1's child is gone and
→ verification backend cycle 2           the launcher has not taken the lease
→ backend stops                          back, so any backend may acquire it
→ reacquire maintenance lease
```

The invariant these tests hold the implementation to is that at every moment
either the launcher holds the lease, or one exact launcher-owned child holds the
lock and has completed the handshake. Never neither.

Every exclusion claim here is made by a **separate process** attempting the same
non-blocking exclusive acquisition a real backend makes at startup. `flock` is
per open file description, so a same-process probe would be answering a different
question, and the between-cycle moment is exactly where an honest answer matters.

The cycle-boundary tests start **real** uvicorn children through the real
verifier. That is the point: the handoff is a property of the production window
and the production child, and a stub going through a stub runner could not
distinguish the fixed code from the defect.
"""

from pathlib import Path
import inspect

import pytest

from launcher.restore import engine as engine_module
from launcher.restore.context import RestoreLifecycleError
from launcher.restore.contracts import RestoreOutcome
from launcher.restore.engine import RestoreServices, execute_restore
from launcher.restore.maintenance_lease import MaintenanceLeaseError
from launcher.restore.phases import RestorePhase
from launcher.restore.state import RestoreOperationStateStore
from launcher.restore.verification import VERIFICATION_CYCLES, verify_restored_backend
from launcher.restore.workspace import RestoreWorkspace

from launcher.tests.restore_fixtures import (
    cycle_shaped_verifier,
    make_source_backup,
    make_workspace,
    migrating_startup,
    read_marker,
    request_for,
    stub_services,
)
from launcher.tests.test_restore_maintenance_lease import (
    another_process_can_take_the_lock,
)


def excluded(context) -> bool:
    """Whether a separate process is currently kept out of this workspace."""
    return not another_process_can_take_the_lock(context.backend_liveness_lock_path)


def code_of(obj) -> str:
    """One callable's source with comments and string literals removed.

    The engine *documents* the old broad window in prose, precisely so a reader
    understands why it is gone. The structural checks below are about what the
    code does, so the prose has to go — otherwise explaining the fix would trip
    the test that proves it.
    """
    import io
    import textwrap
    import tokenize

    source = textwrap.dedent(inspect.getsource(obj))
    kept: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept)


def failing_on_cycle(cycle_number: int, message: str = "verification refused"):
    """A check that refuses exactly the nth call and passes every other one.

    Cycle numbering is per Restore attempt, so `2` is the restartability cycle —
    the one that only runs after cycle 1 has stopped its child and the launcher
    has taken the lease back.
    """
    calls = {"n": 0}

    def check(_config, _paths, _database_path):
        calls["n"] += 1
        if calls["n"] == cycle_number:
            raise RuntimeError(message)
        return None

    return check


# --------------------------------------------------------------------------
# Window A — startup and migrations
# --------------------------------------------------------------------------

def test_startup_and_migrations_run_under_the_retained_lease(monkeypatch, tmp_path):
    """Migrations need no backend, so the lease is never handed over for them.

    `services.startup()` opens and rewrites the restored working database. No
    child is involved, so there is nobody to hand the lock to — releasing it
    there would simply leave the database unreserved while it was being written,
    and a separate backend could open it mid-migration.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    observed: dict[str, bool] = {}
    real_startup = migrating_startup(workspace.database_path)

    def watched_startup(mode, paths):
        observed["lease_held"] = context.maintenance_lease.held
        observed["excluded"] = excluded(context)
        return real_startup(mode, paths)

    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(workspace.database_path, startup=watched_startup),
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.COMPLETED
    assert observed["lease_held"] is True, (
        "startup migrations ran with the maintenance lease released"
    )
    assert observed["excluded"] is True, (
        "a separate backend could have opened the database during migrations"
    )


def test_rollback_startup_and_migrations_also_run_under_the_lease(monkeypatch, tmp_path):
    """The recovery path has the same split, not a looser one."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    observed: list[tuple[bool, bool]] = []
    real_startup = migrating_startup(workspace.database_path)

    def watched_startup(mode, paths):
        observed.append((context.maintenance_lease.held, excluded(context)))
        return real_startup(mode, paths)

    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(
                workspace.database_path,
                verify=failing_on_cycle(1),
                startup=watched_startup,
            ),
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ROLLED_BACK
    # Two startups: the restored candidate's, and the rolled-back workspace's.
    assert observed == [(True, True), (True, True)], (
        "a startup ran without the retained maintenance lease"
    )


# --------------------------------------------------------------------------
# Window B — the boundary between the two verification cycles
# --------------------------------------------------------------------------

def test_each_verification_cycle_releases_and_reacquires_the_lease(monkeypatch, tmp_path):
    """The real verifier, the real window, real children, real probes.

    One observation before and one after each cycle. Both must show the launcher
    holding the lease and a separate process kept out — which for the pair
    `("after", cycle 1)` and `("before", cycle 2)` is the between-cycle moment
    the finding is about.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()

    events: list[tuple[str, int, bool, bool]] = []
    cycle_index = {"n": 0}

    def watched_cycle(cycle):
        cycle_index["n"] += 1
        index = cycle_index["n"]
        events.append(("before", index, context.maintenance_lease.held, excluded(context)))
        try:
            return context.run_owned_backend_cycle(cycle)
        finally:
            events.append(("after", index, context.maintenance_lease.held, excluded(context)))

    try:
        # The lease is taken exactly as the engine takes it, so this exercises the
        # production precondition rather than a hand-set flag.
        context.stop_backend()
        assert context.maintenance_lease.held is True

        report = verify_restored_backend(
            context.config,
            context.paths,
            context.database_path,
            run_backend_cycle=watched_cycle,
        )
        lease_after = context.maintenance_lease.held
    finally:
        context.release()

    assert report.cycles_completed == VERIFICATION_CYCLES == 2
    assert events == [
        ("before", 1, True, True),
        ("after", 1, True, True),
        ("before", 2, True, True),
        ("after", 2, True, True),
    ], "the lease was not held at every verification cycle boundary"
    assert lease_after is True


def test_no_separate_backend_can_acquire_the_lock_between_the_two_cycles(
    monkeypatch, tmp_path
):
    """The exact defect window, probed at the exact moment it existed.

    After cycle 1's child has stopped and before cycle 2's child starts, the
    canonical lock must be unavailable to anyone else — because the launcher took
    the lease back rather than holding one release open across both cycles.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()

    between: list[bool] = []
    completed_cycles = {"n": 0}

    def watched_cycle(cycle):
        if completed_cycles["n"] == 1:
            # Cycle 1 is over, cycle 2 has not started. This is the gap.
            between.append(another_process_can_take_the_lock(
                context.backend_liveness_lock_path
            ))
        try:
            return context.run_owned_backend_cycle(cycle)
        finally:
            completed_cycles["n"] += 1

    try:
        context.stop_backend()
        verify_restored_backend(
            context.config,
            context.paths,
            context.database_path,
            run_backend_cycle=watched_cycle,
        )
    finally:
        context.release()

    assert between == [False], (
        "a separate backend could have taken the workspace between the two "
        "verification cycles"
    )


def test_the_owned_child_holds_the_lock_while_a_cycle_runs(monkeypatch, tmp_path):
    """The other half of the invariant: released only *to* an exact child.

    Inside a cycle the launcher genuinely does not hold the lease. That is safe
    only because the child it started holds the same canonical lock — which its
    pre-import handshake proved before any check could run. Observed from the
    representative-read step, so the child is demonstrably up and serving.
    """
    from launcher.restore import verification as verification_module

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()

    while_serving: list[tuple[bool, bool]] = []
    real_reads = verification_module._check_representative_reads

    def watched_reads(base_url):
        while_serving.append((context.maintenance_lease.held, excluded(context)))
        return real_reads(base_url)

    monkeypatch.setattr(
        verification_module, "_check_representative_reads", watched_reads
    )

    try:
        context.stop_backend()
        verify_restored_backend(
            context.config,
            context.paths,
            context.database_path,
            run_backend_cycle=context.run_owned_backend_cycle,
        )
    finally:
        context.release()

    # The lease is gone, and the workspace is still excluded — by the child, not
    # by the launcher. Never neither.
    assert while_serving == [(False, True), (False, True)]


# --------------------------------------------------------------------------
# Failure paths — the lease comes back before anything destructive
# --------------------------------------------------------------------------

@pytest.mark.parametrize("failing_cycle", [1, 2])
def test_a_failed_verification_cycle_reacquires_the_lease_before_rollback(
    monkeypatch, tmp_path, failing_cycle
):
    """Rollback replaces the working database, so it may only run under the lease.

    Parametrised over both cycles because they fail from different places: cycle
    1 fails with the lease released for the first time, cycle 2 fails after a
    reacquisition has already happened once.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    at_rollback_entry: list[tuple[bool, bool, bool]] = []
    real_rollback = engine_module.perform_rollback

    def watched_rollback(store, record, ws, ctx, services, *args, **kwargs):
        at_rollback_entry.append(
            (ctx.maintenance_lease.held, excluded(ctx), ctx.backend.is_running)
        )
        return real_rollback(store, record, ws, ctx, services, *args, **kwargs)

    monkeypatch.setattr(engine_module, "perform_rollback", watched_rollback)

    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(
                workspace.database_path, verify=failing_on_cycle(failing_cycle)
            ),
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ROLLED_BACK
    assert at_rollback_entry == [(True, True, False)], (
        "rollback was entered without the reacquired lease, or with a child still running"
    )
    assert read_marker(workspace.database_path) == "workspace-A"


def test_a_failed_reacquisition_prevents_the_rollback_replacement(monkeypatch, tmp_path):
    """No lease, no replacement — not even the rollback's own.

    The reacquisition at the end of a verification cycle is made to fail, which
    is what an orphaned backend taking the freed lock would do. The engine must
    refuse to replace the working database rather than rolling back unprotected,
    and it must say so through the existing recovery-safe contract instead of
    claiming an outcome.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    real_acquire = context.maintenance_lease.acquire_with_retry
    attempts = {"n": 0}

    def refuse_after_the_first(*args, **kwargs):
        attempts["n"] += 1
        # The first acquisition is `stop_backend()`'s, before anything has been
        # released. Every later one is a reacquisition after a handover.
        if attempts["n"] == 1:
            return real_acquire(*args, **kwargs)
        raise MaintenanceLeaseError("the workspace is owned by something else")

    monkeypatch.setattr(
        context.maintenance_lease, "acquire_with_retry", refuse_after_the_first
    )

    try:
        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.normal_startup_allowed is False
    # The rollback replacement never ran: the replaced database is still the
    # restored candidate, untouched by an unprotected write-back.
    assert read_marker(workspace.database_path) == "workspace-B"
    assert store.read().phase is RestorePhase.RECOVERY_BLOCKED
    # Every piece of evidence is preserved for the support procedure.
    assert workspace.safety_copies() != []


def test_a_window_cannot_be_opened_without_the_lease_in_hand(monkeypatch, tmp_path):
    """Releasing a lease nobody holds would be a silent no-op, so it is refused."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert context.maintenance_lease.held is False

        with pytest.raises(RestoreLifecycleError, match="maintenance lease"):
            with context.owned_backend_window():  # pragma: no cover - must not run
                pytest.fail("a window opened without the lease")

        with pytest.raises(RestoreLifecycleError, match="maintenance lease"):
            context.run_owned_backend_cycle(
                lambda: pytest.fail("a cycle ran without the lease")  # pragma: no cover
            )
    finally:
        context.release()


def test_a_window_takes_the_lease_back_even_when_the_cycle_raises(monkeypatch, tmp_path):
    """The `finally` is the contract; the original failure is what propagates."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.stop_backend()

        with pytest.raises(RuntimeError, match="the cycle refused"):
            context.run_owned_backend_cycle(
                lambda: (_ for _ in ()).throw(RuntimeError("the cycle refused"))
            )

        assert context.maintenance_lease.held is True
        assert excluded(context) is True
    finally:
        context.release()


# --------------------------------------------------------------------------
# The shape itself
# --------------------------------------------------------------------------

def test_the_engine_never_wraps_startup_and_verification_in_one_window():
    """The defect, refused at the source level.

    A future edit that puts `owned_backend_window()` back around
    `_verify_restored_workspace` would reopen both windows at once, and every
    behavioural test above would still pass on the *stub* path. This is the
    cheap, direct statement of the rule.
    """
    for name, source in (
        ("_verify_restored_workspace", code_of(engine_module._verify_restored_workspace)),
        ("perform_rollback", code_of(engine_module.perform_rollback)),
    ):
        assert "owned_backend_window" not in source, (
            f"{name} opens a backend window of its own; the handoff belongs to "
            "one owned-backend lifetime inside the verifier"
        )
        assert "services . verify ( context )" in source


def test_the_verifier_is_always_given_the_launcher_owned_cycle_runner():
    """One call site, and it is the context's own window that is passed."""
    source = code_of(RestoreServices.verify)

    assert "run_backend_cycle = context . run_owned_backend_cycle" in source
    # And the real verifier cannot be called without one: no default to forget.
    signature = inspect.signature(verify_restored_backend)
    parameter = signature.parameters["run_backend_cycle"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


def test_one_owned_backend_lifetime_is_implemented_in_exactly_one_place():
    """No call site may reimplement half of the handoff.

    `release → child → stop → wait for the lock → reacquire` exists once, in
    `LauncherLifecycleContext.owned_backend_window`. Nothing else in the Restore
    package may release the lease, because a second implementation is how the two
    halves drift apart.
    """
    from launcher.restore import context as context_module
    from launcher.restore import verification as verification_module

    releasing = [
        name
        for name, source in (
            ("engine", code_of(engine_module)),
            ("verification", code_of(verification_module)),
        )
        if "release_maintenance_lease" in source
    ]
    assert releasing == [], f"the lease is released outside the window in: {releasing}"

    window = code_of(context_module.LauncherLifecycleContext.owned_backend_window)
    assert "release_maintenance_lease" in window
    assert "wait_until_liveness_lock_released" in window
    assert "acquire_maintenance_lease" in window


def test_the_stub_verifier_goes_through_the_production_runner():
    """The fixture may not be the thing that makes the lease protocol correct.

    `cycle_shaped_verifier` starts no process, but it calls the runner it is
    given, the production number of times. If it instead managed the lease
    itself, every phase-machine test would be asserting against a test-local
    protocol and `P1-1` could return unnoticed.
    """
    source = code_of(cycle_shaped_verifier)

    assert "run_backend_cycle (" in source
    for forbidden in (
        "release_maintenance_lease",
        "acquire_maintenance_lease",
        "maintenance_lease.acquire",
        "maintenance_lease.release",
    ):
        assert forbidden not in source, (
            f"the stub verifier manages the lease itself via {forbidden}"
        )


def test_the_window_never_discovers_or_signals_a_process():
    """Detection is not authority, and that has not changed here."""
    from launcher.restore import context as context_module

    source = code_of(context_module.LauncherLifecycleContext.owned_backend_window)
    source += code_of(context_module.LauncherLifecycleContext.run_owned_backend_cycle)
    for forbidden in ("pkill", "pgrep", "killall", "lsof", "psutil", "os.kill"):
        assert forbidden not in source


def test_the_restored_database_is_the_one_every_cycle_serves(monkeypatch, tmp_path):
    """Narrowing the window changed nothing about which database is verified."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()

    served: list[Path] = []

    def watched_cycle(cycle):
        served.append(context.database_path)
        return context.run_owned_backend_cycle(cycle)

    try:
        context.stop_backend()
        report = verify_restored_backend(
            context.config,
            context.paths,
            context.database_path,
            run_backend_cycle=watched_cycle,
        )
    finally:
        context.release()

    assert served == [workspace.database_path, workspace.database_path]
    assert report.database_path == workspace.database_path
