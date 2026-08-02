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

from launcher.restore.durability import (
    DurabilityError,
    PublicationCategory,
    PublicationStage,
    flush_file,
    publish_atomically,
)
from launcher.restore.workspace import is_launcher_operation_id

# The sidecars SQLite may keep beside a main database file.
TARGET_SIDECAR_SUFFIXES: tuple[str, ...] = ("-wal", "-shm", "-journal")

# The replacement artifact's name is **deterministic**, derived from the
# operation ID, rather than random. A random `mkstemp` name is unrecoverable
# after a crash: startup recovery would have to glob the database directory to
# find it, and globbing for things to delete beside a user's database is exactly
# the kind of cleanup this engine refuses to do. With a derived name, recovery
# can name the one artifact it owns and touch nothing else.
REPLACEMENT_ARTIFACT_PREFIX = ".cwos-restore-"
REPLACEMENT_ARTIFACT_SUFFIX = ".replacement"

SQLITE_TIMEOUT_SECONDS = 5.0


class ReplacementTargetError(RuntimeError):
    """Raised when the replacement target is not the exact configured database."""


class JournalSafetyError(RuntimeError):
    """Raised when the target's SQLite journal state cannot be proved safe."""


class ReplacementError(RuntimeError):
    """Raised when the replacement artifact or the atomic boundary failed.

    `may_have_replaced` is the field that decides recovery. It is true when the
    rename may already have landed — either because `os.replace` itself failed
    ambiguously, or because it succeeded and only its durability could not be
    proved. Both demand the same conservative response: treat the working
    database as potentially replaced and roll back.
    """

    def __init__(self, message: str, *, may_have_replaced: bool = False) -> None:
        super().__init__(message)
        self.may_have_replaced = may_have_replaced


def assert_replaceable_target(target: Path, context) -> Path:
    """Refuse any target that is not the exact canonical application database.

    The comparison value is **re-derived from the launcher's own startup
    resolver**, not read back off the context. Comparing a caller-supplied value
    with a copy of itself — which an earlier version of this function did — is
    not a check at all: it passes for every path in the filesystem.

    `startup_database_config` only computes a path and creates nothing, so this
    independent derivation is free of side effects and is the same resolution
    ordinary startup will perform later, which is what makes it authoritative.

    The target must also be an existing regular file that is not a symlink. A
    symlinked database path would make the atomic rename replace the *link*,
    quietly leaving the real database untouched while every subsequent check
    passed against the new file.
    """
    from app.services.startup import startup_database_config

    resolved_target = Path(target)
    canonical = Path(startup_database_config(context.mode).path)
    if resolved_target != canonical:
        raise ReplacementTargetError(
            "Restore may only replace the exact canonical application database."
        )
    if resolved_target.is_symlink():
        raise ReplacementTargetError("The canonical application database path is a symlink.")
    if not resolved_target.is_file():
        raise ReplacementTargetError("The canonical application database does not exist.")
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


def replacement_artifact_path(database_path: Path, operation_id: str) -> Path:
    """The one deterministic replacement-artifact path for an operation.

    Derived from the operation ID rather than randomly generated, so startup
    recovery can name the exact file this operation may have left behind. That is
    what makes cleanup possible **without** globbing the directory that holds the
    user's database — the engine never scans for files to delete, it computes the
    single path it owns and touches only that.
    """
    if not is_launcher_operation_id(operation_id):
        raise ReplacementError("Replacement artifacts require a launcher-generated operation ID.")
    base = Path(database_path)
    return base.with_name(f"{REPLACEMENT_ARTIFACT_PREFIX}{operation_id}{REPLACEMENT_ARTIFACT_SUFFIX}")


def prepare_replacement_artifact(
    content_path: Path, database_path: Path, operation_id: str
) -> Path:
    """Copy `content_path` into the exclusively-created artifact beside the target.

    `content_path` is always a **static** file — the validated staged candidate,
    or the verified safety copy — with no live connection and no sidecars. A
    byte copy is correct for those, and is not the case `CR-004` rejected: what
    that decision forbids is raw-copying a *live main database file*, which is
    never what happens here.

    `O_CREAT | O_EXCL` is the ownership proof: the returned path is one this call
    definitely created, so the cleanup below can never remove a foreign file. A
    leftover artifact from an interrupted earlier attempt under the *same*
    operation ID is removed first — it is provably this operation's own, and
    nothing else can hold that name.

    Same directory as the target on purpose. The publication below has to be a
    same-filesystem rename, and an artifact anywhere else could not be one.
    """
    artifact = replacement_artifact_path(database_path, operation_id)
    try:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        # Provably ours by name: only this operation ID maps here. Removing a
        # leftover makes the exclusive create below deterministic on retry.
        with contextlib.suppress(FileNotFoundError):
            artifact.unlink()
        handle = os.open(artifact, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as exc:
        raise ReplacementError(
            f"The replacement artifact could not be created: {type(exc).__name__}"
        ) from exc

    try:
        with open(content_path, "rb") as reader, os.fdopen(handle, "wb", closefd=True) as writer:
            shutil.copyfileobj(reader, writer)
            writer.flush()
            flush_file(writer.fileno(), category=PublicationCategory.REPLACEMENT_ARTIFACT)
    except OSError as exc:
        discard_replacement_artifact(artifact)
        raise ReplacementError(
            f"The replacement artifact could not be written: {type(exc).__name__}"
        ) from exc
    return artifact


def commit_replacement(
    replacement_artifact: Path,
    target: Path,
    *,
    category: PublicationCategory = PublicationCategory.WORKING_DATABASE_REPLACEMENT,
) -> None:
    """The atomic replacement boundary, made durable.

    Nothing between the caller's durable `replacement_intent` and this call, and
    nothing between this call and the caller's durable `replacement_committed`.
    That is the whole ambiguous window, and it is deliberately as short as the
    shared publication primitive allows.

    The **durability** of the rename is part of the boundary, not an afterthought.
    A rename that is visible but not durable can revert across a host
    interruption while the operation record does not, and the launcher would then
    recover a database it has no accurate record of. So a post-rename flush
    failure is raised with `may_have_replaced=True`, and the caller rolls back
    exactly as it would for an ambiguous rename.
    """
    try:
        publish_atomically(Path(replacement_artifact), Path(target), category=category)
    except DurabilityError as exc:
        raise ReplacementError(
            f"The working database replacement could not be completed: {exc.stage.value}",
            # `DURING_REPLACE` is ambiguous and `AFTER_REPLACE` is certain; both
            # mean the target may now hold the replacement.
            may_have_replaced=exc.stage is not PublicationStage.BEFORE_REPLACE,
        ) from exc


def discard_replacement_artifact(replacement_artifact: Path) -> None:
    """Remove a replacement artifact this launcher created, and only that.

    Guarded by the exact derived name, so an arbitrary path handed in by mistake
    is ignored rather than unlinked. After a successful `commit_replacement` the
    artifact path no longer exists, so this can never remove the replaced
    database.
    """
    name = Path(replacement_artifact).name
    if not name.startswith(REPLACEMENT_ARTIFACT_PREFIX) or not name.endswith(
        REPLACEMENT_ARTIFACT_SUFFIX
    ):
        return
    with contextlib.suppress(OSError):
        Path(replacement_artifact).unlink(missing_ok=True)


def discard_owned_replacement_artifact(database_path: Path, operation_id: str) -> None:
    """Remove the one artifact an operation may have left beside the database.

    Used by startup recovery on the non-destructive paths. It computes the single
    owned path and removes only that — no directory listing, no pattern match, no
    chance of touching a file this launcher did not create.
    """
    try:
        artifact = replacement_artifact_path(database_path, operation_id)
    except ReplacementError:
        return
    discard_replacement_artifact(artifact)
