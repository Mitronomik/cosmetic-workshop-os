"""A new attempt never inherits a previous operation's identity or outcome.

Two findings, one root cause: a record on disk was read as *this* attempt's
record without ever checking whose it is.

**The ambiguous initial publication.** When `prepared` fails with the rename
possibly landed, the engine re-reads `operation.json`. If the rename in fact
never landed, what it finds is the previous operation's terminal record:

```text
operation A ends at `completed`
operation B is generated
B's `prepared` publication fails ambiguously
the record on disk still says A / completed
B is reported as `completed`, carrying A's operation ID
```

A Restore that never staged a byte would be reported as a success, using someone
else's identity. So the operation ID is compared first, and a foreign record is
treated as what it is: proof this attempt was never published.

**`recovery_blocked` was replaceable.** `create()` grouped all four terminal
phases together, and `recovery_blocked` is terminal but is emphatically not
*completed*. It is the authoritative pointer to an operation nothing could
resolve, and it names the staged candidate and safety copy a support procedure
needs. Letting an ordinary new attempt overwrite it leaves that evidence with
nothing claiming it, and lets the application start past a blocked recovery.
"""

from pathlib import Path
import hashlib

import pytest

from launcher.restore.contracts import RestoreFailure, RestoreOutcome
from launcher.restore.engine import execute_restore
from launcher.restore.phases import RestorePhase
from launcher.restore.safety_copy import create_verified_safety_copy
from launcher.restore.state import (
    RestoreOperationRecord,
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.workspace import RestoreWorkspace, new_operation_id

from launcher.tests.restore_fixtures import (
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)

SAFE_TERMINAL = ["completed", "aborted", "rolled_back"]


def store_for(workspace) -> RestoreOperationStateStore:
    return RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )


def previous_operation(workspace, phase: RestorePhase) -> tuple[str, str]:
    """Publish a terminal record for a *previous* operation, with evidence.

    Returns its operation ID and the safety-copy filename it names, so a test can
    assert both survive untouched.
    """
    safety = create_verified_safety_copy(workspace.database_path, workspace.backup_dir)
    launcher_workspace = RestoreWorkspace.for_database(workspace.database_path)
    store = RestoreOperationStateStore(launcher_workspace)
    operation_id = new_operation_id()
    operation_dir = launcher_workspace.create_operation_dir(operation_id)
    (operation_dir / "candidate.sqlite").write_bytes(b"staged evidence")
    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=phase,
            created_at="2026-08-01T00:00:00+00:00",
            updated_at="2026-08-01T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety.filename,
        )
    )
    return operation_id, safety.filename


def ambiguous_create(monkeypatch):
    """Make the initial publication report "the rename may have landed".

    Nothing is written, which is the case the finding is about: the record that a
    re-read then finds belongs to the *previous* operation.
    """
    monkeypatch.setattr(
        RestoreOperationStateStore,
        "create",
        lambda _self, _oid, _phase=RestorePhase.PREPARED: (_ for _ in ()).throw(
            RestoreStateError("injected post-rename create failure", published=True)
        ),
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


# --------------------------------------------------------------------------
# P1-3 — a previous safe terminal record
# --------------------------------------------------------------------------

@pytest.mark.parametrize("previous_phase", SAFE_TERMINAL)
def test_an_ambiguous_prepared_never_inherits_a_previous_operation(
    scenario, monkeypatch, previous_phase
):
    workspace, source, context = scenario
    phase = RestorePhase(previous_phase)
    previous_id, safety_filename = previous_operation(workspace, phase)
    store = store_for(workspace)
    record_before = store.record_path.read_bytes()

    ambiguous_create(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    # The new attempt is reported as its own, refused, attempt.
    assert result.operation_id != previous_id, (
        "the previous operation's identity was returned as this attempt's"
    )
    assert result.outcome is RestoreOutcome.ABORTED
    assert result.restore_succeeded is False
    assert result.failure is RestoreFailure.PREPARATION_NOT_PUBLISHED

    # The previous record is untouched, byte for byte.
    assert store.record_path.read_bytes() == record_before
    current = store.read()
    assert current.operation_id == previous_id
    assert current.phase is phase
    assert current.safety_copy_filename == safety_filename

    # The working database was never approached.
    assert read_marker(workspace.database_path) == "workspace-A"


@pytest.mark.parametrize("previous_phase", SAFE_TERMINAL)
def test_a_previous_completed_is_never_reported_as_this_attempt_s_success(
    scenario, monkeypatch, previous_phase
):
    """The exact defect: a terminal record on disk, a Restore that never started.

    `durable_phase` still reports what is genuinely on disk — that is what the
    field means, and hiding it would be its own dishonesty. What may never happen
    is the *outcome* being read off it: this attempt aborted, and every property a
    caller branches on for "did this attempt succeed" says so.
    """
    workspace, source, context = scenario
    previous_id, _ = previous_operation(workspace, RestorePhase(previous_phase))
    ambiguous_create(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.restore_succeeded is False
    assert result.outcome is RestoreOutcome.ABORTED
    assert result.outcome is not RestoreOutcome.COMPLETED
    assert result.operation_id != previous_id
    # The message says the attempt did not start, and claims nothing else.
    assert "Восстановление не началось" in result.message
    assert "Данные мастерской не изменились" in result.message
    assert "завершено" not in result.message


@pytest.mark.parametrize("previous_phase", SAFE_TERMINAL)
def test_startup_continues_only_after_the_existing_record_is_confirmed(
    scenario, monkeypatch, previous_phase
):
    """Durability of the *existing* record decides, not this attempt's outcome."""
    workspace, source, context = scenario
    previous_operation(workspace, RestorePhase(previous_phase))
    ambiguous_create(monkeypatch)

    confirmations: list[str] = []
    real_confirm = RestoreOperationStateStore.confirm_record_durability

    def watched(self):
        confirmations.append("confirmed")
        return real_confirm(self)

    monkeypatch.setattr(RestoreOperationStateStore, "confirm_record_durability", watched)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert confirmations, "the existing record's durability was never confirmed"
    assert result.normal_startup_allowed is True
    assert result.durable_phase is RestorePhase(previous_phase)


@pytest.mark.parametrize("previous_phase", SAFE_TERMINAL)
def test_startup_stays_blocked_when_the_existing_record_cannot_be_confirmed(
    scenario, monkeypatch, previous_phase
):
    workspace, source, context = scenario
    previous_operation(workspace, RestorePhase(previous_phase))
    ambiguous_create(monkeypatch)
    monkeypatch.setattr(
        RestoreOperationStateStore,
        "confirm_record_durability",
        lambda _self: (_ for _ in ()).throw(
            RestoreStateError("durability cannot be proved", published=True)
        ),
    )

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.normal_startup_allowed is False


@pytest.mark.parametrize("previous_phase", SAFE_TERMINAL)
def test_only_this_attempt_s_own_empty_directory_is_cleaned(
    scenario, monkeypatch, previous_phase
):
    """Cleanup reaches the new empty directory and nothing else."""
    workspace, source, context = scenario
    previous_id, _ = previous_operation(workspace, RestorePhase(previous_phase))
    ambiguous_create(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    new_dir = workspace.restore_dir / result.operation_id
    assert not new_dir.exists(), "this attempt's empty operation directory was left behind"
    # The previous operation's staged evidence is exactly where it was.
    previous_candidate = workspace.restore_dir / previous_id / "candidate.sqlite"
    assert previous_candidate.read_bytes() == b"staged evidence"


def test_an_unreadable_previous_record_blocks_the_new_attempt(scenario, monkeypatch):
    workspace, source, context = scenario
    previous_operation(workspace, RestorePhase.COMPLETED)
    store = store_for(workspace)
    store.record_path.write_text("{ truncated", encoding="utf-8")

    ambiguous_create(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.normal_startup_allowed is False
    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.restore_succeeded is False
    assert read_marker(workspace.database_path) == "workspace-A"


# --------------------------------------------------------------------------
# P1-3 / P1-4 — a previous `recovery_blocked` record
# --------------------------------------------------------------------------

def test_an_ambiguous_prepared_over_recovery_blocked_refuses_and_blocks(
    scenario, monkeypatch
):
    workspace, source, context = scenario
    previous_id, safety_filename = previous_operation(
        workspace, RestorePhase.RECOVERY_BLOCKED
    )
    store = store_for(workspace)
    record_before = store.record_path.read_bytes()

    ambiguous_create(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.normal_startup_allowed is False
    assert result.restore_succeeded is False
    assert store.record_path.read_bytes() == record_before
    assert store.read().phase is RestorePhase.RECOVERY_BLOCKED
    assert store.read().operation_id == previous_id
    assert store.read().safety_copy_filename == safety_filename
    # Every piece of the blocked operation's evidence remains.
    assert (workspace.restore_dir / previous_id / "candidate.sqlite").exists()
    assert (workspace.backup_dir / safety_filename).exists()


def test_create_refuses_to_overwrite_recovery_blocked(monkeypatch, tmp_path):
    """The store itself refuses; the engine is not the only line of defence."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    previous_id, safety_filename = previous_operation(
        workspace, RestorePhase.RECOVERY_BLOCKED
    )
    store = store_for(workspace)
    record_before = store.record_path.read_bytes()

    with pytest.raises(RestoreStateError, match="blocked Restore recovery"):
        store.create(new_operation_id())

    assert store.record_path.read_bytes() == record_before
    current = store.read()
    assert current.operation_id == previous_id
    assert current.phase is RestorePhase.RECOVERY_BLOCKED
    assert current.staged_candidate_filename == "candidate.sqlite"
    assert current.safety_copy_filename == safety_filename


@pytest.mark.parametrize("previous_phase", SAFE_TERMINAL)
def test_create_still_replaces_a_previously_completed_record(
    monkeypatch, tmp_path, previous_phase
):
    """The positive half: a *completed* operation is replaceable, as before."""
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    previous_operation(workspace, RestorePhase(previous_phase))
    store = store_for(workspace)

    operation_id = new_operation_id()
    record = store.create(operation_id)

    assert record.operation_id == operation_id
    assert store.read().phase is RestorePhase.PREPARED


def test_create_still_refuses_a_live_operation(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    previous_operation(workspace, RestorePhase.REPLACEMENT_INTENT)
    store = store_for(workspace)

    with pytest.raises(RestoreStateError, match="already in progress"):
        store.create(new_operation_id())


def test_a_new_attempt_over_recovery_blocked_leaves_no_operation_directory(
    scenario,
):
    """Ordinary orchestration, no injection: the refusal comes from `create()`."""
    workspace, source, context = scenario
    previous_id, safety_filename = previous_operation(
        workspace, RestorePhase.RECOVERY_BLOCKED
    )
    store = store_for(workspace)
    record_before = store.record_path.read_bytes()
    directories_before = sorted(
        entry.name for entry in workspace.restore_dir.iterdir() if entry.is_dir()
    )

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.outcome is RestoreOutcome.RECOVERY_BLOCKED
    assert result.normal_startup_allowed is False
    assert result.durable_phase is RestorePhase.RECOVERY_BLOCKED
    assert result.operation_id != previous_id

    # Nothing new is left behind, and nothing existing is disturbed.
    assert (
        sorted(entry.name for entry in workspace.restore_dir.iterdir() if entry.is_dir())
        == directories_before
    )
    assert store.record_path.read_bytes() == record_before
    assert (workspace.backup_dir / safety_filename).exists()
    assert read_marker(workspace.database_path) == "workspace-A"


def test_the_blocked_record_survives_repeated_attempts(scenario):
    """Pressing Restore again is not a way out of a blocked recovery."""
    workspace, source, context = scenario
    previous_id, _ = previous_operation(workspace, RestorePhase.RECOVERY_BLOCKED)
    store = store_for(workspace)
    digest_before = hashlib.sha256(store.record_path.read_bytes()).hexdigest()

    for _ in range(3):
        result = execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
        assert result.normal_startup_allowed is False

    assert hashlib.sha256(store.record_path.read_bytes()).hexdigest() == digest_before
    assert store.read().operation_id == previous_id
