"""C4-II-B2 regression tests for execute vs ordinary backend-exit ordering."""

from __future__ import annotations

import pytest

from launcher import runtime
from launcher.restore.control_protocol import ControlViewState
from launcher.tests.restore_fixtures import build_workspace_database
from launcher.tests.test_restore_execution_coordinator import (
    FakeProcess,
    _accepted_plane,
    request_id,
)


@pytest.fixture
def workspace(tmp_path):
    working = build_workspace_database(tmp_path / "work" / "workshop.sqlite", "working")
    source = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")
    return working, source


def test_late_execute_accepted_during_backend_exit_is_consumed_before_launcher_exit(
    monkeypatch, workspace
):
    plane, token, _source = _accepted_plane(workspace)
    generation = plane.session.current_state.generation
    accepted = []

    class ExitRaceProcess:
        fired = False

        def poll(self):
            if not self.fired:
                self.fired = True
                reply = plane.session.execute(
                    token,
                    request_id=request_id(2),
                    command_seq=2,
                    generation=generation,
                )
                accepted.append(reply)
            return 0

    restarted = FakeProcess(7)
    calls = []

    def fake_execute(intent, context, config, paths, publish):
        calls.append(intent)
        publish(
            intent,
            state=ControlViewState.RESTORE_COMPLETED,
            message="done",
            failure=None,
        )
        return restarted

    import launcher.restore.execution_coordinator as coordinator

    monkeypatch.setattr(coordinator, "execute_restore_intent", fake_execute)
    try:
        result = runtime._run_launcher_owner_loop(
            object(),
            object(),
            object(),
            ExitRaceProcess(),
            plane,
        )
        assert result == 7
        assert len(accepted) == 1
        assert accepted[0].code == "restore_accepted"
        assert len(calls) == 1
        assert calls[0].request_id == request_id(2)
        assert plane.session.current_state.state is ControlViewState.RESTORE_COMPLETED
    finally:
        plane.close()


def test_runtime_exit_seal_refuses_later_execute_without_queueing(workspace):
    plane, token, _source = _accepted_plane(workspace)
    generation = plane.session.current_state.generation
    try:
        assert plane.session.take_execution_intent_or_seal_runtime_exit() is None

        reply = plane.session.execute(
            token,
            request_id=request_id(2),
            command_seq=2,
            generation=generation,
        )
        assert reply.ok is False
        assert reply.code == "launcher_runtime_exiting"
        assert reply.command_seq == 2
        assert plane.session.take_execution_intent() is None

        retry = plane.session.execute(
            token,
            request_id=request_id(2),
            command_seq=2,
            generation=generation,
        )
        assert retry == reply
    finally:
        plane.close()
