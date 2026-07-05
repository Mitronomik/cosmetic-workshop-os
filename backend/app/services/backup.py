from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import shutil

import os

from app.db.config import get_database_config
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths


class BackupError(RuntimeError):
    """Raised when a database backup cannot be created safely."""


class BackupSourceMissingError(BackupError):
    """Raised when the SQLite database file selected for backup is missing."""


@dataclass(frozen=True)
class BackupResult:
    source_path: Path
    backup_path: Path
    created_at: datetime
    reason: str
    size_bytes: int


SQLITE_BACKUP_SUFFIXES = {".sqlite", ".db", ".sqlite3"}


@dataclass(frozen=True)
class BackupPaths:
    database_path: Path
    backup_dir: Path


@dataclass(frozen=True)
class BackupFileMetadata:
    filename: str
    path: Path
    created_at: datetime | None
    reason: str | None
    size_bytes: int


def _safe_filename_part(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value.strip()
    )
    return cleaned.strip("_") or "backup"


def _backup_filename(
    source_path: Path, created_at: datetime, reason: str, suffix: int | None = None
) -> str:
    timestamp = created_at.strftime("%Y%m%dT%H%M%S%fZ")
    reason_part = _safe_filename_part(reason)
    stem_part = _safe_filename_part(source_path.stem)
    suffix_part = f"-{suffix}" if suffix is not None else ""
    return f"{timestamp}-{stem_part}-{reason_part}{suffix_part}{source_path.suffix or '.sqlite'}"


def _unique_backup_path(
    backup_dir: Path, source_path: Path, created_at: datetime, reason: str
) -> Path:
    candidate = backup_dir / _backup_filename(source_path, created_at, reason)
    if not candidate.exists():
        return candidate
    suffix = 1
    while True:
        candidate = backup_dir / _backup_filename(source_path, created_at, reason, suffix)
        if not candidate.exists():
            return candidate
        suffix += 1


def backup_sqlite_database(source_path: Path, backup_dir: Path, reason: str = "manual") -> BackupResult:
    """Copy an existing SQLite database file into the explicit backup directory.

    The operation never modifies the source database and never overwrites an
    existing backup file. The backup directory is created only when this
    function is called.
    """
    resolved_source = Path(source_path)
    resolved_backup_dir = Path(backup_dir)

    if not resolved_source.exists():
        raise BackupSourceMissingError(f"SQLite database file does not exist: {resolved_source}")
    if not resolved_source.is_file():
        raise BackupError(f"SQLite database path is not a file: {resolved_source}")

    created_at = datetime.now(UTC)
    resolved_backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = _unique_backup_path(resolved_backup_dir, resolved_source, created_at, reason)

    try:
        shutil.copy2(resolved_source, backup_path)
    except OSError as exc:
        raise BackupError(f"Could not create SQLite database backup at {backup_path}: {exc}") from exc

    return BackupResult(
        source_path=resolved_source,
        backup_path=backup_path,
        created_at=created_at,
        reason=reason,
        size_bytes=backup_path.stat().st_size,
    )


def normalize_backup_reason(reason: str | None) -> str:
    text = (reason or "manual").strip()
    return text or "manual"


def resolve_backup_paths() -> BackupPaths:
    """Resolve the current SQLite database and safe backup directory.

    In user-data mode, backups live in the resolved user backup directory. In
    development mode, backups stay next to the configured database to avoid
    accidentally writing to the real Documents directory. This function only
    computes paths; it does not create files or directories.
    """
    database_path = get_database_config().path
    user_paths = resolve_user_data_paths()
    user_data_dir_explicit = bool(os.environ.get(USER_DATA_DIR_ENV))
    if database_path == user_paths.database_path or user_data_dir_explicit:
        backup_dir = user_paths.backups_dir
    else:
        backup_dir = database_path.parent / "backups"
    return BackupPaths(database_path=database_path, backup_dir=backup_dir)


def _parse_backup_created_at(filename: str) -> datetime | None:
    timestamp_part = filename.split("-", 1)[0]
    try:
        return datetime.strptime(timestamp_part, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def _parse_backup_reason(path: Path) -> str | None:
    stem_parts = path.stem.split("-")
    if len(stem_parts) < 3:
        return None
    reason_part = stem_parts[-1]
    if reason_part.isdigit() and len(stem_parts) >= 4:
        reason_part = stem_parts[-2]
    return reason_part or None


def _backup_file_metadata(path: Path) -> BackupFileMetadata:
    created_at = _parse_backup_created_at(path.name)
    if created_at is None:
        try:
            created_at = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        except OSError:
            created_at = None
    return BackupFileMetadata(
        filename=path.name,
        path=path,
        created_at=created_at,
        reason=_parse_backup_reason(path),
        size_bytes=path.stat().st_size,
    )


def list_backup_files(backup_dir: Path) -> list[BackupFileMetadata]:
    """List SQLite-like backup files newest first without creating directories."""
    resolved_backup_dir = Path(backup_dir)
    if not resolved_backup_dir.exists() or not resolved_backup_dir.is_dir():
        return []
    backups: list[BackupFileMetadata] = []
    for candidate in resolved_backup_dir.iterdir():
        if not candidate.is_file() or candidate.suffix.lower() not in SQLITE_BACKUP_SUFFIXES:
            continue
        try:
            backups.append(_backup_file_metadata(candidate))
        except OSError:
            continue
    return sorted(
        backups,
        key=lambda item: (item.created_at or datetime.min.replace(tzinfo=UTC), item.filename),
        reverse=True,
    )
