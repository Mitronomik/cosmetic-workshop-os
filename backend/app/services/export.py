from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
import json
import os
import sqlite3
from typing import Any

from app.db.config import get_database_config
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths


class ExportError(RuntimeError):
    """Raised when a JSON export cannot be created safely."""


class ExportSourceMissingError(ExportError):
    """Raised when the SQLite database selected for export is missing."""


EXPORT_SCHEMA_VERSION = 1
EXPORT_SOURCE = "cosmetic-workshop-os"
EXPORT_FILE_SUFFIX = ".json"
EXPORT_TABLES = (
    "app_settings",
    "ingredients",
    "ingredient_lots",
    "stock_movements",
    "packaging_items",
    "packaging_stock_movements",
    "recipe_templates",
    "recipe_versions",
    "recipe_ingredients",
    "clients",
    "client_recipes",
    "client_recipe_ingredients",
    "client_wishes",
    "client_feedback",
    "orders",
    "production_batches",
    "production_batch_ingredients",
    "production_batch_packaging",
    "alerts",
    "purchase_suggestions",
    "audit_logs",
)


@dataclass(frozen=True)
class ExportPaths:
    database_path: Path
    export_dir: Path


@dataclass(frozen=True)
class ExportFile:
    filename: str
    path: Path
    created_at: datetime | None
    reason: str | None
    size_bytes: int


@dataclass(frozen=True)
class ExportResult:
    export_path: Path
    created_at: datetime
    reason: str
    size_bytes: int
    entity_counts: dict[str, int]


def normalize_export_reason(reason: str | None) -> str:
    text = (reason or "manual").strip()
    return text or "manual"


def _safe_filename_part(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value.strip()
    )
    return cleaned.strip("_") or "manual"


def resolve_export_paths() -> ExportPaths:
    """Resolve the current SQLite database and safe export directory.

    This function only computes paths. It does not create files, directories,
    databases, backups, migrations, or exports.
    """
    database_path = get_database_config().path
    user_paths = resolve_user_data_paths()
    user_data_dir_explicit = bool(os.environ.get(USER_DATA_DIR_ENV))
    if database_path == user_paths.database_path or user_data_dir_explicit:
        export_dir = user_paths.exports_dir
    else:
        export_dir = database_path.parent / "exports"
    return ExportPaths(database_path=database_path, export_dir=export_dir)


def _export_filename(created_at: datetime, reason: str, suffix: int | None = None) -> str:
    timestamp = created_at.strftime("%Y%m%dT%H%M%S%fZ")
    reason_part = _safe_filename_part(reason)
    suffix_part = f"-{suffix}" if suffix is not None else ""
    return f"{timestamp}-cosmetic_workshop-export-{reason_part}{suffix_part}.json"


def _unique_export_path(export_dir: Path, created_at: datetime, reason: str) -> Path:
    candidate = export_dir / _export_filename(created_at, reason)
    if not candidate.exists():
        return candidate
    suffix = 1
    while True:
        candidate = export_dir / _export_filename(created_at, reason, suffix)
        if not candidate.exists():
            return candidate
        suffix += 1


def _parse_export_created_at(filename: str) -> datetime | None:
    timestamp_part = filename.split("-", 1)[0]
    try:
        return datetime.strptime(timestamp_part, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def _parse_export_reason(path: Path) -> str | None:
    marker = "-cosmetic_workshop-export-"
    stem = path.stem
    if marker not in stem:
        return None
    reason_part = stem.split(marker, 1)[1]
    parts = reason_part.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        reason_part = parts[0]
    return reason_part or None


def _export_file_metadata(path: Path) -> ExportFile:
    created_at = _parse_export_created_at(path.name)
    if created_at is None:
        try:
            created_at = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        except OSError:
            created_at = None
    return ExportFile(
        filename=path.name,
        path=path,
        created_at=created_at,
        reason=_parse_export_reason(path),
        size_bytes=path.stat().st_size,
    )


def list_export_files(export_dir: Path) -> list[ExportFile]:
    """List JSON export files newest first without creating directories."""
    resolved_export_dir = Path(export_dir)
    if not resolved_export_dir.exists() or not resolved_export_dir.is_dir():
        return []
    exports: list[ExportFile] = []
    for candidate in resolved_export_dir.iterdir():
        if not candidate.is_file() or candidate.suffix.lower() != EXPORT_FILE_SUFFIX:
            continue
        try:
            exports.append(_export_file_metadata(candidate))
        except OSError:
            continue
    return sorted(
        exports,
        key=lambda item: (item.created_at or datetime.min.replace(tzinfo=UTC), item.filename),
        reverse=True,
    )


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _read_whitelisted_data(database_path: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    data: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}
    uri = f"file:{database_path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        for table_name in EXPORT_TABLES:
            if not _table_exists(connection, table_name):
                continue
            rows = connection.execute(f'SELECT * FROM "{table_name}" ORDER BY rowid').fetchall()
            table_rows = [dict(row) for row in rows]
            data[table_name] = table_rows
            counts[table_name] = len(table_rows)
    finally:
        connection.close()
    return data, counts


def create_json_export(database_path: Path, export_dir: Path, reason: str = "manual") -> ExportResult:
    """Create an explicit local JSON export snapshot.

    The operation reads the configured SQLite database, writes only a new JSON
    file under export_dir, and never overwrites existing export files.
    """
    resolved_database_path = Path(database_path)
    resolved_export_dir = Path(export_dir)
    normalized_reason = normalize_export_reason(reason)

    if not resolved_database_path.exists():
        raise ExportSourceMissingError(f"SQLite database file does not exist: {resolved_database_path}")
    if not resolved_database_path.is_file():
        raise ExportError(f"SQLite database path is not a file: {resolved_database_path}")

    created_at = datetime.now(UTC)
    data, entity_counts = _read_whitelisted_data(resolved_database_path)
    payload = {
        "manifest": {
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "reason": normalized_reason,
            "source": EXPORT_SOURCE,
            "database_path": str(resolved_database_path),
            "tables": entity_counts,
        },
        "data": data,
    }

    resolved_export_dir.mkdir(parents=True, exist_ok=True)
    export_path = _unique_export_path(resolved_export_dir, created_at, normalized_reason)
    try:
        export_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ExportError(f"Could not create JSON export at {export_path}: {exc}") from exc

    return ExportResult(
        export_path=export_path,
        created_at=created_at,
        reason=normalized_reason,
        size_bytes=export_path.stat().st_size,
        entity_counts=entity_counts,
    )
