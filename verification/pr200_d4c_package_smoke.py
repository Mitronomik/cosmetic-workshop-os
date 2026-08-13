from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import time
import urllib.request

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids

RUNNER_TEMP = Path(os.environ["RUNNER_TEMP"])
EVIDENCE = Path(os.environ["EVIDENCE_DIR"])
APP = RUNNER_TEMP / "pr200-build/package/CosmeticWorkshopOS.app"
EXECUTABLE = APP / "Contents/MacOS/CosmeticWorkshopOS"
EXPECTED_VERSION = Path("backend/VERSION").read_text(encoding="utf-8").strip()
EXPECTED_LINEAGE = expected_migration_ids()
SOURCE_LINEAGE = EXPECTED_LINEAGE[:-1]
OWNED = []


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def lineage(path: Path) -> list[str]:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as c:
        return [r[0] for r in c.execute("SELECT migration_id FROM schema_migrations ORDER BY rowid")]


def marker(path: Path) -> str:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as c:
        return c.execute("SELECT value FROM d4c_package_marker").fetchone()[0]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def start_app(user_data: Path, log_name: str):
    front, back = free_port(), free_port()
    while back == front:
        back = free_port()
    log_path = EVIDENCE / log_name
    log = log_path.open("w", encoding="utf-8")
    env = os.environ.copy()
    env["COSMETIC_WORKSHOP_USER_DATA_DIR"] = str(user_data)
    env["COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS"] = "1"
    proc = subprocess.Popen(
        [str(EXECUTABLE), "--no-browser", "--frontend-port", str(front), "--backend-port", str(back)],
        env=env, stdout=log, stderr=subprocess.STDOUT, text=True,
    )
    OWNED.append((proc, log))
    return proc, log, log_path, front, back


def stop(proc, log):
    if proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=5)
    log.flush(); log.close()
    OWNED[:] = [item for item in OWNED if item[0] is not proc]


def wait_exit(proc, log, timeout=30):
    try: code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        proc.kill(); proc.wait(timeout=5)
        raise AssertionError("packaged failure did not exit") from exc
    log.flush(); log.close()
    OWNED[:] = [item for item in OWNED if item[0] is not proc]
    return code


def wait_json(proc, url: str, timeout=60):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        if proc.poll() is not None:
            raise AssertionError(f"app exited early: {proc.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.load(response)
        except Exception as exc:
            last = exc; time.sleep(0.25)
    raise AssertionError(f"endpoint not ready: {url}: {last!r}")


def seed(user_data: Path, exclude_last: int) -> Path:
    db = user_data / "data/cosmetic_workshop.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-exclude_last] if exclude_last else original
        apply_migrations(DatabaseConfig(path=db))
    finally:
        MIGRATION_MODULES[:] = original
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE d4c_package_marker (value TEXT NOT NULL)")
        c.execute("INSERT INTO d4c_package_marker VALUES ('d4c-marker')")
    return db


def write_started(user_data: Path, *, from_lineage: list[str], to_lineage: list[str]):
    journal = user_data / "data/update-journal.json"
    payload = {"format_version": 1, "operations": [{
        "operation_id": "c" * 32,
        "from_app_version": None,
        "to_app_version": EXPECTED_VERSION,
        "from_schema_identity": from_lineage,
        "to_schema_identity": to_lineage,
        "before_migration_backup_identity": None,
        "stage_identity": ".cosmetic_workshop.update-" + "c" * 32 + ".stage",
        "started_at": "2026-08-13T10:00:00.000000Z",
        "finished_at": None,
        "status": "started",
        "failure_category": None,
        "safe_failure_message": None,
    }]}
    journal.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return journal


def assert_safe_failure_log(log_path: Path, expected_text: str):
    text = log_path.read_text(encoding="utf-8")
    assert expected_text in text
    for forbidden in (
        "Traceback (most recent call last)", "operation_id", "schema_identity",
        "stage_identity", "backup_identity", "secret-precommit", "secret-ambiguous",
        "no such column", str(RUNNER_TEMP),
    ):
        assert forbidden not in text, (forbidden, text)


def run():
    assert EXECUTABLE.is_file() and os.access(EXECUTABLE, os.X_OK)

    # A — fresh/current: bounded neutral status and no update journal.
    fresh = RUNNER_TEMP / "pr200-fresh"
    proc, log, _, front, _ = start_app(fresh, "fresh.log")
    status = wait_json(proc, f"http://127.0.0.1:{front}/api/settings/status")
    assert status["app"]["version"] == EXPECTED_VERSION
    assert status["update_status"]["state"] == "not_required"
    assert status["update_status"]["to_app_version"] is None
    assert status["update_status"]["next_action"] == "Ничего делать не нужно."
    serialized = json.dumps(status["update_status"], ensure_ascii=False)
    for forbidden in ("operation_id", "failure_category", "schema_identity", "stage_identity", "backup_identity"):
        assert forbidden not in serialized
    assert not (fresh / "data/update-journal.json").exists()
    stop(proc, log)

    # B — supported older migration: completed status is human-facing and marker survives.
    older = RUNNER_TEMP / "pr200-older"
    db = seed(older, 1)
    proc, log, _, front, _ = start_app(older, "older.log")
    status = wait_json(proc, f"http://127.0.0.1:{front}/api/settings/status")
    assert status["update_status"]["state"] == "completed"
    assert status["update_status"]["to_app_version"] == EXPECTED_VERSION
    assert status["update_status"]["next_action"] == "Можно продолжать работу."
    assert lineage(db) == EXPECTED_LINEAGE and marker(db) == "d4c-marker"
    stop(proc, log)

    # C — real stage migration failure before commit. The canonical DB remains source-authoritative.
    failed = RUNNER_TEMP / "pr200-precommit-failure"
    failed_db = seed(failed, 1)
    with sqlite3.connect(failed_db) as c:
        c.execute("CREATE TABLE artifact_audit_operations (wrong_column TEXT)")
    before = sha256(failed_db)
    proc, log, log_path, _, _ = start_app(failed, "precommit-failure.log")
    code = wait_exit(proc, log)
    assert code == 17
    assert sha256(failed_db) == before
    assert lineage(failed_db) == SOURCE_LINEAGE
    assert marker(failed_db) == "d4c-marker"
    assert_safe_failure_log(log_path, "Обновление остановлено до замены рабочей базы данных.")

    # D — durable ambiguous started state: completion cannot be confirmed automatically.
    ambiguous = RUNNER_TEMP / "pr200-ambiguous"
    ambiguous_db = seed(ambiguous, 1)
    write_started(ambiguous, from_lineage=EXPECTED_LINEAGE[:-2], to_lineage=EXPECTED_LINEAGE)
    before = sha256(ambiguous_db)
    proc, log, log_path, _, _ = start_app(ambiguous, "ambiguous.log")
    code = wait_exit(proc, log)
    assert code == 18
    assert sha256(ambiguous_db) == before
    assert lineage(ambiguous_db) == SOURCE_LINEAGE
    assert_safe_failure_log(log_path, "Не удалось подтвердить завершение обновления данных.")
    text = log_path.read_text(encoding="utf-8")
    assert "Ваши данные не изменились." not in text
    assert "Не пытайтесь вручную откатывать или заменять файлы данных." in text

    (EVIDENCE / "d4c-package-smoke.json").write_text(json.dumps({
        "expected_head": os.environ["EXPECTED_HEAD"],
        "fresh_status": "not_required",
        "older_status": "completed",
        "precommit_exit": 17,
        "uncertain_exit": 18,
        "status": "passed",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


try:
    run()
finally:
    for proc, log in list(OWNED):
        try: stop(proc, log)
        except Exception: pass
