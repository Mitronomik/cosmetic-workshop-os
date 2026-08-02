"""The one narrow durable Restore operation record, and how it is published.

Authoritative contract: ``docs/decisions/0016-launcher-assisted-restore.md``
§ 7 and § 7.3.

The record lives on the filesystem, **outside the working database**, because the
working database is the thing being replaced — an in-database record of the
replacement would be discarded by the operation it describes.

## What may be persisted

Exactly the fields of :class:`RestoreOperationRecord`: a launcher-generated
operation ID, the authoritative `phase`, two timestamps, and safe *relative*
launcher-owned filenames. Nothing else. No database contents, no client, recipe,
order or stock data, no credentials, no SQL, no stack trace, no user-authored
text, no raw absolute selected-source path, no event history, no job-queue or
outbox fields — and no independent `replacement_happened` / `rollback_completed`
booleans, which are derived from `phase`.

Serialization is a closed set in both directions: an unknown key on read is a
rejection, not something to ignore, so a record written by anything other than
this module can never be acted on.

## How it is published

`CR-010` § 7.3 rejects an in-place truncate-and-rewrite of the only authoritative
record: a crash mid-write leaves a file that is neither the old state nor the new
one, and the recovery matrix has no entry for "half a phase". The publication
primitive here is:

```text
create an exclusively-owned scratch file in the same directory
→ write the complete record
→ flush the Python buffer
→ os.fsync the file descriptor
→ os.replace onto the authoritative name        <- atomic publication boundary
→ best-effort os.fsync of the parent directory
→ remove only the scratch file this call created
```

`os.replace` is the boundary. It is POSIX `rename(2)` within one directory, which
is atomic with respect to other processes: a concurrent reader sees either the
complete old record or the complete new one, never a mixture. Interruption before
it leaves the old record intact and one orphan scratch file that
`clean_owned_temp_files` recognizes.

**Durability is claimed only as far as the primitive proves it.** `os.fsync`
pushes the file's data out of the operating system's cache. On macOS it does
*not* guarantee the drive has flushed its own write cache — that needs
`F_FULLFSYNC` — so no claim of power-loss durability is made here, and none is
made in the documentation. What is proved, and what the recovery matrix actually
depends on, is old-or-new atomicity across process death and OS crash.

The parent-directory `fsync` is best-effort by design. It is what makes the
rename itself durable on ext4/APFS-style filesystems, but some platforms and some
mounts refuse `O_RDONLY` fsync on a directory. Refusing to continue there would
break Restore on a filesystem where the atomic boundary is still perfectly sound,
so the failure is recorded and tolerated rather than fatal.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
import contextlib
import json
import os
import tempfile

from launcher.restore.phases import RestorePhase, require_allowed_transition
from launcher.restore.workspace import (
    OWNED_TEMP_PREFIX,
    OWNED_TEMP_SUFFIX,
    RestoreWorkspace,
    is_safe_relative_filename,
)

# The complete set of keys the authoritative record may contain. Used for both
# directions, so a field cannot be written that reading would reject, and a
# reader cannot silently accept a field a writer never produced.
ALLOWED_RECORD_FIELDS: frozenset[str] = frozenset(
    {
        "operation_id",
        "phase",
        "created_at",
        "updated_at",
        "staged_candidate_filename",
        "safety_copy_filename",
    }
)

# Bytes reserved for one publication scratch record in the disk-space preflight.
# The record is a few hundred bytes; this is a deliberately generous bound so the
# preflight can never be the thing that makes a publication fail.
STATE_RESERVE_BYTES = 1 * 1024 * 1024


class RestoreStateError(RuntimeError):
    """Raised when the authoritative operation record cannot be trusted.

    Never swallowed into "no operation". A record that exists but cannot be read
    is the one case where the launcher knows something happened and cannot tell
    what, and the accepted answer to that is `recovery_blocked`, not ordinary
    startup.
    """


def _now() -> str:
    """One UTC timestamp spelling, second-free of local time zones."""
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class RestoreOperationRecord:
    """The complete authoritative Restore operation state.

    `phase` is the sole authoritative lifecycle field. `staged_candidate_filename`
    and `safety_copy_filename` are safe relative names, resolved against the
    launcher-owned operation directory and the configured backup directory
    respectively — the raw absolute selected-source path is deliberately never
    stored, because a staged relative identity is sufficient for recovery.
    """

    operation_id: str
    phase: RestorePhase
    created_at: str
    updated_at: str
    staged_candidate_filename: str | None = None
    safety_copy_filename: str | None = None

    def to_json_object(self) -> dict[str, object]:
        return {
            "operation_id": self.operation_id,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "staged_candidate_filename": self.staged_candidate_filename,
            "safety_copy_filename": self.safety_copy_filename,
        }

    @classmethod
    def from_json_object(cls, payload: object) -> "RestoreOperationRecord":
        """Parse one record, rejecting anything outside the closed field set.

        An unexpected extra key is a rejection rather than something to drop.
        A record this module did not write is a record whose meaning is unknown,
        and the safe response to an unknown authoritative record is to refuse it,
        not to interpret the parts that happen to parse.
        """
        if not isinstance(payload, dict):
            raise RestoreStateError("Restore operation record is not an object.")
        keys = set(payload)
        if keys != ALLOWED_RECORD_FIELDS:
            raise RestoreStateError("Restore operation record has an unexpected field set.")

        operation_id = payload["operation_id"]
        if not is_safe_relative_filename(operation_id):
            raise RestoreStateError("Restore operation record has an unsafe operation identity.")

        raw_phase = payload["phase"]
        try:
            phase = RestorePhase(raw_phase)
        except ValueError as exc:
            raise RestoreStateError("Restore operation record has an unknown phase.") from exc

        for key in ("created_at", "updated_at"):
            if not isinstance(payload[key], str) or not payload[key]:
                raise RestoreStateError("Restore operation record has an invalid timestamp.")

        for key in ("staged_candidate_filename", "safety_copy_filename"):
            value = payload[key]
            if value is None:
                continue
            if not is_safe_relative_filename(value):
                raise RestoreStateError("Restore operation record has an unsafe filename.")

        return cls(
            operation_id=str(operation_id),
            phase=phase,
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            staged_candidate_filename=payload["staged_candidate_filename"],
            safety_copy_filename=payload["safety_copy_filename"],
        )


# --------------------------------------------------------------------------
# The publication primitive
# --------------------------------------------------------------------------
#
# Each step is a named module-level function so a test can inject a deterministic
# fault at exactly one boundary without stubbing out the whole store. That is not
# a testing convenience bolted on afterwards: § 7.3 requires faults injected at
# *every* publication boundary, and a single monolithic function has no boundaries
# to inject at.


def _create_owned_scratch(directory: Path) -> tuple[int, Path]:
    """Create an exclusively-owned scratch file in the publication directory.

    `mkstemp` uses `O_CREAT | O_EXCL`, so the returned path is one this process
    definitely created. That is what makes the cleanup below safe, and it is the
    same ownership argument the accepted backup engine uses for its own scratch
    file. Same directory on purpose: `os.replace` must stay within one filesystem.
    """
    handle, path = tempfile.mkstemp(
        dir=directory, prefix=OWNED_TEMP_PREFIX, suffix=OWNED_TEMP_SUFFIX
    )
    return handle, Path(path)


def _write_scratch_record(handle: int, payload: bytes) -> None:
    """Write the complete record and force it out of the process buffer."""
    with os.fdopen(handle, "wb", closefd=True) as stream:
        stream.write(payload)
        stream.flush()
        _fsync_file(stream.fileno())


def _fsync_file(fileno: int) -> None:
    """Flush the file's data out of the operating-system cache.

    Separate from `_write_scratch_record` so a test can fail exactly this step.
    A failure here is fatal to the publication: the record has not been published
    yet, so refusing costs nothing and continuing would publish bytes that may
    not be on the device.
    """
    os.fsync(fileno)


def _publish_scratch(scratch_path: Path, record_path: Path) -> None:
    """The atomic publication boundary.

    `os.replace`, not `os.link` — unlike the backup engine, this file *must* be
    overwritten, and it must be overwritten in one step. `os.link` refuses an
    existing target; `unlink`-then-`link` would open exactly the window this
    primitive exists to close.
    """
    os.replace(scratch_path, record_path)


def _fsync_directory(directory: Path) -> None:
    """Best-effort durability for the rename itself.

    Tolerated on failure: see the module docstring. The atomic boundary holds
    without it; only the persistence of the rename across a host crash does not.
    """
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        return
    finally:
        os.close(fd)


class RestoreOperationStateStore:
    """Reads and durably publishes the one authoritative operation record."""

    def __init__(self, workspace: RestoreWorkspace) -> None:
        self.workspace = workspace

    @property
    def record_path(self) -> Path:
        return self.workspace.record_path

    # -------------------------------------------------------------- reading

    def has_record(self) -> bool:
        return self.record_path.exists()

    def read(self) -> RestoreOperationRecord | None:
        """The current record, `None` when no Restore was ever attempted.

        A malformed or unreadable record raises rather than returning `None`.
        "There is no operation" and "there is an operation I cannot read" are
        different facts with different recovery behaviour, and collapsing them
        would let an unreadable record fall through to ordinary startup — the one
        outcome § 7.5 forbids for every unsafe phase.
        """
        try:
            raw = self.record_path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise RestoreStateError(
                f"Restore operation record could not be read: {type(exc).__name__}"
            ) from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RestoreStateError("Restore operation record is not readable JSON.") from exc
        return RestoreOperationRecord.from_json_object(payload)

    # ------------------------------------------------------------ publishing

    def publish(self, record: RestoreOperationRecord) -> RestoreOperationRecord:
        """Durably publish one complete record through the atomic boundary."""
        directory = self.workspace.ensure_restore_dir()
        payload = json.dumps(
            record.to_json_object(), ensure_ascii=False, sort_keys=True, indent=2
        ).encode("utf-8")

        try:
            handle, scratch_path = _create_owned_scratch(directory)
        except OSError as exc:
            # Nothing was created, so there is nothing to clean up and the
            # previously published record is untouched.
            raise RestoreStateError(
                f"Restore operation state could not be staged: {type(exc).__name__}"
            ) from exc

        published = False
        try:
            _write_scratch_record(handle, payload)
            _publish_scratch(scratch_path, self.record_path)
            published = True
        except OSError as exc:
            raise RestoreStateError(
                f"Restore operation state could not be published: {type(exc).__name__}"
            ) from exc
        finally:
            if not published:
                # Only ever the scratch file this call created. After a
                # successful `os.replace` the scratch path no longer exists, so
                # this cleanup cannot touch the published record.
                with contextlib.suppress(OSError):
                    scratch_path.unlink(missing_ok=True)
        _fsync_directory(directory)
        return record

    def create(
        self, operation_id: str, phase: RestorePhase = RestorePhase.PREPARED
    ) -> RestoreOperationRecord:
        """Publish the initial record for a new attempt.

        Refuses to start on top of a non-terminal operation. A live record means
        another attempt is in flight or an interrupted one has not been recovered
        yet, and starting a second attempt over either would leave two operations
        claiming the same working database.
        """
        existing = self.read()
        if existing is not None and existing.phase not in _TERMINAL:
            raise RestoreStateError(
                "A Restore operation is already in progress and has not been recovered."
            )
        if existing is not None and existing.operation_id == operation_id:
            raise RestoreStateError("A terminal Restore operation is never reactivated.")
        timestamp = _now()
        return self.publish(
            RestoreOperationRecord(
                operation_id=operation_id,
                phase=phase,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

    def transition(
        self,
        record: RestoreOperationRecord,
        target: RestorePhase,
        *,
        staged_candidate_filename: str | None = None,
        safety_copy_filename: str | None = None,
    ) -> RestoreOperationRecord:
        """Move one operation to `target`, refusing unauthorized transitions.

        The filename arguments are additive only: once a staged candidate or a
        safety copy has been recorded, a later transition cannot blank it. That is
        what keeps `recovery_blocked` able to name the evidence it must preserve.
        """
        require_allowed_transition(record.phase, target)
        updated = replace(
            record,
            phase=target,
            updated_at=_now(),
            staged_candidate_filename=staged_candidate_filename
            or record.staged_candidate_filename,
            safety_copy_filename=safety_copy_filename or record.safety_copy_filename,
        )
        return self.publish(updated)


_TERMINAL = frozenset(
    {
        RestorePhase.COMPLETED,
        RestorePhase.ABORTED,
        RestorePhase.ROLLED_BACK,
        RestorePhase.RECOVERY_BLOCKED,
    }
)
