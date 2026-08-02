"""The one safety-critical filesystem publication primitive.

Every durable Restore publication goes through here: the operation record, the
staged candidate, the replacement artifact, the working-database replacement and
the rollback replacement. One implementation means one set of guarantees to
reason about, and one place where those guarantees are honest.

## The primitive

```text
exclusive scratch creation (O_CREAT | O_EXCL)
→ complete write
→ flush the userspace buffer
→ flush the file to durable media          (F_FULLFSYNC on macOS, else fsync)
→ atomic same-directory os.replace          <- the publication boundary
→ flush the published target
→ flush the parent directory                <- MANDATORY, not best effort
```

## Why the parent-directory flush is mandatory

`os.replace` makes the new content *visible* atomically. It does not make the
**rename itself** durable: after a host interruption the directory entry can
revert to the old one. For an ordinary file that is a lost update. For this
engine it is a correctness failure of a specific and dangerous shape — the
working database could come back replaced while the operation record reverted to
a phase that says nothing was replaced, and startup recovery would then take the
`aborted` branch over a database that is not the one it thinks it is.

So a directory-flush failure is never swallowed. It is reported with the stage it
happened at, and the caller decides using the rule that the stage implies.

## Failure stages, and what each one means

`BEFORE_REPLACE`
    Nothing was published. The previous state is intact and the caller may treat
    the operation as not having happened.

`DURING_REPLACE`
    `os.replace` itself failed. Ambiguous by construction — treated exactly like
    a completed replacement, because the safe direction is to assume it may have
    landed.

`AFTER_REPLACE`
    The rename returned successfully; only its durability is unproven. The new
    content **is** visible right now. A caller that persists state must re-read
    the authoritative record rather than assume either value, and a caller that
    replaced a database must treat it as potentially committed and roll back.

## What is and is not claimed

On macOS, `F_FULLFSYNC` asks the drive to flush its own write cache, which is
the strongest flush the platform offers; plain `fsync` on macOS does not. Where
`F_FULLFSYNC` is unsupported by the filesystem the code falls back to `fsync`
and **records that it did**, so no stronger guarantee is claimed than the call
that actually ran. On Linux `fsync` is used directly.

Directories are flushed with `fsync` only — `F_FULLFSYNC` on a directory
descriptor is not supported and is not attempted.

Supported platforms: macOS and Linux. Windows is not supported and no Windows
guarantee is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import errno
import fcntl
import os
import sys

# macOS `fcntl.h`: ask the drive to flush its write cache. `fcntl.F_FULLFSYNC`
# exists on macOS builds of CPython; the literal keeps this importable elsewhere.
F_FULLFSYNC = getattr(fcntl, "F_FULLFSYNC", 51)

IS_MACOS = sys.platform == "darwin"


class PublicationStage(str, Enum):
    """Where a publication failed, which is what decides the safe response."""

    BEFORE_REPLACE = "before_replace"
    DURING_REPLACE = "during_replace"
    AFTER_REPLACE = "after_replace"


class DurabilityError(RuntimeError):
    """Raised when a safety-critical publication could not be proved durable.

    `stage` is the load-bearing field. `AFTER_REPLACE` means the new content is
    already visible and the caller must re-read reality rather than assume the
    operation did not happen.
    """

    def __init__(self, message: str, stage: PublicationStage) -> None:
        super().__init__(message)
        self.stage = stage

    @property
    def may_have_published(self) -> bool:
        """Whether the publication may already be visible.

        True for both `DURING_REPLACE` and `AFTER_REPLACE`. The first is
        ambiguous and the second is certain, and both demand the same
        conservative response, so callers branch on this rather than on the exact
        stage.
        """
        return self.stage in (PublicationStage.DURING_REPLACE, PublicationStage.AFTER_REPLACE)


@dataclass(frozen=True)
class FlushMethod:
    """Which flush actually ran, so documentation cannot outrun the code."""

    name: str
    full_device_flush: bool


FULL_SYNC = FlushMethod(name="F_FULLFSYNC", full_device_flush=True)
PLAIN_FSYNC = FlushMethod(name="fsync", full_device_flush=False)


# Each syscall boundary is a named module-level function. That is not
# indirection for its own sake: § 7.3 requires faults injected at *every*
# publication boundary, and a monolithic function has no boundaries to inject at.


def _full_device_flush(fd: int) -> None:
    """macOS `F_FULLFSYNC`: ask the drive to flush its own write cache."""
    fcntl.fcntl(fd, F_FULLFSYNC)


def _fsync_fd(fd: int) -> None:
    os.fsync(fd)


def _open_for_flush(path: Path) -> int:
    return os.open(path, os.O_RDONLY)


def _atomic_rename(scratch_path: Path, target_path: Path) -> None:
    os.replace(scratch_path, target_path)


def flush_file(fd: int) -> FlushMethod:
    """Flush one open regular file as durably as the platform supports.

    Returns the method that actually ran. On macOS `F_FULLFSYNC` is attempted
    first; a filesystem that does not implement it reports `ENOTSUP`/`EINVAL`/
    `EOPNOTSUPP` and the call falls back to `fsync`. Every other error is a real
    I/O failure and is raised — a flush that failed for an unexpected reason is
    not a flush that can be quietly downgraded.
    """
    if IS_MACOS:
        try:
            _full_device_flush(fd)
            return FULL_SYNC
        except OSError as exc:
            if exc.errno not in (errno.ENOTSUP, errno.EINVAL, errno.EOPNOTSUPP):
                raise
    _fsync_fd(fd)
    return PLAIN_FSYNC


def flush_path(path: Path) -> FlushMethod:
    """Flush an already-published regular file by path."""
    fd = _open_for_flush(path)
    try:
        return flush_file(fd)
    finally:
        os.close(fd)


def flush_directory(path: Path) -> None:
    """Make a directory's entries durable. Mandatory, and never swallowed.

    `fsync` only: `F_FULLFSYNC` is not supported on a directory descriptor and is
    not attempted. A failure here is raised so the caller can classify it — the
    previous behaviour of ignoring it as harmless was wrong, because it is
    exactly what makes a rename survive a host interruption.
    """
    fd = _open_for_flush(path)
    try:
        _fsync_fd(fd)
    finally:
        os.close(fd)


def publish_atomically(scratch_path: Path, target_path: Path) -> None:
    """Publish a completed scratch file onto its final name, durably.

    The scratch file must already contain the complete content and must live in
    the target's own directory, so the rename stays within one filesystem.

    Every failure is raised as :class:`DurabilityError` carrying the stage it
    happened at. Nothing here decides what a failure *means* — that belongs to
    the caller, whose safe response depends on whether it was publishing a phase
    or replacing a database.
    """
    scratch = Path(scratch_path)
    target = Path(target_path)
    directory = target.parent

    try:
        _atomic_rename(scratch, target)
    except OSError as exc:
        raise DurabilityError(
            f"Atomic publication failed: {type(exc).__name__}",
            PublicationStage.DURING_REPLACE,
        ) from exc

    # From here the new content is visible. Any failure below is `AFTER_REPLACE`,
    # and no caller may conclude the publication did not happen.
    try:
        flush_path(target)
    except OSError as exc:
        raise DurabilityError(
            f"The published file could not be flushed: {type(exc).__name__}",
            PublicationStage.AFTER_REPLACE,
        ) from exc
    try:
        flush_directory(directory)
    except OSError as exc:
        raise DurabilityError(
            f"The publication directory could not be flushed: {type(exc).__name__}",
            PublicationStage.AFTER_REPLACE,
        ) from exc


def _open_scratch_for_write(path: Path) -> int:
    return os.open(path, os.O_WRONLY)


def write_and_publish_bytes(payload: bytes, target_path: Path, scratch_path: Path) -> None:
    """Write `payload` into an existing exclusive scratch file, then publish it.

    `scratch_path` must already have been created exclusively by the caller —
    that is what makes the cleanup on failure provably safe, and this function
    deliberately does not create it, so ownership stays with whoever will clean
    it up.
    """
    scratch = Path(scratch_path)
    try:
        fd = _open_scratch_for_write(scratch)
    except OSError as exc:
        raise DurabilityError(
            f"The publication scratch file could not be opened: {type(exc).__name__}",
            PublicationStage.BEFORE_REPLACE,
        ) from exc
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            flush_file(stream.fileno())
    except OSError as exc:
        raise DurabilityError(
            f"The publication scratch file could not be written: {type(exc).__name__}",
            PublicationStage.BEFORE_REPLACE,
        ) from exc
    publish_atomically(scratch, target_path)
