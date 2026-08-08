#!/usr/bin/env python3
"""Exact-head non-destructive browser-session smoke for C4-II-A4."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

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
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
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
            ("smoke.restore_browser_session_marker", marker, "string", "A4 smoke marker"),
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


def _run_frontend_checks() -> None:
    frontend = ROOT / "frontend"
    subprocess.run(["npm", "run", "build"], cwd=frontend, check=True)
    subprocess.run(["npm", "run", "test:restore-control"], cwd=frontend, check=True)


def run(expected_head: str) -> None:
    _assert_exact_head(expected_head)
    _assert_clean_workspace()
    _run_frontend_checks()

    from launcher.config import build_runtime_config, resolve_runtime_paths
    from launcher.runtime import ensure_backend_import_path

    ensure_backend_import_path(resolve_runtime_paths())

    from launcher.restore.browser_handoff import runtime_config_with_restore_handoff
    from launcher.restore.control_plane import RestoreControlPlane
    from launcher.restore.macos_picker import MacOSNativeSourceSelectionAdapter, PICKER_APPLESCRIPT
    from launcher.restore.workspace import resolve_restore_dir

    with tempfile.TemporaryDirectory(prefix="cwos-a4-smoke-") as temporary:
        root = Path(temporary)
        working = _build_workspace(root / "work" / "workshop.sqlite", "working")
        source = _build_workspace(root / "chosen" / "backup.sqlite", "source")
        fake_osascript = root / "bin" / "osascript"
        fake_osascript.parent.mkdir(parents=True)
        fake_osascript.write_text("owned test helper", encoding="utf-8")
        captured: dict[str, object] = {}

        def process_factory(argv, **kwargs):
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            return _CompletedPickerProcess(source)

        adapter = MacOSNativeSourceSelectionAdapter(
            process_factory=process_factory,
            platform_name="darwin",
            osascript_path=fake_osascript,
        )
        plane = RestoreControlPlane(
            working,
            frontend_url="http://127.0.0.1:5173",
            picker_adapter=adapter,
        )
        source_before = _sha256(source)
        working_before = _sha256(working)
        audit_before = _audit_count(working)
        durable_restore_dir = resolve_restore_dir(working)
        assert not durable_restore_dir.exists()
        run_dir = plane._candidate_service._scratch.run_dir
        try:
            plane.start()
            browser_config = runtime_config_with_restore_handoff(
                build_runtime_config(frontend_url="http://127.0.0.1:5173", open_browser=False),
                plane,
            )
            assert browser_config.frontend_url is not None
            assert "?" not in browser_config.frontend_url
            assert "#cw-control=" in browser_config.frontend_url

            node_input = json.dumps(
                {
                    "launchUrl": browser_config.frontend_url,
                    "frontendOrigin": "http://127.0.0.1:5173",
                }
            )
            completed = subprocess.run(
                ["node", "scripts/smoke-restore-control-client.mjs"],
                cwd=ROOT / "frontend",
                input=node_input,
                text=True,
                capture_output=True,
                check=True,
            )
            result = json.loads(completed.stdout)
            assert result["state"] == "accepted"
            assert result["filename"] == source.name
            assert result["fragmentRemoved"] is True
            assert result["storedKeys"] == result["expectedStorageKeys"]
            assert result["nextCommandSeq"] == 2
            assert result["pending"] is None

            proof = plane._candidate_service.retained_proof
            assert proof is not None
            assert proof.source_path == source.resolve()
            assert _sha256(source) == source_before
            assert _sha256(working) == working_before
            assert _audit_count(working) == audit_before
            assert not durable_restore_dir.exists()
            assert captured["argv"] == [str(fake_osascript), "-e", PICKER_APPLESCRIPT]
            assert captured["kwargs"]["shell"] is False
        finally:
            plane.close()

        assert plane._candidate_service.retained_proof is None
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
    except Exception as exc:  # noqa: BLE001 - smoke must emit one verdict
        print(f"FAIL — PRODUCT: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("PASS — C4-II-A4 BROWSER RESTORE SESSION SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
