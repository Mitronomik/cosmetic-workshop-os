"""C4-II-A2 loopback HTTP control-plane security and concurrency tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import secrets
import threading
import time

import pytest

from launcher.restore.control_plane import RestoreControlPlane, RestoreControlPlaneError
from launcher.restore.control_protocol import SourceSelectionResult
from launcher.tests.restore_fixtures import build_workspace_database


class BlockingAdapter:
    def __init__(self, source: Path) -> None:
        self.source = source
        self.started = threading.Event()
        self.release = threading.Event()

    def select(self, cancel_event: threading.Event) -> SourceSelectionResult:
        self.started.set()
        while not self.release.wait(0.01):
            if cancel_event.is_set():
                return SourceSelectionResult.cancelled()
        return SourceSelectionResult.selected(self.source)


@pytest.fixture
def database(tmp_path):
    return build_workspace_database(tmp_path / "work" / "workshop.sqlite", "working")


@pytest.fixture
def plane(database):
    control = RestoreControlPlane(
        database,
        frontend_url="http://127.0.0.1:5173",
    ).start()
    try:
        yield control
    finally:
        control.close()


def _request(
    plane: RestoreControlPlane,
    method: str,
    path: str,
    *,
    payload: dict[str, object] | None = None,
    token: str | None = None,
    host: str | None = None,
    origin: str | None = None,
    headers: dict[str, str] | None = None,
):
    connection = http.client.HTTPConnection("127.0.0.1", plane.bound_port, timeout=2.0)
    request_headers = {
        "Host": host if host is not None else plane.expected_host,
        "Origin": origin if origin is not None else plane.allowed_origin,
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
        request_headers["Content-Length"] = str(len(body))
    if token is not None:
        request_headers["Authorization"] = f"Bearer {token}"
    if headers:
        request_headers.update(headers)
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    raw = response.read()
    response_headers = {key.lower(): value for key, value in response.getheaders()}
    connection.close()
    data = json.loads(raw.decode("utf-8")) if raw else None
    return response.status, response_headers, data


def _bootstrap(plane: RestoreControlPlane):
    status, headers, data = _request(
        plane,
        "POST",
        "/v1/bootstrap",
        payload={"bootstrap_token": plane.bootstrap_capability},
    )
    assert status == 200
    return headers, data["session_token"]


def _retry_until_code(
    plane: RestoreControlPlane,
    token: str,
    request_id: str,
    command_seq: int,
    expected: str,
    timeout: float = 2.0,
):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        status, _headers, data = _request(
            plane,
            "POST",
            "/v1/restore/select",
            payload={"request_id": request_id, "command_seq": command_seq},
            token=token,
        )
        assert status == 200
        last = data
        if data["code"] == expected:
            return data
        time.sleep(0.01)
    raise AssertionError(f"command code did not become {expected!r}; last={last!r}")


def test_binds_exact_loopback_on_ephemeral_port_and_uses_no_store(plane):
    assert plane.bound_port > 0
    assert plane.control_origin == f"http://127.0.0.1:{plane.bound_port}"
    headers, token = _bootstrap(plane)
    assert token
    assert headers["cache-control"] == "no-store"
    assert headers["pragma"] == "no-cache"
    assert headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "access-control-allow-credentials" not in headers


def test_unsafe_frontend_origin_is_refused_before_bind(database):
    for unsafe in (
        "https://127.0.0.1:5173",
        "http://localhost:5173",
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173/path",
    ):
        with pytest.raises(RestoreControlPlaneError):
            RestoreControlPlane(database, frontend_url=unsafe)


def test_wrong_host_and_origin_do_not_consume_bootstrap(plane):
    capability = plane.bootstrap_capability
    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/bootstrap",
        payload={"bootstrap_token": capability},
        host="localhost:9999",
    )
    assert status == 421
    assert data["code"] == "host_rejected"

    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/bootstrap",
        payload={"bootstrap_token": capability},
        origin="http://127.0.0.1:5999",
    )
    assert status == 403
    assert data["code"] == "origin_rejected"

    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/bootstrap",
        payload={"bootstrap_token": capability},
    )
    assert status == 200
    assert data["session_token"]


def test_bootstrap_compare_and_consume_is_atomic_under_concurrency(plane):
    capability = plane.bootstrap_capability

    def exchange():
        return _request(
            plane,
            "POST",
            "/v1/bootstrap",
            payload={"bootstrap_token": capability},
        )[0]

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted([pool.submit(exchange).result(), pool.submit(exchange).result()])
    assert statuses == [200, 401]


def test_preflight_is_narrow_and_never_wildcard(plane):
    status, headers, _data = _request(
        plane,
        "OPTIONS",
        "/v1/restore/select",
        headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert status == 204
    assert headers["access-control-allow-origin"] == plane.allowed_origin
    assert headers["access-control-allow-methods"] == "POST"
    assert "Authorization" in headers["access-control-allow-headers"]
    assert "*" not in headers["access-control-allow-origin"]

    status, _headers, data = _request(
        plane,
        "OPTIONS",
        "/v1/restore/select",
        headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, X-Escape",
        },
    )
    assert status == 403
    assert data["code"] == "preflight_headers_rejected"


def test_malformed_path_bearing_select_does_not_consume_sequence(plane):
    _headers, token = _bootstrap(plane)
    rid = secrets.token_hex(16)
    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/restore/select",
        payload={
            "request_id": rid,
            "command_seq": 1,
            "source_path": "/tmp/forbidden.sqlite",
        },
        token=token,
    )
    assert status == 400
    assert data["code"] == "invalid_request_schema"

    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/restore/select",
        payload={"request_id": rid, "command_seq": 1},
        token=token,
    )
    assert status == 200
    assert data["code"] == "select_started"
    final = _retry_until_code(plane, token, rid, 1, "picker_unavailable")
    assert final["state"]["filename"] == ""
    assert "/tmp" not in repr(final)


def test_wrong_auth_does_not_consume_command_sequence(plane):
    _headers, token = _bootstrap(plane)
    rid = secrets.token_hex(16)
    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/restore/cancel",
        payload={"request_id": rid, "command_seq": 1},
        token="not-the-session-token",
    )
    assert status == 401
    assert data["code"] == "invalid_session"

    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/restore/cancel",
        payload={"request_id": rid, "command_seq": 1},
        token=token,
    )
    assert status == 200
    assert data["command_seq"] == 1


def test_query_cookie_and_wrong_method_are_refused(plane):
    _headers, token = _bootstrap(plane)
    status, _headers, data = _request(
        plane,
        "GET",
        "/v1/state?source_path=/tmp/x",
        token=token,
    )
    assert status == 404
    assert data["code"] == "not_found"

    status, _headers, data = _request(
        plane,
        "GET",
        "/v1/state",
        token=token,
        headers={"Cookie": "session=ambient"},
    )
    assert status == 400
    assert data["code"] == "cookies_not_allowed"

    status, _headers, data = _request(
        plane,
        "POST",
        "/v1/state",
        payload={},
        token=token,
    )
    assert status == 405
    assert data["code"] == "method_not_allowed"


def test_http_heartbeat_state_and_cancel_remain_responsive_while_worker_blocks(
    tmp_path, database
):
    source = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")
    adapter = BlockingAdapter(source)
    plane = RestoreControlPlane(
        database,
        frontend_url="http://127.0.0.1:5173",
        picker_adapter=adapter,
    ).start()
    try:
        _headers, token = _bootstrap(plane)
        rid1 = secrets.token_hex(16)
        status, _headers, data = _request(
            plane,
            "POST",
            "/v1/restore/select",
            payload={"request_id": rid1, "command_seq": 1},
            token=token,
        )
        assert status == 200
        assert data["code"] == "select_started"
        assert adapter.started.wait(1.0)

        started = time.monotonic()
        status, _headers, heartbeat = _request(
            plane,
            "POST",
            "/v1/heartbeat",
            payload={},
            token=token,
        )
        assert status == 200
        status, _headers, state = _request(plane, "GET", "/v1/state", token=token)
        assert status == 200
        assert heartbeat["state"]["state"] == "selecting"
        assert state["state"]["state"] == "selecting"
        assert time.monotonic() - started < 0.75

        status, _headers, cancelled = _request(
            plane,
            "POST",
            "/v1/restore/cancel",
            payload={"request_id": secrets.token_hex(16), "command_seq": 2},
            token=token,
        )
        assert status == 200
        assert cancelled["code"] == "cancelled"
    finally:
        adapter.release.set()
        plane.close()
