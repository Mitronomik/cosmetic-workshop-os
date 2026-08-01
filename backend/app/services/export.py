from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
import json
import os
import sqlite3
from typing import Any

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.services.local_artifact_filenames import (
    normalize_artifact_reason,
    normalize_artifact_reason_segment,
)


class ExportError(RuntimeError):
    """Raised when a JSON export cannot be created safely."""


class ExportSourceMissingError(ExportError):
    """Raised when the SQLite database selected for export is missing."""


EXPORT_SCHEMA_VERSION = 1
SUPPORTED_EXPORT_SCHEMA_VERSIONS: frozenset[int] = frozenset({EXPORT_SCHEMA_VERSION})
EXPORT_SOURCE = "cosmetic-workshop-os"
EXPORT_FILE_SUFFIX = ".json"
# The structural middle of the export filename grammar:
# `{timestamp}-cosmetic_workshop-export-{canonical_reason}[-N].json`.
EXPORT_FILENAME_MARKER = "-cosmetic_workshop-export-"
# The one timestamp spelling the generator emits and the strict parser accepts.
EXPORT_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S%fZ"
EXPORT_PAYLOAD_KEYS: frozenset[str] = frozenset({"manifest", "data"})
EXPORT_TABLES = (
    "app_settings",
    "ingredients",
    "ingredient_lots",
    "stock_movements",
    "packaging_items",
    "packaging_stock_movements",
    "catalog_categories",
    "catalog_tags",
    "ingredient_catalog_tags",
    "packaging_item_catalog_tags",
    "recipe_template_catalog_tags",
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
    """Return the human export reason preserved in the export manifest."""
    return normalize_artifact_reason(reason)


def _database_location_kind(database_path: Path) -> str:
    user_paths = resolve_user_data_paths()
    user_data_dir_explicit = bool(os.environ.get(USER_DATA_DIR_ENV))
    if database_path == user_paths.database_path or user_data_dir_explicit:
        return "user_data"
    return "development"


def resolve_export_dir(config: "DatabaseConfig | None" = None) -> Path:
    """The safe export directory for one database configuration.

    Startup reconciliation runs before the API and holds its own
    `DatabaseConfig`, so it must be able to resolve the same directory the API
    will use without depending on process-wide configuration lookup. This is the
    one algorithm both paths share.
    """
    database_path = (config or get_database_config()).path
    user_paths = resolve_user_data_paths()
    if database_path == user_paths.database_path or os.environ.get(USER_DATA_DIR_ENV):
        return user_paths.exports_dir
    return database_path.parent / "exports"


def resolve_export_paths() -> ExportPaths:
    """Resolve the current SQLite database and safe export directory.

    This function only computes paths. It does not create files, directories,
    databases, backups, migrations, or exports.
    """
    config = get_database_config()
    return ExportPaths(database_path=config.path, export_dir=resolve_export_dir(config))


def _export_filename(created_at: datetime, reason: str, suffix: int | None = None) -> str:
    timestamp = created_at.strftime(EXPORT_TIMESTAMP_FORMAT)
    reason_part = normalize_artifact_reason_segment(reason)
    suffix_part = f"-{suffix}" if suffix is not None else ""
    return f"{timestamp}{EXPORT_FILENAME_MARKER}{reason_part}{suffix_part}{EXPORT_FILE_SUFFIX}"


@dataclass(frozen=True)
class GeneratedExportFilename:
    """The three fields a generated export filename encodes, once proven valid."""

    created_at: datetime
    reason: str
    suffix: int | None


def parse_generated_export_filename(name: str) -> GeneratedExportFilename | None:
    """Strictly parse a filename **this application's generator could have produced**.

    Returns `None` for anything else. This is the exact-grammar boundary the
    CR-009 ledger and the export writer both need: a name that merely *looks*
    export-shaped — right marker, right extension, a reason that happens to
    parse — is not proof that this application generated it, and the ledger must
    never audit an artifact on that basis.

    The check that does the real work is the final one: the parsed fields are
    fed back through `_export_filename`, the single generation algorithm, and
    the result must equal the original name byte for byte. That is why this
    function cannot drift from the generator, and why it needs no separate
    description of the grammar. Everything before it exists to extract
    candidate fields safely, or to reject input `strptime` and `int` would
    otherwise accept too liberally.

    Deliberately **not** applied to `list_export_files`. That listing stays
    best-effort so legacy exports written before this contract keep appearing in
    `GET /api/exports` and `GET /api/exports/status`; CR-005 accepted exactly
    that, and tightening it here would make old files silently vanish from the
    user's history.
    """
    if not isinstance(name, str) or not name or Path(name).name != name:
        return None
    if not name.endswith(EXPORT_FILE_SUFFIX):
        return None
    stem = name[: -len(EXPORT_FILE_SUFFIX)]
    timestamp_part, marker, remainder = stem.partition(EXPORT_FILENAME_MARKER)
    if not marker or not timestamp_part or not remainder:
        return None

    try:
        created_at = datetime.strptime(timestamp_part, EXPORT_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None

    reason_part = remainder
    suffix: int | None = None
    head, separator, tail = remainder.rpartition("-")
    if separator and _is_ascii_digits(tail):
        # `int()` accepts Unicode digits, surrounding whitespace and a sign, so
        # the ASCII-only test comes first; the round trip below then rejects any
        # spelling the generator would not produce, such as a leading zero.
        reason_part, suffix = head, int(tail)

    if not reason_part or reason_part.isdigit():
        return None
    if normalize_artifact_reason_segment(reason_part) != reason_part:
        return None

    if _export_filename(created_at, reason_part, suffix) != name:
        return None
    return GeneratedExportFilename(created_at=created_at, reason=reason_part, suffix=suffix)


def is_generated_export_filename(name: str) -> bool:
    """Whether `name` is exactly a filename this application's generator produces."""
    return parse_generated_export_filename(name) is not None


def _is_ascii_digits(value: str) -> bool:
    return bool(value) and all("0" <= character <= "9" for character in value)


def reserve_export_path(
    export_dir: Path,
    created_at: datetime,
    reason: str,
    *,
    is_identity_active: "Callable[[str], bool] | None" = None,
) -> Path:
    """Choose the one exact final export path, and choose it exactly once.

    This is the *only* filename-selection algorithm for JSON exports. CR-009
    requires the exact final filename to be committed to the ledger before the
    export is written, and CR-006 requires the create response to describe the
    exact file the creator produced. Both break the moment two places can pick a
    name, so `create_json_export` accepts the reserved path rather than
    re-deriving one of its own.

    An identity is free only when no file already occupies it *and* no active
    ledger operation already owns it. A `prepared` operation owns its filename
    before that file exists, so file existence alone cannot tell whether a
    candidate is free. The numeric suffix advances exactly as before, so
    generated filenames stay byte-compatible with every export created so far.
    """
    suffix: int | None = None
    while True:
        candidate = export_dir / _export_filename(created_at, reason, suffix)
        if not candidate.exists() and not (is_identity_active and is_identity_active(candidate.name)):
            return candidate
        suffix = 1 if suffix is None else suffix + 1


def _parse_export_created_at(filename: str) -> datetime | None:
    timestamp_part = filename.split("-", 1)[0]
    try:
        return datetime.strptime(timestamp_part, EXPORT_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None


def parse_export_reason(path: Path) -> str | None:
    """The canonical filename-derived API reason, with the uniqueness suffix stripped.

    CR-005 makes this value — not the human manifest reason — the `reason` the
    create, list and status responses report, and ADR 0014 requires all three to
    derive it through this one function so the same file can never report two
    different reasons.
    """
    marker = EXPORT_FILENAME_MARKER
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
        reason=parse_export_reason(path),
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


def require_exportable_source(database_path: Path) -> None:
    """Raise the existing source errors when the database cannot be exported.

    Extracted so the audited create path can check this precondition *before* it
    reserves a filename or commits a ledger row. A missing source database must
    still return the existing `404`, and it must not leave a prepared operation
    or create a database file behind on its way there.
    """
    resolved = Path(database_path)
    if not resolved.exists():
        raise ExportSourceMissingError(f"SQLite database file does not exist: {resolved}")
    if not resolved.is_file():
        raise ExportError(f"SQLite database path is not a file: {resolved}")


def _validate_reserved_export_path(export_dir: Path, reserved_export_path: Path) -> Path:
    """Accept a caller-reserved path only when it is exactly one this writer could have chosen.

    The reservation comes from `reserve_export_path`, but the writer must not
    take that on trust: a reserved path is the identity a ledger row was already
    committed against, so a mismatched one would silently write the export
    somewhere reconciliation can never find it.
    """
    candidate = Path(reserved_export_path)
    if candidate.parent.resolve(strict=False) != export_dir.resolve(strict=False):
        raise ExportError("Reserved export path is not inside the configured export directory.")
    if not is_generated_export_filename(candidate.name):
        # The full grammar, verified by round-tripping through the generator —
        # not merely the marker and the extension. A name this writer could not
        # have produced is not a name the ledger can later reconcile.
        raise ExportError("Reserved export filename does not match the accepted export filename grammar.")
    if candidate.exists():
        raise ExportError("Reserved export path already exists; exports are never overwritten.")
    return candidate


def create_json_export(
    database_path: Path,
    export_dir: Path,
    reason: str = "manual",
    *,
    reserved_export_path: Path | None = None,
) -> ExportResult:
    """Create an explicit local JSON export snapshot.

    The operation reads the configured SQLite database, writes only a new JSON
    file under export_dir, and never overwrites existing export files.

    When `reserved_export_path` is supplied, the export is written to exactly
    that path and no other. The audited create path reserves the name before it
    commits its ledger row, and a writer that quietly chose a different name
    would leave a durable row pointing at a file that does not exist.
    """
    resolved_database_path = Path(database_path)
    resolved_export_dir = Path(export_dir)
    normalized_reason = normalize_export_reason(reason)

    require_exportable_source(resolved_database_path)

    # A reserved path already encodes the moment the reservation was made. Taking
    # `created_at` from it rather than from a second `now()` keeps the filename
    # timestamp, the manifest timestamp and the reported timestamp identical, so
    # the create response and every later listing describe the same instant.
    reserved_created_at = (
        _parse_export_created_at(Path(reserved_export_path).name) if reserved_export_path is not None else None
    )
    created_at = reserved_created_at or datetime.now(UTC)
    data, entity_counts = _read_whitelisted_data(resolved_database_path)
    payload = {
        "manifest": {
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "reason": normalized_reason,
            "source": EXPORT_SOURCE,
            "database_filename": resolved_database_path.name,
            "database_location_kind": _database_location_kind(resolved_database_path),
            "tables": entity_counts,
        },
        "data": data,
    }

    resolved_export_dir.mkdir(parents=True, exist_ok=True)
    if reserved_export_path is None:
        export_path = reserve_export_path(resolved_export_dir, created_at, normalized_reason)
    else:
        export_path = _validate_reserved_export_path(resolved_export_dir, reserved_export_path)
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
