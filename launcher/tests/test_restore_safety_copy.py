"""The mandatory `before_restore` safety copy.

Three properties, all from `CR-010` § 5:

1. it is taken by the **existing** SQLite Online Backup engine, never by a raw
   file copy and never by a second backup implementation;
2. it is **verified** before the replacement boundary, and a failure aborts
   there rather than continuing optimistically;
3. it creates **no** ledger row and **no** AuditLog event — it is launcher
   recovery infrastructure, not a user action.
"""

from pathlib import Path
import sqlite3

import pytest

from app.services import backup as backup_module

from launcher.restore.safety_copy import (
    SAFETY_COPY_REASON,
    SafetyCopyError,
    create_verified_safety_copy,
    verify_safety_copy,
)

from launcher.tests.restore_fixtures import MARKER_KEY, build_workspace_database, read_marker


@pytest.fixture
def database_path(tmp_path):
    return build_workspace_database(tmp_path / "data" / "workshop.sqlite", "workspace-A")


@pytest.fixture
def backup_dir(tmp_path):
    return tmp_path / "backups"


def test_the_exact_working_database_is_copied(database_path, backup_dir):
    copy = create_verified_safety_copy(database_path, backup_dir)

    assert copy.path.parent == backup_dir
    assert read_marker(copy.path) == "workspace-A"
    assert copy.size_bytes > 0


def test_the_canonical_reason_is_exactly_before_restore(database_path, backup_dir):
    copy = create_verified_safety_copy(database_path, backup_dir)

    assert SAFETY_COPY_REASON == "before_restore"
    assert "-before_restore" in copy.filename
    assert backup_module.canonical_backup_reason(copy.path) == "before_restore"


def test_the_existing_safe_backup_engine_is_used(database_path, backup_dir, monkeypatch):
    """Not `shutil.copy2`, and not a second implementation."""
    calls: list[str] = []
    real = backup_module.backup_sqlite_database

    def watched(**kwargs):
        calls.append(kwargs["reason"])
        return real(**kwargs)

    monkeypatch.setattr(backup_module, "backup_sqlite_database", watched)
    create_verified_safety_copy(database_path, backup_dir)

    assert calls == ["before_restore"]


def test_the_safety_copy_is_a_consistent_snapshot_not_a_raw_file_copy(database_path, backup_dir):
    """It opens independently, with no sidecar and no dependence on the source."""
    copy = create_verified_safety_copy(database_path, backup_dir)

    for suffix in ("-wal", "-shm", "-journal"):
        assert not copy.path.with_name(copy.path.name + suffix).exists()
    with sqlite3.connect(f"file:{copy.path}?mode=ro", uri=True) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"


def test_a_missing_working_database_aborts_before_the_safety_gate(tmp_path, backup_dir):
    """`C4-I` requires an existing working database and never fabricates one."""
    with pytest.raises(SafetyCopyError):
        create_verified_safety_copy(tmp_path / "absent.sqlite", backup_dir)

    assert not backup_dir.exists() or list(backup_dir.iterdir()) == []


def test_a_failing_backup_engine_aborts_the_safety_gate(database_path, backup_dir, monkeypatch):
    def refuse(**_kwargs):
        raise backup_module.BackupError("engine refused")

    monkeypatch.setattr(backup_module, "backup_sqlite_database", refuse)

    with pytest.raises(SafetyCopyError):
        create_verified_safety_copy(database_path, backup_dir)


def test_verification_rejects_an_empty_safety_copy(tmp_path):
    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")

    with pytest.raises(SafetyCopyError):
        verify_safety_copy(empty)


def test_verification_rejects_a_foreign_database(tmp_path):
    """`quick_check = ok` never authorizes a safety copy either."""
    foreign = tmp_path / "foreign.sqlite"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE anything (x INTEGER)")

    with pytest.raises(SafetyCopyError):
        verify_safety_copy(foreign)


def test_verification_rejects_a_symlink(tmp_path, database_path):
    link = tmp_path / "link.sqlite"
    link.symlink_to(database_path)

    with pytest.raises(SafetyCopyError):
        verify_safety_copy(link)


def test_verification_changes_nothing(database_path, backup_dir):
    copy = create_verified_safety_copy(database_path, backup_dir)
    before = copy.path.read_bytes()

    verify_safety_copy(copy.path)

    assert copy.path.read_bytes() == before


def test_no_ledger_row_and_no_audit_log_event_are_created(database_path, backup_dir):
    """The safety copy is system recovery infrastructure, not a user action."""
    create_verified_safety_copy(database_path, backup_dir)

    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        operations = connection.execute(
            "SELECT COUNT(*) FROM artifact_audit_operations"
        ).fetchone()[0]
        events = connection.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]

    assert operations == 0
    assert events == 0


def test_the_safety_copy_does_not_modify_the_source_database(database_path, backup_dir):
    before = read_marker(database_path)

    create_verified_safety_copy(database_path, backup_dir)

    assert read_marker(database_path) == before
    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM app_settings WHERE key = ?", (MARKER_KEY,)
        ).fetchone()[0] == 1
