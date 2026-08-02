"""Source-path intake and the staged read-only candidate.

`CR-010` § 1 and § 3: the user-selected file is **immutable input**. It is opened
read-only, copied once into the launcher-owned operation directory, and never
renamed, deleted, migrated, rewritten, chmod-ed, truncated or opened writable —
on any path, including rollback and `recovery_blocked`.

Everything downstream validates the *staged copy*, never the original. That is
not a convenience: validating the user's own file in place would mean the
validator holds a handle on a file it must be unable to change, and on a
removable volume it would mean the candidate can vanish between validation and
replacement.

The stage copy is published completely before `source_staged` is persisted, so an
interrupted copy can never become a valid staged candidate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import contextlib
import os
import shutil
import tempfile

from launcher.restore.workspace import (
    OWNED_TEMP_PREFIX,
    OWNED_TEMP_SUFFIX,
    STAGED_CANDIDATE_FILENAME,
    RestoreWorkspace,
)

# The SQLite suffixes an application backup can carry. The accepted backup
# contract generates exactly these, and `CR-010` § 1 refuses JSON exports, CSV,
# XLSX and report documents — a suffix check is the cheapest place to say so,
# long before anything is copied.
ACCEPTED_SOURCE_SUFFIXES: frozenset[str] = frozenset({".sqlite", ".db", ".sqlite3"})

SourceRejection = Literal[
    "source-missing",
    "source-not-local-path",
    "source-is-directory",
    "source-is-symlink",
    "source-not-regular-file",
    "source-unsupported-suffix",
    "source-empty",
    "source-unreadable",
    "source-is-working-database",
]


class SourceRejectedError(RuntimeError):
    """Raised when the selected source cannot be accepted as a Restore source.

    Carries the internal reason code for local technical logs. The user-facing
    text is chosen from the fixed category vocabulary in `contracts`, never from
    this message.
    """

    def __init__(self, rejection: SourceRejection) -> None:
        super().__init__(f"Restore source rejected: {rejection}")
        self.rejection: SourceRejection = rejection


class StagingError(RuntimeError):
    """Raised when the staged candidate could not be established."""


@dataclass(frozen=True)
class AcceptedSource:
    """One accepted local source path, with the facts intake established.

    `size_bytes` is what the disk-space preflight sizes its artifacts from, and
    it is read here — before anything is created — so the preflight never has to
    stat the source a second time on a volume that may be slow or disconnecting.
    """

    path: Path
    size_bytes: int


def _is_same_file(left: Path, right: Path) -> bool:
    """Whether two paths are the same file, by identity rather than spelling.

    `os.path.samefile` compares device and inode, so a hard link, a relative
    spelling and a symlink alias to the working database are all caught by one
    check. A textual comparison would catch none of them.
    """
    try:
        return os.path.samefile(left, right)
    except OSError:
        return False


def accept_source_path(selected_source: object, database_path: Path) -> AcceptedSource:
    """Validate the selected source before anything destructive can be confirmed.

    Every rejection here happens before staging, before the safety copy and
    therefore long before the working database can change. The order is
    deliberate: identity and type checks come before any read, so an unreadable
    device node or a directory is refused without this process opening it.
    """
    if not isinstance(selected_source, (str, Path)):
        # A URL, a stream, a remote handle or anything else that is not a local
        # path. `CR-010` § 1 authorizes a locally selected file and nothing else.
        raise SourceRejectedError("source-not-local-path")
    source = Path(selected_source)
    if not source.is_absolute():
        # A relative path resolves against whatever the launcher's working
        # directory happens to be, which is not a property of the user's choice.
        raise SourceRejectedError("source-not-local-path")

    if source.is_symlink():
        # Checked before `exists()`, which follows the link: a symlink pointing
        # at a perfectly valid backup is still not an accepted source, because
        # the thing that stays byte-identical afterwards must be the file the
        # user actually selected.
        raise SourceRejectedError("source-is-symlink")
    if not source.exists():
        raise SourceRejectedError("source-missing")
    if source.is_dir():
        raise SourceRejectedError("source-is-directory")
    if not source.is_file():
        raise SourceRejectedError("source-not-regular-file")
    if source.suffix.lower() not in ACCEPTED_SOURCE_SUFFIXES:
        raise SourceRejectedError("source-unsupported-suffix")

    if _is_same_file(source, database_path):
        # Restoring the working database over itself is not a no-op: it would
        # mean replacing the target with a copy of itself while a safety copy and
        # a replacement artifact were being built from it. Refused outright.
        raise SourceRejectedError("source-is-working-database")

    try:
        size_bytes = source.stat().st_size
    except OSError as exc:
        raise SourceRejectedError("source-unreadable") from exc
    if size_bytes == 0:
        # A zero-byte file is a *valid empty SQLite database* and passes
        # `quick_check`. CR-004 produced exactly that from an aborted copy.
        raise SourceRejectedError("source-empty")

    try:
        # The one read intake performs, and it proves the property that matters:
        # this process can open the file read-only. Opened and closed here so a
        # source that cannot be read safely is refused before any artifact
        # exists, rather than halfway through a copy.
        with open(source, "rb") as probe:
            probe.read(1)
    except OSError as exc:
        raise SourceRejectedError("source-unreadable") from exc

    return AcceptedSource(path=source, size_bytes=size_bytes)


def stage_source(
    workspace: RestoreWorkspace, operation_id: str, source: AcceptedSource
) -> Path:
    """Copy the accepted source into this operation's isolated directory.

    Publication, not a plain copy. The bytes go into an exclusively-created
    scratch file inside the operation directory and are moved onto
    `candidate.sqlite` with `os.replace` only once the copy has completed. An
    interruption therefore leaves an orphan scratch file that nothing recognizes
    as a candidate — never a truncated `candidate.sqlite` that later validation
    might partially accept.

    The source is opened `"rb"`. `shutil.copyfileobj` never opens the
    destination-side semantics onto it, and no metadata is copied back: this is
    deliberately not `shutil.copy2`, which would touch the source's access time
    handling and implies a symmetry Restore must not have.
    """
    operation_dir = workspace.operation_dir(operation_id)
    if not operation_dir.is_dir():
        raise StagingError("The isolated Restore operation directory does not exist.")

    handle, scratch_name = tempfile.mkstemp(
        dir=operation_dir, prefix=OWNED_TEMP_PREFIX, suffix=OWNED_TEMP_SUFFIX
    )
    scratch_path = Path(scratch_name)
    published = False
    try:
        with open(source.path, "rb") as reader, os.fdopen(handle, "wb", closefd=True) as writer:
            shutil.copyfileobj(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
        staged_path = operation_dir / STAGED_CANDIDATE_FILENAME
        os.replace(scratch_path, staged_path)
        published = True
    except OSError as exc:
        raise StagingError(
            f"The selected backup could not be staged: {type(exc).__name__}"
        ) from exc
    finally:
        if not published:
            with contextlib.suppress(OSError):
                scratch_path.unlink(missing_ok=True)
    return staged_path
