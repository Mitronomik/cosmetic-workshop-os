#!/usr/bin/env python3
"""Exact-head service-level smoke for C4-II-A1 candidate preparation.

The runner uses only temporary SQLite files and never starts destructive Restore.
It verifies the published git head supplied by the caller both before and after
execution.  A1 has no browser/control/picker surface yet, so this is deliberately
a launcher/service smoke rather than a product browser smoke.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _assert_exact_head(expected: str) -> None:
    actual = _git("rev-parse", "HEAD")
    if actual != expected:
        raise RuntimeError(f"exact-head mismatch: expected {expected}, got {actual}")


def _assert_clean_workspace() -> None:
    dirty = _git("status", "--porcelain")
    if dirty:
        raise RuntimeError("git workspace is not clean")


def _build_workspace(path: Path, marker: str) -> Path:
    from app.db.config import DatabaseConfig
    from app.db.migrations import apply_migrations

    path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(DatabaseConfig(path=path))
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type, description) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("smoke.restore_validation_marker", marker, "string", "A1 smoke marker"),
        )
    return path


def _audit_count(path: Path) -> int:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])


def run(expected_head: str) -> None:
    _assert_exact_head(expected_head)
    _assert_clean_workspace()

    from launcher.config import resolve_runtime_paths
    from launcher.runtime import ensure_backend_import_path

    ensure_backend_import_path(resolve_runtime_paths())

    from launcher.restore.validation_session import (
        CandidateCompatibility,
        CandidatePreparationState,
        RestoreCandidatePreparationService,
    )
    from launcher.restore.workspace import resolve_restore_dir

    with tempfile.TemporaryDirectory(prefix="cwos-a1-smoke-") as temporary:
        root = Path(temporary)
        working = _build_workspace(root / "work" / "workshop.sqlite", "working")
        source = _build_workspace(root / "chosen" / "backup.sqlite", "source")
        scratch = root / "system-temp" / "cosmetic-workshop-os" / "restore-validation"

        working_before = _sha256(working)
        source_before = _sha256(source)
        audit_before = _audit_count(working)
        durable_restore_dir = resolve_restore_dir(working)
        if durable_restore_dir.exists():
            raise AssertionError("fixture unexpectedly contains durable Restore state")

        service = RestoreCandidatePreparationService(working, scratch_root=scratch)
        run_dir = service._scratch.run_dir
        try:
            result = service.prepare_restore_candidate(source)
            proof = service.retained_proof

            assert result.state is CandidatePreparationState.ACCEPTED
            assert result.compatibility is CandidateCompatibility.CURRENT_SCHEMA
            assert proof is not None
            assert proof.source_path == source.resolve()
            assert proof.sha256 == source_before
            assert str(source) not in repr(result)
            assert _sha256(source) == source_before
            assert _sha256(working) == working_before
            assert _audit_count(working) == audit_before
            assert not durable_restore_dir.exists()
            assert not (run_dir / result.session_id / "candidate.sqlite").exists()
        finally:
            service.close()

        assert not run_dir.exists(), "validation run scratch was not cleaned on close"
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
        # Exact-head / dirty-workspace failures are environment/preflight failures,
        # not evidence of a product defect.
        print(f"INCONCLUSIVE — ENVIRONMENT: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - smoke must always emit a verdict
        print(f"FAIL — PRODUCT: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("PASS — C4-II-A1 VALIDATION-SESSION SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
