"""The working-database replacement boundary, and the journal safety it needs.

`CR-010` § 6. Two separate problems live here.

## 1. The target's SQLite sidecars

Replacing `cosmetic_workshop.sqlite` while a `-wal`, `-shm` or `-journal` file
survives beside it is not a replacement — it is a new main database with another
database's transaction state pointed at it. SQLite would then either apply WAL
frames that belong to the *old* file or roll back a hot journal over the *new*
one, and the result is corruption that every structural check would call `ok`.

The fix is SQLite's own lifecycle, not `unlink`. Opening the target and setting
`PRAGMA journal_mode = DELETE` checkpoints any WAL content into the main file and
removes `-wal`/`-shm` through SQLite itself; opening it at all also completes any
pending hot-journal rollback. After the connection closes, the sidecars must
actually be gone — and if any is still there, the launcher **stops** rather than
deleting a file it cannot account for. Blind unlinking is exactly the operation
that turns a recoverable state into a lost one.

This runs after `safety_copy_verified` and before `replacement_intent`: it is a
checkpoint against the working database, so the accepted contract forbids it
until candidate validation has passed and a verified recovery point exists.

## 2. The replacement itself

The working database is never replaced directly from the user-selected path, and
never from the staged candidate either — that file is preserved as recovery
evidence. A separate launcher-owned replacement artifact is created *in the
working database's own directory*, so the publication step can be
`os.replace`: one atomic same-filesystem rename.

The target is not accepted from untrusted input. It is the exact path the
launcher's startup preparation resolved, and `assert_replaceable_target` checks
that before anything is created, so no foreign path can be silently overwritten.
"""

from __future__ import annotations

from pathlib import Path
import contextlib
import os
import shutil
import sqlite3
import tempfile

from launcher.restore.workspace import OWNED_TEMP_PREFIX, OWNED_TEMP_SUFFIX

# The sidecars SQLite may keep beside a main database file.
TARGET_SIDECAR_SUFFIXES: tuple[str, ...] = ("-wal", "-shm", "-journal")

SQLITE_TIMEOUT_SECONDS = 5.0


class ReplacementTargetError(RuntimeError):
    """Raised when the replacement target is not the exact configured database."""


class JournalSafetyError(RuntimeError):
    """Raised when the target's SQLite journal state cannot be proved safe."""


class ReplacementError(RuntimeError):
    """Raised when the replacement artifact or the atomic boundary failed."""


def assert_replaceable_target(target: Path, configured_database_path: Path) -> Path:
    """Refuse any target that is not the exact configured application database.

    Compared by resolved path, and required to be an existing regular file that
    is not a symlink. A symlinked database path would make the atomic rename
    replace the *link*, quietly leaving the real database untouched while every
    subsequent check passed against the new file.
    """
    resolved_target = Path(target)
    if resolved_target != Path(configured_database_path):
        raise ReplacementTargetError(
            "Restore may only replace the exact configured application database."
        )
    if resolved_target.is_symlink():
        raise ReplacementTargetError("The configured application database path is a symlink.")
    if not resolved_target.is_file():
        raise ReplacementTargetError("The configured application database does not exist.")
    return resolved_target


def target_sidecar_paths(database_path: Path) -> list[Path]:
    """The exact owned sidecar paths for one database, by name.

    Exact paths only. Nothing here globs a directory or reasons about files it
    did not name, so an unrelated file can never be considered — let alone
    removed.
    """
    base = Path(database_path)
    return [base.with_name(base.name + suffix) for suffix in TARGET_SIDECAR_SUFFIXES]


def existing_target_sidecars(database_path: Path) -> list[Path]:
    return [path for path in target_sidecar_paths(database_path) if path.exists()]


def quiesce_target_journal(database_path: Path) -> None:
    """Bring the target to a state where no sidecar can be applied to its successor.

    Uses SQLite's supported lifecycle behaviour, in this exact order:

    1. **open the database.** This alone completes any pending hot-journal
       rollback, so an unclean previous shutdown is resolved by SQLite rather
       than reasoned about here.
    2. **`journal_mode = WAL`.** Switching *into* WAL is what removes a rollback
       journal through SQLite. Setting `DELETE` directly does not: a rolled-back
       hot journal is left on disk, which measurement confirmed, and the
       verification below would then refuse a database that is in fact fine.
    3. **`wal_checkpoint(TRUNCATE)`.** Every committed frame is written into the
       main database file. This is what makes the round trip lossless.
    4. **`journal_mode = DELETE`.** Leaving WAL removes `-wal` and `-shm`.
    5. **close.** The last handle this process holds is released.

    Then it **verifies**. If a sidecar still exists afterwards, something outside
    this launcher owns it — another process, or a state SQLite would not resolve —
    and the operation stops before the replacement boundary rather than deleting
    it. Committed data in a WAL is real user data, and unlinking the WAL would
    discard it.
    """
    resolved = Path(database_path)
    try:
        connection = sqlite3.connect(resolved, timeout=SQLITE_TIMEOUT_SECONDS)
    except sqlite3.Error as exc:
        raise JournalSafetyError(
            f"The working database could not be opened to settle its journal: {type(exc).__name__}"
        ) from exc
    try:
        connection.execute("PRAGMA journal_mode = WAL").fetchone()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        mode = connection.execute("PRAGMA journal_mode = DELETE").fetchone()
        if not mode or str(mode[0]).lower() != "delete":
            raise JournalSafetyError(
                "The working database would not leave WAL mode before replacement."
            )
        # A no-op on a clean database, and the thing that flushes any residual
        # page cache on one that is not.
        connection.commit()
    except sqlite3.Error as exc:
        raise JournalSafetyError(
            f"The working database journal could not be settled: {type(exc).__name__}"
        ) from exc
    finally:
        connection.close()

    remaining = existing_target_sidecars(resolved)
    if remaining:
        raise JournalSafetyError(
            "The working database still has SQLite sidecar files that cannot be handled safely."
        )


def prepare_replacement_artifact(content_path: Path, database_path: Path) -> Path:
    """Copy `content_path` into an exclusively-owned scratch file beside the target.

    `content_path` is always a **static** file — the validated staged candidate,
    or the verified safety copy — with no live connection and no sidecars. A
    byte copy is correct for those, and is not the case `CR-004` rejected: what
    that decision forbids is raw-copying a *live main database file*, which is
    never what happens here.

    Same directory as the target on purpose. The publication below has to be a
    same-filesystem rename, and a scratch file anywhere else could not be one.
    """
    target_dir = Path(database_path).parent
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        handle, scratch_name = tempfile.mkstemp(
            dir=target_dir, prefix=OWNED_TEMP_PREFIX, suffix=OWNED_TEMP_SUFFIX
        )
    except OSError as exc:
        raise ReplacementError(
            f"The replacement artifact could not be created: {type(exc).__name__}"
        ) from exc

    scratch_path = Path(scratch_name)
    try:
        with open(content_path, "rb") as reader, os.fdopen(handle, "wb", closefd=True) as writer:
            shutil.copyfileobj(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
    except OSError as exc:
        discard_replacement_artifact(scratch_path)
        raise ReplacementError(
            f"The replacement artifact could not be written: {type(exc).__name__}"
        ) from exc
    return scratch_path


def commit_replacement(replacement_artifact: Path, target: Path) -> None:
    """The atomic replacement boundary: one same-filesystem rename.

    Nothing between the caller's durable `replacement_intent` and this call, and
    nothing between this call and the caller's durable `replacement_committed`.
    That is the whole ambiguous window, and it is deliberately as short as one
    syscall.
    """
    try:
        os.replace(replacement_artifact, target)
    except OSError as exc:
        raise ReplacementError(
            f"The working database could not be replaced: {type(exc).__name__}"
        ) from exc


def discard_replacement_artifact(replacement_artifact: Path) -> None:
    """Remove a replacement artifact this launcher created, and only that.

    Called when the boundary was never entered. After a successful
    `commit_replacement` the scratch path no longer exists, so this can never
    remove the replaced database.
    """
    name = Path(replacement_artifact).name
    if not name.startswith(OWNED_TEMP_PREFIX) or not name.endswith(OWNED_TEMP_SUFFIX):
        return
    with contextlib.suppress(OSError):
        Path(replacement_artifact).unlink(missing_ok=True)
