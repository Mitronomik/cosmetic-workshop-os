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
APP = RUNNER_TEMP / "pr198-final-build/package/CosmeticWorkshopOS.app"
EXECUTABLE = APP / "Contents/MacOS/CosmeticWorkshopOS"
EXPECTED_VERSION = Path("backend/VERSION").read_text(encoding="utf-8").strip()
EXPECTED_LINEAGE = expected_migration_ids()
SOURCE_LINEAGE = EXPECTED_LINEAGE[:-1]
OWNED: list[tuple[subprocess.Popen[str], object]] = []
RESULTS: dict[str, object] = {
    "expected_head": os.environ["EXPECTED_HEAD"],
    "expected_version": EXPECTED_VERSION,
    "status": "running",
    "scenarios": {},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lineage(path: Path) -> list[str]:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            )
        ]


def quick_check(path: Path) -> str:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return connection.execute("PRAGMA quick_check").fetchone()[0]


def marker(path: Path) -> str:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return connection.execute("SELECT value FROM d4b_package_marker").fetchone()[0]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def port_closed(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def start_app(user_data: Path, log_name: str):
    frontend = free_port()
    backend = free_port()
    while backend == frontend:
        backend = free_port()
    log = (EVIDENCE / log_name).open("w", encoding="utf-8")
    env = os.environ.copy()
    env["COSMETIC_WORKSHOP_USER_DATA_DIR"] = str(user_data)
    env["COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS"] = "1"
    process = subprocess.Popen(
        [
            str(EXECUTABLE),
            "--no-browser",
            "--frontend-port",
            str(frontend),
            "--backend-port",
            str(backend),
        ],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    OWNED.append((process, log))
    return process, log, frontend, backend


def forget_owned(process) -> None:
    for item in list(OWNED):
        if item[0] is process:
            OWNED.remove(item)
            return


def stop_app(process, log, frontend: int, backend: int) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    log.flush()
    log.close()
    forget_owned(process)
    deadline = time.time() + 10
    while time.time() < deadline and (not port_closed(frontend) or not port_closed(backend)):
        time.sleep(0.1)
    assert port_closed(frontend), f"frontend port still open: {frontend}"
    assert port_closed(backend), f"backend port still open: {backend}"


def wait_exit(process, log, frontend: int, backend: int, timeout: float = 25.0) -> int:
    try:
        exit_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        raise AssertionError("packaged start did not fail within bound") from exc
    log.flush()
    log.close()
    forget_owned(process)
    deadline = time.time() + 10
    while time.time() < deadline and (not port_closed(frontend) or not port_closed(backend)):
        time.sleep(0.1)
    assert port_closed(frontend)
    assert port_closed(backend)
    return exit_code


def wait_json(process, url: str, timeout: float = 60.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"app exited before readiness: {process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                return json.load(response)
        except Exception as exc:  # transient local startup refusal
            last = exc
            time.sleep(0.25)
    raise AssertionError(f"endpoint did not become ready: {url}: {last!r}")


def seed_prefix(user_data: Path, *, exclude_last: int) -> Path:
    database = user_data / "data/cosmetic_workshop.sqlite"
    database.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-exclude_last] if exclude_last else original
        apply_migrations(DatabaseConfig(path=database))
    finally:
        MIGRATION_MODULES[:] = original
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE d4b_package_marker (value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO d4b_package_marker (value) VALUES ('package-marker-secret')"
        )
    return database


def stage_name(database: Path, operation_id: str) -> str:
    return f".{database.stem}.update-{operation_id}.stage"


def write_started_journal(
    user_data: Path,
    database: Path,
    operation_id: str,
    from_lineage: list[str],
    to_lineage: list[str],
) -> tuple[Path, Path, list[Path]]:
    journal_path = user_data / "data/update-journal.json"
    stage = database.parent / stage_name(database, operation_id)
    stage.write_bytes(b"runner-owned interrupted stage evidence")
    sidecars = [
        stage.parent / f"{stage.name}-wal",
        stage.parent / f"{stage.name}-shm",
        stage.parent / f"{stage.name}-journal",
    ]
    for sidecar in sidecars:
        sidecar.write_bytes(b"runner-owned interrupted sidecar evidence")
    payload = {
        "format_version": 1,
        "operations": [
            {
                "operation_id": operation_id,
                "from_app_version": None,
                "to_app_version": EXPECTED_VERSION,
                "from_schema_identity": from_lineage,
                "to_schema_identity": to_lineage,
                "before_migration_backup_identity": None,
                "stage_identity": stage.name,
                "started_at": "2026-08-13T10:00:00.000000Z",
                "finished_at": None,
                "status": "started",
                "failure_category": None,
                "safe_failure_message": None,
            }
        ],
    }
    journal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return journal_path, stage, sidecars


def read_journal(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def no_stage_artifacts(data_dir: Path) -> bool:
    if not data_dir.exists():
        return True
    for path in data_dir.iterdir():
        name = path.name
        if ".update-" in name and (
            name.endswith(".stage")
            or name.endswith(".partial")
            or name.endswith(".stage-wal")
            or name.endswith(".stage-shm")
            or name.endswith(".stage-journal")
        ):
            return False
    return True


def mark(name: str) -> None:
    scenarios = RESULTS["scenarios"]
    assert isinstance(scenarios, dict)
    scenarios[name] = "passed"


def run() -> None:
    assert EXECUTABLE.is_file() and os.access(EXECUTABLE, os.X_OK)

    # A — fresh package: normal first-run, no D4 update artifacts.
    fresh = RUNNER_TEMP / "pr198-final-fresh-user-data"
    process, log, front, back = start_app(fresh, "package-fresh.log")
    health = wait_json(process, f"http://127.0.0.1:{front}/api/health")
    settings = wait_json(process, f"http://127.0.0.1:{front}/api/settings/status")
    assert health["version"] == EXPECTED_VERSION
    assert settings["app"]["version"] == EXPECTED_VERSION
    fresh_db = fresh / "data/cosmetic_workshop.sqlite"
    assert lineage(fresh_db) == EXPECTED_LINEAGE
    assert quick_check(fresh_db) == "ok"
    assert not (fresh / "data/update-journal.json").exists()
    assert not list((fresh / "backups").iterdir())
    stop_app(process, log, front, back)
    mark("fresh")

    # B — supported older package update: backup -> stage -> commit -> journal.
    older = RUNNER_TEMP / "pr198-final-older-user-data"
    older_db = seed_prefix(older, exclude_last=1)
    original_marker = marker(older_db)
    assert original_marker == "package-marker-secret"
    process, log, front, back = start_app(older, "package-older-update.log")
    health = wait_json(process, f"http://127.0.0.1:{front}/api/health")
    assert health["version"] == EXPECTED_VERSION
    assert lineage(older_db) == EXPECTED_LINEAGE
    assert marker(older_db) == original_marker
    assert quick_check(older_db) == "ok"
    stop_app(process, log, front, back)

    journal_path = older / "data/update-journal.json"
    raw_journal = journal_path.read_text(encoding="utf-8")
    journal = json.loads(raw_journal)
    assert journal["format_version"] == 1
    assert len(journal["operations"]) == 1
    operation = journal["operations"][0]
    assert operation["status"] == "completed"
    assert operation["from_app_version"] is None
    assert operation["to_app_version"] == EXPECTED_VERSION
    assert operation["from_schema_identity"] == SOURCE_LINEAGE
    assert operation["to_schema_identity"] == EXPECTED_LINEAGE
    assert operation["finished_at"]
    assert operation["failure_category"] is None
    assert operation["safe_failure_message"] is None
    backup_identity = operation["before_migration_backup_identity"]
    recorded_stage = operation["stage_identity"]
    assert isinstance(backup_identity, str) and Path(backup_identity).name == backup_identity
    assert isinstance(recorded_stage, str) and Path(recorded_stage).name == recorded_stage
    assert recorded_stage.endswith(".stage")
    assert str(older) not in raw_journal
    assert "package-marker-secret" not in raw_journal
    backups = list((older / "backups").iterdir())
    assert len(backups) == 1
    backup = backups[0]
    assert backup.name == backup_identity
    assert lineage(backup) == SOURCE_LINEAGE
    assert quick_check(backup) == "ok"
    assert marker(backup) == original_marker
    assert no_stage_artifacts(older / "data")
    mark("supported_older_update")

    # C — repeated current launch: no second migration, backup or UpdateLog operation.
    backup_count = len(backups)
    journal_count = len(journal["operations"])
    process, log, front, back = start_app(older, "package-older-repeat.log")
    wait_json(process, f"http://127.0.0.1:{front}/api/health")
    stop_app(process, log, front, back)
    assert len(list((older / "backups").iterdir())) == backup_count
    journal2 = read_journal(journal_path)
    assert len(journal2["operations"]) == journal_count
    assert journal2["operations"][0]["status"] == "completed"
    assert lineage(older_db) == EXPECTED_LINEAGE
    assert marker(older_db) == original_marker
    assert no_stage_artifacts(older / "data")
    mark("repeat_after_update")

    # D — interrupted before commit: source canonical stays authoritative; same launch stops.
    interrupted_source = RUNNER_TEMP / "pr198-final-interrupted-source"
    source_db = seed_prefix(interrupted_source, exclude_last=1)
    source_sha = sha256(source_db)
    operation_id = "e" * 32
    source_journal, source_stage, source_sidecars = write_started_journal(
        interrupted_source,
        source_db,
        operation_id,
        SOURCE_LINEAGE,
        EXPECTED_LINEAGE,
    )
    process, log, front, back = start_app(
        interrupted_source, "package-interrupted-source.log"
    )
    exit_code = wait_exit(process, log, front, back)
    assert exit_code != 0
    assert sha256(source_db) == source_sha
    assert lineage(source_db) == SOURCE_LINEAGE
    source_record = read_journal(source_journal)["operations"][0]
    assert source_record["status"] == "failed"
    assert source_record["failure_category"] == "interrupted-before-commit"
    assert source_record["finished_at"]
    assert not source_stage.exists()
    assert all(not path.exists() for path in source_sidecars)
    assert not list((interrupted_source / "backups").iterdir())
    mark("interrupted_source_no_retry")

    # E — commit happened but terminal journal write did not: target canonical reconciles completed.
    interrupted_target = RUNNER_TEMP / "pr198-final-interrupted-target"
    target_db = seed_prefix(interrupted_target, exclude_last=0)
    target_marker = marker(target_db)
    operation_id = "f" * 32
    target_journal, target_stage, target_sidecars = write_started_journal(
        interrupted_target,
        target_db,
        operation_id,
        SOURCE_LINEAGE,
        EXPECTED_LINEAGE,
    )
    process, log, front, back = start_app(
        interrupted_target, "package-interrupted-target.log"
    )
    wait_json(process, f"http://127.0.0.1:{front}/api/health")
    stop_app(process, log, front, back)
    assert lineage(target_db) == EXPECTED_LINEAGE
    assert marker(target_db) == target_marker
    target_record = read_journal(target_journal)["operations"][0]
    assert target_record["status"] == "completed"
    assert target_record["failure_category"] is None
    assert target_record["finished_at"]
    assert not target_stage.exists()
    assert all(not path.exists() for path in target_sidecars)
    assert not list((interrupted_target / "backups").iterdir())
    mark("interrupted_target_reconciles_completed")

    # F — newer schema: D4-A refusal happens before journal, backup or migration.
    newer = RUNNER_TEMP / "pr198-final-newer-user-data"
    newer_db = seed_prefix(newer, exclude_last=0)
    with sqlite3.connect(newer_db) as connection:
        connection.execute("INSERT INTO schema_migrations (migration_id) VALUES ('0021_future')")
    before_sha = sha256(newer_db)
    assert not (newer / "backups").exists()
    assert not (newer / "data/update-journal.json").exists()
    process, log, front, back = start_app(newer, "package-newer-refusal.log")
    exit_code = wait_exit(process, log, front, back)
    assert exit_code != 0
    assert sha256(newer_db) == before_sha
    assert not (newer / "data/update-journal.json").exists()
    assert not (newer / "backups").exists()
    mark("newer_schema_refusal")


try:
    run()
    RESULTS["status"] = "passed"
except Exception as exc:
    RESULTS["status"] = "failed"
    RESULTS["error"] = f"{type(exc).__name__}: {exc}"
    raise
finally:
    for process, log in list(OWNED):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        try:
            log.flush()
            log.close()
        except Exception:
            pass
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "package-smoke-results.json").write_text(
        json.dumps(RESULTS, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
