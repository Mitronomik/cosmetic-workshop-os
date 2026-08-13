from __future__ import annotations

from importlib import import_module
from pathlib import Path
import hashlib
import json
import os
import sqlite3

import pytest

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.db.startup_compatibility import inspect_startup_schema_compatibility
from app.services import update_safety
from app.services.startup import initialize_startup
from app.services.update_safety import (
    SAFE_BACKUP_FAILURE,
    SAFE_COMMIT_FAILURE,
    SAFE_RECONCILIATION_FAILURE,
    UpdateJournalError,
    UpdateOperationRecord,
    UpdatePostCommitError,
    UpdateSafetyError,
    _stage_path,
    _write_update_journal,
    execute_staged_update,
    load_update_journal,
    update_journal_path,
)
from app.version import read_repository_app_version


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lineage(path: Path) -> list[str]:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            )
        ]


def marker(path: Path) -> str:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return connection.execute("SELECT value FROM d4b_marker").fetchone()[0]


def build_prefix(path: Path, *, exclude_last: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-exclude_last] if exclude_last else original
        apply_migrations(DatabaseConfig(path=path))
    finally:
        MIGRATION_MODULES[:] = original
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE d4b_marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO d4b_marker (value) VALUES ('marker-secret')")
    return path


def build_user_prefix(tmp_path, monkeypatch, *, exclude_last: int = 1):
    base = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(base))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    paths = resolve_user_data_paths()
    build_prefix(paths.database_path, exclude_last=exclude_last)
    return paths


def stage_artifacts(paths) -> list[Path]:
    if not paths.data_dir.exists():
        return []
    return [
        path
        for path in paths.data_dir.iterdir()
        if path.name.endswith(".stage") or path.name.endswith(".partial")
    ]


def test_supported_older_user_startup_migrates_stage_then_commits(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    old_lineage = expected_migration_ids()[:-1]

    result = initialize_startup("user")

    assert result.applied_migrations == expected_migration_ids()[-1:]
    assert result.backup is not None
    assert lineage(result.backup.backup_path) == old_lineage
    assert lineage(paths.database_path) == expected_migration_ids()
    assert marker(paths.database_path) == "marker-secret"
    assert marker(result.backup.backup_path) == "marker-secret"
    records = load_update_journal(update_journal_path(paths))
    assert len(records) == 1
    operation = records[0]
    assert operation.status == "completed"
    assert operation.from_app_version is None
    assert operation.from_schema_identity == tuple(old_lineage)
    assert operation.to_schema_identity == tuple(expected_migration_ids())
    assert operation.before_migration_backup_identity == result.backup.backup_path.name
    assert Path(operation.stage_identity).name == operation.stage_identity
    assert operation.stage_identity.endswith(".stage")
    assert not stage_artifacts(paths)
    raw_journal = update_journal_path(paths).read_text(encoding="utf-8")
    assert str(paths.base_dir) not in raw_journal
    assert "marker-secret" not in raw_journal


def test_previous_completed_update_is_not_misreported_as_immediate_from_app_version(
    tmp_path, monkeypatch
):
    paths = build_user_prefix(tmp_path, monkeypatch)
    previous = UpdateOperationRecord(
        operation_id="d" * 32,
        from_app_version=None,
        to_app_version="0.0.9",
        from_schema_identity=tuple(expected_migration_ids()[:-2]),
        to_schema_identity=tuple(expected_migration_ids()[:-1]),
        before_migration_backup_identity=None,
        stage_identity=".cosmetic_workshop.update-" + "d" * 32 + ".stage",
        started_at="2026-08-12T10:00:00.000000Z",
        finished_at="2026-08-12T10:01:00.000000Z",
        status="completed",
        failure_category=None,
        safe_failure_message=None,
    )
    _write_update_journal(update_journal_path(paths), [previous])

    result = initialize_startup("user")

    assert result.applied_migrations == expected_migration_ids()[-1:]
    records = load_update_journal(update_journal_path(paths))
    assert len(records) == 2
    assert records[0] == previous
    assert records[1].status == "completed"
    assert records[1].from_app_version is None
    assert records[1].to_app_version == read_repository_app_version()


def test_staged_migration_failure_keeps_canonical_unchanged(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    before = digest(paths.database_path)
    migration = import_module(MIGRATION_MODULES[-1])
    original_upgrade = migration.upgrade

    def failing_upgrade(connection):
        connection.execute("CREATE TABLE d4b_stage_only (id INTEGER PRIMARY KEY)")
        raise RuntimeError("forced staged migration failure")

    monkeypatch.setattr(migration, "upgrade", failing_upgrade)
    with pytest.raises(UpdateSafetyError) as caught:
        initialize_startup("user")
    monkeypatch.setattr(migration, "upgrade", original_upgrade)

    assert caught.value.category == "staged-migration-failed"
    assert digest(paths.database_path) == before
    assert lineage(paths.database_path) == expected_migration_ids()[:-1]
    with sqlite3.connect(paths.database_path) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='d4b_stage_only'"
        ).fetchone() is None
    backups = list(paths.backups_dir.iterdir())
    assert len(backups) == 1
    assert lineage(backups[0]) == expected_migration_ids()[:-1]
    records = load_update_journal(update_journal_path(paths))
    assert records[-1].status == "failed"
    assert records[-1].failure_category == "staged-migration-failed"
    assert not stage_artifacts(paths)


def test_backup_verification_failure_prevents_stage(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    before = digest(paths.database_path)

    def reject_backup(*_args, **_kwargs):
        raise UpdateSafetyError("backup-verification-failed", SAFE_BACKUP_FAILURE)

    monkeypatch.setattr(update_safety, "_verify_before_migration_backup", reject_backup)
    with pytest.raises(UpdateSafetyError) as caught:
        initialize_startup("user")

    assert caught.value.category == "backup-verification-failed"
    assert digest(paths.database_path) == before
    assert len(list(paths.backups_dir.iterdir())) == 1
    assert load_update_journal(update_journal_path(paths))[-1].status == "failed"
    assert not stage_artifacts(paths)


def test_commit_failure_never_replaces_canonical(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    before = digest(paths.database_path)

    def fail_commit(*_args, **_kwargs):
        raise UpdateSafetyError("database-commit-failed", SAFE_COMMIT_FAILURE)

    monkeypatch.setattr(update_safety, "_replace_stage_file", fail_commit)
    with pytest.raises(UpdateSafetyError) as caught:
        initialize_startup("user")

    assert caught.value.category == "database-commit-failed"
    assert digest(paths.database_path) == before
    assert lineage(paths.database_path) == expected_migration_ids()[:-1]
    assert len(list(paths.backups_dir.iterdir())) == 1
    record = load_update_journal(update_journal_path(paths))[-1]
    assert record.status == "failed"
    assert record.failure_category == "database-commit-failed"
    assert not stage_artifacts(paths)


def test_post_commit_journal_failure_reconciles_completed_next_launch(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    original_persist = update_safety._persist_operation

    def fail_completed(path, records, record):
        if record.status == "completed":
            raise UpdateJournalError("forced-terminal-write-failure")
        return original_persist(path, records, record)

    monkeypatch.setattr(update_safety, "_persist_operation", fail_completed)
    with pytest.raises(UpdatePostCommitError) as caught:
        initialize_startup("user")

    assert caught.value.category == "post-commit-journal-write-failed"
    assert lineage(paths.database_path) == expected_migration_ids()
    records = load_update_journal(update_journal_path(paths))
    assert records[-1].status == "started"
    backup_count = len(list(paths.backups_dir.iterdir()))

    monkeypatch.setattr(update_safety, "_persist_operation", original_persist)
    result = initialize_startup("user")

    assert result.applied_migrations == []
    records = load_update_journal(update_journal_path(paths))
    assert records[-1].status == "completed"
    assert len(list(paths.backups_dir.iterdir())) == backup_count


def test_interrupted_source_lineage_stops_same_launch_without_blind_retry(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    operation_id = "a" * 32
    stage = _stage_path(paths.database_path, operation_id)
    stage.write_text("owned interrupted stage", encoding="utf-8")
    sidecars = [
        stage.parent / f"{stage.name}-wal",
        stage.parent / f"{stage.name}-shm",
        stage.parent / f"{stage.name}-journal",
    ]
    for sidecar in sidecars:
        sidecar.write_bytes(b"runner-owned interrupted sidecar")
    record = UpdateOperationRecord(
        operation_id=operation_id,
        from_app_version=None,
        to_app_version=read_repository_app_version(),
        from_schema_identity=tuple(expected_migration_ids()[:-1]),
        to_schema_identity=tuple(expected_migration_ids()),
        before_migration_backup_identity=None,
        stage_identity=stage.name,
        started_at="2026-08-13T10:00:00.000000Z",
        finished_at=None,
        status="started",
        failure_category=None,
        safe_failure_message=None,
    )
    _write_update_journal(update_journal_path(paths), [record])

    with pytest.raises(UpdateSafetyError) as caught:
        initialize_startup("user")

    assert caught.value.category == "interrupted-before-commit"
    assert not stage.exists()
    assert all(not sidecar.exists() for sidecar in sidecars)
    assert list(paths.backups_dir.iterdir()) == []
    records = load_update_journal(update_journal_path(paths))
    assert records[0].status == "failed"
    assert lineage(paths.database_path) == expected_migration_ids()[:-1]

    result = initialize_startup("user")
    assert result.applied_migrations == expected_migration_ids()[-1:]
    records = load_update_journal(update_journal_path(paths))
    assert [record.status for record in records] == ["failed", "completed"]


def test_tampered_interrupted_stage_identity_fails_closed_without_cleanup(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    operation_id = "c" * 32
    expected_stage = _stage_path(paths.database_path, operation_id)
    expected_stage.write_text("expected owned stage evidence", encoding="utf-8")
    foreign_stage = paths.data_dir / "foreign-owned.stage"
    foreign_stage.write_text("foreign file", encoding="utf-8")
    record = UpdateOperationRecord(
        operation_id=operation_id,
        from_app_version=None,
        to_app_version=read_repository_app_version(),
        from_schema_identity=tuple(expected_migration_ids()[:-1]),
        to_schema_identity=tuple(expected_migration_ids()),
        before_migration_backup_identity=None,
        stage_identity=foreign_stage.name,
        started_at="2026-08-13T10:00:00.000000Z",
        finished_at=None,
        status="started",
        failure_category=None,
        safe_failure_message=None,
    )
    _write_update_journal(update_journal_path(paths), [record])
    before = digest(paths.database_path)

    with pytest.raises(UpdateSafetyError) as caught:
        initialize_startup("user")

    assert caught.value.category == "interrupted-stage-identity-mismatch"
    assert digest(paths.database_path) == before
    assert expected_stage.read_text(encoding="utf-8") == "expected owned stage evidence"
    assert foreign_stage.read_text(encoding="utf-8") == "foreign file"
    assert load_update_journal(update_journal_path(paths))[0].status == "started"
    assert list(paths.backups_dir.iterdir()) == []


def test_ambiguous_interrupted_record_fails_closed_and_keeps_stage(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch, exclude_last=2)
    operation_id = "b" * 32
    stage = _stage_path(paths.database_path, operation_id)
    stage.write_text("owned ambiguous stage", encoding="utf-8")
    record = UpdateOperationRecord(
        operation_id=operation_id,
        from_app_version=None,
        to_app_version=read_repository_app_version(),
        from_schema_identity=tuple(expected_migration_ids()[:-1]),
        to_schema_identity=tuple(expected_migration_ids()),
        before_migration_backup_identity=None,
        stage_identity=stage.name,
        started_at="2026-08-13T10:00:00.000000Z",
        finished_at=None,
        status="started",
        failure_category=None,
        safe_failure_message=None,
    )
    _write_update_journal(update_journal_path(paths), [record])
    before = digest(paths.database_path)

    with pytest.raises(UpdateSafetyError) as caught:
        initialize_startup("user")

    assert caught.value.category == "interrupted-update-ambiguous"
    assert digest(paths.database_path) == before
    assert stage.exists()
    assert load_update_journal(update_journal_path(paths))[0].status == "started"
    assert list(paths.backups_dir.iterdir()) == []


def test_canonical_sidecar_refuses_before_backup_or_stage(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch)
    config = DatabaseConfig(path=paths.database_path)
    compatibility = inspect_startup_schema_compatibility(config)
    sidecar = paths.database_path.parent / f"{paths.database_path.name}-journal"
    sidecar.write_bytes(b"foreign sidecar evidence")
    before = digest(paths.database_path)

    with pytest.raises(UpdateSafetyError) as caught:
        execute_staged_update(
            config,
            paths,
            read_repository_app_version(),
            compatibility,
        )

    assert caught.value.category == "canonical-sidecar-present"
    assert digest(paths.database_path) == before
    assert sidecar.read_bytes() == b"foreign sidecar evidence"
    assert not paths.backups_dir.exists()
    record = load_update_journal(update_journal_path(paths))[-1]
    assert record.status == "failed"
    assert not stage_artifacts(paths)


def test_current_user_schema_creates_no_update_journal(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch, exclude_last=0)

    result = initialize_startup("user")

    assert result.applied_migrations == []
    assert result.backup is None
    assert not update_journal_path(paths).exists()
    assert marker(paths.database_path) == "marker-secret"


def test_development_mode_keeps_direct_migration_and_no_user_journal(tmp_path, monkeypatch):
    database = build_prefix(tmp_path / "development.sqlite")
    user_base = tmp_path / "unused-user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_base))

    result = initialize_startup("development")

    assert result.applied_migrations == expected_migration_ids()[-1:]
    assert lineage(database) == expected_migration_ids()
    assert not (user_base / "data" / "update-journal.json").exists()
    assert not user_base.exists()


def test_malformed_update_journal_fails_closed_before_current_startup(tmp_path, monkeypatch):
    paths = build_user_prefix(tmp_path, monkeypatch, exclude_last=0)
    journal = update_journal_path(paths)
    journal.write_text("{", encoding="utf-8")
    before = digest(paths.database_path)

    with pytest.raises(UpdateJournalError):
        initialize_startup("user")

    assert digest(paths.database_path) == before
    assert list(paths.backups_dir.iterdir()) == []
    assert marker(paths.database_path) == "marker-secret"
