"""Exact single Host/Origin authority for the A2 loopback boundary."""

from __future__ import annotations

import http.client
import json

from launcher.restore.control_plane import RestoreControlPlane
from launcher.tests.restore_fixtures import build_workspace_database


def _raw_bootstrap(
    plane: RestoreControlPlane,
    capability: str,
    *,
    hosts: list[str],
    origins: list[str],
):
    body = json.dumps({"bootstrap_token": capability}).encode("utf-8")
    connection = http.client.HTTPConnection("127.0.0.1", plane.bound_port, timeout=2.0)
    connection.putrequest("POST", "/v1/bootstrap", skip_host=True, skip_accept_encoding=True)
    for value in hosts:
        connection.putheader("Host", value)
    for value in origins:
        connection.putheader("Origin", value)
    connection.putheader("Content-Type", "application/json")
    connection.putheader("Content-Length", str(len(body)))
    connection.endheaders(body)
    response = connection.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    status = response.status
    connection.close()
    return status, data


def test_missing_or_duplicate_host_origin_fail_before_bootstrap_consumption(tmp_path):
    database = build_workspace_database(tmp_path / "workshop.sqlite", "working")
    plane = RestoreControlPlane(
        database,
        frontend_url="http://127.0.0.1:5173",
    ).start()
    capability = plane.bootstrap_capability
    try:
        status, data = _raw_bootstrap(
            plane,
            capability,
            hosts=[],
            origins=[plane.allowed_origin],
        )
        assert status == 421
        assert data["code"] == "host_rejected"

        status, data = _raw_bootstrap(
            plane,
            capability,
            hosts=[plane.expected_host, plane.expected_host],
            origins=[plane.allowed_origin],
        )
        assert status == 421
        assert data["code"] == "host_rejected"

        status, data = _raw_bootstrap(
            plane,
            capability,
            hosts=[plane.expected_host],
            origins=[],
        )
        assert status == 403
        assert data["code"] == "origin_rejected"

        status, data = _raw_bootstrap(
            plane,
            capability,
            hosts=[plane.expected_host],
            origins=[plane.allowed_origin, plane.allowed_origin],
        )
        assert status == 403
        assert data["code"] == "origin_rejected"

        # All authority-header refusals happened before one-use capability consume.
        status, data = _raw_bootstrap(
            plane,
            capability,
            hosts=[plane.expected_host],
            origins=[plane.allowed_origin],
        )
        assert status == 200
        assert data["session_token"]
    finally:
        plane.close()
