"""Orchestration of one Restore attempt, in the exact accepted order.

This module is the only place that decides *when* each step runs. Every step
itself lives in a focused module beside it, and the phase machine lives in
`phases`. What is here is the sequence `CR-010` § 6 and § 7.3 accept, and the
failure handling § 10 requires:

```text
accept the selected source            (nothing created yet)
→ disk-space preflight                (before any large artifact)
→ isolated operation directory        [prepared]
→ stage the source                    [source_staged]
→ validate the staged candidate       [candidate_validated]
→ create and verify the safety copy   [safety_copy_verified]
→ settle the target's SQLite journal   (checkpoint, after the recovery point exists)
→ prepare the replacement artifact
→ durably persist                     [replacement_intent]
→ ATOMIC REPLACEMENT BOUNDARY
→ durably persist                     [replacement_committed]
→ durably persist                     [verification_in_progress]
→ startup + migrations against the exact restored path
→ bounded backend verification, twice  (restartability)
→ durably persist                     [completed]
→ clean only launcher-owned staging
```

Any failure **before** `replacement_intent` ends at `aborted` and the working
database was never touched. Any failure **at or after** `replacement_intent`
enters rollback — including the case where the replacement call itself failed,
because a persisted `replacement_intent` is treated as though replacement may
have occurred, and no filesystem appearance may be used to argue otherwise.

`C4-I` is internal. There is no endpoint, no CLI, no product terminal workflow
and no user-facing entry point here; a future `C4-II` calls
:func:`execute_restore` and renders `RestoreResult.message`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import logging

from launcher.restore.capacity import InsufficientDiskSpaceError, assert_sufficient_disk_space
from launcher.restore.contracts import (
    RestoreFailure,
    RestoreOutcome,
    RestoreRequest,
    RestoreResult,
    SUCCESS_MESSAGE,
    USER_SAFE_MESSAGES,
)
from launcher.restore.instance_lock import LauncherAlreadyRunningError, LauncherInstanceLock
from launcher.restore.phases import RestorePhase
from launcher.restore.replacement import (
    JournalSafetyError,
    ReplacementError,
    ReplacementTargetError,
    assert_replaceable_target,
    commit_replacement,
    discard_replacement_artifact,
    prepare_replacement_artifact,
    quiesce_target_journal,
)
from launcher.restore.safety_copy import SafetyCopyError, create_verified_safety_copy, verify_safety_copy
from launcher.restore.staging import SourceRejectedError, StagingError, accept_source_path, stage_source
from launcher.restore.state import (
    RestoreOperationRecord,
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.validation import CandidateRejectedError, validate_staged_candidate
from launcher.restore.verification import BackendVerificationError, verify_restored_backend
from launcher.restore.workspace import RestoreWorkspace, RestoreWorkspaceError, new_operation_id

logger = logging.getLogger(__name__)

# Injection seams. Both default to the real implementations; tests substitute
# them to reach failure boundaries that cannot be produced any other way, and to
# avoid starting a real uvicorn child in every unit test.
BackendVerifier = Callable[[object, object, Path], object]
StartupInitializer = Callable[[str, object], object]


@dataclass(frozen=True)
class RestoreServices:
    """The replaceable collaborators of one Restore attempt."""

    verify_backend: BackendVerifier = verify_restored_backend
    initialize_startup: StartupInitializer | None = None

    def startup(self, mode: str, paths: object):
        initializer = self.initialize_startup
        if initializer is None:
            from launcher.runtime import initialize_backend_startup

            initializer = initialize_backend_startup
        return initializer(mode, paths)


class RestoreEngineError(RuntimeError):
    """Raised for an internal orchestration fault that has no safe continuation."""


def _result(
    outcome: RestoreOutcome,
    phase: RestorePhase,
    operation_id: str,
    *,
    failure: RestoreFailure | None = None,
    record: RestoreOperationRecord | None = None,
    message: str | None = None,
) -> RestoreResult:
    return RestoreResult(
        outcome=outcome,
        phase=phase,
        operation_id=operation_id,
        message=message or (USER_SAFE_MESSAGES[failure] if failure else SUCCESS_MESSAGE),
        failure=failure,
        safety_copy_filename=record.safety_copy_filename if record else None,
        staged_candidate_filename=record.staged_candidate_filename if record else None,
    )


def _candidate_failure(error: CandidateRejectedError) -> RestoreFailure:
    return (
        RestoreFailure.UNSUPPORTED_SCHEMA
        if error.is_newer_schema
        else RestoreFailure.CANDIDATE_INVALID
    )


def _abort(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    workspace: RestoreWorkspace,
    failure: RestoreFailure,
) -> RestoreResult:
    """End an operation that never reached the replacement boundary.

    The working database was never touched, so this cleans only launcher-owned
    staging. A verified safety copy, when one already exists, lives in the backup
    directory and is deliberately out of reach of this cleanup.
    """
    aborted = store.transition(record, RestorePhase.ABORTED)
    workspace.clean_owned_staging(aborted.operation_id)
    workspace.clean_owned_temp_files()
    return _result(RestoreOutcome.ABORTED, RestorePhase.ABORTED, aborted.operation_id,
                   failure=failure, record=aborted)


def execute_restore(
    request: RestoreRequest,
    config,
    paths,
    *,
    services: RestoreServices | None = None,
    lock: LauncherInstanceLock | None = None,
) -> RestoreResult:
    """Execute one complete Restore attempt against the selected source.

    `lock` is the launcher-instance lock. When the caller already holds it — the
    ordinary case, since the launcher takes it at startup — it is passed in and
    reused. When it is `None`, this function acquires it for the duration, so a
    direct internal call can never run a Restore beside a live launcher.
    """
    active_services = services or RestoreServices()
    workspace = RestoreWorkspace(
        restore_dir=Path(request.restore_dir), database_path=Path(request.database_path)
    )
    operation_id = new_operation_id()

    if lock is not None and lock.held:
        return _execute_locked(request, config, paths, active_services, workspace, operation_id)
    try:
        with LauncherInstanceLock.for_workspace(workspace):
            return _execute_locked(
                request, config, paths, active_services, workspace, operation_id
            )
    except LauncherAlreadyRunningError:
        logger.warning("Restore refused: another launcher instance holds the lifecycle lock.")
        return _result(
            RestoreOutcome.ABORTED,
            RestorePhase.ABORTED,
            operation_id,
            failure=RestoreFailure.LAUNCHER_ALREADY_RUNNING,
        )


def _execute_locked(
    request: RestoreRequest,
    config,
    paths,
    services: RestoreServices,
    workspace: RestoreWorkspace,
    operation_id: str,
) -> RestoreResult:
    store = RestoreOperationStateStore(workspace)

    # ---------------------------------------------------------------- intake
    #
    # Before `prepared`, exactly as ADR 0016 § 6 orders it. Nothing has been
    # created at this point, so a rejected source leaves no operation record and
    # nothing to recover — which is the truthful state, not an omission.
    try:
        source = accept_source_path(request.selected_source, request.database_path)
    except SourceRejectedError as exc:
        logger.warning("Restore source rejected: %s", exc.rejection)
        return _result(
            RestoreOutcome.ABORTED,
            RestorePhase.ABORTED,
            operation_id,
            failure=RestoreFailure.SOURCE_REJECTED,
        )

    try:
        assert_replaceable_target(Path(request.database_path), Path(request.database_path))
    except ReplacementTargetError as exc:
        logger.warning("Restore target rejected: %s", exc)
        return _result(
            RestoreOutcome.ABORTED,
            RestorePhase.ABORTED,
            operation_id,
            failure=RestoreFailure.SAFETY_COPY_FAILED,
        )

    try:
        working_size = Path(request.database_path).stat().st_size
        assert_sufficient_disk_space(
            source_size_bytes=source.size_bytes,
            working_database_size_bytes=working_size,
            restore_dir=workspace.restore_dir,
            database_dir=Path(request.database_path).parent,
            backup_dir=Path(request.backup_dir),
        )
    except (InsufficientDiskSpaceError, OSError) as exc:
        logger.warning("Restore refused before staging: %s", type(exc).__name__)
        return _result(
            RestoreOutcome.ABORTED,
            RestorePhase.ABORTED,
            operation_id,
            failure=RestoreFailure.INSUFFICIENT_DISK_SPACE,
        )

    # -------------------------------------------------------------- prepared
    try:
        workspace.create_operation_dir(operation_id)
        record = store.create(operation_id)
    except (RestoreWorkspaceError, RestoreStateError) as exc:
        logger.error("Restore could not be prepared: %s", type(exc).__name__)
        return _result(
            RestoreOutcome.ABORTED,
            RestorePhase.ABORTED,
            operation_id,
            failure=RestoreFailure.SOURCE_REJECTED,
        )

    # --------------------------------------------------------- source_staged
    try:
        staged_path = stage_source(workspace, operation_id, source)
        record = store.transition(
            record, RestorePhase.SOURCE_STAGED, staged_candidate_filename=staged_path.name
        )
    except (StagingError, RestoreStateError, RestoreWorkspaceError) as exc:
        logger.warning("Restore staging failed: %s", type(exc).__name__)
        return _abort(store, record, workspace, RestoreFailure.SOURCE_REJECTED)

    # ---------------------------------------------------- candidate_validated
    try:
        candidate = validate_staged_candidate(staged_path)
        record = store.transition(record, RestorePhase.CANDIDATE_VALIDATED)
    except CandidateRejectedError as exc:
        logger.warning("Restore candidate rejected: %s", exc.rejection)
        return _abort(store, record, workspace, _candidate_failure(exc))
    except RestoreStateError as exc:
        logger.error("Restore state could not be published: %s", type(exc).__name__)
        return _abort(store, record, workspace, RestoreFailure.CANDIDATE_INVALID)

    # -------------------------------------------------- safety_copy_verified
    try:
        safety_copy = create_verified_safety_copy(
            Path(request.database_path), Path(request.backup_dir)
        )
        record = store.transition(
            record,
            RestorePhase.SAFETY_COPY_VERIFIED,
            safety_copy_filename=safety_copy.filename,
        )
    except (SafetyCopyError, RestoreStateError) as exc:
        logger.warning("Restore safety copy failed: %s", type(exc).__name__)
        return _abort(store, record, workspace, RestoreFailure.SAFETY_COPY_FAILED)

    # ------------------------------------------------- pre-replacement safety
    #
    # The checkpoint below mutates the working database, so it may only run once
    # the candidate is validated *and* a verified recovery point exists. Both
    # hold here. A failure is still an abort: the replacement boundary has not
    # been entered and the safety copy is retained.
    try:
        quiesce_target_journal(Path(request.database_path))
        replacement_artifact = prepare_replacement_artifact(
            candidate.path, Path(request.database_path)
        )
    except (JournalSafetyError, ReplacementError) as exc:
        logger.warning("Restore stopped before replacement: %s", type(exc).__name__)
        return _abort(store, record, workspace, RestoreFailure.REPLACEMENT_FAILED)

    # --------------------------------------------- THE DESTRUCTIVE BOUNDARY
    #
    # From here on, every failure recovers through rollback. The intent is
    # durable *before* the rename, and stays durable if the rename never happens:
    # that ambiguity is the accepted design, not a gap in it.
    try:
        record = store.transition(record, RestorePhase.REPLACEMENT_INTENT)
    except RestoreStateError as exc:
        # The intent was never published, so the boundary was never entered and
        # nothing is ambiguous. Clean up the artifact and abort.
        discard_replacement_artifact(replacement_artifact)
        logger.error("Restore could not persist the replacement intent: %s", type(exc).__name__)
        return _abort(store, record, workspace, RestoreFailure.REPLACEMENT_FAILED)

    try:
        commit_replacement(replacement_artifact, Path(request.database_path))
    except ReplacementError as exc:
        logger.error("Restore replacement failed: %s", type(exc).__name__)
        discard_replacement_artifact(replacement_artifact)
        return _enter_rollback(
            store, record, workspace, request, config, paths, services,
            RestoreFailure.REPLACEMENT_FAILED,
        )

    try:
        record = store.transition(record, RestorePhase.REPLACEMENT_COMMITTED)
        record = store.transition(record, RestorePhase.VERIFICATION_IN_PROGRESS)
    except RestoreStateError as exc:
        logger.error("Restore could not persist a post-replacement phase: %s", type(exc).__name__)
        return _enter_rollback(
            store, record, workspace, request, config, paths, services,
            RestoreFailure.REPLACEMENT_FAILED,
        )

    # ------------------------------------------------ verification_in_progress
    try:
        _verify_restored_workspace(request, config, paths, services)
    except Exception as exc:  # noqa: BLE001 - every failure here rolls back
        logger.warning("Restored workspace failed verification: %s", type(exc).__name__)
        return _enter_rollback(
            store, record, workspace, request, config, paths, services,
            RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK,
        )

    # ------------------------------------------------------------- completed
    try:
        record = store.transition(record, RestorePhase.COMPLETED)
    except RestoreStateError:
        # Verification passed but completion could not be recorded. The durable
        # state still says `verification_in_progress`, and the accepted matrix
        # requires rollback from that phase — so rolling back now is the same
        # decision the next startup would make, taken while this process is still
        # here to make it cleanly.
        logger.error("Restore could not persist completion; rolling back.")
        return _enter_rollback(
            store, record, workspace, request, config, paths, services,
            RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK,
        )

    workspace.clean_owned_staging(record.operation_id)
    workspace.clean_owned_temp_files()
    return _result(
        RestoreOutcome.COMPLETED, RestorePhase.COMPLETED, record.operation_id, record=record
    )


def _verify_restored_workspace(request: RestoreRequest, config, paths, services: RestoreServices) -> None:
    """Migrate and verify the restored working copy, and nothing else.

    Migrations run through the **existing** startup system against the exact
    restored path, so an older supported schema takes the ordinary
    `before_migration` backup on the way. The selected source and the preserved
    staged candidate are never migrated: neither is this path.
    """
    startup = services.startup(request.mode, paths)
    startup_path = Path(getattr(startup, "database_path", request.database_path))
    if startup_path != Path(request.database_path):
        raise RestoreEngineError(
            "Restored startup resolved a different database than the replacement target."
        )
    services.verify_backend(config, paths, Path(request.database_path))


# --------------------------------------------------------------------------
# Rollback
# --------------------------------------------------------------------------


def _enter_rollback(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    workspace: RestoreWorkspace,
    request: RestoreRequest,
    config,
    paths,
    services: RestoreServices,
    failure: RestoreFailure,
) -> RestoreResult:
    """Durably request rollback, then perform it.

    Any partially started backend has already been stopped: the verifier
    terminates its own child in a `finally`, so no process survives the failure
    that brought us here.
    """
    try:
        record = store.transition(record, RestorePhase.ROLLBACK_IN_PROGRESS)
    except RestoreStateError:
        # The rollback request itself could not be made durable. Nothing may
        # continue against a database whose state cannot be described.
        logger.error("Restore could not persist the rollback request.")
        return _blocked(store, record, failure_message=None)
    return perform_rollback(store, record, workspace, request, config, paths, services, failure)


def perform_rollback(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    workspace: RestoreWorkspace,
    request: RestoreRequest,
    config,
    paths,
    services: RestoreServices,
    failure: RestoreFailure = RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK,
) -> RestoreResult:
    """Restore the verified safety copy to the exact working database path.

    Safely repeatable. Every step is idempotent — verify the copy, write a fresh
    replacement artifact, rename it into place, verify the result — so a crash
    part-way through simply runs again on the next launcher start, from the same
    persisted `rollback_in_progress`.

    The one thing it will not do is guess. Without a recorded safety copy, or
    with one that no longer verifies, there is nothing provably safe to restore
    and the operation ends at `recovery_blocked` with all evidence preserved.
    """
    if record.phase is not RestorePhase.ROLLBACK_IN_PROGRESS:
        raise RestoreEngineError("Rollback may only run from a persisted rollback_in_progress.")

    if not record.safety_copy_filename:
        logger.error("Rollback has no recorded safety copy; recovery is blocked.")
        return _blocked(store, record)
    safety_copy_path = Path(request.backup_dir) / record.safety_copy_filename

    try:
        verify_safety_copy(safety_copy_path)
        quiesce_target_journal(Path(request.database_path))
        artifact = prepare_replacement_artifact(safety_copy_path, Path(request.database_path))
    except (SafetyCopyError, JournalSafetyError, ReplacementError) as exc:
        logger.error("Rollback could not be prepared: %s", type(exc).__name__)
        return _blocked(store, record)

    try:
        commit_replacement(artifact, Path(request.database_path))
    except ReplacementError as exc:
        discard_replacement_artifact(artifact)
        logger.error("Rollback replacement failed: %s", type(exc).__name__)
        return _blocked(store, record)

    try:
        startup = services.startup(request.mode, paths)
        if Path(getattr(startup, "database_path", request.database_path)) != Path(
            request.database_path
        ):
            raise RestoreEngineError("Rollback startup resolved a different database.")
        services.verify_backend(config, paths, Path(request.database_path))
    except Exception as exc:  # noqa: BLE001 - an unverifiable rollback blocks recovery
        logger.error("Rolled-back workspace failed verification: %s", type(exc).__name__)
        return _blocked(store, record)

    try:
        record = store.transition(record, RestorePhase.ROLLED_BACK)
    except RestoreStateError:
        logger.error("Rollback succeeded but could not be recorded.")
        return _blocked(store, record)

    # The previous workspace is authoritative again, so this operation's staging
    # may go. The safety copy stays exactly where it is.
    workspace.clean_owned_staging(record.operation_id)
    workspace.clean_owned_temp_files()
    return _result(
        RestoreOutcome.ROLLED_BACK,
        RestorePhase.ROLLED_BACK,
        record.operation_id,
        failure=failure,
        record=record,
    )


def _blocked(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    *,
    failure_message: str | None = None,
) -> RestoreResult:
    """End at `recovery_blocked`, preserving every piece of evidence.

    Nothing is cleaned here — not the staged candidate, not the operation record,
    not the safety copy. Only a separately defined support procedure moves an
    installation out of this condition, and it needs all of it.
    """
    try:
        blocked = store.transition(record, RestorePhase.RECOVERY_BLOCKED)
        operation_id = blocked.operation_id
        published = blocked
    except RestoreStateError:
        # Even the block could not be recorded. The reported outcome is still
        # `recovery_blocked`: the launcher cannot prove anything is safe, which
        # is precisely what that outcome means.
        logger.error("Recovery-blocked state could not be published.")
        operation_id = record.operation_id
        published = record
    return _result(
        RestoreOutcome.RECOVERY_BLOCKED,
        RestorePhase.RECOVERY_BLOCKED,
        operation_id,
        failure=RestoreFailure.RECOVERY_BLOCKED,
        record=published,
        message=failure_message,
    )
