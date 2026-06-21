from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import shutil


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
