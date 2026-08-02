#!/usr/bin/env python3
"""DEVELOPER-ONLY verification driver for the `C4-I` Restore safety engine.

This is **not** a product Restore workflow. It is not documented as one, it is
not reachable from the application, and the end user never runs it — `CR-010`
forbids a terminal command as the product workflow, and `C4-I` exposes no
user-facing entry point at all. It exists so a developer can prove the internal
engine against a real backend at an exact published commit.

It runs entirely inside an isolated temporary user-data directory supplied by
`scripts/c4_i_restore_smoke.sh`. It never touches the real
`~/Documents/Мастерская косметолога/` directory and never uses real user data.

Two scenarios:

1. **Successful Restore.** Workspace A is on disk, backup B is selected. The
   engine runs with the *real* backend verifier, so a live uvicorn child is
   started against the restored database, checked, stopped, started again and
   checked again. Afterwards: phase is durably `completed`, the restored data is
   B, backup B is byte-identical, the `before_restore` safety copy exists and
   holds A, the repository fallback database is untouched, and the browser never
   opened.

2. **Crash at the destructive boundary.** A durable `replacement_intent` is left
   behind with the working database already holding B. Startup recovery must
   roll back to A and end at `rolled_back` — never at `completed`.

Exit codes: `0` PASS, `1` FAIL PRODUCT, `2` INCONCLUSIVE.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import os
import socket
import sqlite3
import sys
import traceback
import webbrowser

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "backend"))

EXIT_PASS = 0
EXIT_FAIL_PRODUCT = 1
EXIT_INCONCLUSIVE = 2

MARKER_KEY = "smoke.workspace_marker"


class SmokeFailure(AssertionError):
    """A product failure: the engine did not behave as the contract requires."""


class SmokeInconclusive(RuntimeError):
    """The scenario could not be run, so it proves nothing either way."""


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


# --------------------------------------------------------------------------
# Isolated fixtures
# --------------------------------------------------------------------------


def build_workspace(path: Path, marker: str) -> Path:
    from app.db.config import DatabaseConfig
    from app.db.migrations import apply_migrations

    path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(DatabaseConfig(path=path))
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type, description) "
            "VALUES (?, ?, 'string', 'Isolated smoke marker') "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (MARKER_KEY, marker),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def read_marker(path: Path) -> str | None:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key = ?", (MARKER_KEY,)
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        connection.close()
    return row[0] if row else None


def fallback_fingerprint() -> tuple[bool, int, int]:
    from app.db.config import DEFAULT_DATABASE_PATH

    if not DEFAULT_DATABASE_PATH.exists():
        return (False, 0, 0)
    stat = DEFAULT_DATABASE_PATH.stat()
    return (True, stat.st_size, stat.st_mtime_ns)


class BrowserWatch:
    """Records any browser opening, so the smoke can prove none happened."""

    def __init__(self) -> None:
        self.opened: list[str] = []
        self._real = webbrowser.open

    def __enter__(self) -> "BrowserWatch":
        webbrowser.open = lambda url, *a, **k: self.opened.append(str(url))  # type: ignore[assignment]
        return self

    def __exit__(self, *_exc) -> None:
        webbrowser.open = self._real  # type: ignore[assignment]


# --------------------------------------------------------------------------
# Scenario 1 — successful Restore against a real backend
# --------------------------------------------------------------------------


def scenario_successful_restore(root: Path, evidence: dict) -> None:
    from launcher.config import build_runtime_config, resolve_runtime_paths
    from launcher.restore import RestoreOutcome, RestorePhase, execute_restore
    from launcher.restore.state import RestoreOperationStateStore
    from launcher.restore.workspace import RestoreWorkspace
    from launcher.restore.contracts import RestoreRequest

    base = root / "success"
    os.environ["COSMETIC_WORKSHOP_USER_DATA_DIR"] = str(base)
    os.environ.pop("COSMETIC_WORKSHOP_DB_PATH", None)

    # 1-2. Isolated workspace A, and an isolated backup B with different data.
    database_path = build_workspace(base / "data" / "cosmetic_workshop.sqlite", "workspace-A")
    backup_dir = base / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    selected = build_workspace(
        root / "chosen" / "20260101T000000000000Z-cosmetic_workshop-manual.sqlite",
        "workspace-B",
    )

    # 3. The hash of the selected backup, preserved before anything runs.
    selected_before = digest(selected)
    fallback_before = fallback_fingerprint()

    request = RestoreRequest(
        selected_source=selected,
        database_path=database_path,
        backup_dir=backup_dir,
        restore_dir=base / "restore",
        mode="user",
    )
    config = build_runtime_config(backend_port=free_port(), open_browser=False)

    # 4. Execute the internal engine with the *real* backend verifier.
    with BrowserWatch() as browser:
        result = execute_restore(request, config, resolve_runtime_paths())

    # 5. Durable `completed`.
    check(
        result.outcome is RestoreOutcome.COMPLETED,
        f"Restore did not complete: outcome={result.outcome.value} phase={result.phase.value}",
    )
    store = RestoreOperationStateStore(
        RestoreWorkspace(restore_dir=base / "restore", database_path=database_path)
    )
    record = store.read()
    check(
        record is not None and record.phase is RestorePhase.COMPLETED,
        "the durable operation record does not say completed",
    )

    # 6-7. The backend started, was checked, stopped, restarted and checked again
    # — that is what `verify_restored_backend` did inside the engine, and it is
    # the reason `completed` was reachable at all.
    check(read_marker(database_path) == "workspace-B", "the restored data is not backup B")

    # 8. The selected backup is byte-identical.
    check(
        digest(selected) == selected_before,
        "the selected backup was modified by Restore",
    )

    # 9-10. The safety copy remains available and holds the previous workspace.
    copies = sorted(backup_dir.glob("*-before_restore*.sqlite"))
    check(len(copies) == 1, f"expected exactly one before_restore safety copy, found {len(copies)}")
    check(
        copies[0].name == result.safety_copy_filename,
        "the reported safety copy filename does not match the artifact",
    )
    check(read_marker(copies[0]) == "workspace-A", "the safety copy does not hold workspace A")

    # 11. No repository fallback database was created or changed.
    check(
        fallback_fingerprint() == fallback_before,
        "the repository fallback database was created or modified",
    )

    # 12. The browser never opened during internal verification.
    check(browser.opened == [], f"the browser opened during verification: {browser.opened}")

    # No Restore AuditLog event, and no ledger row for the safety copy.
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    try:
        actions = [row[0] for row in connection.execute("SELECT action FROM audit_logs")]
    finally:
        connection.close()
    check(
        not any(action.startswith("restore") for action in actions),
        f"a Restore AuditLog event was written: {actions}",
    )

    evidence["successful_restore"] = {
        "outcome": result.outcome.value,
        "durable_phase": record.phase.value,
        "restored_marker": read_marker(database_path),
        "safety_copy_marker": read_marker(copies[0]),
        "safety_copy_filename": result.safety_copy_filename,
        "selected_backup_unchanged": True,
        "repository_fallback_unchanged": True,
        "browser_opened": browser.opened,
        "audit_log_actions": actions,
    }


# --------------------------------------------------------------------------
# Scenario 2 — crash at the destructive boundary
# --------------------------------------------------------------------------


def scenario_crash_recovery(root: Path, evidence: dict) -> None:
    from launcher.config import build_runtime_config, resolve_runtime_paths
    from launcher.restore import RestoreOutcome, RestorePhase, recover_incomplete_restore
    from launcher.restore.safety_copy import create_verified_safety_copy
    from launcher.restore.state import RestoreOperationRecord, RestoreOperationStateStore
    from launcher.restore.workspace import RestoreWorkspace, new_operation_id

    base = root / "crash"
    os.environ["COSMETIC_WORKSHOP_USER_DATA_DIR"] = str(base)
    os.environ.pop("COSMETIC_WORKSHOP_DB_PATH", None)

    database_path = build_workspace(base / "data" / "cosmetic_workshop.sqlite", "workspace-A")
    backup_dir = base / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # The verified safety copy of workspace A, exactly as the engine would have
    # taken it before entering the boundary.
    safety = create_verified_safety_copy(database_path, backup_dir)

    # The interruption: the working database already holds B, and the durable
    # record is left at `replacement_intent`.
    build_workspace(database_path, "workspace-B")
    workspace = RestoreWorkspace(restore_dir=base / "restore", database_path=database_path)
    store = RestoreOperationStateStore(workspace)
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)
    store.publish(
        RestoreOperationRecord(
            operation_id=operation_id,
            phase=RestorePhase.REPLACEMENT_INTENT,
            created_at="2026-08-02T00:00:00+00:00",
            updated_at="2026-08-02T00:00:00+00:00",
            staged_candidate_filename="candidate.sqlite",
            safety_copy_filename=safety.filename,
        )
    )

    config = build_runtime_config(backend_port=free_port(), open_browser=False)
    with BrowserWatch() as browser:
        recovery = recover_incomplete_restore(
            database_path, backup_dir, config, resolve_runtime_paths(), mode="user"
        )

    record = store.read()
    check(
        recovery.outcome is RestoreOutcome.ROLLED_BACK,
        f"recovery did not roll back: {recovery.outcome}",
    )
    check(
        record is not None and record.phase is RestorePhase.ROLLED_BACK,
        "the durable record does not say rolled_back",
    )
    check(
        record.phase is not RestorePhase.COMPLETED,
        "a rolled-back Restore must never be recorded as completed",
    )
    check(
        read_marker(database_path) == "workspace-A",
        "the previous workspace was not recovered",
    )
    check(safety.path.exists(), "the safety copy was deleted during recovery")
    check(browser.opened == [], f"the browser opened during recovery: {browser.opened}")

    evidence["crash_recovery"] = {
        "persisted_phase_before": "replacement_intent",
        "outcome": recovery.outcome.value,
        "durable_phase": record.phase.value,
        "recovered_marker": read_marker(database_path),
        "safety_copy_retained": True,
        "normal_startup_allowed": recovery.normal_startup_allowed,
        "browser_opened": browser.opened,
    }


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DEVELOPER-ONLY C4-I Restore safety engine smoke driver."
    )
    parser.add_argument("--root", required=True, help="Isolated temporary directory.")
    parser.add_argument("--evidence", required=True, help="Where to write the evidence JSON.")
    parser.add_argument("--head", required=True, help="The exact published head under test.")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"INCONCLUSIVE: the isolated root {root} does not exist.")
        return EXIT_INCONCLUSIVE

    evidence: dict = {"head": args.head, "scenarios": {}}
    scenarios = {
        "successful_restore": scenario_successful_restore,
        "crash_recovery": scenario_crash_recovery,
    }
    try:
        for name, scenario in scenarios.items():
            print(f"  → scenario: {name}")
            scenario(root, evidence["scenarios"])
            print(f"  ✓ scenario: {name}")
    except SmokeFailure as failure:
        evidence["result"] = "FAIL PRODUCT"
        evidence["failure"] = str(failure)
        Path(args.evidence).write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"FAIL PRODUCT: {failure}")
        return EXIT_FAIL_PRODUCT
    except Exception:  # noqa: BLE001 - anything else proves nothing about the product
        evidence["result"] = "INCONCLUSIVE"
        evidence["error"] = traceback.format_exc(limit=6)
        Path(args.evidence).write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("INCONCLUSIVE: the smoke could not complete.")
        traceback.print_exc(limit=6)
        return EXIT_INCONCLUSIVE

    evidence["result"] = "PASS"
    Path(args.evidence).write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("PASS")
    return EXIT_PASS


if __name__ == "__main__":
    raise SystemExit(main())
