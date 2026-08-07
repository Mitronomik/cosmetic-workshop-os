"""Non-destructive launcher-owned candidate preparation for C4-II-A1.

This module is intentionally *not* the destructive Restore engine.  It creates
no durable operation record, enters no Restore phase, creates no safety copy,
stops no backend, mutates no working database and writes no Restore AuditLog.

The service reuses the accepted C4-I source intake, held-descriptor staging and
read-only candidate validation exactly as they exist today.  Its only durable
output is nothing: the staged candidate is deleted before a successful result is
published.  The launcher may retain one in-memory source proof for the current
selection generation so a later, separately authorized C4-II-B can re-open and
re-prove the original source before any destructive work.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib
import logging
import threading

from launcher.restore.contracts import RestoreFailure, USER_SAFE_MESSAGES
from launcher.restore.staging import (
    SourceIdentity,
    SourceRejectedError,
    StagingError,
    open_selected_source,
    stage_source,
)
from launcher.restore.validation import CandidateRejectedError, validate_staged_candidate
from launcher.restore.validation_scratch import (
    ValidationScratchError,
    ValidationScratchManager,
)
from launcher.restore.workspace import RestoreWorkspaceError

logger = logging.getLogger(__name__)

READ_CHUNK_BYTES = 1024 * 1024
MAX_DISPLAY_FILENAME_CHARS = 160
FALLBACK_DISPLAY_FILENAME = "резервная копия"

CANCELLED_MESSAGE = "Проверка резервной копии отменена. Данные мастерской не изменились."
TECHNICAL_FAILURE_MESSAGE = (
    "Не удалось проверить резервную копию. Данные мастерской не изменились. "
    "Попробуйте снова."
)


class CandidatePreparationState(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TECHNICAL_FAILURE = "technical_failure"


class CandidateCompatibility(str, Enum):
    CURRENT_SCHEMA = "current_schema"
    OLDER_SUPPORTED_SCHEMA = "older_supported_schema"


class CandidatePreparationFailure(str, Enum):
    SOURCE_REJECTED = "source_rejected"
    CANDIDATE_INVALID = "candidate_invalid"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    CANCELLED = "cancelled"
    TECHNICAL_FAILURE = "technical_failure"


@dataclass(frozen=True)
class CandidatePreparationResult:
    """Presentation-safe result of one validation generation.

    Deliberately contains no absolute source path, staged path, SQL text,
    migration IDs, stack trace or database content.
    """

    state: CandidatePreparationState
    run_id: str
    session_id: str | None
    generation: int
    filename: str
    message: str
    compatibility: CandidateCompatibility | None = None
    failure: CandidatePreparationFailure | None = None

    @property
    def accepted(self) -> bool:
        return self.state is CandidatePreparationState.ACCEPTED


@dataclass(frozen=True)
class RetainedSourceProof:
    """Launcher-private in-memory proof; never a browser DTO or authority token."""

    source_path: Path
    source_identity: SourceIdentity
    sha256: str
    generation: int
    compatibility: CandidateCompatibility


@dataclass(frozen=True)
class _PreparedCandidate:
    source_path: Path
    source_identity: SourceIdentity
    sha256: str
    compatibility: CandidateCompatibility


def _safe_filename(selected_source: object) -> str:
    """Return a bounded, display-only basename with no control formatting.

    The real path remains launcher-private authority.  This value is only a UI
    label, so non-printable/control characters are replaced with spaces,
    whitespace is collapsed and length is bounded before it can reach a future
    browser surface.
    """

    if not isinstance(selected_source, (str, Path)):
        return FALLBACK_DISPLAY_FILENAME
    name = Path(selected_source).name
    if not name:
        return FALLBACK_DISPLAY_FILENAME
    printable = "".join(character if character.isprintable() else " " for character in name)
    collapsed = " ".join(printable.split()).strip()
    if not collapsed:
        return FALLBACK_DISPLAY_FILENAME
    return collapsed[:MAX_DISPLAY_FILENAME_CHARS]


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            chunk = stream.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _source_failure(error: SourceRejectedError) -> CandidatePreparationFailure:
    if error.is_sidecar_dependency:
        return CandidatePreparationFailure.CANDIDATE_INVALID
    return CandidatePreparationFailure.SOURCE_REJECTED


def _candidate_failure(error: CandidateRejectedError) -> CandidatePreparationFailure:
    if error.is_newer_schema:
        return CandidatePreparationFailure.UNSUPPORTED_SCHEMA
    return CandidatePreparationFailure.CANDIDATE_INVALID


def _safe_failure_message(failure: CandidatePreparationFailure) -> str:
    if failure is CandidatePreparationFailure.SOURCE_REJECTED:
        return USER_SAFE_MESSAGES[RestoreFailure.SOURCE_REJECTED]
    if failure is CandidatePreparationFailure.CANDIDATE_INVALID:
        return USER_SAFE_MESSAGES[RestoreFailure.CANDIDATE_INVALID]
    if failure is CandidatePreparationFailure.UNSUPPORTED_SCHEMA:
        return USER_SAFE_MESSAGES[RestoreFailure.UNSUPPORTED_SCHEMA]
    if failure is CandidatePreparationFailure.CANCELLED:
        return CANCELLED_MESSAGE
    return TECHNICAL_FAILURE_MESSAGE


class RestoreCandidatePreparationService:
    """Own one launcher's non-destructive Restore validation generations.

    The service creates no threads.  A future A2 control-plane worker may call it
    from a worker thread; generation checks make a concurrently issued cancel or
    reselection invalidate late publication without A1 inventing the A2 worker
    ownership model early.
    """

    def __init__(
        self,
        database_path: Path,
        *,
        scratch_root: Path | None = None,
        run_id: str | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self._lock = threading.RLock()
        self._generation = 0
        self._retained_proof: RetainedSourceProof | None = None
        self._closed = False
        self._active_preparations = 0
        self._scratch = ValidationScratchManager(
            self.database_path,
            root=scratch_root,
            run_id=run_id,
        )

    @property
    def run_id(self) -> str:
        return self._scratch.run_id

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    @property
    def retained_proof(self) -> RetainedSourceProof | None:
        """Launcher-private proof for later source re-proof, or ``None``."""

        with self._lock:
            return self._retained_proof

    def cleanup_interrupted_validation_scratch(self) -> int:
        """Clean recognized previous-run scratch without touching this run."""

        return self._scratch.cleanup_interrupted_runs()

    def cancel(self) -> int:
        """Invalidate the current generation and any retained source authority."""

        with self._lock:
            self._generation += 1
            self._retained_proof = None
            return self._generation

    def invalidate(self) -> int:
        """Alias used by future launcher lifecycle transitions."""

        return self.cancel()

    def close(self) -> None:
        """Invalidate authority; remove the run root once callers have quiesced."""

        should_cleanup = False
        with self._lock:
            if not self._closed:
                self._closed = True
                self._generation += 1
                self._retained_proof = None
            should_cleanup = self._active_preparations == 0
        if should_cleanup:
            self._scratch.cleanup_current_run_if_empty()

    def __enter__(self) -> "RestoreCandidatePreparationService":
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()

    def _begin(self) -> int | None:
        with self._lock:
            if self._closed:
                return None
            self._generation += 1
            self._retained_proof = None
            self._active_preparations += 1
            return self._generation

    def _finish(self) -> None:
        should_cleanup = False
        with self._lock:
            self._active_preparations -= 1
            should_cleanup = self._closed and self._active_preparations == 0
        if should_cleanup:
            self._scratch.cleanup_current_run_if_empty()

    def _is_current(self, generation: int) -> bool:
        with self._lock:
            return not self._closed and generation == self._generation

    def _publish_proof(self, generation: int, prepared: _PreparedCandidate) -> bool:
        with self._lock:
            if self._closed or generation != self._generation:
                return False
            self._retained_proof = RetainedSourceProof(
                source_path=prepared.source_path,
                source_identity=prepared.source_identity,
                sha256=prepared.sha256,
                generation=generation,
                compatibility=prepared.compatibility,
            )
            return True

    def _clear_if_current(self, generation: int) -> None:
        with self._lock:
            if generation == self._generation:
                self._retained_proof = None

    def _result(
        self,
        *,
        state: CandidatePreparationState,
        generation: int,
        session_id: str | None,
        filename: str,
        compatibility: CandidateCompatibility | None = None,
        failure: CandidatePreparationFailure | None = None,
    ) -> CandidatePreparationResult:
        message = (
            "Резервная копия проверена и готова к следующему шагу."
            if state is CandidatePreparationState.ACCEPTED
            else _safe_failure_message(failure or CandidatePreparationFailure.TECHNICAL_FAILURE)
        )
        return CandidatePreparationResult(
            state=state,
            run_id=self.run_id,
            session_id=session_id,
            generation=generation,
            filename=filename,
            message=message,
            compatibility=compatibility,
            failure=failure,
        )

    def _cancelled_result(
        self, generation: int, session_id: str | None, filename: str
    ) -> CandidatePreparationResult:
        return self._result(
            state=CandidatePreparationState.CANCELLED,
            generation=generation,
            session_id=session_id,
            filename=filename,
            failure=CandidatePreparationFailure.CANCELLED,
        )

    def prepare_restore_candidate(self, selected_source: object) -> CandidatePreparationResult:
        """Stage and validate one selected source without destructive Restore state."""

        filename = _safe_filename(selected_source)
        generation = self._begin()
        if generation is None:
            return CandidatePreparationResult(
                state=CandidatePreparationState.TECHNICAL_FAILURE,
                run_id=self.run_id,
                session_id=None,
                generation=self.generation,
                filename=filename,
                message=TECHNICAL_FAILURE_MESSAGE,
                failure=CandidatePreparationFailure.TECHNICAL_FAILURE,
            )

        session_id: str | None = None
        prepared: _PreparedCandidate | None = None
        failure: CandidatePreparationFailure | None = None
        technical_failure = False

        try:
            try:
                session = self._scratch.create_session()
                session_id = session.session_id
            except ValidationScratchError as exc:
                logger.error("Validation scratch setup failed: %s", type(exc).__name__)
                technical_failure = True
                return self._result(
                    state=CandidatePreparationState.TECHNICAL_FAILURE,
                    generation=generation,
                    session_id=None,
                    filename=filename,
                    failure=CandidatePreparationFailure.TECHNICAL_FAILURE,
                )

            if not self._is_current(generation):
                return self._cancelled_result(generation, session_id, filename)

            try:
                with open_selected_source(selected_source, self.database_path) as held:
                    if not self._is_current(generation):
                        return self._cancelled_result(generation, session_id, filename)

                    staged_path = stage_source(session.workspace, session.session_id, held)

                    if not self._is_current(generation):
                        return self._cancelled_result(generation, session_id, filename)

                    staged_digest = _sha256_file(staged_path)
                    source_digest, source_bytes = held.digest()
                    held.revalidate()
                    held.assert_still_self_contained()
                    if source_bytes != held.size_bytes or source_digest != staged_digest:
                        raise SourceRejectedError("source-identity-changed")

                    candidate = validate_staged_candidate(staged_path)

                    # Re-prove after validation too.  The staged copy may be
                    # healthy while the original path changes during the read.
                    final_digest, final_bytes = held.digest()
                    held.revalidate()
                    held.assert_still_self_contained()
                    if (
                        final_bytes != held.size_bytes
                        or final_digest != source_digest
                        or final_digest != staged_digest
                    ):
                        raise SourceRejectedError("source-identity-changed")

                    try:
                        canonical_source = held.path.resolve(strict=True)
                    except OSError as exc:
                        raise SourceRejectedError("source-identity-changed") from exc

                    compatibility = (
                        CandidateCompatibility.CURRENT_SCHEMA
                        if candidate.is_current_head
                        else CandidateCompatibility.OLDER_SUPPORTED_SCHEMA
                    )
                    prepared = _PreparedCandidate(
                        source_path=canonical_source,
                        source_identity=held.identity,
                        sha256=final_digest,
                        compatibility=compatibility,
                    )
            except SourceRejectedError as exc:
                logger.warning("Candidate source rejected: %s", exc.rejection)
                failure = _source_failure(exc)
            except CandidateRejectedError as exc:
                logger.warning("Candidate validation rejected: %s", exc.rejection)
                failure = _candidate_failure(exc)
            except (StagingError, RestoreWorkspaceError, ValidationScratchError, OSError) as exc:
                logger.error("Candidate preparation failed safely: %s", type(exc).__name__)
                technical_failure = True
            except Exception as exc:  # noqa: BLE001 - boundary returns fixed safe vocabulary
                logger.exception("Unexpected candidate-preparation failure: %s", type(exc).__name__)
                technical_failure = True

            # The worker/caller that owns this call also owns cleanup.  A future
            # A2 cancel can invalidate generation immediately, but scratch is not
            # removed until this call has quiesced here.
            cleaned = self._scratch.cleanup_session(session.session_id)
            if not cleaned:
                logger.error("Validation scratch cleanup could not be proved.")
                technical_failure = True
                prepared = None
                self._clear_if_current(generation)

            if not self._is_current(generation):
                return self._cancelled_result(generation, session_id, filename)

            if technical_failure:
                self._clear_if_current(generation)
                return self._result(
                    state=CandidatePreparationState.TECHNICAL_FAILURE,
                    generation=generation,
                    session_id=session_id,
                    filename=filename,
                    failure=CandidatePreparationFailure.TECHNICAL_FAILURE,
                )

            if failure is not None:
                self._clear_if_current(generation)
                return self._result(
                    state=CandidatePreparationState.REJECTED,
                    generation=generation,
                    session_id=session_id,
                    filename=filename,
                    failure=failure,
                )

            if prepared is None:
                self._clear_if_current(generation)
                return self._result(
                    state=CandidatePreparationState.TECHNICAL_FAILURE,
                    generation=generation,
                    session_id=session_id,
                    filename=filename,
                    failure=CandidatePreparationFailure.TECHNICAL_FAILURE,
                )

            if not self._publish_proof(generation, prepared):
                return self._cancelled_result(generation, session_id, filename)

            return self._result(
                state=CandidatePreparationState.ACCEPTED,
                generation=generation,
                session_id=session_id,
                filename=filename,
                compatibility=prepared.compatibility,
            )
        finally:
            # If control left early before the normal cleanup point (for example
            # cancel immediately after session allocation), cleanup occurs here
            # after this call itself is quiescent.
            if session_id is not None:
                session_path = self._scratch.run_dir / session_id
                if session_path.exists() and not session_path.is_symlink():
                    self._scratch.cleanup_session(session_id)
            self._finish()
