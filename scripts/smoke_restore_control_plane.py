#!/usr/bin/env python3
"""Exact-head direct-local-HTTP smoke for C4-II-A2.

No browser handoff and no native picker are used.  A launcher-owned injected fake
adapter selects a temporary prepared backup, then the real loopback HTTP control
plane drives the real A1 candidate-preparation service and C4-I validation path.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _assert_exact_head(expected: str) -> None:
    actual = _git("rev-parse", "HEAD")
    if actual != expected:
        raise RuntimeError(f"exact-head mismatch: expected {expected}, got {actual}")


def _assert_clean_workspace() -> None:
    if _git("status", "--porcelain"):
        raise RuntimeError("git workspace is not clean")


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _build_workspace(path: Path, marker: str) -> Path:
    from app.db.config import DatabaseConfig
    from app.db.migrations import apply_migrations

    path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(DatabaseConfig(path=path))
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type, description) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("smoke.restore_control_marker", marker, "string", "A2 smoke marker"),
        )
    return path


def _audit_count(path: Path) -> int:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])


class _FakePicker:
    def __init__(self, source: Path) -> None:
        self.source = source

    def select(self, cancel_event: threading.Event):
        from launcher.restore.control_protocol import SourceSelectionResult

        if cancel_event.is_set():
            return SourceSelectionResult.cancelled()
        return SourceSelectionResult.selected(self.source)


def _request(plane, method: str, path: str, *, payload=None, token=None):
    connection = http.client.HTTPConnection("127.0.0.1", plane.bound_port, timeout=3.0)
    headers = {
        "Host": plane.expected_host,
        "Origin": plane.allowed_origin,
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    response_headers = {key.lower(): value for key, value in response.getheaders()}
    connection.close()
    data = json.loads(raw.decode("utf-8")) if raw else None
    return response.status, response_headers, data


def run(expected_head: str) -> None:
    _assert_exact_head(expected_head)
    _assert_clean_workspace()

    from launcher.config import resolve_runtime_paths
    from launcher.runtime import ensure_backend_import_path

    ensure_backend_import_path(resolve_runtime_paths())

    from launcher.restore.control_plane import RestoreControlPlane
    from launcher.restore.workspace import resolve_restore_dir

    with tempfile.TemporaryDirectory(prefix="cwos-a2-smoke-") as temporary:
        root = Path(temporary)
        working = _build_workspace(root / "work" / "workshop.sqlite", "working")
        source = _build_workspace(root / "chosen" / "backup.sqlite", "source")
        working_before = _sha256(working)
        source_before = _sha256(source)
        audit_before = _audit_count(working)
        durable_restore_dir = resolve_restore_dir(working)
        assert not durable_restore_dir.exists()

        plane = RestoreControlPlane(
            working,
            frontend_url="http://127.0.0.1:5173",
            picker_adapter=_FakePicker(source),
        )
        run_dir = plane._candidate_service._scratch.run_dir
        try:
            plane.start()
            assert plane.control_origin.startswith("http://127.0.0.1:")
            assert plane.control_origin != "http://127.0.0.1:0"

            status, headers, bootstrap = _request(
                plane,
                "POST",
                "/v1/bootstrap",
                payload={"bootstrap_token": plane.bootstrap_capability},
            )
            assert status == 200
            assert headers.get("cache-control") == "no-store"
            assert headers.get("access-control-allow-origin") == plane.allowed_origin
            token = bootstrap["session_token"]
            assert token

            request_id = secrets.token_hex(16)
            status, _headers, started = _request(
                plane,
                "POST",
                "/v1/restore/select",
                payload={"request_id": request_id, "command_seq": 1},
                token=token,
            )
            assert status == 200
            assert started["code"] in {"select_started", "validation_started", "candidate_accepted"}

            deadline = time.monotonic() + 5.0
            accepted = None
            while time.monotonic() < deadline:
                status, _headers, state = _request(plane, "GET", "/v1/state", token=token)
                assert status == 200
                if state["state"]["state"] == "accepted":
                    accepted = state
                    break
                time.sleep(0.02)
            assert accepted is not None
            serialized = json.dumps(accepted, ensure_ascii=False)
            assert str(source) not in serialized
            assert str(source.parent) not in serialized
            assert accepted["state"]["filename"] == source.name
            assert plane._candidate_service.retained_proof is not None
            assert plane._candidate_service.retained_proof.source_path == source.resolve()

            status, _headers, cancelled = _request(
                plane,
                "POST",
                "/v1/restore/cancel",
                payload={"request_id": secrets.token_hex(16), "command_seq": 2},
                token=token,
            )
            assert status == 200
            assert cancelled["code"] == "cancelled"
            assert plane._candidate_service.retained_proof is None

            assert _sha256(source) == source_before
            assert _sha256(working) == working_before
            assert _audit_count(working) == audit_before
            assert not durable_restore_dir.exists()
        finally:
            plane.close()

        assert not run_dir.exists()
        assert _sha256(source) == source_before
        assert _sha256(working) == working_before
        assert _audit_count(working) == audit_before
        assert not durable_restore_dir.exists()

    _assert_exact_head(expected_head)
    _assert_clean_workspace()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    try:
        run(args.expected_head)
    except (FileNotFoundError, PermissionError, subprocess.CalledProcessError) as exc:
        print(f"INCONCLUSIVE — ENVIRONMENT: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"INCONCLUSIVE — ENVIRONMENT: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - smoke must always emit a verdict
        print(f"FAIL — PRODUCT: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("PASS — C4-II-A2 RESTORE CONTROL-PLANE SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
