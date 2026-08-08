"""HTTP refusals that must occur before C4-II-A2 command-sequence consumption."""

from __future__ import annotations

import http.client
import json
import secrets

from launcher.restore.control_plane import RestoreControlPlane
from launcher.tests.restore_fixtures import build_workspace_database


def _request(
    plane: RestoreControlPlane,
    path: str,
    payload: dict[str, object],
    *,
    token: str | None = None,
    host: str | None = None,
    origin: str | None = None,
):
    body = json.dumps(payload).encode("utf-8")
    connection = http.client.HTTPConnection("127.0.0.1", plane.bound_port, timeout=2.0)
    headers = {
        "Host": host or plane.expected_host,
        "Origin": origin or plane.allowed_origin,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    connection.request("POST", path, body=body, headers=headers)
    response = connection.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    status = response.status
    connection.close()
    return status, data


def test_wrong_host_origin_and_schema_do_not_consume_expected_command(tmp_path):
    database = build_workspace_database(tmp_path / "workshop.sqlite", "working")
    plane = RestoreControlPlane(
        database,
        frontend_url="http://127.0.0.1:5173",
    ).start()
    try:
        status, bootstrap = _request(
            plane,
            "/v1/bootstrap",
            {"bootstrap_token": plane.bootstrap_capability},
        )
        assert status == 200
        token = bootstrap["session_token"]
        request_id = secrets.token_hex(16)
        command = {"request_id": request_id, "command_seq": 1}

        status, rejected = _request(
            plane,
            "/v1/restore/cancel",
            command,
            token=token,
            host="localhost:9999",
        )
        assert status == 421
        assert rejected["code"] == "host_rejected"

        status, rejected = _request(
            plane,
            "/v1/restore/cancel",
            command,
            token=token,
            origin="http://127.0.0.1:5999",
        )
        assert status == 403
        assert rejected["code"] == "origin_rejected"

        status, rejected = _request(
            plane,
            "/v1/restore/cancel",
            {**command, "source_path": "/tmp/forbidden.sqlite"},
            token=token,
        )
        assert status == 400
        assert rejected["code"] == "invalid_request_schema"

        # The same expected sequence is still valid because all three failures
        # happened before session command consumption.
        status, accepted = _request(
            plane,
            "/v1/restore/cancel",
            command,
            token=token,
        )
        assert status == 200
        assert accepted["command_seq"] == 1
    finally:
        plane.close()
