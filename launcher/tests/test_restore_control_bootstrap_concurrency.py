"""Real concurrent bootstrap race for C4-II-A2."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import threading

from launcher.restore.control_plane import RestoreControlPlane
from launcher.tests.restore_fixtures import build_workspace_database


def test_exact_same_bootstrap_capability_has_one_concurrent_winner(tmp_path):
    database = build_workspace_database(tmp_path / "workshop.sqlite", "working")
    plane = RestoreControlPlane(
        database,
        frontend_url="http://127.0.0.1:5173",
    ).start()
    gate = threading.Barrier(2)
    capability = plane.bootstrap_capability

    def exchange() -> int:
        body = json.dumps({"bootstrap_token": capability}).encode("utf-8")
        gate.wait(timeout=2.0)
        connection = http.client.HTTPConnection(
            "127.0.0.1", plane.bound_port, timeout=2.0
        )
        connection.request(
            "POST",
            "/v1/bootstrap",
            body=body,
            headers={
                "Host": plane.expected_host,
                "Origin": plane.allowed_origin,
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
        )
        response = connection.getresponse()
        status = response.status
        response.read()
        connection.close()
        return status

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(exchange)
            second = pool.submit(exchange)
            statuses = sorted([first.result(timeout=3.0), second.result(timeout=3.0)])
        assert statuses == [200, 401]
    finally:
        plane.close()
