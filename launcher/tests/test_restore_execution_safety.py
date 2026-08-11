"""C4-II-B2 fail-closed maintenance-exclusion regression."""

from __future__ import annotations

import pytest

from launcher.restore.contracts import RestoreFailure, RestoreOutcome, RestoreResult
from launcher.restore.execution_coordinator import (
    RestoreExecutionSafetyError,
    execute_restore_intent,
)
from launcher.tests.restore_fixtures import build_workspace_database
from launcher.tests.test_restore_execution_coordinator import FakeContext, _make_intent


@pytest.fixture
def workspace(tmp_path):
    working = build_workspace_database(tmp_path / "work" / "workshop.sqlite", "working")
    source = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")
    return working, source


def test_unprovable_maintenance_exclusion_raises_launcher_safe_failure(workspace):
    working, _source = workspace
    plane, intent = _make_intent(workspace)
    context = FakeContext(working)
    context.maintenance_lease.held = False

    def fail_acquire():
        raise RuntimeError("synthetic foreign lock")

    context.acquire_maintenance_lease = fail_acquire

    def fake_execute(_request, _context):
        return RestoreResult(
            outcome=RestoreOutcome.RECOVERY_BLOCKED,
            durable_phase=None,
            operation_id="op-test",
            message="blocked",
            normal_startup_allowed=False,
            failure=RestoreFailure.RECOVERY_BLOCKED,
        )

    try:
        with pytest.raises(RestoreExecutionSafetyError):
            execute_restore_intent(
                intent,
                context,
                object(),
                object(),
                plane.session.publish_execution_result,
                execute_restore_fn=fake_execute,
            )

        # The coordinator must not publish an ordinary safe blocked state when it
        # cannot prove the workspace is excluded. Runtime unwinding owns cleanup.
        assert plane.session.current_state.state.value == "restoring"
        assert context.backend.starts == []
    finally:
        plane.close()
