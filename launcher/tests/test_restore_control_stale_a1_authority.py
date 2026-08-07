"""Race proofs for stale control workers crossing the A2 -> A1 begin boundary."""

from __future__ import annotations

from pathlib import Path
import threading
import time

import pytest

from launcher.restore.control_protocol import SourceSelectionResult
from launcher.restore.control_session import RestoreControlSession
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.tests.restore_fixtures import build_workspace_database


class ImmediateSelectedAdapter:
    def __init__(self, source: Path) -> None:
        self.source = source

    def select(self, _cancel_event: threading.Event) -> SourceSelectionResult:
        return SourceSelectionResult.selected(self.source)


class FakeClock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


@pytest.fixture
def workspace(tmp_path):
    working = build_workspace_database(tmp_path / "work" / "workshop.sqlite", "working")
    source = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")
    return working, source, tmp_path / "scratch"


def _request_id(number: int) -> str:
    return f"{number:032x}"


def _wait_worker_done(session: RestoreControlSession, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with session._lock:  # test-only proof of launcher-owned worker quiescence
            worker = session._worker
        if worker is None:
            return
        time.sleep(0.01)
    raise AssertionError("restore control worker did not quiesce")


def _pause_exactly_before_a1_begin(service: RestoreCandidatePreparationService):
    original = service.prepare_restore_candidate
    entered = threading.Event()
    release = threading.Event()
    returned = threading.Event()

    def paused(selected_source: object):
        entered.set()
        if not release.wait(2.0):
            raise AssertionError("test did not release A1 begin boundary")
        result = original(selected_source)
        returned.set()
        return result

    service.prepare_restore_candidate = paused  # type: ignore[method-assign]
    return entered, release, returned


def test_cancel_before_a1_begin_cannot_leave_resurrected_retained_proof(workspace):
    working, source, scratch = workspace
    service = RestoreCandidatePreparationService(working, scratch_root=scratch)
    session = RestoreControlSession(service, picker_adapter=ImmediateSelectedAdapter(source))
    token, _state = session.bootstrap(session.bootstrap_capability)
    entered, release, returned = _pause_exactly_before_a1_begin(service)

    try:
        session.select(token, request_id=_request_id(1), command_seq=1)
        assert entered.wait(1.0), "worker must pass control generation check before cancel"

        cancelled = session.cancel(token, request_id=_request_id(2), command_seq=2)
        assert cancelled.code == "cancelled"
        assert service.retained_proof is None

        # The stale worker now enters A1 only after cancel. A1 is allowed to create
        # its own newer internal generation, so the A2 coordinator must clear any
        # retained proof it creates before the stale worker is considered quiescent.
        release.set()
        assert returned.wait(2.0)
        _wait_worker_done(session)

        assert session.current_state.state.value == "cancelled"
        assert service.retained_proof is None
    finally:
        release.set()
        session.close()


def test_expiry_before_a1_begin_cannot_leave_resurrected_retained_proof(workspace):
    working, source, scratch = workspace
    clock = FakeClock()
    service = RestoreCandidatePreparationService(working, scratch_root=scratch)
    session = RestoreControlSession(
        service,
        picker_adapter=ImmediateSelectedAdapter(source),
        clock=clock,
    )
    token, _state = session.bootstrap(session.bootstrap_capability)
    entered, release, returned = _pause_exactly_before_a1_begin(service)

    try:
        session.select(token, request_id=_request_id(1), command_seq=1)
        assert entered.wait(1.0), "worker must pass control generation check before expiry"

        clock.advance(61)
        assert session.expire_if_needed() is True
        assert service.retained_proof is None

        release.set()
        assert returned.wait(2.0)
        _wait_worker_done(session)

        assert session.current_state.failure == "session_expired"
        assert service.retained_proof is None
        with pytest.raises(Exception) as exc_info:
            session.get_state(token)
        assert getattr(exc_info.value, "code", None) == "invalid_session"
    finally:
        release.set()
        session.close()
