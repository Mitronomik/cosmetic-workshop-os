"""An orphaned backend blocks startup as a **result**, never as an exception.

The finding: `recover_incomplete_restore()` called `context.stop_backend()`
directly. With an orphan holding the liveness lock that raises
`RestoreLifecycleError` — and `run_local_runtime()` expects a `RecoveryResult`,
so an entirely expected condition of the gate escaped the launcher boundary as an
unhandled exception. The user would see a Python traceback where the design calls
for one fixed non-technical sentence.

An orphan is not a fault in the gate. It is the exact situation the gate exists to
notice, and noticing it has one accepted answer: block startup, start nothing,
open no browser, change nothing on disk, and say so.

Both shapes are covered here — an interrupted Restore record present, and no
record at all — because the second is the one a reader is most likely to assume
"cannot happen": with no Restore ever attempted, an orphan alone is still reason
enough to refuse, since ordinary startup would put a second writer on one SQLite
database.

The orphan is modelled by a **separate process** holding the real canonical lock.
That is what a hard-crashed launcher leaves behind, and `flock` is per open file
description, so nothing less would reproduce it.
"""

from pathlib import Path
import subprocess
import sys

import pytest

from launcher import runtime
from launcher.restore.contracts import (
    RECOVERY_BLOCKED_MESSAGE,
    RecoveryResult,
    RestoreOutcome,
)
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    build_workspace_database,
    free_port,
    make_workspace,
    read_marker,
    stub_services,
)

HOLDER = (
    "import fcntl, os, sys, time\n"
    "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
    "fcntl.flock(fd, fcntl.LOCK_EX)\n"
    "print('held', flush=True)\n"
    "time.sleep(300)\n"
)


@pytest.fixture
def workspace_with_orphan(monkeypatch, tmp_path):
    """An isolated workspace whose liveness lock is held by another process."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    lock_path = workspace.restore_dir / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(lock_path)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "held"
        yield workspace
    finally:
        holder.terminate()
        holder.wait(timeout=10)


def unsafe_record(workspace) -> tuple[RestoreOperationStateStore, str]:
    """A durable `replacement_intent` — an interrupted, unrecovered Restore."""
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


# --------------------------------------------------------------------------
# The typed result
# --------------------------------------------------------------------------

def test_an_orphan_with_an_unsafe_record_returns_a_typed_blocked_result(
    workspace_with_orphan,
):
    workspace = workspace_with_orphan
    store, operation_id = unsafe_record(workspace)
    record_before = store.record_path.read_bytes()

    context = workspace.context()
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
    # The phase reported is the one really on disk, and the record is byte-for-byte
    # what it was: no transition, authorized or otherwise, was attempted.
    assert result.durable_phase is RestorePhase.REPLACEMENT_INTENT
    assert result.operation_id == operation_id
    assert store.record_path.read_bytes() == record_before
    # No rollback replacement ran while the orphan was alive.
    assert read_marker(workspace.database_path) == "workspace-B"


def test_an_orphan_with_no_record_at_all_returns_a_typed_blocked_result(
    workspace_with_orphan,
):
    """No Restore was ever attempted; the orphan alone is reason to refuse."""
    workspace = workspace_with_orphan
    store = RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )
    assert store.has_record() is False

    context = workspace.context()
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
    assert result.no_operation is False
    assert result.durable_phase is None
    # And nothing was created on the way to saying so.
    assert store.has_record() is False
    assert read_marker(workspace.database_path) == "workspace-A"


def test_no_lifecycle_error_escapes_the_public_launcher_boundary(workspace_with_orphan):
    """The public entry point returns; it does not raise."""
    from launcher.restore.context import RestoreLifecycleError

    workspace = workspace_with_orphan
    unsafe_record(workspace)

    context = workspace.context()
    try:
        try:
            result = recover_incomplete_restore(
                context, services=stub_services(workspace.database_path)
            )
        except RestoreLifecycleError as exc:  # pragma: no cover - the defect
            pytest.fail(f"a lifecycle error escaped startup recovery: {exc}")
    finally:
        context.release()

    assert result.normal_startup_allowed is False


# --------------------------------------------------------------------------
# What the launcher does with it
# --------------------------------------------------------------------------

def test_run_local_runtime_returns_the_blocked_exit_code(
    workspace_with_orphan, monkeypatch, capsys
):
    """The whole launcher run: one sentence, one exit code, no traceback."""
    workspace = workspace_with_orphan
    unsafe_record(workspace)

    browser_opened: list[str] = []
    started_children: list[object] = []

    monkeypatch.setattr(
        runtime, "open_runtime_browser", lambda config: browser_opened.append("opened")
    )

    def refuse_to_start(*_args, **_kwargs):  # pragma: no cover - must not be called
        started_children.append("started")
        raise AssertionError("a second backend must never be started while blocked")

    monkeypatch.setattr(runtime, "start_backend_process", refuse_to_start)
    monkeypatch.setattr(runtime, "start_owned_backend_process", refuse_to_start)

    from launcher.config import build_runtime_config, resolve_runtime_paths

    config = build_runtime_config(backend_port=free_port(), open_browser=True)
    exit_code = runtime.run_local_runtime(config, resolve_runtime_paths())

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert browser_opened == [], "the browser must stay closed while startup is blocked"
    assert started_children == [], "no backend may be started while startup is blocked"

    printed = capsys.readouterr().out
    assert RECOVERY_BLOCKED_MESSAGE in printed
    # Technical detail stays in the local log. Nothing resembling a traceback,
    # an exception class or a path reaches the user's output.
    assert "Traceback" not in printed
    assert "RestoreLifecycleError" not in printed
    assert "MaintenanceLeaseError" not in printed


def test_the_blocked_run_leaves_the_workspace_exactly_as_it_was(
    workspace_with_orphan, monkeypatch
):
    workspace = workspace_with_orphan
    store, operation_id = unsafe_record(workspace)
    record_before = store.record_path.read_bytes()
    database_before = Path(workspace.database_path).read_bytes()
    safety_copies_before = [path.name for path in workspace.safety_copies()]

    monkeypatch.setattr(runtime, "open_runtime_browser", lambda _config: None)

    from launcher.config import build_runtime_config, resolve_runtime_paths

    config = build_runtime_config(backend_port=free_port(), open_browser=False)
    exit_code = runtime.run_local_runtime(config, resolve_runtime_paths())

    assert exit_code == runtime.RESTORE_BLOCKED_EXIT_CODE
    assert store.record_path.read_bytes() == record_before
    assert Path(workspace.database_path).read_bytes() == database_before
    assert [path.name for path in workspace.safety_copies()] == safety_copies_before
    assert store.read().operation_id == operation_id
