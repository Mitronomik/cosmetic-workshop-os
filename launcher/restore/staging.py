"""Source-path intake and the staged read-only candidate.

`CR-010` § 1 and § 3: the user-selected file is **immutable input**. It is opened
read-only, copied once into the launcher-owned operation directory, and never
renamed, deleted, migrated, rewritten, chmod-ed, truncated or opened writable —
on any path, including rollback and `recovery_blocked`.

Two properties do the real work here, and both were missing from a naive
implementation.

## 1. Sidecars are checked beside the *original selected source*

Staging copies the main SQLite file and nothing else. So a selected source that
still has a `-wal` beside it is a database whose committed rows live in a file
this engine will not copy:

```text
source.sqlite                  (main file, missing the newest commits)
source.sqlite-wal              (committed rows, never staged)
→ copy only source.sqlite
→ the staged candidate has no sidecar to notice
→ PRAGMA quick_check returns ok
→ Restore silently installs stale data
```

Checking beside the *staged candidate* cannot catch this — by construction the
staged copy is alone in a directory this launcher just created. The check has to
happen against the original path, and it happens **twice**: once before the copy
begins, and again after the copy completes and before `candidate.sqlite` is
published. A sidecar that appears mid-copy is a source being written to, which is
not a backup artifact.

The accepted `C4-I` source is a **self-contained backup**. Converting a live WAL
database into one is a different operation with a different safety contract, and
this slice deliberately does not do it.

## 2. The copy reads a held descriptor, not a re-opened path

Intake opens the source once with `O_RDONLY | O_NOFOLLOW` and keeps that
descriptor for the whole of staging. Everything afterwards reads *that*
descriptor rather than re-opening the path, so a path swapped between validation
and copy cannot substitute different bytes. Identity is re-proved from the
descriptor with `fstat` — same device, inode, size and mode — and the path is
re-checked with `lstat` to prove it still resolves to the same file and has not
become a symlink.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Literal
import contextlib
import os
import stat
import tempfile

from launcher.restore.durability import DurabilityError, flush_file, publish_atomically
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

# The exact adjacent paths that would make a selected source non-self-contained.
SOURCE_SIDECAR_SUFFIXES: tuple[str, ...] = ("-wal", "-shm", "-journal")

# `O_NOFOLLOW` refuses to open the final component if it is a symlink. Absent on
# some platforms; the explicit `lstat` check below covers the same ground, so the
# fallback is a plain open rather than a refusal to run.
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)

COPY_CHUNK_BYTES = 1024 * 1024

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
    "source-has-wal-sidecar",
    "source-has-shm-sidecar",
    "source-has-journal-sidecar",
    "source-identity-changed",
]

# The rejections that mean "this file is not a self-contained snapshot". Grouped
# so the user-facing category and the tests can name the class rather than each
# suffix.
SIDECAR_REJECTIONS: frozenset[str] = frozenset(
    {"source-has-wal-sidecar", "source-has-shm-sidecar", "source-has-journal-sidecar"}
)

_SIDECAR_REJECTION_BY_SUFFIX: dict[str, SourceRejection] = {
    "-wal": "source-has-wal-sidecar",
    "-shm": "source-has-shm-sidecar",
    "-journal": "source-has-journal-sidecar",
}


class SourceRejectedError(RuntimeError):
    """Raised when the selected source cannot be accepted as a Restore source.

    Carries the internal reason code for local technical logs. The user-facing
    text is chosen from the fixed category vocabulary in `contracts`, never from
    this message.
    """

    def __init__(self, rejection: SourceRejection) -> None:
        super().__init__(f"Restore source rejected: {rejection}")
        self.rejection: SourceRejection = rejection

    @property
    def is_sidecar_dependency(self) -> bool:
        return self.rejection in SIDECAR_REJECTIONS


class StagingError(RuntimeError):
    """Raised when the staged candidate could not be established."""


@dataclass(frozen=True)
class SourceIdentity:
    """The stat facts that must not change while the source is being staged."""

    st_dev: int
    st_ino: int
    st_size: int
    st_mode: int

    @classmethod
    def from_stat(cls, info: os.stat_result) -> "SourceIdentity":
        return cls(
            st_dev=info.st_dev,
            st_ino=info.st_ino,
            st_size=info.st_size,
            st_mode=stat.S_IFMT(info.st_mode),
        )


def _assert_no_sidecars(source: Path) -> None:
    """Refuse a selected source that is not self-contained.

    `os.path.lexists`, not `exists`: a *symlinked* `-wal` beside the source is
    still a sidecar, and `exists` would miss a dangling one entirely.
    """
    for suffix in SOURCE_SIDECAR_SUFFIXES:
        if os.path.lexists(str(source) + suffix):
            raise SourceRejectedError(_SIDECAR_REJECTION_BY_SUFFIX[suffix])


class HeldSource:
    """One selected source, held open read-only for the whole of staging.

    The descriptor is the identity. Reads come from it rather than from the path,
    and `revalidate()` proves — from the descriptor *and* from the path — that
    nothing was substituted while the copy was running.
    """

    def __init__(self, path: Path, fd: int, identity: SourceIdentity) -> None:
        self.path = path
        self.fd = fd
        self.identity = identity

    @property
    def size_bytes(self) -> int:
        return self.identity.st_size

    def revalidate(self) -> None:
        """Prove the source is still the same regular file it was at intake.

        Two independent checks, because they catch different attacks:

        `fstat(fd)` follows the open file itself, so it notices content that was
        rewritten or truncated underneath a still-valid descriptor.

        `lstat(path)` follows nothing, so it notices the path being replaced by a
        different file or by a symlink — a swap the descriptor alone cannot see,
        because it keeps pointing at the original inode.
        """
        try:
            current = SourceIdentity.from_stat(os.fstat(self.fd))
        except OSError as exc:
            raise SourceRejectedError("source-unreadable") from exc
        if current != self.identity:
            raise SourceRejectedError("source-identity-changed")

        try:
            on_path = os.lstat(self.path)
        except OSError as exc:
            raise SourceRejectedError("source-identity-changed") from exc
        if stat.S_ISLNK(on_path.st_mode):
            raise SourceRejectedError("source-identity-changed")
        if (on_path.st_dev, on_path.st_ino) != (self.identity.st_dev, self.identity.st_ino):
            raise SourceRejectedError("source-identity-changed")

    def assert_still_self_contained(self) -> None:
        _assert_no_sidecars(self.path)

    def close(self) -> None:
        with contextlib.suppress(OSError):
            os.close(self.fd)

    def __enter__(self) -> "HeldSource":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _is_same_file(identity: SourceIdentity, other: Path) -> bool:
    """Whether the held source and `other` are the same file, by identity.

    Device and inode, so a hard link, a relative spelling and a symlink alias to
    the working database are all caught by one check. A textual comparison would
    catch none of them.
    """
    try:
        info = os.stat(other)
    except OSError:
        return False
    return (info.st_dev, info.st_ino) == (identity.st_dev, identity.st_ino)


def open_selected_source(selected_source: object, database_path: Path) -> HeldSource:
    """Validate and open the selected source, returning a held descriptor.

    Every rejection here happens before staging, before the safety copy and
    therefore long before the working database can change. The caller **owns the
    returned descriptor** and must close it.

    Order is deliberate: cheap type and identity checks first, then the sidecar
    check, then the open. Nothing is opened until the file has been shown to be a
    plausible self-contained backup.
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

    try:
        link_info = os.lstat(source)
    except FileNotFoundError as exc:
        raise SourceRejectedError("source-missing") from exc
    except OSError as exc:
        raise SourceRejectedError("source-unreadable") from exc

    if stat.S_ISLNK(link_info.st_mode):
        # Checked with `lstat`, which does not follow: a symlink pointing at a
        # perfectly valid backup is still not an accepted source, because the
        # thing that stays byte-identical afterwards must be the file the user
        # actually selected.
        raise SourceRejectedError("source-is-symlink")
    if stat.S_ISDIR(link_info.st_mode):
        raise SourceRejectedError("source-is-directory")
    if not stat.S_ISREG(link_info.st_mode):
        raise SourceRejectedError("source-not-regular-file")
    if source.suffix.lower() not in ACCEPTED_SOURCE_SUFFIXES:
        raise SourceRejectedError("source-unsupported-suffix")

    # The first of two sidecar checks, before anything is opened or copied.
    _assert_no_sidecars(source)

    try:
        fd = os.open(source, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise SourceRejectedError("source-unreadable") from exc

    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise SourceRejectedError("source-not-regular-file")
        identity = SourceIdentity.from_stat(info)
        if identity.st_size == 0:
            # A zero-byte file is a *valid empty SQLite database* and passes
            # `quick_check`. CR-004 produced exactly that from an aborted copy.
            raise SourceRejectedError("source-empty")
        if _is_same_file(identity, Path(database_path)):
            # Restoring the working database over itself is not a no-op: it would
            # mean replacing the target with a copy of itself while a safety copy
            # and a replacement artifact were being built from it.
            raise SourceRejectedError("source-is-working-database")
        # The one read intake performs, proving this descriptor is readable
        # before any artifact exists rather than halfway through a copy.
        os.pread(fd, 1, 0)
    except SourceRejectedError:
        os.close(fd)
        raise
    except OSError as exc:
        os.close(fd)
        raise SourceRejectedError("source-unreadable") from exc

    return HeldSource(path=source, fd=fd, identity=identity)


def stage_source(workspace: RestoreWorkspace, operation_id: str, held: HeldSource) -> Path:
    """Copy the held source into this operation's isolated directory.

    Publication, not a plain copy. The bytes go into an exclusively-created
    scratch file inside the operation directory and are moved onto
    `candidate.sqlite` through the shared durability primitive only once the copy
    has completed **and** the source has re-proved its identity and
    self-containment. An interruption therefore leaves an orphan scratch file
    that nothing recognizes as a candidate — never a truncated `candidate.sqlite`
    that later validation might partially accept.

    Reads come from the held descriptor. The path is never re-opened, so a swap
    between validation and copy cannot substitute different bytes.
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
        copied = 0
        with os.fdopen(handle, "wb", closefd=True) as writer:
            offset = 0
            while True:
                chunk = os.pread(held.fd, COPY_CHUNK_BYTES, offset)
                if not chunk:
                    break
                writer.write(chunk)
                offset += len(chunk)
                copied += len(chunk)
            writer.flush()
            flush_file(writer.fileno())

        # Everything below runs *before* `candidate.sqlite` exists, so a failure
        # here can never leave a usable staged candidate.
        if copied != held.size_bytes:
            raise SourceRejectedError("source-identity-changed")
        held.revalidate()
        # The second sidecar check. A `-wal` that appeared during the copy means
        # the source was being written to, which is not a backup artifact.
        held.assert_still_self_contained()

        publish_atomically(scratch_path, operation_dir / STAGED_CANDIDATE_FILENAME)
        published = True
    except SourceRejectedError:
        raise
    except DurabilityError as exc:
        raise StagingError(
            f"The staged candidate could not be published: {exc.stage.value}"
        ) from exc
    except OSError as exc:
        raise StagingError(
            f"The selected backup could not be staged: {type(exc).__name__}"
        ) from exc
    finally:
        if not published:
            with contextlib.suppress(OSError):
                scratch_path.unlink(missing_ok=True)
    return operation_dir / STAGED_CANDIDATE_FILENAME
