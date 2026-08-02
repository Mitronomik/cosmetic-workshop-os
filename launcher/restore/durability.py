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
and **records that it did** — literally, into
:data:`DURABILITY_DIAGNOSTICS` and the technical log, so no stronger guarantee is
claimed than the call that actually ran. On Linux `fsync` is used directly.

"Records" is not a figure of speech here. Every safety-critical flush reports the
category it belonged to, whether the target was a file or a directory, the
platform, and the method that ran. Documentation that says "F_FULLFSYNC where
supported" is only honest if a reader can check which one happened on their
machine, and that is what the diagnostics are for. They carry **no** path, no
database content and no user data: a category name, a target kind, a platform
string and a method name.

The diagnostics are deliberately **not** part of the authoritative operation
record. The flush method is not a lifecycle fact and has no place in the phase
machine; it is evidence about how a write was made durable, which belongs in
logs and smoke evidence.

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
import logging
import os
import sys

logger = logging.getLogger(__name__)

# macOS `fcntl.h`: ask the drive to flush its write cache. `fcntl.F_FULLFSYNC`
# exists on macOS builds of CPython; the literal keeps this importable elsewhere.
F_FULLFSYNC = getattr(fcntl, "F_FULLFSYNC", 51)

IS_MACOS = sys.platform == "darwin"


class PublicationCategory(str, Enum):
    """Which safety-critical publication a flush belonged to.

    A closed vocabulary rather than free text, so diagnostics stay comparable
    across runs and can never carry a path or a filename.
    """

    OPERATION_RECORD = "operation_record"
    RECORD_DURABILITY_CONFIRMATION = "record_durability_confirmation"
    STAGED_CANDIDATE = "staged_candidate"
    REPLACEMENT_ARTIFACT = "replacement_artifact"
    WORKING_DATABASE_REPLACEMENT = "working_database_replacement"
    ROLLBACK_REPLACEMENT = "rollback_replacement"
    UNCATEGORIZED = "uncategorized"


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
DIRECTORY_FSYNC = FlushMethod(name="directory_fsync", full_device_flush=False)


@dataclass(frozen=True)
class FlushObservation:
    """One recorded flush: what it was for, and what actually ran.

    Contains no path, no filename, no database content and no user data — the
    category is a fixed enum value and the target is `"file"` or `"directory"`.
    """

    category: str
    target: str
    platform: str
    method: str
    full_device_flush: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "target": self.target,
            "platform": self.platform,
            "method": self.method,
            "full_device_flush": self.full_device_flush,
        }


class DurabilityDiagnostics:
    """A narrow in-memory record of which flush actually ran, and for what.

    Bounded on purpose: it holds observations for the current process and is read
    by tests and by the external smoke runner. It is not persisted, not part of
    the operation record, and not a metrics framework.
    """

    def __init__(self) -> None:
        self._observations: list[FlushObservation] = []

    def record(
        self, category: "PublicationCategory | str", target: str, method: FlushMethod
    ) -> FlushObservation:
        observation = FlushObservation(
            category=category.value if isinstance(category, PublicationCategory) else str(category),
            target=target,
            platform=sys.platform,
            method=method.name,
            full_device_flush=method.full_device_flush,
        )
        self._observations.append(observation)
        logger.debug(
            "durability flush: category=%s target=%s platform=%s method=%s full_device_flush=%s",
            observation.category,
            observation.target,
            observation.platform,
            observation.method,
            observation.full_device_flush,
        )
        return observation

    @property
    def observations(self) -> tuple[FlushObservation, ...]:
        return tuple(self._observations)

    def snapshot(self) -> list[dict[str, object]]:
        return [observation.as_dict() for observation in self._observations]

    def methods_for(self, category: "PublicationCategory | str") -> list[str]:
        wanted = category.value if isinstance(category, PublicationCategory) else str(category)
        return [o.method for o in self._observations if o.category == wanted]

    def clear(self) -> None:
        self._observations.clear()


# The process-wide recorder. A module-level singleton rather than a parameter
# threaded through every call site: the alternative would put a diagnostics
# argument on primitives whose whole job is to be simple and hard to misuse.
DURABILITY_DIAGNOSTICS = DurabilityDiagnostics()


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


def flush_file(
    fd: int, *, category: PublicationCategory | str = PublicationCategory.UNCATEGORIZED
) -> FlushMethod:
    """Flush one open regular file as durably as the platform supports.

    Returns **and records** the method that actually ran. On macOS `F_FULLFSYNC`
    is attempted first; a filesystem that does not implement it reports
    `ENOTSUP`/`EINVAL`/`EOPNOTSUPP` and the call falls back to `fsync`. Every
    other error is a real I/O failure and is raised — a flush that failed for an
    unexpected reason is not a flush that can be quietly downgraded.

    The recording is the point of the `category` argument: a claim that
    `F_FULLFSYNC` is used "where supported" is only checkable if the fallback is
    visible when it happens.
    """
    if IS_MACOS:
        try:
            _full_device_flush(fd)
            DURABILITY_DIAGNOSTICS.record(category, "file", FULL_SYNC)
            return FULL_SYNC
        except OSError as exc:
            if exc.errno not in (errno.ENOTSUP, errno.EINVAL, errno.EOPNOTSUPP):
                raise
    _fsync_fd(fd)
    DURABILITY_DIAGNOSTICS.record(category, "file", PLAIN_FSYNC)
    return PLAIN_FSYNC


def flush_path(
    path: Path, *, category: PublicationCategory | str = PublicationCategory.UNCATEGORIZED
) -> FlushMethod:
    """Flush an already-published regular file by path."""
    fd = _open_for_flush(path)
    try:
        return flush_file(fd, category=category)
    finally:
        os.close(fd)


def flush_directory(
    path: Path, *, category: PublicationCategory | str = PublicationCategory.UNCATEGORIZED
) -> FlushMethod:
    """Make a directory's entries durable. Mandatory, and never swallowed.

    `fsync` only: `F_FULLFSYNC` is not supported on a directory descriptor and is
    not attempted. Recorded separately as `directory_fsync`, so evidence never
    conflates a directory flush with a full-device file flush.

    A failure here is raised so the caller can classify it — treating it as
    harmless was wrong, because it is exactly what makes a rename survive a host
    interruption.
    """
    fd = _open_for_flush(path)
    try:
        _fsync_fd(fd)
    finally:
        os.close(fd)
    DURABILITY_DIAGNOSTICS.record(category, "directory", DIRECTORY_FSYNC)
    return DIRECTORY_FSYNC


def publish_atomically(
    scratch_path: Path,
    target_path: Path,
    *,
    category: PublicationCategory | str = PublicationCategory.UNCATEGORIZED,
) -> None:
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
        flush_path(target, category=category)
    except OSError as exc:
        raise DurabilityError(
            f"The published file could not be flushed: {type(exc).__name__}",
            PublicationStage.AFTER_REPLACE,
        ) from exc
    try:
        flush_directory(directory, category=category)
    except OSError as exc:
        raise DurabilityError(
            f"The publication directory could not be flushed: {type(exc).__name__}",
            PublicationStage.AFTER_REPLACE,
        ) from exc


def _open_scratch_for_write(path: Path) -> int:
    return os.open(path, os.O_WRONLY)


def write_and_publish_bytes(
    payload: bytes,
    target_path: Path,
    scratch_path: Path,
    *,
    category: PublicationCategory | str = PublicationCategory.UNCATEGORIZED,
) -> None:
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
            flush_file(stream.fileno(), category=category)
    except OSError as exc:
        raise DurabilityError(
            f"The publication scratch file could not be written: {type(exc).__name__}",
            PublicationStage.BEFORE_REPLACE,
        ) from exc
    publish_atomically(scratch, target_path, category=category)


def confirm_existing_durability(
    target_path: Path,
    *,
    category: PublicationCategory | str = PublicationCategory.RECORD_DURABILITY_CONFIRMATION,
) -> tuple[FlushMethod, FlushMethod]:
    """Re-flush a file that is **already** published, and its parent directory.

    Changes nothing. It opens the existing file read-only, flushes it, flushes the
    directory holding it, and returns the two methods that ran.

    This exists for the one window the publication primitive cannot close by
    itself: `os.replace` succeeded, so the new content is visible, but the flush
    that follows it failed. The content is correct and must not be rewritten — a
    rewrite would produce a new scratch file and a second rename for a value that
    is already there — yet its durability is unproven, so nothing may be allowed
    to depend on it surviving a host interruption.

    Retrying the flush alone is the proportionate response: it re-proves the
    thing that failed and touches nothing that succeeded. A failure here is
    raised, and the caller's answer is always the same — keep the actual phase,
    keep the evidence, block ordinary startup, and try again on the next start.
    """
    resolved = Path(target_path)
    if not resolved.is_file():
        raise DurabilityError(
            "The published file to confirm does not exist.", PublicationStage.AFTER_REPLACE
        )
    try:
        file_method = flush_path(resolved, category=category)
    except OSError as exc:
        raise DurabilityError(
            f"The published file could not be re-flushed: {type(exc).__name__}",
            PublicationStage.AFTER_REPLACE,
        ) from exc
    try:
        directory_method = flush_directory(resolved.parent, category=category)
    except OSError as exc:
        raise DurabilityError(
            f"The publication directory could not be re-flushed: {type(exc).__name__}",
            PublicationStage.AFTER_REPLACE,
        ) from exc
    return file_method, directory_method
