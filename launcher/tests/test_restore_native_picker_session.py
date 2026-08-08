"""C4-II-A3 integration with the closed A2 session and A1 validation service."""

from __future__ import annotations

from pathlib import Path
import subprocess
import threading
import time

from launcher.restore.control_protocol import ControlViewState
from launcher.restore.control_session import RestoreControlSession
from launcher.restore.macos_picker import MacOSNativeSourceSelectionAdapter
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.tests.restore_fixtures import build_workspace_database


class BlockingProcess:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.terminated = False
        self.killed = False
        self.returncode = None

    def communicate(self, timeout=None):
        self.started.set()
        if self.killed:
            self.returncode = -9
            return "", ""
        if self.terminated:
            self.returncode = -15
            return "", ""
        raise subprocess.TimeoutExpired(cmd="osascript", timeout=timeout or 0)

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class CompletedProcess:
    def __init__(self, output: str) -> None:
        self.output = output
        self.returncode = 0

    def communicate(self, timeout=None):
        del timeout
        return self.output, ""

    def poll(self):
        return self.returncode

    def terminate(self):
        raise AssertionError("completed picker must not be terminated")

    def kill(self):
        raise AssertionError("completed picker must not be killed")


def _fake_osascript(tmp_path: Path) -> Path:
    path = tmp_path / "osascript"
    path.write_text("fake", encoding="utf-8")
    return path


def _wait_for_state(session: RestoreControlSession, expected: ControlViewState) -> None:
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if session.current_state.state is expected:
            return
        time.sleep(0.01)
    raise AssertionError(f"state did not reach {expected}: {session.current_state}")


def test_control_cancel_terminates_owned_native_picker_process(tmp_path: Path):
    working = build_workspace_database(tmp_path / "working.sqlite", "working")
    service = RestoreCandidatePreparationService(
        working,
        scratch_root=tmp_path / "scratch",
    )
    process = BlockingProcess()
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: process,
        platform_name="darwin",
        osascript_path=_fake_osascript(tmp_path),
        poll_seconds=0.01,
    )
    session = RestoreControlSession(service, picker_adapter=adapter)
    token, _state = session.bootstrap(session.bootstrap_capability)
    try:
        session.select(token, request_id="a" * 32, command_seq=1)
        assert process.started.wait(timeout=1.0)

        reply = session.cancel(token, request_id="b" * 32, command_seq=2)
        session.close()

        assert reply.ok is True
        assert reply.code == "cancelled"
        assert process.terminated is True
        assert service.retained_proof is None
    finally:
        session.close()


def test_session_expiry_terminates_owned_native_picker_process(tmp_path: Path):
    working = build_workspace_database(tmp_path / "working.sqlite", "working")
    service = RestoreCandidatePreparationService(
        working,
        scratch_root=tmp_path / "scratch",
    )
    process = BlockingProcess()
    now = [100.0]
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: process,
        platform_name="darwin",
        osascript_path=_fake_osascript(tmp_path),
        poll_seconds=0.01,
    )
    session = RestoreControlSession(service, picker_adapter=adapter, clock=lambda: now[0])
    token, _state = session.bootstrap(session.bootstrap_capability)
    try:
        session.select(token, request_id="c" * 32, command_seq=1)
        assert process.started.wait(timeout=1.0)

        now[0] += 61.0
        assert session.expire_if_needed() is True
        session.close()

        assert process.terminated is True
        assert service.retained_proof is None
        assert session.current_state.failure == "session_expired"
    finally:
        session.close()


def test_native_selected_path_flows_only_through_a1_candidate_preparation(tmp_path: Path):
    working = build_workspace_database(tmp_path / "working.sqlite", "working")
    candidate = build_workspace_database(tmp_path / "candidate.sqlite", "candidate")
    service = RestoreCandidatePreparationService(
        working,
        scratch_root=tmp_path / "scratch",
    )
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: CompletedProcess(f"{candidate}\n"),
        platform_name="darwin",
        osascript_path=_fake_osascript(tmp_path),
    )
    session = RestoreControlSession(service, picker_adapter=adapter)
    token, _state = session.bootstrap(session.bootstrap_capability)
    try:
        session.select(token, request_id="d" * 32, command_seq=1)
        _wait_for_state(session, ControlViewState.ACCEPTED)

        proof = service.retained_proof
        assert proof is not None
        assert proof.source_path == candidate
        assert session.current_state.filename == candidate.name
        assert str(candidate) not in session.current_state.to_dict().values()
    finally:
        session.close()
