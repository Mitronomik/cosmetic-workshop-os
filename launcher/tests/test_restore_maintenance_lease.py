"""The retained maintenance lease, and what it keeps out of the workspace.

The finding: the backend-liveness lock was checked *momentarily*. The launcher
opened it, took a non-blocking exclusive `flock`, released it and closed the
descriptor. That answers "was the lock free at this instant" — and Restore needs
"will it stay free for the whole destructive interval":

```text
launcher checks the lock            ← free
launcher releases it
another backend acquires it         ← nothing prevented this
launcher settles the SQLite journal
launcher replaces the working database
```

Every step reported success and a live writer held the database throughout.

The fix is to keep the lock rather than sample it. These tests prove the keeping
is real, and they prove it the only way it can honestly be proved: with a
**separate process** actually attempting the acquisition, at the exact moments
that matter. `flock` is per open file description, so a same-process probe would
be answering a different question.
"""

from pathlib import Path
import os
import subprocess
import sys

import pytest

from launcher.restore import engine as engine_module
from launcher.restore.context import RestoreLifecycleError
from launcher.restore.contracts import RestoreOutcome
from launcher.restore.durability import PublicationCategory
from launcher.restore.engine import execute_restore
from launcher.restore.maintenance_lease import (
    BackendMaintenanceLease,
    MaintenanceLeaseError,
)
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
from launcher.restore.verification import VERIFICATION_CYCLES
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    failing_verifier,
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)

# A separate process that tries the same non-blocking exclusive acquisition a real
# backend would make. Its exit status is the answer, so nothing is inferred from
# this process's own descriptors.
_PROBE = (
    "import fcntl, os, sys\n"
    "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
    "try:\n"
    "    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
    "except OSError:\n"
    "    sys.exit(1)\n"
    "sys.exit(0)\n"
)


def another_process_can_take_the_lock(lock_path: Path) -> bool:
    """Whether a *second process* could acquire the backend-liveness lock now.

    This is the question a real backend asks at startup, asked the same way. A
    check inside this process would not answer it: `flock` is associated with the
    open file description, and a same-process probe on a second descriptor tests
    the platform's re-entrancy rules rather than the exclusion being claimed.
    """
    completed = subprocess.run(
        [sys.executable, "-c", _PROBE, str(lock_path)], timeout=60
    )
    return completed.returncode == 0


# --------------------------------------------------------------------------
# The lease primitive
# --------------------------------------------------------------------------

def test_a_held_lease_keeps_a_separate_process_out(tmp_path):
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lease = BackendMaintenanceLease(lock_path)

    assert another_process_can_take_the_lock(lock_path) is True

    lease.acquire()
    try:
        assert lease.held is True
        assert another_process_can_take_the_lock(lock_path) is False, (
            "a retained lease must keep a second backend out"
        )
    finally:
        lease.release()

    assert lease.held is False
    assert another_process_can_take_the_lock(lock_path) is True


def test_a_momentary_check_would_not_have_kept_anyone_out(tmp_path):
    """The defect, stated as a test: availability is not reservation."""
    from launcher.restore.context import backend_liveness_lock_is_free

    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # The old proof: free at this instant.
    assert backend_liveness_lock_is_free(lock_path) is True
    # And immediately afterwards anybody may take it, which is exactly the window
    # a destructive interval used to run inside.
    assert another_process_can_take_the_lock(lock_path) is True


def test_acquiring_a_held_lease_again_is_a_no_op(tmp_path):
    """Nested destructive intervals re-enter; that is not a conflict."""
    lease = BackendMaintenanceLease(tmp_path / "restore" / "backend-liveness.lock")
    lease.acquire()
    try:
        assert lease.acquire() is lease
        assert lease.held is True
    finally:
        lease.release()
    # Releasing twice is equally harmless.
    lease.release()
    assert lease.held is False


def test_a_lease_is_refused_while_another_process_holds_the_lock(tmp_path):
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
        lease = BackendMaintenanceLease(lock_path)
        with pytest.raises(MaintenanceLeaseError):
            lease.acquire()
        with pytest.raises(MaintenanceLeaseError):
            lease.acquire_with_retry(timeout_seconds=0.5, poll_seconds=0.05)
        assert lease.held is False
    finally:
        holder.terminate()
        holder.wait(timeout=10)


# --------------------------------------------------------------------------
# The lease inside the lifecycle
# --------------------------------------------------------------------------

def test_stopping_the_backend_takes_and_retains_the_lease(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert context.maintenance_lease.held is False

        context.stop_backend()

        assert context.maintenance_lease.held is True
        assert another_process_can_take_the_lock(
            context.backend_liveness_lock_path
        ) is False
    finally:
        context.release()

    # Releasing the context gives the workspace back.
    assert another_process_can_take_the_lock(workspace.restore_dir / "backend-liveness.lock") is True


def test_touching_the_working_database_requires_the_retained_lease(monkeypatch, tmp_path):
    """`require_backend_stopped()` is not satisfied by a past momentary check."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        context.stop_backend()
        context.require_backend_stopped()

        # The stop proof is untouched and no backend is running; only the lease
        # has gone. That alone must be refusal, because the workspace is no longer
        # reserved and a backend could take it at any moment.
        context.release_maintenance_lease()

        with pytest.raises(RestoreLifecycleError, match="maintenance lease"):
            context.require_backend_stopped()
    finally:
        context.release()


def test_the_lease_is_held_at_journal_settlement_and_replacement(monkeypatch, tmp_path):
    """The two moments the finding names, observed from a separate process."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    observed: dict[str, bool] = {}
    lock_path = context.backend_liveness_lock_path

    real_quiesce = engine_module.quiesce_target_journal
    real_commit = engine_module.commit_replacement

    def watched_quiesce(path):
        observed["journal_lease_held"] = context.maintenance_lease.held
        observed["journal_excluded"] = not another_process_can_take_the_lock(lock_path)
        return real_quiesce(path)

    def watched_commit(artifact, database_path, **kwargs):
        observed["replacement_lease_held"] = context.maintenance_lease.held
        observed["replacement_excluded"] = not another_process_can_take_the_lock(lock_path)
        return real_commit(artifact, database_path, **kwargs)

    monkeypatch.setattr(engine_module, "quiesce_target_journal", watched_quiesce)
    monkeypatch.setattr(engine_module, "commit_replacement", watched_commit)

    try:
        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.COMPLETED
    assert observed["journal_lease_held"] is True
    assert observed["journal_excluded"] is True, (
        "a backend could have started while the journal was being settled"
    )
    assert observed["replacement_lease_held"] is True
    assert observed["replacement_excluded"] is True, (
        "a backend could have started while the database was being replaced"
    )


def test_the_lease_is_held_at_the_rollback_replacement(monkeypatch, tmp_path):
    """Rollback writes the safety copy over the working database; same rule."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    observed: list[tuple[bool, bool]] = []
    lock_path = context.backend_liveness_lock_path
    real_commit = engine_module.commit_replacement

    def watched_commit(artifact, database_path, **kwargs):
        if kwargs.get("category") is PublicationCategory.ROLLBACK_REPLACEMENT:
            observed.append(
                (
                    context.maintenance_lease.held,
                    not another_process_can_take_the_lock(lock_path),
                )
            )
        return real_commit(artifact, database_path, **kwargs)

    monkeypatch.setattr(engine_module, "commit_replacement", watched_commit)

    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(
                workspace.database_path, verify=failing_verifier()
            ),
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ROLLED_BACK
    assert observed == [(True, True)], (
        "the rollback replacement ran without exclusive use of the workspace"
    )
    assert read_marker(workspace.database_path) == "workspace-A"


def test_verification_releases_the_lease_and_takes_it_back(monkeypatch, tmp_path):
    """The accepted cycle, observed at each step.

    Verification is the one part of Restore that must *start* a backend, and a
    backend cannot start while the launcher retains the lease. So the lease is
    released for exactly that interval and taken back before anything may
    continue or roll back.

    Once per cycle, not once for the whole verification: each of the two cycles
    is its own release and its own reacquisition. The between-cycle moment is
    proved separately, against real backend children, in
    `launcher/tests/test_restore_verification_lease_boundaries.py`.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    during_verification: list[bool] = []

    def verify(_config, _paths, _database_path):
        during_verification.append(context.maintenance_lease.held)
        # The window really is open: a backend could take the lock right now,
        # which is the whole reason the lease had to be released.
        during_verification.append(
            another_process_can_take_the_lock(context.backend_liveness_lock_path)
        )
        return None

    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(workspace.database_path, verify=verify),
        )
        lease_after = context.maintenance_lease.held
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.COMPLETED
    assert during_verification == [False, True] * VERIFICATION_CYCLES, (
        "the lease must be released for each owned verification backend"
    )
    assert lease_after is True, "the lease must be back before anything continues"


def test_a_failed_verification_rolls_back_only_with_the_lease_reacquired(
    monkeypatch, tmp_path
):
    """The failure path takes the lease back too — rollback is destructive."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()

    at_rollback_entry: list[bool] = []
    real_enter = engine_module.perform_rollback

    def watched_rollback(store, record, ws, ctx, services, *args, **kwargs):
        at_rollback_entry.append(ctx.maintenance_lease.held)
        return real_enter(store, record, ws, ctx, services, *args, **kwargs)

    monkeypatch.setattr(engine_module, "perform_rollback", watched_rollback)

    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(workspace.database_path, verify=failing_verifier()),
        )
    finally:
        context.release()

    assert result.outcome is RestoreOutcome.ROLLED_BACK
    assert at_rollback_entry == [True], (
        "rollback was entered without the reacquired maintenance lease"
    )


def test_rollback_is_refused_when_the_lease_cannot_be_reacquired(monkeypatch, tmp_path):
    """No lease, no replacement. Recovery blocks instead.

    Startup recovery resolves a crashed `rollback_in_progress`, which replaces the
    working database from the safety copy. With the lease unavailable — modelled
    here by a lease that refuses to be taken, as an orphaned backend would make it
    — the rollback must not run at all.
    """
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    build_workspace_database(workspace.database_path, "workspace-B")

    launcher_workspace = RestoreWorkspace.for_database(workspace.database_path)
    store = RestoreOperationStateStore(launcher_workspace)
    operation_id = new_operation_id()
    launcher_workspace.create_operation_dir(operation_id)
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

    context = workspace.context()

    def refuse(*_args, **_kwargs):
        raise MaintenanceLeaseError("the workspace is owned by something else")

    monkeypatch.setattr(context.maintenance_lease, "acquire_with_retry", refuse)

    try:
        result = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    # The rollback replacement never ran: the restored candidate is still there.
    assert read_marker(workspace.database_path) == "workspace-B"
    assert store.read().phase is RestorePhase.ROLLBACK_IN_PROGRESS


def test_the_lease_guards_the_canonical_backend_liveness_lock(monkeypatch, tmp_path):
    """A lease over some other path would leave the real target unguarded."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    context = workspace.context()
    try:
        assert (
            context.maintenance_lease.lock_path
            == context.workspace.backend_liveness_lock_path
        )
        context.maintenance_lease = BackendMaintenanceLease(tmp_path / "elsewhere.lock")

        with pytest.raises(RestoreLifecycleError, match="canonical backend-liveness lock"):
            context.require_authority()
    finally:
        context.lock.release()


def test_the_lease_never_discovers_or_signals_a_process():
    """Detection is not authority; the lease has neither, by construction."""
    from launcher.restore import maintenance_lease as lease_module
    from launcher.tests.test_restore_context import executable_source

    code = executable_source(lease_module)
    for forbidden in ("pkill", "pgrep", "killall", "lsof", "psutil", "getoutput", "kill"):
        assert forbidden not in code, f"{forbidden} must never appear in the lease"
    assert "os.kill" not in code
