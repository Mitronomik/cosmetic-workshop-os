"""D4-B staged migration, verified commit and external durable UpdateLog.

This module is deliberately a startup service, not a second launcher or migration
framework. The ordinary launcher already holds the exclusive workspace lifecycle
lease before :func:`app.services.startup.initialize_startup` reaches this code.
D4-B reuses the existing migration registry and ADR 0015 SQLite Online Backup
primitive, but changes one safety property: migrations run only against a
runner-owned stage until one verified atomic publication replaces the canonical
working database.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal
import contextlib
import json
import os
import sqlite3
import tempfile
import uuid

from app.db.config import DatabaseConfig
from app.db.migration_lineage import inspect_migration_lineage
from app.db.migrations import apply_migrations
from app.db.paths import UserDataPaths
from app.db.startup_compatibility import StartupSchemaCompatibility
from app.services.backup import (
    PARTIAL_BACKUP_SUFFIX,
    BackupError,
    BackupResult,
    _copy_sqlite_database,
    _publish_without_replacing,
    backup_sqlite_database,
    parse_generated_backup_filename,
)

UpdateStatus = Literal["started", "completed", "failed"]
UpdateUserStatusState = Literal["not_required", "completed", "attention_required"]
UpdateUserFailureKind = Literal["before_commit", "completion_uncertain"]
UPDATE_JOURNAL_FORMAT_VERSION = 1
UPDATE_JOURNAL_FILENAME = "update-journal.json"
STAGE_SUFFIX = ".stage"

SAFE_BACKUP_FAILURE = "Не удалось подготовить безопасную резервную копию перед обновлением."
SAFE_STAGE_FAILURE = "Не удалось подготовить безопасную рабочую копию для обновления."
SAFE_MIGRATION_FAILURE = "Обновление базы данных не завершено. Рабочая база не была заменена."
SAFE_VERIFICATION_FAILURE = "Обновлённая рабочая копия не прошла проверку безопасности."
SAFE_COMMIT_FAILURE = "Не удалось безопасно завершить замену рабочей базы данных."
SAFE_INTERRUPTED_FAILURE = "Предыдущее обновление было прервано до замены рабочей базы данных."
SAFE_RECONCILIATION_FAILURE = "Состояние предыдущего обновления нельзя подтвердить автоматически."
SAFE_JOURNAL_FAILURE = "Не удалось надёжно записать состояние обновления."
SAFE_NO_UPDATE_STATUS = "Обновление данных для этой установки пока не требовалось."
SAFE_COMPLETED_UPDATE_STATUS = "Данные успешно подготовлены для этой версии приложения."


class UpdateSafetyError(RuntimeError):
    """A D4-B update path cannot continue safely."""

    def __init__(self, category: str, safe_message: str, *, committed: bool = False) -> None:
        super().__init__(f"D4-B update safety stopped: {category}")
        self.category = category
        self.safe_message = safe_message
        self.committed = committed


class UpdateJournalError(UpdateSafetyError):
    def __init__(self, category: str = "update-journal-unavailable") -> None:
        super().__init__(category, SAFE_JOURNAL_FAILURE)


class UpdatePostCommitError(UpdateSafetyError):
    """The database commit point was crossed but startup cannot continue yet."""

    def __init__(self, category: str) -> None:
        super().__init__(category, SAFE_RECONCILIATION_FAILURE, committed=True)


def classify_update_failure_for_user(error: UpdateSafetyError) -> UpdateUserFailureKind:
    """Collapse internal D4-B failures into the only two D4-C packaged outcomes."""
    if error.committed or isinstance(error, (UpdateJournalError, UpdatePostCommitError)):
        return "completion_uncertain"
    if error.safe_message == SAFE_RECONCILIATION_FAILURE:
        return "completion_uncertain"
    return "before_commit"


@dataclass(frozen=True)
class UpdateOperationRecord:
    operation_id: str
    from_app_version: str | None
    to_app_version: str
    from_schema_identity: tuple[str, ...]
    to_schema_identity: tuple[str, ...]
    before_migration_backup_identity: str | None
    stage_identity: str
    started_at: str
    finished_at: str | None
    status: UpdateStatus
    failure_category: str | None
    safe_failure_message: str | None


@dataclass(frozen=True)
class StagedUpdateResult:
    operation: UpdateOperationRecord
    backup: BackupResult
    applied_migrations: list[str]


@dataclass(frozen=True)
class UpdateReconciliationResult:
    operation: UpdateOperationRecord | None = None
    reconciled_to_completed: bool = False


@dataclass(frozen=True)
class UpdateUserStatus:
    state: UpdateUserStatusState
    to_app_version: str | None
    updated_at: str | None
    message: str


def update_journal_path(paths: UserDataPaths) -> Path:
    """Durable D4 metadata beside, but never inside, the working database."""
    return paths.data_dir / UPDATE_JOURNAL_FILENAME


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _operation_to_payload(record: UpdateOperationRecord) -> dict[str, object]:
    return {
        "operation_id": record.operation_id,
        "from_app_version": record.from_app_version,
        "to_app_version": record.to_app_version,
        "from_schema_identity": list(record.from_schema_identity),
        "to_schema_identity": list(record.to_schema_identity),
        "before_migration_backup_identity": record.before_migration_backup_identity,
        "stage_identity": record.stage_identity,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "status": record.status,
        "failure_category": record.failure_category,
        "safe_failure_message": record.safe_failure_message,
    }


def _safe_filename(value: object, *, field: str, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or Path(value).name != value:
        raise UpdateJournalError(f"update-journal-invalid-{field}")
    return value


def _schema_identity(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise UpdateJournalError(f"update-journal-invalid-{field}")
    return tuple(value)


def _operation_from_payload(payload: object) -> UpdateOperationRecord:
    if not isinstance(payload, dict):
        raise UpdateJournalError("update-journal-invalid-operation")
    operation_id = payload.get("operation_id")
    if (
        not isinstance(operation_id, str)
        or len(operation_id) != 32
        or any(character not in "0123456789abcdef" for character in operation_id)
    ):
        raise UpdateJournalError("update-journal-invalid-operation-id")
    from_app_version = payload.get("from_app_version")
    if from_app_version is not None and (not isinstance(from_app_version, str) or not from_app_version):
        raise UpdateJournalError("update-journal-invalid-from-app-version")
    to_app_version = payload.get("to_app_version")
    if not isinstance(to_app_version, str) or not to_app_version:
        raise UpdateJournalError("update-journal-invalid-to-app-version")
    status = payload.get("status")
    if status not in {"started", "completed", "failed"}:
        raise UpdateJournalError("update-journal-invalid-status")
    started_at = payload.get("started_at")
    finished_at = payload.get("finished_at")
    if not isinstance(started_at, str) or not started_at:
        raise UpdateJournalError("update-journal-invalid-started-at")
    if finished_at is not None and (not isinstance(finished_at, str) or not finished_at):
        raise UpdateJournalError("update-journal-invalid-finished-at")
    if status == "started" and finished_at is not None:
        raise UpdateJournalError("update-journal-started-has-finished-at")
    if status != "started" and finished_at is None:
        raise UpdateJournalError("update-journal-terminal-without-finished-at")
    failure_category = payload.get("failure_category")
    safe_failure_message = payload.get("safe_failure_message")
    if failure_category is not None and not isinstance(failure_category, str):
        raise UpdateJournalError("update-journal-invalid-failure-category")
    if safe_failure_message is not None and not isinstance(safe_failure_message, str):
        raise UpdateJournalError("update-journal-invalid-safe-message")
    return UpdateOperationRecord(
        operation_id=operation_id,
        from_app_version=from_app_version,
        to_app_version=to_app_version,
        from_schema_identity=_schema_identity(payload.get("from_schema_identity"), field="from-schema"),
        to_schema_identity=_schema_identity(payload.get("to_schema_identity"), field="to-schema"),
        before_migration_backup_identity=_safe_filename(
            payload.get("before_migration_backup_identity"), field="backup-identity", optional=True
        ),
        stage_identity=_safe_filename(payload.get("stage_identity"), field="stage-identity") or "",
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        failure_category=failure_category,
        safe_failure_message=safe_failure_message,
    )


def load_update_journal(path: Path) -> list[UpdateOperationRecord]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UpdateJournalError("update-journal-unreadable") from exc
    if not isinstance(payload, dict) or payload.get("format_version") != UPDATE_JOURNAL_FORMAT_VERSION:
        raise UpdateJournalError("update-journal-format-unsupported")
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise UpdateJournalError("update-journal-invalid-operations")
    records = [_operation_from_payload(item) for item in operations]
    ids = [record.operation_id for record in records]
    if len(ids) != len(set(ids)):
        raise UpdateJournalError("update-journal-duplicate-operation-id")
    return records


def read_user_update_status(paths: UserDataPaths) -> UpdateUserStatus:
    """Read the durable journal as a bounded, non-technical D4-C status."""
    try:
        records = load_update_journal(update_journal_path(paths))
    except UpdateJournalError:
        return UpdateUserStatus(
            state="attention_required",
            to_app_version=None,
            updated_at=None,
            message=SAFE_RECONCILIATION_FAILURE,
        )
    if not records:
        return UpdateUserStatus(
            state="not_required",
            to_app_version=None,
            updated_at=None,
            message=SAFE_NO_UPDATE_STATUS,
        )
    latest = records[-1]
    if latest.status == "completed":
        return UpdateUserStatus(
            state="completed",
            to_app_version=latest.to_app_version,
            updated_at=latest.finished_at,
            message=SAFE_COMPLETED_UPDATE_STATUS,
        )
    if latest.status == "failed":
        return UpdateUserStatus(
            state="attention_required",
            to_app_version=latest.to_app_version,
            updated_at=latest.finished_at,
            message=latest.safe_failure_message or SAFE_RECONCILIATION_FAILURE,
        )
    return UpdateUserStatus(
        state="attention_required",
        to_app_version=latest.to_app_version,
        updated_at=latest.started_at,
        message=SAFE_RECONCILIATION_FAILURE,
    )


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_update_journal(path: Path, records: list[UpdateOperationRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": UPDATE_JOURNAL_FORMAT_VERSION,
        "operations": [_operation_to_payload(record) for record in records],
    }
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".partial"
    )
    temporary = Path(temporary_name)
    replaced = False
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        replaced = True
        _fsync_directory(path.parent)
    except (OSError, TypeError, ValueError) as exc:
        raise UpdateJournalError("update-journal-write-failed") from exc
    finally:
        if not replaced:
            with contextlib.suppress(OSError):
                temporary.unlink(missing_ok=True)


def _persist_operation(
    journal_path: Path,
    records: list[UpdateOperationRecord],
    record: UpdateOperationRecord,
) -> None:
    matches = [index for index, item in enumerate(records) if item.operation_id == record.operation_id]
    if len(matches) > 1:
        raise UpdateJournalError("update-journal-duplicate-operation-id")
    if matches:
        records[matches[0]] = record
    else:
        records.append(record)
    _write_update_journal(journal_path, records)


def _stage_filename(database_path: Path, operation_id: str) -> str:
    return f".{database_path.stem}.update-{operation_id}{STAGE_SUFFIX}"


def _stage_path(database_path: Path, operation_id: str) -> Path:
    return database_path.parent / _stage_filename(database_path, operation_id)


def _require_recorded_stage_ownership(
    database_path: Path, record: UpdateOperationRecord
) -> None:
    """Prove a persisted stage identity before deleting runner-owned artifacts."""
    expected = _stage_filename(database_path, record.operation_id)
    if record.stage_identity != expected:
        raise UpdateSafetyError(
            "interrupted-stage-identity-mismatch", SAFE_RECONCILIATION_FAILURE
        )


def _cleanup_owned_stage_artifacts(database_path: Path, operation_id: str) -> None:
    stage = _stage_path(database_path, operation_id)
    for candidate in (
        stage,
        stage.parent / f"{stage.name}-wal",
        stage.parent / f"{stage.name}-shm",
        stage.parent / f"{stage.name}-journal",
    ):
        with contextlib.suppress(OSError):
            candidate.unlink(missing_ok=True)
    pattern = f".{stage.name}.*{PARTIAL_BACKUP_SUFFIX}"
    for candidate in database_path.parent.glob(pattern):
        if candidate.parent == database_path.parent and candidate.is_file():
            with contextlib.suppress(OSError):
                candidate.unlink(missing_ok=True)


def _create_consistent_stage_snapshot(source_path: Path, stage_path: Path) -> None:
    """Create a runner-owned stage with the ADR 0015 SQLite backup primitive."""
    if stage_path.parent != source_path.parent:
        raise UpdateSafetyError("stage-not-on-canonical-filesystem", SAFE_STAGE_FAILURE)
    if os.path.lexists(stage_path):
        raise UpdateSafetyError("stage-identity-already-exists", SAFE_STAGE_FAILURE)
    descriptor, partial_name = tempfile.mkstemp(
        dir=stage_path.parent, prefix=f".{stage_path.name}.", suffix=PARTIAL_BACKUP_SUFFIX
    )
    os.close(descriptor)
    partial_path = Path(partial_name)
    try:
        _copy_sqlite_database(source_path, partial_path)
        _publish_without_replacing(partial_path, stage_path)
    except (BackupError, sqlite3.Error, OSError) as exc:
        raise UpdateSafetyError("stage-snapshot-failed", SAFE_STAGE_FAILURE) from exc
    finally:
        with contextlib.suppress(OSError):
            partial_path.unlink(missing_ok=True)


def _open_read_only(path: Path) -> sqlite3.Connection:
    try:
        return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5.0)
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise UpdateSafetyError("database-verification-open-failed", SAFE_VERIFICATION_FAILURE) from exc


def _verify_database(path: Path, expected_lineage: tuple[str, ...], *, category: str) -> None:
    connection = _open_read_only(path)
    try:
        quick_check = connection.execute("PRAGMA quick_check").fetchall()
        if quick_check != [("ok",)]:
            raise UpdateSafetyError(category, SAFE_VERIFICATION_FAILURE)
        lineage = inspect_migration_lineage(connection)
    except sqlite3.Error as exc:
        raise UpdateSafetyError(category, SAFE_VERIFICATION_FAILURE) from exc
    finally:
        connection.close()
    if not lineage.is_known_prefix or lineage.applied_ids != expected_lineage:
        raise UpdateSafetyError(category, SAFE_VERIFICATION_FAILURE)


def _verify_before_migration_backup(
    backup: BackupResult,
    paths: UserDataPaths,
    expected_lineage: tuple[str, ...],
) -> None:
    if backup.backup_path.parent != paths.backups_dir:
        raise UpdateSafetyError("backup-verification-failed", SAFE_BACKUP_FAILURE)
    generated = parse_generated_backup_filename(backup.backup_path.name)
    if generated is None or generated.reason != "before_migration":
        raise UpdateSafetyError("backup-verification-failed", SAFE_BACKUP_FAILURE)
    _verify_database(
        backup.backup_path,
        expected_lineage,
        category="backup-verification-failed",
    )


def _database_digest(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise UpdateSafetyError("canonical-identity-read-failed", SAFE_VERIFICATION_FAILURE) from exc
    return digest.hexdigest()


def _sqlite_sidecars(path: Path) -> tuple[Path, ...]:
    candidates = (
        path.parent / f"{path.name}-wal",
        path.parent / f"{path.name}-shm",
        path.parent / f"{path.name}-journal",
    )
    return tuple(candidate for candidate in candidates if os.path.lexists(candidate))


def _require_no_sqlite_sidecars(path: Path, *, category: str) -> None:
    if _sqlite_sidecars(path):
        raise UpdateSafetyError(category, SAFE_COMMIT_FAILURE)


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _replace_stage_file(stage_path: Path, canonical_path: Path) -> None:
    """The D4 database commit point. No call below this function can undo it."""
    try:
        os.replace(stage_path, canonical_path)
    except OSError as exc:
        raise UpdateSafetyError("database-commit-failed", SAFE_COMMIT_FAILURE) from exc


def _commit_verified_stage(stage_path: Path, canonical_path: Path) -> None:
    if stage_path.parent != canonical_path.parent:
        raise UpdateSafetyError("stage-not-on-canonical-filesystem", SAFE_COMMIT_FAILURE)
    _require_no_sqlite_sidecars(canonical_path, category="canonical-sidecar-present")
    _require_no_sqlite_sidecars(stage_path, category="stage-sidecar-present")
    try:
        _fsync_file(stage_path)
    except OSError as exc:
        raise UpdateSafetyError("stage-fsync-failed", SAFE_COMMIT_FAILURE) from exc
    _replace_stage_file(stage_path, canonical_path)
    # os.replace above is the commit point. A failure from here on is not a
    # migration failure; the next startup reconciles the canonical target lineage.
    try:
        _fsync_directory(canonical_path.parent)
    except OSError as exc:
        raise UpdatePostCommitError("database-directory-fsync-failed") from exc


def _failed_record(
    record: UpdateOperationRecord, category: str, safe_message: str
) -> UpdateOperationRecord:
    return replace(
        record,
        status="failed",
        finished_at=_utc_now(),
        failure_category=category,
        safe_failure_message=safe_message,
    )


def _completed_record(record: UpdateOperationRecord) -> UpdateOperationRecord:
    return replace(
        record,
        status="completed",
        finished_at=_utc_now(),
        failure_category=None,
        safe_failure_message=None,
    )


def reconcile_interrupted_update(
    paths: UserDataPaths,
    compatibility: StartupSchemaCompatibility,
) -> UpdateReconciliationResult:
    """Resolve one durable `started` record without resuming or retrying its stage."""
    journal_path = update_journal_path(paths)
    records = load_update_journal(journal_path)
    started = [record for record in records if record.status == "started"]
    if not started:
        return UpdateReconciliationResult()
    if len(started) != 1:
        raise UpdateSafetyError("multiple-interrupted-updates", SAFE_RECONCILIATION_FAILURE)

    record = started[0]
    _require_recorded_stage_ownership(paths.database_path, record)
    canonical_lineage = compatibility.applied_migration_ids
    if canonical_lineage == record.to_schema_identity:
        _verify_database(
            paths.database_path,
            record.to_schema_identity,
            category="interrupted-target-verification-failed",
        )
        _cleanup_owned_stage_artifacts(paths.database_path, record.operation_id)
        completed = _completed_record(record)
        _persist_operation(journal_path, records, completed)
        return UpdateReconciliationResult(operation=completed, reconciled_to_completed=True)

    if canonical_lineage == record.from_schema_identity:
        _verify_database(
            paths.database_path,
            record.from_schema_identity,
            category="interrupted-source-verification-failed",
        )
        _cleanup_owned_stage_artifacts(paths.database_path, record.operation_id)
        failed = _failed_record(
            record,
            "interrupted-before-commit",
            SAFE_INTERRUPTED_FAILURE,
        )
        _persist_operation(journal_path, records, failed)
        # Do not turn this same repeated launch into an automatic retry. A later
        # explicit launch may start a fresh fully guarded operation from the
        # still-authoritative source lineage.
        raise UpdateSafetyError("interrupted-before-commit", SAFE_INTERRUPTED_FAILURE)

    raise UpdateSafetyError("interrupted-update-ambiguous", SAFE_RECONCILIATION_FAILURE)


def execute_staged_update(
    config: DatabaseConfig,
    paths: UserDataPaths,
    app_version: str,
    compatibility: StartupSchemaCompatibility,
) -> StagedUpdateResult:
    if not compatibility.migrations_pending:
        raise ValueError("D4-B staged update requires a supported older schema.")
    if config.path != paths.database_path:
        raise ValueError("D4-B user update must target the canonical user database.")

    journal_path = update_journal_path(paths)
    records = load_update_journal(journal_path)
    if any(record.status == "started" for record in records):
        raise UpdateSafetyError("unreconciled-started-update", SAFE_RECONCILIATION_FAILURE)

    operation_id = uuid.uuid4().hex
    stage_path = _stage_path(config.path, operation_id)
    record = UpdateOperationRecord(
        operation_id=operation_id,
        # D4-B cannot prove the immediately previous package version. A prior
        # completed update only proves which app last *migrated* this database;
        # another package version may have run later without changing schema.
        # Keep the metadata explicitly unknown instead of fabricating identity
        # from prior journal entries or legacy mutable AppSettings.
        from_app_version=None,
        to_app_version=app_version,
        from_schema_identity=compatibility.applied_migration_ids,
        to_schema_identity=compatibility.target_migration_ids,
        before_migration_backup_identity=None,
        stage_identity=stage_path.name,
        started_at=_utc_now(),
        finished_at=None,
        status="started",
        failure_category=None,
        safe_failure_message=None,
    )
    _persist_operation(journal_path, records, record)

    backup: BackupResult | None = None
    stage_owned = False
    committed = False
    try:
        # A stale WAL/journal means the old package did not leave one closed main
        # database identity suitable for atomic one-file replacement. Refuse before
        # snapshot/migration rather than deleting evidence from the authoritative DB.
        _require_no_sqlite_sidecars(config.path, category="canonical-sidecar-present")
        source_digest = _database_digest(config.path)

        try:
            backup = backup_sqlite_database(
                source_path=config.path,
                backup_dir=paths.backups_dir,
                reason="before_migration",
            )
        except BackupError as exc:
            raise UpdateSafetyError("before-migration-backup-failed", SAFE_BACKUP_FAILURE) from exc
        _verify_before_migration_backup(backup, paths, compatibility.applied_migration_ids)
        record = replace(record, before_migration_backup_identity=backup.backup_path.name)
        _persist_operation(journal_path, records, record)

        _create_consistent_stage_snapshot(config.path, stage_path)
        stage_owned = True
        _verify_database(
            stage_path,
            compatibility.applied_migration_ids,
            category="stage-source-verification-failed",
        )

        expected_pending = list(
            compatibility.target_migration_ids[len(compatibility.applied_migration_ids) :]
        )
        try:
            applied = apply_migrations(DatabaseConfig(path=stage_path))
        except Exception as exc:  # migration code may raise domain/runtime errors, not only sqlite3.Error
            raise UpdateSafetyError("staged-migration-failed", SAFE_MIGRATION_FAILURE) from exc
        if applied != expected_pending:
            raise UpdateSafetyError("staged-migration-set-unexpected", SAFE_VERIFICATION_FAILURE)
        _verify_database(
            stage_path,
            compatibility.target_migration_ids,
            category="stage-target-verification-failed",
        )

        if _database_digest(config.path) != source_digest:
            raise UpdateSafetyError("canonical-changed-during-staging", SAFE_COMMIT_FAILURE)
        _commit_verified_stage(stage_path, config.path)
        committed = True
        _verify_database(
            config.path,
            compatibility.target_migration_ids,
            category="post-commit-verification-failed",
        )
        completed = _completed_record(record)
        try:
            _persist_operation(journal_path, records, completed)
        except UpdateJournalError as exc:
            raise UpdatePostCommitError("post-commit-journal-write-failed") from exc
        return StagedUpdateResult(
            operation=completed,
            backup=backup,
            applied_migrations=applied,
        )
    except UpdatePostCommitError:
        # The canonical DB is already the target. Leave `started` durable truth for
        # next-launch lineage reconciliation; never write the false word `failed`.
        raise
    except UpdateSafetyError as exc:
        if committed or exc.committed:
            raise UpdatePostCommitError(exc.category) from exc
        if stage_owned:
            _cleanup_owned_stage_artifacts(config.path, operation_id)
        failed = _failed_record(record, exc.category, exc.safe_message)
        _persist_operation(journal_path, records, failed)
        raise
    except Exception as exc:
        if committed:
            raise UpdatePostCommitError("post-commit-unexpected-failure") from exc
        if stage_owned:
            _cleanup_owned_stage_artifacts(config.path, operation_id)
        failed = _failed_record(record, "update-unexpected-failure", SAFE_MIGRATION_FAILURE)
        _persist_operation(journal_path, records, failed)
        raise UpdateSafetyError("update-unexpected-failure", SAFE_MIGRATION_FAILURE) from exc
