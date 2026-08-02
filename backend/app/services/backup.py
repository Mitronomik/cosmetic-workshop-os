"""Transactionally consistent SQLite backups, and the backup filename grammar.

Durable contract:
``docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md`` (CR-004),
``docs/backup-and-restore.md`` and ``docs/backend-baseline-failure-triage.md``
§ 18.

The copy is performed by the SQLite Online Backup API through
:meth:`sqlite3.Connection.backup`, never by copying the database file with
``shutil``. CR-004 proved that a raw copy of the live main database file is not
a backup of the committed source state:

- in WAL mode every committed but uncheckpointed row is silently missing from a
  file that still passes ``PRAGMA quick_check``;
- in rollback-journal mode a copy taken while a large transaction is in flight
  mixes two transaction states in one file — including rows from a transaction
  that was subsequently rolled back and therefore never existed — and can fail
  ``quick_check`` outright.

Both were reproduced with the stock page cache and no PRAGMA tuning. A
structurally valid SQLite file is not the same thing as a transactionally
consistent snapshot, and only the second is a backup.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import contextlib
import sqlite3
import tempfile

import os

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.services.local_artifact_filenames import (
    normalize_artifact_reason,
    normalize_artifact_reason_segment,
)


class BackupError(RuntimeError):
    """Raised when a database backup cannot be created safely."""


class BackupSourceMissingError(BackupError):
    """Raised when the SQLite database file selected for backup is missing."""


class BackupBusyError(BackupError):
    """Raised when the source database stayed locked for the whole bounded wait.

    This is the bound itself. CPython's :meth:`sqlite3.Connection.backup` retries
    ``sqlite3_backup_step`` for as long as it reports ``SQLITE_BUSY`` or
    ``SQLITE_LOCKED``, and the source connection's own busy timeout does **not**
    end that loop — CR-004 observed the plain call still running after the source
    had been locked for well beyond any acceptable request. Refusing the first
    busy status is what turns an unbounded invisible retry into one bounded wait.
    """


@dataclass(frozen=True)
class BackupResult:
    source_path: Path
    backup_path: Path
    created_at: datetime
    reason: str
    size_bytes: int


SQLITE_BACKUP_SUFFIXES = {".sqlite", ".db", ".sqlite3"}
DEFAULT_BACKUP_SUFFIX = ".sqlite"

# Deliberately not an accepted SQLite backup suffix: an interrupted operation
# must leave something `list_backup_files` ignores, never a listable backup.
PARTIAL_BACKUP_SUFFIX = ".partial"

# The one timestamp spelling the generator emits and the strict parser accepts.
BACKUP_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S%fZ"

# The bounded wait for a locked source, in seconds. This is the repository's
# existing implicit convention rather than a new knob: `sqlite3.connect` already
# defaults to `timeout=5.0`, which `app.db.connection.connect` accepts unchanged
# for every other database access in the application.
BACKUP_BUSY_TIMEOUT_SECONDS = 5.0

# The `sqlite3.SQLITE_*` names exist from Python 3.11. The literals are the
# stable documented SQLite result codes and keep this module working on an older
# interpreter without a version check at every call site.
_SQLITE_BUSY = getattr(sqlite3, "SQLITE_BUSY", 5)
_SQLITE_LOCKED = getattr(sqlite3, "SQLITE_LOCKED", 6)


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


def _safe_source_stem_part(value: str) -> str:
    """Sanitize the source database stem.

    This is deliberately separate from the canonical reason segment: a source
    database stem may legitimately keep hyphens.
    """
    cleaned = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value.strip()
    )
    return cleaned.strip("_") or "backup"


def _backup_filename(
    source_path: Path, created_at: datetime, reason: str, suffix: int | None = None
) -> str:
    timestamp = created_at.strftime(BACKUP_TIMESTAMP_FORMAT)
    reason_part = normalize_artifact_reason_segment(reason)
    stem_part = _safe_source_stem_part(source_path.stem)
    suffix_part = f"-{suffix}" if suffix is not None else ""
    return f"{timestamp}-{stem_part}-{reason_part}{suffix_part}{source_path.suffix or DEFAULT_BACKUP_SUFFIX}"


@dataclass(frozen=True)
class GeneratedBackupFilename:
    """The four fields a generated backup filename encodes, once proven valid."""

    created_at: datetime
    source_stem: str
    reason: str
    suffix: int | None
    extension: str


def _is_ascii_digits(value: str) -> bool:
    return bool(value) and all("0" <= character <= "9" for character in value)


def parse_generated_backup_filename(name: str) -> GeneratedBackupFilename | None:
    """Strictly parse a filename **this application's generator could have produced**.

    Returns `None` for anything else. This is the exact-grammar boundary the
    CR-009 ledger needs: a name that merely looks backup-shaped, or a valid
    SQLite database that happens to sit at the right path, is not proof that this
    application generated it, and the ledger must never audit an artifact on that
    basis.

    The grammar is

    ```text
    {timestamp}-{safe_source_stem}-{canonical_reason}[-N].{sqlite_suffix}
    ```

    where the source stem may itself contain hyphens, the canonical reason may
    not (CR-005), and `-N` is a uniqueness suffix only. The fields are therefore
    peeled off the right-hand end: the optional all-digit suffix first, then the
    hyphen-free reason, leaving the stem.

    The check that does the real work is the last one: the parsed fields are fed
    back through `_backup_filename`, the single generation algorithm, and the
    result must equal the original name byte for byte. That is why this function
    cannot drift from the generator, and why a leading-zero suffix, a
    non-canonical reason or an unsanitized stem is rejected without a rule of its
    own.

    Deliberately **not** applied to `list_backup_files`. That listing stays
    best-effort so backups written before this contract keep appearing in
    `GET /api/backups` and `GET /api/backups/status`; CR-005 accepted exactly
    that, and tightening it here would make old files silently vanish from the
    user's history.
    """
    if not isinstance(name, str) or not name or Path(name).name != name:
        return None
    extension = Path(name).suffix
    if extension not in SQLITE_BACKUP_SUFFIXES:
        return None

    stem = name[: -len(extension)]
    timestamp_part, separator, remainder = stem.partition("-")
    if not separator or not timestamp_part or not remainder:
        return None
    try:
        created_at = datetime.strptime(timestamp_part, BACKUP_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None

    suffix: int | None = None
    head, separator, tail = remainder.rpartition("-")
    if separator and _is_ascii_digits(tail):
        # `int()` accepts Unicode digits, surrounding whitespace and a sign, so
        # the ASCII-only test comes first; the round trip below then rejects any
        # spelling the generator would not produce, such as a leading zero.
        remainder, suffix = head, int(tail)

    source_stem, separator, reason_part = remainder.rpartition("-")
    if not separator or not source_stem or not reason_part:
        return None
    if reason_part.isdigit():
        return None
    if normalize_artifact_reason_segment(reason_part) != reason_part:
        return None

    if _backup_filename(Path(f"{source_stem}{extension}"), created_at, reason_part, suffix) != name:
        return None
    return GeneratedBackupFilename(
        created_at=created_at,
        source_stem=source_stem,
        reason=reason_part,
        suffix=suffix,
        extension=extension,
    )


def is_generated_backup_filename(name: str) -> bool:
    """Whether `name` is exactly a filename this application's generator produces."""
    return parse_generated_backup_filename(name) is not None


def canonical_backup_reason(path: Path) -> str | None:
    """The canonical filename-derived reason of a *generated* backup filename.

    Used for the create response, which by construction describes a filename this
    generator just produced. `None` for anything the strict grammar rejects, so a
    caller can never quietly report a reason it did not actually parse.
    """
    generated = parse_generated_backup_filename(Path(path).name)
    return generated.reason if generated is not None else None


def reserve_backup_path(
    backup_dir: Path,
    source_path: Path,
    created_at: datetime,
    reason: str,
    *,
    is_identity_active: Callable[[str], bool] | None = None,
) -> Path:
    """Choose the one exact final backup path, and choose it exactly once.

    This is the *only* filename-selection algorithm for backups. CR-009 requires
    the exact final filename to be committed to the ledger before the backup is
    written, and the create response must describe the exact file the engine
    produced. Both break the moment two places can pick a name, so
    `backup_sqlite_database` accepts the reserved path rather than re-deriving
    one of its own.

    An identity is free only when no file already occupies it *and* no active
    ledger operation already owns it. A `prepared` operation owns its filename
    before that file exists, so file existence alone cannot tell whether a
    candidate is free. The numeric suffix advances exactly as before, so
    generated filenames stay byte-compatible with every backup created so far.
    """
    suffix: int | None = None
    while True:
        candidate = backup_dir / _backup_filename(source_path, created_at, reason, suffix)
        if not candidate.exists() and not (is_identity_active and is_identity_active(candidate.name)):
            return candidate
        suffix = 1 if suffix is None else suffix + 1


def require_backupable_source(source_path: Path) -> Path:
    """Raise the existing source errors when the database cannot be backed up.

    Checked before any destination artifact is created, so a missing or unusable
    source still returns its existing `404`/`409` and leaves no file, no
    directory and no prepared ledger operation behind on its way there.
    """
    resolved = Path(source_path)
    if not resolved.exists():
        raise BackupSourceMissingError(f"SQLite database file does not exist: {resolved}")
    if not resolved.is_file():
        raise BackupError(f"SQLite database path is not a file: {resolved}")
    return resolved


def _copy_sqlite_database(source_path: Path, destination_path: Path) -> None:
    """Copy committed source state into a new database through SQLite itself.

    `pages=-1` copies the whole database in a **single** backup step, so SQLite
    holds one read lock for the entire copy and the destination can only ever be
    one committed point of the source — never a mixture of two, and never a
    partially applied transaction.

    The progress callback is the bound, and it bounds exactly one thing. Each
    individual step is already limited by the source connection's busy timeout,
    but CPython retries the step for as long as it reports `SQLITE_BUSY` or
    `SQLITE_LOCKED`, which is the unbounded loop CR-004 measured. Refusing those
    two statuses means exactly one attempt: one busy wait, then a truthful
    failure.

    Only those two. Every other unsuccessful status is a real error rather than
    contention — a source that is not a database, an I/O failure, a full disk —
    and CPython already ends the loop and raises it. Swallowing those here would
    relabel a genuine fault as "the database was busy", which is both untrue and
    the harder problem to diagnose.
    """

    def refuse_retry(status: int, remaining: int, total: int) -> None:
        if status in (_SQLITE_BUSY, _SQLITE_LOCKED):
            raise BackupBusyError(
                "The workshop database stayed busy for the whole bounded wait, "
                "so no consistent snapshot could be taken."
            )

    source_connection = sqlite3.connect(
        f"file:{source_path}?mode=ro", uri=True, timeout=BACKUP_BUSY_TIMEOUT_SECONDS
    )
    try:
        destination_connection = sqlite3.connect(
            destination_path, timeout=BACKUP_BUSY_TIMEOUT_SECONDS
        )
        try:
            source_connection.backup(destination_connection, pages=-1, progress=refuse_retry)
        finally:
            # Closing the destination is what finalizes it. It happens before
            # success is reported, so a returned backup is always a completed
            # file rather than one still owned by an open connection.
            destination_connection.close()
    finally:
        source_connection.close()


def _create_owned_partial(backup_dir: Path, final_name: str) -> Path:
    """Create an exclusively-owned scratch file in the destination directory.

    `mkstemp` creates with `O_CREAT | O_EXCL`, so the returned path is one this
    process definitely created and definitely owns. That is what makes the
    cleanup below safe: it can never unlink a file some other process put there.

    The scratch suffix is deliberately **not** an accepted SQLite backup suffix,
    so an interrupted operation leaves something `list_backup_files` ignores.
    A crash therefore cannot leave a misleading, successful-looking backup — the
    final name does not exist until the snapshot is complete.

    Same directory on purpose: publication below must stay within one filesystem.
    """
    handle, partial = tempfile.mkstemp(
        dir=backup_dir, prefix=f".{final_name}.", suffix=PARTIAL_BACKUP_SUFFIX
    )
    os.close(handle)
    return Path(partial)


def _publish_without_replacing(partial_path: Path, backup_path: Path) -> None:
    """Move a completed snapshot onto its final name, or fail without touching it.

    `os.link` is the whole point. It is atomic and it **refuses** when the target
    exists, which `os.rename` does not: rename would silently replace whatever is
    already there. `exists()` followed by an open is not an ownership guarantee
    either — another process can create the file in between — so the no-replace
    decision has to be made by the same syscall that publishes.

    On `FileExistsError` the foreign file is left exactly as it was; the caller
    removes only the scratch file it created itself.
    """
    try:
        os.link(partial_path, backup_path)
    except FileExistsError as exc:
        raise BackupError(
            f"Backup destination already exists: {backup_path.name}"
        ) from exc
    except OSError as exc:
        raise BackupError(
            f"Could not publish the backup {backup_path.name}: {type(exc).__name__}"
        ) from exc


def backup_sqlite_database(
    source_path: Path,
    backup_dir: Path,
    reason: str = "manual",
    *,
    reserved_backup_path: Path | None = None,
) -> BackupResult:
    """Write one transactionally consistent snapshot of the source database.

    The snapshot contains only committed data, never part of one SQLite
    transaction, and opens independently without the source WAL or rollback
    journal. It is not required to be byte-identical to the source file, and the
    source's own business data is never modified.

    **Publication is the artifact commit point.** The snapshot is written into an
    exclusively created scratch file, every fallible engine-owned read is taken
    from that scratch file, and only then is it published onto the reserved name
    atomically. Once publication succeeds this function cannot fail, so a
    completed backup is never reported to the user as a failure.

    `reserved_backup_path` is the exact final path an audited manual backup
    already committed to the CR-009 ledger. Without it — the automatic
    `before_migration` startup backup — the same single filename-selection
    algorithm picks a free name here instead.

    Never overwrites an existing backup. The backup directory is created only
    when this function is called.
    """
    resolved_source = require_backupable_source(source_path)
    resolved_backup_dir = Path(backup_dir)

    if reserved_backup_path is None:
        created_at = datetime.now(UTC)
        resolved_backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = reserve_backup_path(
            resolved_backup_dir, resolved_source, created_at, reason
        )
    else:
        backup_path, generated = _validate_reserved_backup_path(
            resolved_backup_dir, reserved_backup_path
        )
        # The reserved filename is authoritative about when this backup was
        # created: the ledger row, the artifact name and the create response must
        # all agree, and re-reading the clock here would make them disagree.
        created_at = generated.created_at
        resolved_backup_dir.mkdir(parents=True, exist_ok=True)

    if backup_path == resolved_source:
        raise BackupError("A backup cannot be written over its own source database.")
    # An early courtesy check only. It is deliberately **not** the no-overwrite
    # guarantee: another process can create the file between this call and the
    # publication below, so the guarantee has to come from the publishing syscall
    # itself. A filesystem failure while merely asking becomes a `BackupError`
    # rather than escaping raw, because nothing has been created yet.
    try:
        if backup_path.exists():
            raise BackupError(f"Backup destination already exists: {backup_path.name}")
    except OSError as exc:
        raise BackupError(
            f"Could not check the backup destination {backup_path.name}: {type(exc).__name__}"
        ) from exc

    # Write into a file this process exclusively created, then publish it onto
    # the reserved name with no-replace semantics. Everything the engine may
    # delete on failure is the scratch file it made itself, so cleanup can never
    # touch a foreign file — and the reserved name never exists in a half-written
    # state, so a crash cannot leave a misleading successful-looking backup.
    partial_path = _create_owned_partial(resolved_backup_dir, backup_path.name)
    try:
        _copy_sqlite_database(resolved_source, partial_path)
        # Every fallible engine-owned read happens *before* publication. Reading
        # the size afterwards would mean a `stat` failure could turn a completed,
        # published backup into a reported failure — a false total failure that
        # invites the user to make a second copy of the same thing, which is the
        # exact class of defect removing the create-response directory re-list
        # was meant to end.
        #
        # The two paths are hard links to one inode once publication succeeds, so
        # this size describes the published content exactly.
        size_bytes = partial_path.stat().st_size
        # Publication is the commit point. Nothing below it may fail.
        _publish_without_replacing(partial_path, backup_path)
    except (BackupError, sqlite3.Error, OSError) as exc:
        if isinstance(exc, BackupError):
            raise
        raise BackupError(
            f"Could not create SQLite database backup {backup_path.name}: {type(exc).__name__}"
        ) from exc
    finally:
        # Only ever the scratch file. After a successful publication the final
        # name is a second link to the same content, so removing this one leaves
        # the published backup intact.
        with contextlib.suppress(OSError):
            partial_path.unlink(missing_ok=True)

    return BackupResult(
        source_path=resolved_source,
        backup_path=backup_path,
        created_at=created_at,
        reason=reason,
        size_bytes=size_bytes,
    )


def _validate_reserved_backup_path(
    backup_dir: Path, reserved_backup_path: Path
) -> tuple[Path, GeneratedBackupFilename]:
    """Accept a caller-reserved path only when this engine could have chosen it.

    The reservation comes from `reserve_backup_path`, but the engine must not
    take an arbitrary path on trust: it is about to create a file there.
    """
    candidate = Path(reserved_backup_path)
    if candidate.parent != backup_dir:
        raise BackupError("Reserved backup path is not inside the configured backup directory.")
    generated = parse_generated_backup_filename(candidate.name)
    if generated is None:
        raise BackupError("Reserved backup path is not a valid generated backup filename.")
    return candidate, generated


def normalize_backup_reason(reason: str | None) -> str:
    """Return the human backup reason kept for display and request handling."""
    return normalize_artifact_reason(reason)


def resolve_backup_dir(config: "DatabaseConfig | None" = None) -> Path:
    """The safe backup directory for one database configuration.

    In user-data mode, backups live in the resolved user backup directory. In
    development mode, backups stay next to the configured database to avoid
    accidentally writing to the real Documents directory.

    Startup reconciliation runs before the API and holds its own
    `DatabaseConfig`, so it must be able to resolve the same directory the API
    will use without depending on process-wide configuration lookup. This is the
    one algorithm both paths share. It only computes a path and creates nothing.
    """
    database_path = (config or get_database_config()).path
    user_paths = resolve_user_data_paths()
    user_data_dir_explicit = bool(os.environ.get(USER_DATA_DIR_ENV))
    if database_path == user_paths.database_path or user_data_dir_explicit:
        return user_paths.backups_dir
    return database_path.parent / "backups"


def resolve_backup_paths() -> BackupPaths:
    """Resolve the current SQLite database and safe backup directory.

    This function only computes paths; it does not create files or directories.
    """
    config = get_database_config()
    return BackupPaths(database_path=config.path, backup_dir=resolve_backup_dir(config))


def _parse_backup_created_at(filename: str) -> datetime | None:
    timestamp_part = filename.split("-", 1)[0]
    try:
        return datetime.strptime(timestamp_part, BACKUP_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
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
