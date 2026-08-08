#!/usr/bin/env python3
"""Exact-head macOS native-picker smoke for C4-II-A3.

The smoke proves the exact system osascript helper is executable without opening a
modal picker, then drives the real A3 adapter through the real A2 control plane and
A1/C4-I validation path using a launcher-owned process-factory seam. No browser
path authority and no destructive Restore action are used.
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
            ("smoke.restore_native_picker_marker", marker, "string", "A3 smoke marker"),
        )
    return path


def _audit_count(path: Path) -> int:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])


class _CompletedPickerProcess:
    def __init__(self, selected: Path) -> None:
        self.selected = selected
        self.returncode = 0

    def communicate(self, timeout=None):
        del timeout
        return f"{self.selected}\n", ""

    def poll(self):
        return self.returncode

    def terminate(self):
        raise AssertionError("completed picker must not be terminated")

    def kill(self):
        raise AssertionError("completed picker must not be killed")


def _request(plane, method: str, path: str, *, payload=None, token=None):
    connection = http.client.HTTPConnection("127.0.0.1", plane.bound_port, timeout=3.0)
    headers = {"Host": plane.expected_host, "Origin": plane.allowed_origin}
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


def _probe_exact_osascript() -> None:
    from launcher.restore.macos_picker import OSASCRIPT_PATH

    if sys.platform != "darwin":
        raise RuntimeError("A3 native-picker smoke requires macOS")
    if OSASCRIPT_PATH != Path("/usr/bin/osascript") or not OSASCRIPT_PATH.is_file():
        raise RuntimeError("exact /usr/bin/osascript helper is unavailable")
    probe = subprocess.run(
        [str(OSASCRIPT_PATH), "-e", 'return "__CWOS_A3_OSASCRIPT_PROBE__"'],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        shell=False,
        check=True,
    )
    if probe.stdout.strip() != "__CWOS_A3_OSASCRIPT_PROBE__":
        raise RuntimeError("osascript probe returned an unexpected result")


def run(expected_head: str) -> None:
    _assert_exact_head(expected_head)
    _assert_clean_workspace()
    _probe_exact_osascript()

    from launcher.config import resolve_runtime_paths
    from launcher.runtime import ensure_backend_import_path

    ensure_backend_import_path(resolve_runtime_paths())

    from launcher.restore.control_plane import RestoreControlPlane
    from launcher.restore.macos_picker import (
        MacOSNativeSourceSelectionAdapter,
        OSASCRIPT_PATH,
        PICKER_APPLESCRIPT,
    )
    from launcher.restore.workspace import resolve_restore_dir

    with tempfile.TemporaryDirectory(prefix="cwos-a3-smoke-") as temporary:
        root = Path(temporary)
        working = _build_workspace(root / "work" / "workshop.sqlite", "working")
        source = _build_workspace(root / "chosen" / "backup.sqlite", "source")
        working_before = _sha256(working)
        source_before = _sha256(source)
        audit_before = _audit_count(working)
        durable_restore_dir = resolve_restore_dir(working)
        assert not durable_restore_dir.exists()
        captured = {}

        def process_factory(argv, **kwargs):
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            return _CompletedPickerProcess(source)

        adapter = MacOSNativeSourceSelectionAdapter(process_factory=process_factory)
        plane = RestoreControlPlane(
            working,
            frontend_url="http://127.0.0.1:5173",
            picker_adapter=adapter,
        )
        run_dir = plane._candidate_service._scratch.run_dir
        try:
            plane.start()
            status, headers, bootstrap = _request(
                plane,
                "POST",
                "/v1/bootstrap",
                payload={"bootstrap_token": plane.bootstrap_capability},
            )
            assert status == 200
            assert headers.get("cache-control") == "no-store"
            token = bootstrap["session_token"]

            status, _headers, started = _request(
                plane,
                "POST",
                "/v1/restore/select",
                payload={"request_id": secrets.token_hex(16), "command_seq": 1},
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
            assert accepted["state"]["filename"] == source.name
            serialized = json.dumps(accepted, ensure_ascii=False)
            assert str(source) not in serialized
            assert str(source.parent) not in serialized
            proof = plane._candidate_service.retained_proof
            assert proof is not None
            assert proof.source_path == source.resolve()

            assert captured["argv"] == [str(OSASCRIPT_PATH), "-e", PICKER_APPLESCRIPT]
            assert captured["kwargs"]["shell"] is False
            assert "System Events" not in PICKER_APPLESCRIPT

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

    print("PASS — C4-II-A3 NATIVE MACOS PICKER SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
