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
one, and the recovery matrix has no entry for "half a phase". Publication is
delegated to :mod:`launcher.restore.durability`, the one shared safety-critical
primitive — exclusive scratch creation, complete write, file flush
(`F_FULLFSYNC` on macOS where the filesystem supports it), atomic same-directory
`os.replace`, published-file flush, then a **mandatory** parent-directory flush.

**The parent-directory flush is not best effort.** `os.replace` makes the new
record visible atomically but does not make the rename itself survive a host
interruption. Ignoring that failure is precisely what could leave the working
database replaced while this record reverted to a phase saying nothing was
replaced — and startup recovery would then take the `aborted` branch over a
database that is not the one it thinks it is.

So a publication failure is **classified, never swallowed**. `RestoreStateError`
carries `published`: when the underlying failure happened at or after the rename,
the new record may already be on disk, and the caller must **re-read the
authoritative record** rather than assume the transition did not happen. That is
the difference between "this phase did not persist" and "I do not know which
phase persisted", and only the second is safe to resolve by reading.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
import contextlib
import json
import os
import tempfile

from launcher.restore.durability import (
    DurabilityError,
    PublicationCategory,
    confirm_existing_durability,
    write_and_publish_bytes,
)
from launcher.restore.phases import RestorePhase, require_allowed_transition
from launcher.restore.workspace import (
    OWNED_TEMP_PREFIX,
    OWNED_TEMP_SUFFIX,
    RestoreWorkspace,
    is_launcher_operation_id,
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

    `published` is what a caller must branch on after a failed transition. When
    it is true the rename already happened, so the new phase may well be the
    durable one — assuming otherwise would mean acting on a phase that is not on
    disk. The caller re-reads instead of guessing.
    """

    def __init__(self, message: str, *, published: bool = False) -> None:
        super().__init__(message)
        self.published = published


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
        if not is_launcher_operation_id(operation_id):
            # Stricter than a safe filename on purpose: this value becomes a
            # directory name, so anything this launcher could not have generated
            # is refused rather than acted on.
            raise RestoreStateError("Restore operation record has a non-launcher operation identity.")

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


def _create_owned_scratch(directory: Path) -> Path:
    """Create an exclusively-owned scratch file in the publication directory.

    `mkstemp` uses `O_CREAT | O_EXCL`, so the returned path is one this process
    definitely created. That is what makes the cleanup below safe, and it is the
    same ownership argument the accepted backup engine uses for its own scratch
    file. Same directory on purpose: `os.replace` must stay within one filesystem.

    The descriptor is closed immediately and the durability primitive reopens the
    path it was handed. Ownership of the *path* is what matters for cleanup, and
    keeping the write in one place is what keeps the guarantees in one place.
    """
    handle, path = tempfile.mkstemp(
        dir=directory, prefix=OWNED_TEMP_PREFIX, suffix=OWNED_TEMP_SUFFIX
    )
    os.close(handle)
    return Path(path)


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

    def read_durable_record(
        self, fallback: RestoreOperationRecord
    ) -> RestoreOperationRecord:
        """The record actually on disk, or `fallback` when it cannot be read.

        Called after a publication whose durability could not be proved. The
        rename may already have landed, so neither the old nor the new phase may
        be assumed — the only honest answer is whatever a complete read returns.

        `fallback` is the caller's last *known* durable record, used when the
        file itself is now unreadable. That is deliberately the more dangerous of
        the two values, because the caller's safe response is keyed off the
        pre-transition phase and re-reading must never make the situation look
        better than it is.
        """
        try:
            current = self.read()
        except RestoreStateError:
            return fallback
        return current if current is not None else fallback

    def confirm_record_durability(self) -> None:
        """Re-flush the existing authoritative record. Changes nothing.

        No transition, no content rewrite, no new scratch file — it opens the
        record that is already published, flushes it, and flushes the directory
        holding it.

        This exists for the window `publish` cannot close by itself: `os.replace`
        succeeded, so the new phase *is* visible, but the flush after it failed.
        Rewriting would be wrong (the content is already correct and a rewrite
        means another rename) and ignoring it would be worse (the rename can
        revert across a host interruption). Re-proving the flush is the one
        proportionate answer.

        Raises :class:`RestoreStateError` when durability still cannot be proved.
        The caller's response is always the same: keep the actual phase, keep the
        evidence, block ordinary startup, and retry on the next launcher start.
        """
        if not self.record_path.is_file():
            raise RestoreStateError("There is no authoritative record to confirm.")
        try:
            confirm_existing_durability(
                self.record_path,
                category=PublicationCategory.RECORD_DURABILITY_CONFIRMATION,
            )
        except DurabilityError as exc:
            raise RestoreStateError(
                f"Restore operation state durability could not be confirmed: {exc.stage.value}",
                published=True,
            ) from exc

    # ------------------------------------------------------------ publishing

    def publish(self, record: RestoreOperationRecord) -> RestoreOperationRecord:
        """Durably publish one complete record through the shared primitive.

        A failure is classified rather than flattened. `RestoreStateError.published`
        is true when the rename already happened and only its durability is
        unproven — in that case the record on disk **is** the new one, and a
        caller that assumed otherwise would act on a phase that is not there.
        """
        directory = self.workspace.ensure_restore_dir()
        payload = json.dumps(
            record.to_json_object(), ensure_ascii=False, sort_keys=True, indent=2
        ).encode("utf-8")

        try:
            scratch_path = _create_owned_scratch(directory)
        except OSError as exc:
            # Nothing was created, so there is nothing to clean up and the
            # previously published record is untouched.
            raise RestoreStateError(
                f"Restore operation state could not be staged: {type(exc).__name__}"
            ) from exc

        try:
            write_and_publish_bytes(
                payload,
                self.record_path,
                scratch_path,
                category=PublicationCategory.OPERATION_RECORD,
            )
        except DurabilityError as exc:
            if not exc.may_have_published:
                # The rename never ran, so the scratch file is still ours to
                # remove and the previous record is intact.
                with contextlib.suppress(OSError):
                    scratch_path.unlink(missing_ok=True)
            raise RestoreStateError(
                f"Restore operation state could not be published: {exc.stage.value}",
                published=exc.may_have_published,
            ) from exc
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
        if not is_launcher_operation_id(operation_id):
            raise RestoreStateError(
                "A Restore operation identity must be a canonical launcher-generated UUID."
            )
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
