"""C4-II-A2 session/replay/generation coordination tests."""

from __future__ import annotations

from pathlib import Path
import threading
import time

import pytest

from launcher.restore.control_protocol import SourceSelectionResult
from launcher.restore.control_session import RestoreControlSession
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.tests.restore_fixtures import build_workspace_database


class FakeClock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class BlockingAdapter:
    def __init__(self, result: SourceSelectionResult) -> None:
        self.result = result
        self.started = threading.Event()
        self.release = threading.Event()

    def select(self, cancel_event: threading.Event) -> SourceSelectionResult:
        self.started.set()
        while not self.release.wait(0.01):
            if cancel_event.is_set():
                return SourceSelectionResult.cancelled()
        return self.result


class LateSelectedAdapter:
    """Returns a path even after cancel so generation gating must reject it."""

    def __init__(self, source: Path) -> None:
        self.source = source
        self.started = threading.Event()
        self.release = threading.Event()

    def select(self, _cancel_event: threading.Event) -> SourceSelectionResult:
        self.started.set()
        self.release.wait(2.0)
        return SourceSelectionResult.selected(self.source)


@pytest.fixture
def workspace(tmp_path):
    working = build_workspace_database(tmp_path / "work" / "workshop.sqlite", "working")
    source = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")
    scratch = tmp_path / "scratch"
    return working, source, scratch


def make_session(workspace, *, adapter=None, clock=None):
    working, _source, scratch = workspace
    service = RestoreCandidatePreparationService(working, scratch_root=scratch)
    session = RestoreControlSession(
        service,
        picker_adapter=adapter,
        clock=clock or time.monotonic,
    )
    token, _state = session.bootstrap(session.bootstrap_capability)
    return session, service, token


def request_id(number: int) -> str:
    return f"{number:032x}"


def wait_for_state(session: RestoreControlSession, state: str, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if session.current_state.state.value == state:
            return
        time.sleep(0.01)
    raise AssertionError(
        f"state did not become {state!r}; current={session.current_state.state.value!r}"
    )


def test_bootstrap_is_one_use(workspace):
    working, _source, scratch = workspace
    service = RestoreCandidatePreparationService(working, scratch_root=scratch)
    session = RestoreControlSession(service)
    capability = session.bootstrap_capability
    try:
        token, _state = session.bootstrap(capability)
        assert token
        with pytest.raises(Exception) as exc_info:
            session.bootstrap(capability)
        assert getattr(exc_info.value, "code", None) == "bootstrap_invalid"
    finally:
        session.close()


def test_picker_unavailable_is_typed_and_pathless(workspace):
    session, service, token = make_session(workspace)
    try:
        started = session.select(token, request_id=request_id(1), command_seq=1)
        assert started.code == "select_started"
        wait_for_state(session, "idle")
        retry = session.select(token, request_id=request_id(1), command_seq=1)
        assert retry.code == "picker_unavailable"
        assert retry.state.filename == ""
        assert service.retained_proof is None
    finally:
        session.close()


def test_same_sequence_same_request_is_idempotent(workspace):
    session, _service, token = make_session(workspace)
    try:
        first = session.cancel(token, request_id=request_id(1), command_seq=1)
        second = session.cancel(token, request_id=request_id(1), command_seq=1)
        assert second == first
    finally:
        session.close()


def test_same_sequence_different_request_conflicts(workspace):
    session, _service, token = make_session(workspace)
    try:
        session.cancel(token, request_id=request_id(1), command_seq=1)
        with pytest.raises(Exception) as exc_info:
            session.cancel(token, request_id=request_id(2), command_seq=1)
        assert getattr(exc_info.value, "code", None) == "command_sequence_conflict"
    finally:
        session.close()


def test_future_sequence_does_not_consume_expected_sequence(workspace):
    session, _service, token = make_session(workspace)
    try:
        with pytest.raises(Exception) as exc_info:
            session.cancel(token, request_id=request_id(2), command_seq=2)
        assert getattr(exc_info.value, "code", None) == "command_sequence_future"
        accepted = session.cancel(token, request_id=request_id(1), command_seq=1)
        assert accepted.command_seq == 1
    finally:
        session.close()


def test_action_in_progress_consumes_its_valid_sequence(workspace):
    _working, source, _scratch = workspace
    adapter = BlockingAdapter(SourceSelectionResult.selected(source))
    session, _service, token = make_session(workspace, adapter=adapter)
    try:
        session.select(token, request_id=request_id(1), command_seq=1)
        assert adapter.started.wait(1.0)

        rejected = session.select(token, request_id=request_id(2), command_seq=2)
        assert rejected.code == "action_in_progress"

        # The exact retry stays the original business rejection even if the
        # underlying action later becomes cancellable/completes.
        retry = session.select(token, request_id=request_id(2), command_seq=2)
        assert retry.code == "action_in_progress"

        cancelled = session.cancel(token, request_id=request_id(3), command_seq=3)
        assert cancelled.code == "cancelled"
    finally:
        adapter.release.set()
        session.close()


def test_heartbeat_and_state_remain_serviceable_while_worker_blocks(workspace):
    _working, source, _scratch = workspace
    adapter = BlockingAdapter(SourceSelectionResult.selected(source))
    session, _service, token = make_session(workspace, adapter=adapter)
    try:
        session.select(token, request_id=request_id(1), command_seq=1)
        assert adapter.started.wait(1.0)

        started = time.monotonic()
        assert session.heartbeat(token).state.value == "selecting"
        assert session.get_state(token).state.value == "selecting"
        elapsed = time.monotonic() - started
        assert elapsed < 0.5

        session.cancel(token, request_id=request_id(2), command_seq=2)
    finally:
        adapter.release.set()
        session.close()


def test_cancel_prevents_late_selected_path_publication(workspace):
    _working, source, _scratch = workspace
    adapter = LateSelectedAdapter(source)
    session, service, token = make_session(workspace, adapter=adapter)
    try:
        session.select(token, request_id=request_id(1), command_seq=1)
        assert adapter.started.wait(1.0)
        session.cancel(token, request_id=request_id(2), command_seq=2)
        adapter.release.set()
        wait_for_state(session, "cancelled")
        time.sleep(0.05)
        assert session.current_state.state.value == "cancelled"
        assert service.retained_proof is None
    finally:
        adapter.release.set()
        session.close()


def test_fake_launcher_picker_can_reach_real_a1_validation_without_path_in_state(workspace):
    _working, source, _scratch = workspace
    adapter = BlockingAdapter(SourceSelectionResult.selected(source))
    adapter.release.set()
    session, service, token = make_session(workspace, adapter=adapter)
    try:
        session.select(token, request_id=request_id(1), command_seq=1)
        wait_for_state(session, "accepted")
        state = session.get_state(token)
        assert state.filename == source.name
        assert str(source.parent) not in repr(state.to_dict())
        assert service.retained_proof is not None
        assert service.retained_proof.source_path == source.resolve()
    finally:
        session.close()


def test_expiry_invalidates_token_generation_and_retained_proof(workspace):
    _working, source, _scratch = workspace
    adapter = BlockingAdapter(SourceSelectionResult.selected(source))
    adapter.release.set()
    clock = FakeClock()
    session, service, token = make_session(workspace, adapter=adapter, clock=clock)
    try:
        session.select(token, request_id=request_id(1), command_seq=1)
        wait_for_state(session, "accepted")
        assert service.retained_proof is not None

        clock.advance(59)
        session.heartbeat(token)
        clock.advance(59)
        assert session.get_state(token).state.value == "accepted"
        clock.advance(61)
        assert session.expire_if_needed() is True
        assert service.retained_proof is None
        with pytest.raises(Exception) as exc_info:
            session.get_state(token)
        assert getattr(exc_info.value, "code", None) == "invalid_session"
    finally:
        session.close()
