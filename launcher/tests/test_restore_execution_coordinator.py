"""Focused C4-II-B2 launcher Restore execution coordinator tests."""

from __future__ import annotations

import http.client
import inspect
import json
from pathlib import Path
import time

import pytest

from launcher import runtime
from launcher.restore.contracts import (
    ProofBoundRestoreRequest,
    RestoreFailure,
    RestoreOutcome,
    RestoreResult,
)
from launcher.restore.control_plane import RestoreControlPlane
from launcher.restore.control_protocol import ControlViewState, SourceSelectionResult
from launcher.restore.execution_coordinator import execute_restore_intent
from launcher.restore.verification import RetryableBackendStartError
from launcher.tests.restore_fixtures import build_workspace_database


class ImmediateAdapter:
    def __init__(self, source: Path) -> None:
        self.source = source

    def select(self, _cancel_event):
        return SourceSelectionResult.selected(self.source)


class FakeClock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeLease:
    def __init__(self, held: bool = True) -> None:
        self.held = held


class FakeProcess:
    def __init__(self, return_code=None) -> None:
        self.return_code = return_code

    def poll(self):
        return self.return_code


class FakeBackend:
    def __init__(self, *, fail_start: bool = False, return_code=None) -> None:
        self.fail_start = fail_start
        self.process = FakeProcess(return_code)
        self.starts: list[tuple[object, object, Path]] = []

    def start(self, config, paths, database_path: Path):
        self.starts.append((config, paths, Path(database_path)))
        if self.fail_start:
            raise RuntimeError("synthetic restart failure")
        return self.process


class FakeContext:
    def __init__(self, database_path: Path, *, fail_start: bool = False) -> None:
        self.database_path = Path(database_path)
        self.maintenance_lease = FakeLease(True)
        self.backend = FakeBackend(fail_start=fail_start)
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire_maintenance_lease(self) -> None:
        self.acquire_calls += 1
        self.maintenance_lease.held = True

    def release_maintenance_lease(self) -> None:
        self.release_calls += 1
        self.maintenance_lease.held = False


@pytest.fixture
def workspace(tmp_path):
    working = build_workspace_database(tmp_path / "work" / "workshop.sqlite", "working")
    source = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")
    return working, source


def request_id(number: int) -> str:
    return f"{number:032x}"


def _request(
    plane: RestoreControlPlane,
    method: str,
    path: str,
    *,
    payload: dict[str, object] | None = None,
    token: str | None = None,
    host: str | None = None,
    origin: str | None = None,
):
    connection = http.client.HTTPConnection("127.0.0.1", plane.bound_port, timeout=2.0)
    headers = {
        "Host": host if host is not None else plane.expected_host,
        "Origin": origin if origin is not None else plane.allowed_origin,
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    connection.close()
    return response.status, json.loads(raw.decode("utf-8")) if raw else None


def _bootstrap(plane: RestoreControlPlane) -> str:
    status, data = _request(
        plane,
        "POST",
        "/v1/bootstrap",
        payload={"bootstrap_token": plane.bootstrap_capability},
    )
    assert status == 200
    return data["session_token"]


def _wait_for_state(plane: RestoreControlPlane, state: str, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if plane.session.current_state.state.value == state:
            worker = getattr(plane.session, "_worker", None)
            if worker is None or not worker.is_alive():
                return
        time.sleep(0.01)
    raise AssertionError(
        f"state did not settle at {state!r}; current={plane.session.current_state.state.value!r}"
    )


def _accepted_plane(workspace, *, clock=None):
    working, source = workspace
    plane = RestoreControlPlane(
        working,
        frontend_url="http://127.0.0.1:5173",
        picker_adapter=ImmediateAdapter(source),
        clock=clock,
    ).start()
    token = _bootstrap(plane)
    status, data = _request(
        plane,
        "POST",
        "/v1/restore/select",
        payload={"request_id": request_id(1), "command_seq": 1},
        token=token,
    )
    assert status == 200
    assert data["code"] == "select_started"
    _wait_for_state(plane, "accepted")
    return plane, token, source


@pytest.mark.parametrize(
    "payload",
    [
        {"request_id": request_id(1), "command_seq": 1},
        {"request_id": request_id(1), "command_seq": 1, "generation": 1, "source_path": "/tmp/x"},
        {"request_id": request_id(1), "command_seq": 1, "generation": 1, "proof": "x"},
        {"request_id": request_id(1), "command_seq": 1, "generation": 1, "sha256": "x"},
        {"request_id": request_id(1), "command_seq": 1, "generation": True},
        {"request_id": request_id(1), "command_seq": 1, "generation": 0},
    ],
)
def test_execute_http_schema_is_exact_and_bad_schema_does_not_consume_sequence(
    workspace, payload
):
    working, _source = workspace
    plane = RestoreControlPlane(
        working,
        frontend_url="http://127.0.0.1:5173",
    ).start()
    try:
        token = _bootstrap(plane)
        status, _data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload=payload,
            token=token,
        )
        assert status == 400

        status, data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload={"request_id": request_id(2), "command_seq": 1, "generation": 1},
            token=token,
        )
        assert status == 200
        assert data["code"] == "candidate_not_accepted"
    finally:
        plane.close()


def test_execute_wrong_host_origin_and_auth_do_not_consume_sequence(workspace):
    working, _source = workspace
    plane = RestoreControlPlane(
        working,
        frontend_url="http://127.0.0.1:5173",
    ).start()
    try:
        token = _bootstrap(plane)
        payload = {"request_id": request_id(1), "command_seq": 1, "generation": 1}
        status, _data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload=payload,
            token=token,
            host="localhost:9999",
        )
        assert status == 421
        status, _data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload=payload,
            token=token,
            origin="http://127.0.0.1:5999",
        )
        assert status == 403
        status, _data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload=payload,
            token="wrong",
        )
        assert status == 401

        status, data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload=payload,
            token=token,
        )
        assert status == 200
        assert data["code"] == "candidate_not_accepted"
    finally:
        plane.close()


def test_acceptance_transfers_current_private_proof_once_without_conflating_generations(
    workspace,
):
    plane, token, source = _accepted_plane(workspace)
    try:
        retained = plane._candidate_service.retained_proof
        assert retained is not None
        control_generation = plane.session.current_state.generation
        assert retained.generation != control_generation

        status, data = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload={
                "request_id": request_id(2),
                "command_seq": 2,
                "generation": control_generation,
            },
            token=token,
        )
        assert status == 200
        assert data["code"] == "restore_accepted"
        assert data["state"]["state"] == "restoring"
        assert str(source.parent) not in repr(data)
        assert retained.sha256 not in repr(data)
        assert plane._candidate_service.retained_proof is None

        retry_status, retry = _request(
            plane,
            "POST",
            "/v1/restore/execute",
            payload={
                "request_id": request_id(2),
                "command_seq": 2,
                "generation": control_generation,
            },
            token=token,
        )
        assert retry_status == 200
        assert retry == data

        intent = plane.session.take_execution_intent()
        assert intent is not None
        assert intent.selected_source == source.resolve()
        assert intent.expected_source_proof.source_identity == retained.source_identity
        assert intent.expected_source_proof.sha256 == retained.sha256
        assert plane.session.take_execution_intent() is None
    finally:
        plane.close()


def test_stale_generation_and_missing_authority_consume_sequence_without_queueing(workspace):
    plane, token, _source = _accepted_plane(workspace)
    try:
        current = plane.session.current_state.generation
        stale = plane.session.execute(
            token,
            request_id=request_id(2),
            command_seq=2,
            generation=current + 1,
        )
        assert stale.code == "selection_generation_stale"
        assert plane.session.take_execution_intent() is None

        plane._candidate_service.invalidate()
        missing = plane.session.execute(
            token,
            request_id=request_id(3),
            command_seq=3,
            generation=current,
        )
        assert missing.code == "restore_authority_missing"
        assert plane.session.take_execution_intent() is None
    finally:
        plane.close()


def test_restoring_consumes_mutating_sequences_without_cancel_or_duplicate(workspace):
    plane, token, _source = _accepted_plane(workspace)
    try:
        generation = plane.session.current_state.generation
        accepted = plane.session.execute(
            token,
            request_id=request_id(2),
            command_seq=2,
            generation=generation,
        )
        assert accepted.code == "restore_accepted"

        assert plane.session.heartbeat(token).state is ControlViewState.RESTORING
        assert plane.session.get_state(token).state is ControlViewState.RESTORING

        select = plane.session.select(token, request_id=request_id(3), command_seq=3)
        cancel = plane.session.cancel(token, request_id=request_id(4), command_seq=4)
        second = plane.session.execute(
            token,
            request_id=request_id(5),
            command_seq=5,
            generation=generation,
        )
        assert select.code == "restore_in_progress"
        assert cancel.code == "restore_in_progress"
        assert second.code == "restore_in_progress"
        assert plane.session.current_state.state is ControlViewState.RESTORING

        assert plane.session.take_execution_intent() is not None
        assert plane.session.take_execution_intent() is None
    finally:
        plane.close()


def test_session_expiry_during_restoring_does_not_cancel_or_overwrite_result(workspace):
    clock = FakeClock()
    plane, token, _source = _accepted_plane(workspace, clock=clock)
    try:
        generation = plane.session.current_state.generation
        plane.session.execute(
            token,
            request_id=request_id(2),
            command_seq=2,
            generation=generation,
        )
        intent = plane.session.take_execution_intent()
        assert intent is not None

        clock.advance(61)
        # Either this call or the already-running expiry monitor may win the
        # expiry race. The product invariant is the resulting state/auth, not
        # which thread happened to perform the invalidation first.
        plane.session.expire_if_needed()
        assert plane.session.current_state.state is ControlViewState.RESTORING
        assert plane._candidate_service.retained_proof is None

        with pytest.raises(Exception) as exc_info:
            plane.session.get_state(token)
        assert getattr(exc_info.value, "code", None) == "invalid_session"

        published = plane.session.publish_execution_result(
            intent,
            state=ControlViewState.RESTORE_COMPLETED,
            message="done",
            failure=None,
        )
        assert published is True
        assert plane.session.current_state.state is ControlViewState.RESTORE_COMPLETED
        assert plane.session.expire_if_needed() is False
        assert plane.session.current_state.state is ControlViewState.RESTORE_COMPLETED
    finally:
        plane.close()


def _make_intent(workspace):
    plane, token, _source = _accepted_plane(workspace)
    generation = plane.session.current_state.generation
    plane.session.execute(
        token,
        request_id=request_id(2),
        command_seq=2,
        generation=generation,
    )
    intent = plane.session.take_execution_intent()
    assert intent is not None
    return plane, intent


def _restore_result(*, outcome, normal_startup_allowed, failure=None, message="result"):
    return RestoreResult(
        outcome=outcome,
        durable_phase=None,
        operation_id="op-test",
        message=message,
        normal_startup_allowed=normal_startup_allowed,
        failure=failure,
    )


def test_synchronous_coordinator_builds_proof_bound_request_and_restarts_canonical_backend(
    workspace,
):
    working, _source = workspace
    plane, intent = _make_intent(workspace)
    context = FakeContext(working)
    captured = []

    def fake_execute(request, passed_context):
        captured.append((request, passed_context))
        context.maintenance_lease.held = True
        return _restore_result(
            outcome=RestoreOutcome.COMPLETED,
            normal_startup_allowed=True,
            message="completed",
        )

    try:
        process = execute_restore_intent(
            intent,
            context,
            object(),
            object(),
            plane.session.publish_execution_result,
            execute_restore_fn=fake_execute,
        )
        assert process is context.backend.process
        assert len(captured) == 1
        request, passed_context = captured[0]
        assert isinstance(request, ProofBoundRestoreRequest)
        assert request.selected_source == intent.selected_source
        assert request.expected_source_proof == intent.expected_source_proof
        assert passed_context is context
        assert len(context.backend.starts) == 1
        assert context.backend.starts[0][2] == context.database_path
        assert plane.session.current_state.state is ControlViewState.RESTORE_COMPLETED
    finally:
        plane.close()


def test_safe_unsuccessful_restore_restarts_and_publishes_failed(workspace):
    working, _source = workspace
    plane, intent = _make_intent(workspace)
    context = FakeContext(working)

    def fake_execute(_request, _context):
        context.maintenance_lease.held = True
        return _restore_result(
            outcome=RestoreOutcome.ABORTED,
            normal_startup_allowed=True,
            failure=RestoreFailure.SOURCE_CHANGED,
            message="failed safely",
        )

    try:
        process = execute_restore_intent(
            intent,
            context,
            object(),
            object(),
            plane.session.publish_execution_result,
            execute_restore_fn=fake_execute,
        )
        assert process is context.backend.process
        assert len(context.backend.starts) == 1
        assert plane.session.current_state.state is ControlViewState.RESTORE_FAILED
        assert plane.session.current_state.failure == RestoreFailure.SOURCE_CHANGED.value
    finally:
        plane.close()


def test_unsafe_result_starts_no_backend_and_publishes_blocked(workspace):
    working, _source = workspace
    plane, intent = _make_intent(workspace)
    context = FakeContext(working)

    def fake_execute(_request, _context):
        context.maintenance_lease.held = True
        return _restore_result(
            outcome=RestoreOutcome.RECOVERY_BLOCKED,
            normal_startup_allowed=False,
            failure=RestoreFailure.RECOVERY_BLOCKED,
            message="blocked",
        )

    try:
        process = execute_restore_intent(
            intent,
            context,
            object(),
            object(),
            plane.session.publish_execution_result,
            execute_restore_fn=fake_execute,
        )
        assert process is None
        assert context.backend.starts == []
        assert context.maintenance_lease.held is True
        assert plane.session.current_state.state is ControlViewState.RESTORE_BLOCKED
    finally:
        plane.close()


def test_restart_failure_preserves_result_truth_and_reacquires_exclusion(workspace):
    working, _source = workspace
    plane, intent = _make_intent(workspace)
    context = FakeContext(working, fail_start=True)

    def fake_execute(_request, _context):
        context.maintenance_lease.held = True
        return _restore_result(
            outcome=RestoreOutcome.COMPLETED,
            normal_startup_allowed=True,
            message="completed",
        )

    try:
        process = execute_restore_intent(
            intent,
            context,
            object(),
            object(),
            plane.session.publish_execution_result,
            execute_restore_fn=fake_execute,
        )
        assert process is None
        assert len(context.backend.starts) == 1
        assert context.acquire_calls == 1
        assert context.maintenance_lease.held is True
        assert plane.session.current_state.state is ControlViewState.RESTORE_BLOCKED
        assert plane.session.current_state.failure == "backend_restart_failed"
    finally:
        plane.close()


def test_retryable_verification_port_condition_starts_no_backend(workspace):
    working, _source = workspace
    plane, intent = _make_intent(workspace)
    context = FakeContext(working)

    def fake_execute(_request, _context):
        context.maintenance_lease.held = True
        raise RetryableBackendStartError("busy")

    try:
        process = execute_restore_intent(
            intent,
            context,
            object(),
            object(),
            plane.session.publish_execution_result,
            execute_restore_fn=fake_execute,
        )
        assert process is None
        assert context.backend.starts == []
        assert context.maintenance_lease.held is True
        assert plane.session.current_state.state is ControlViewState.RESTORE_BLOCKED
        assert (
            plane.session.current_state.failure
            == RestoreFailure.BACKEND_PORT_UNAVAILABLE.value
        )
    finally:
        plane.close()


def test_http_and_session_layers_do_not_call_c4_i():
    from launcher.restore import control_plane, control_session

    assert "execute_restore(" not in inspect.getsource(control_plane)
    assert "execute_restore(" not in inspect.getsource(control_session)


def test_main_owner_loop_consumes_intent_before_observing_intentional_old_exit(monkeypatch):
    sentinel_intent = object()
    calls = []

    class Session:
        def __init__(self):
            self.intent = sentinel_intent

        def take_execution_intent(self):
            intent, self.intent = self.intent, None
            return intent

        def take_execution_intent_or_seal_runtime_exit(self):
            intent, self.intent = self.intent, None
            return intent

        def publish_execution_result(self, *_args, **_kwargs):
            return True

    class Plane:
        session = Session()

    old_process = FakeProcess(0)
    new_process = FakeProcess(7)

    def fake_execute(intent, context, config, paths, publish):
        calls.append((intent, context, config, paths, publish))
        return new_process

    import launcher.restore.execution_coordinator as coordinator

    monkeypatch.setattr(coordinator, "execute_restore_intent", fake_execute)
    result = runtime._run_launcher_owner_loop(
        object(),
        object(),
        object(),
        old_process,
        Plane(),
    )
    assert result == 7
    assert len(calls) == 1
    assert calls[0][0] is sentinel_intent
