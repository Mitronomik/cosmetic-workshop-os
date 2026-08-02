"""Orchestration of one Restore attempt, in the exact accepted order.

This module is the only place that decides *when* each step runs. Every step
itself lives in a focused module beside it, and the phase machine lives in
`phases`. What is here is the sequence `CR-010` § 6 and § 7.3 accept, and the
failure handling § 10 requires:

```text
require launcher authority (held lock, canonical paths)
→ stop any launcher-owned backend, and prove it stopped
→ open the selected source read-only and hold the descriptor
→ disk-space preflight                (before any large artifact)
→ isolated operation directory        [prepared]
→ stage from the held descriptor      [source_staged]
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

Two rules govern every failure path.

**Before `replacement_intent`, failure ends at `aborted`** and the working
database was never touched. **At or after it, failure enters rollback** —
including when the replacement call itself failed, because a persisted
`replacement_intent` is treated as though replacement may have occurred and no
filesystem appearance may be used to argue otherwise.

**A phase that could not be durably published is never assumed.** When a
publication fails with `published=True` the rename already landed and only its
durability is unproven, so the engine **re-reads the authoritative record** and
acts on whatever is actually there. Every result reports that real durable phase
alongside the outcome, so a caller can never be told a phase is on disk when it
is not.

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
from launcher.restore.context import LauncherLifecycleContext, RestoreLifecycleError
from launcher.restore.contracts import (
    RestoreFailure,
    RestoreOutcome,
    RestoreRequest,
    RestoreResult,
    SUCCESS_MESSAGE,
    USER_SAFE_MESSAGES,
)
from launcher.restore.phases import (
    ROLLBACK_REQUIRED_PHASES,
    UNSAFE_STARTUP_PHASES,
    RestorePhase,
)
from launcher.restore.replacement import (
    JournalSafetyError,
    ReplacementError,
    ReplacementTargetError,
    assert_replaceable_target,
    commit_replacement,
    discard_owned_replacement_artifact,
    discard_replacement_artifact,
    prepare_replacement_artifact,
    quiesce_target_journal,
)
from launcher.restore.safety_copy import SafetyCopyError, create_verified_safety_copy, verify_safety_copy
from launcher.restore.staging import (
    SourceRejectedError,
    StagingError,
    open_selected_source,
    stage_source,
)
from launcher.restore.state import (
    RestoreOperationRecord,
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.validation import CandidateRejectedError, validate_staged_candidate
from launcher.restore.verification import verify_restored_backend
from launcher.restore.workspace import RestoreWorkspaceError, new_operation_id

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


# --------------------------------------------------------------------------
# Result construction
# --------------------------------------------------------------------------


def _durable_phase(store: RestoreOperationStateStore) -> RestorePhase | None:
    """The phase actually on disk right now, or `None` when it cannot be read.

    `None` is not "no operation" — a record that exists but will not parse also
    lands here, and every caller treats an unknown phase as unsafe.
    """
    try:
        record = store.read()
    except RestoreStateError:
        return None
    return record.phase if record is not None else None


def _result(
    outcome: RestoreOutcome,
    durable_phase: RestorePhase | None,
    operation_id: str,
    *,
    failure: RestoreFailure | None = None,
    record: RestoreOperationRecord | None = None,
    message: str | None = None,
    normal_startup_allowed: bool | None = None,
) -> RestoreResult:
    if normal_startup_allowed is None:
        # Derived from the phase actually on disk, never from the intent. An
        # unknown phase is unsafe by construction.
        normal_startup_allowed = (
            durable_phase is not None and durable_phase not in UNSAFE_STARTUP_PHASES
        )
    return RestoreResult(
        outcome=outcome,
        durable_phase=durable_phase,
        operation_id=operation_id,
        message=message or (USER_SAFE_MESSAGES[failure] if failure else SUCCESS_MESSAGE),
        normal_startup_allowed=normal_startup_allowed,
        failure=failure,
        safety_copy_filename=record.safety_copy_filename if record else None,
        staged_candidate_filename=record.staged_candidate_filename if record else None,
    )


def _refused_before_any_state(
    operation_id: str, failure: RestoreFailure
) -> RestoreResult:
    """A refusal that happened before any operation record existed.

    Nothing was created, so there is no durable phase and nothing to recover.
    Ordinary startup stays allowed: the working database was never approached.
    """
    return RestoreResult(
        outcome=RestoreOutcome.ABORTED,
        durable_phase=None,
        operation_id=operation_id,
        message=USER_SAFE_MESSAGES[failure],
        normal_startup_allowed=True,
        failure=failure,
    )


def _source_failure(error: SourceRejectedError) -> RestoreFailure:
    return (
        RestoreFailure.CANDIDATE_INVALID
        if error.is_sidecar_dependency
        else RestoreFailure.SOURCE_REJECTED
    )


def _candidate_failure(error: CandidateRejectedError) -> RestoreFailure:
    return (
        RestoreFailure.UNSUPPORTED_SCHEMA
        if error.is_newer_schema
        else RestoreFailure.CANDIDATE_INVALID
    )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def execute_restore(
    request: RestoreRequest,
    context: LauncherLifecycleContext,
    *,
    services: RestoreServices | None = None,
) -> RestoreResult:
    """Execute one complete Restore attempt against the selected source.

    `context` is the launcher's authority: it carries the held instance lock, the
    canonically derived database, backup and Restore paths, and ownership of any
    backend child. There is no code path that reaches the replacement boundary
    without one, so a bare internal call cannot bypass the gate.
    """
    active_services = services or RestoreServices()
    operation_id = new_operation_id()

    try:
        context.require_authority()
    except RestoreLifecycleError as exc:
        logger.error("Restore refused: %s", exc)
        return _refused_before_any_state(
            operation_id, RestoreFailure.LAUNCHER_ALREADY_RUNNING
        )

    # The ordinary backend must be provably stopped before anything can touch the
    # working database — including the safety copy, which reads it. A free port
    # is not proof, and the launcher lock is not proof either, because the
    # backend child never takes it. Owning the handle and watching it die is.
    try:
        context.stop_backend()
    except RestoreLifecycleError as exc:
        logger.error("Restore refused: %s", exc)
        return _refused_before_any_state(
            operation_id, RestoreFailure.LAUNCHER_ALREADY_RUNNING
        )

    return _execute_authorized(request, context, active_services, operation_id)


def _execute_authorized(
    request: RestoreRequest,
    context: LauncherLifecycleContext,
    services: RestoreServices,
    operation_id: str,
) -> RestoreResult:
    workspace = context.workspace
    store = RestoreOperationStateStore(workspace)
    database_path = context.database_path
    backup_dir = context.backup_dir

    # ---------------------------------------------------------------- intake
    #
    # Before `prepared`, exactly as ADR 0016 § 6 orders it. Nothing has been
    # created at this point, so a rejected source leaves no operation record and
    # nothing to recover — which is the truthful state, not an omission.
    try:
        assert_replaceable_target(database_path, context)
    except ReplacementTargetError as exc:
        logger.error("Restore target rejected: %s", exc)
        return _refused_before_any_state(operation_id, RestoreFailure.SAFETY_COPY_FAILED)

    try:
        held = open_selected_source(request.selected_source, database_path)
    except SourceRejectedError as exc:
        logger.warning("Restore source rejected: %s", exc.rejection)
        return _refused_before_any_state(operation_id, _source_failure(exc))

    # The descriptor is held for the whole of staging, so identity cannot be
    # swapped underneath the copy.
    with held:
        return _execute_with_source(
            held, context, services, operation_id, store, database_path, backup_dir
        )


def _execute_with_source(
    held,
    context: LauncherLifecycleContext,
    services: RestoreServices,
    operation_id: str,
    store: RestoreOperationStateStore,
    database_path: Path,
    backup_dir: Path,
) -> RestoreResult:
    workspace = context.workspace

    try:
        working_size = database_path.stat().st_size
        assert_sufficient_disk_space(
            source_size_bytes=held.size_bytes,
            working_database_size_bytes=working_size,
            restore_dir=workspace.restore_dir,
            database_dir=database_path.parent,
            backup_dir=backup_dir,
        )
    except (InsufficientDiskSpaceError, OSError) as exc:
        logger.warning("Restore refused before staging: %s", type(exc).__name__)
        return _refused_before_any_state(
            operation_id, RestoreFailure.INSUFFICIENT_DISK_SPACE
        )

    # -------------------------------------------------------------- prepared
    try:
        workspace.create_operation_dir(operation_id)
        record = store.create(operation_id)
    except (RestoreWorkspaceError, RestoreStateError) as exc:
        logger.error("Restore could not be prepared: %s", type(exc).__name__)
        return _refused_before_any_state(operation_id, RestoreFailure.SOURCE_REJECTED)

    # --------------------------------------------------------- source_staged
    try:
        staged_path = stage_source(workspace, operation_id, held)
    except SourceRejectedError as exc:
        logger.warning("Restore source rejected during staging: %s", exc.rejection)
        return _abort(store, record, workspace, context, _source_failure(exc))
    except (StagingError, RestoreWorkspaceError) as exc:
        logger.warning("Restore staging failed: %s", type(exc).__name__)
        return _abort(store, record, workspace, context, RestoreFailure.SOURCE_REJECTED)

    published = _publish(
        store, record, RestorePhase.SOURCE_STAGED, staged_candidate_filename=staged_path.name
    )
    if published.failed:
        return _handle_publication_failure(
            store, published, workspace, context, services, RestoreFailure.SOURCE_REJECTED
        )
    record = published.record

    # ---------------------------------------------------- candidate_validated
    try:
        candidate = validate_staged_candidate(staged_path)
    except CandidateRejectedError as exc:
        logger.warning("Restore candidate rejected: %s", exc.rejection)
        return _abort(store, record, workspace, context, _candidate_failure(exc))

    published = _publish(store, record, RestorePhase.CANDIDATE_VALIDATED)
    if published.failed:
        return _handle_publication_failure(
            store, published, workspace, context, services, RestoreFailure.CANDIDATE_INVALID
        )
    record = published.record

    # -------------------------------------------------- safety_copy_verified
    try:
        safety_copy = create_verified_safety_copy(database_path, backup_dir)
    except SafetyCopyError as exc:
        logger.warning("Restore safety copy failed: %s", type(exc).__name__)
        return _abort(store, record, workspace, context, RestoreFailure.SAFETY_COPY_FAILED)

    published = _publish(
        store,
        record,
        RestorePhase.SAFETY_COPY_VERIFIED,
        safety_copy_filename=safety_copy.filename,
    )
    if published.failed:
        return _handle_publication_failure(
            store, published, workspace, context, services, RestoreFailure.SAFETY_COPY_FAILED
        )
    record = published.record

    # ------------------------------------------------- pre-replacement safety
    #
    # The checkpoint below mutates the working database, so it may only run once
    # the candidate is validated, a verified recovery point exists, **and** the
    # backend is still provably stopped. A failure is still an abort: the
    # replacement boundary has not been entered and the safety copy is retained.
    try:
        context.require_backend_stopped()
        quiesce_target_journal(database_path)
        replacement_artifact = prepare_replacement_artifact(
            candidate.path, database_path, operation_id
        )
    except (RestoreLifecycleError, JournalSafetyError, ReplacementError) as exc:
        logger.warning("Restore stopped before replacement: %s", type(exc).__name__)
        return _abort(store, record, workspace, context, RestoreFailure.REPLACEMENT_FAILED)

    # --------------------------------------------- THE DESTRUCTIVE BOUNDARY
    #
    # From here on, every failure recovers through rollback. The intent is
    # durable *before* the rename, and stays durable if the rename never happens:
    # that ambiguity is the accepted design, not a gap in it.
    published = _publish(store, record, RestorePhase.REPLACEMENT_INTENT)
    if published.failed:
        if not published.may_be_durable:
            # The intent was never published, so the boundary was never entered
            # and nothing is ambiguous. Clean up the artifact and abort.
            discard_replacement_artifact(replacement_artifact)
            logger.error("Restore could not persist the replacement intent.")
            return _abort(store, record, workspace, context, RestoreFailure.REPLACEMENT_FAILED)
        # The intent may already be on disk. Re-read and let the actual phase
        # decide, because aborting over a durable `replacement_intent` would be
        # exactly the unauthorized shortcut § 7.4 forbids.
        return _handle_publication_failure(
            store, published, workspace, context, services, RestoreFailure.REPLACEMENT_FAILED
        )
    record = published.record

    try:
        commit_replacement(replacement_artifact, database_path)
    except ReplacementError as exc:
        logger.error("Restore replacement failed: %s", type(exc).__name__)
        if not exc.may_have_replaced:
            discard_replacement_artifact(replacement_artifact)
        # Either way the durable phase is `replacement_intent`, which the
        # accepted matrix resolves through rollback.
        return _enter_rollback(
            store, record, workspace, context, services, RestoreFailure.REPLACEMENT_FAILED
        )

    for target_phase in (RestorePhase.REPLACEMENT_COMMITTED, RestorePhase.VERIFICATION_IN_PROGRESS):
        published = _publish(store, record, target_phase)
        if published.failed:
            return _handle_publication_failure(
                store, published, workspace, context, services,
                RestoreFailure.REPLACEMENT_FAILED,
            )
        record = published.record

    # ------------------------------------------------ verification_in_progress
    try:
        _verify_restored_workspace(context, services)
    except Exception as exc:  # noqa: BLE001 - every failure here rolls back
        logger.warning("Restored workspace failed verification: %s", type(exc).__name__)
        return _enter_rollback(
            store, record, workspace, context, services,
            RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK,
        )

    # ------------------------------------------------------------- completed
    published = _publish(store, record, RestorePhase.COMPLETED)
    if published.failed:
        # Verification passed but completion could not be recorded. If the record
        # may already say `completed`, re-reading settles it; if it certainly does
        # not, the durable state is still `verification_in_progress`, and the
        # accepted matrix requires rollback from there — the same decision the
        # next startup would make, taken while this process can make it cleanly.
        return _handle_publication_failure(
            store, published, workspace, context, services,
            RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK,
        )
    record = published.record

    workspace.clean_owned_staging(record.operation_id)
    workspace.clean_owned_temp_files()
    discard_owned_replacement_artifact(database_path, record.operation_id)
    return _result(
        RestoreOutcome.COMPLETED, RestorePhase.COMPLETED, record.operation_id, record=record
    )


def _verify_restored_workspace(context: LauncherLifecycleContext, services: RestoreServices) -> None:
    """Migrate and verify the restored working copy, and nothing else.

    Migrations run through the **existing** startup system against the exact
    restored path, so an older supported schema takes the ordinary
    `before_migration` backup on the way. The selected source and the preserved
    staged candidate are never migrated: neither is this path.
    """
    startup = services.startup(context.mode, context.paths)
    startup_path = Path(getattr(startup, "database_path", context.database_path))
    if startup_path != context.database_path:
        raise RestoreEngineError(
            "Restored startup resolved a different database than the replacement target."
        )
    services.verify_backend(context.config, context.paths, context.database_path)


# --------------------------------------------------------------------------
# Durable publication, and what a failed one means
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _Publication:
    """The outcome of one attempted phase publication.

    `may_be_durable` is the whole point. A publication that failed *before* the
    rename definitely did not happen; one that failed at or after it may already
    be on disk, and the only honest next step is to re-read.
    """

    record: RestoreOperationRecord
    failed: bool = False
    may_be_durable: bool = False


def _publish(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    target: RestorePhase,
    **fields,
) -> _Publication:
    """Attempt one authorized transition, classifying any failure."""
    try:
        return _Publication(record=store.transition(record, target, **fields))
    except RestoreStateError as exc:
        logger.error(
            "Restore could not publish %s (may be durable: %s)", target.value, exc.published
        )
        return _Publication(record=record, failed=True, may_be_durable=exc.published)


def _handle_publication_failure(
    store: RestoreOperationStateStore,
    published: _Publication,
    workspace,
    context: LauncherLifecycleContext,
    services: RestoreServices,
    failure: RestoreFailure,
) -> RestoreResult:
    """Resolve a failed publication from the phase that is *actually* on disk.

    Never assumes. The record is re-read, and the accepted matrix for whatever
    phase is really there decides: a pre-replacement phase aborts, a
    rollback-required phase rolls back, and an unreadable record blocks.
    """
    actual = store.read_durable_record(published.record)
    phase = actual.phase

    if phase in ROLLBACK_REQUIRED_PHASES:
        return _enter_rollback(store, actual, workspace, context, services, failure)
    if phase is RestorePhase.ROLLBACK_IN_PROGRESS:
        return perform_rollback(store, actual, workspace, context, services, failure)
    if phase in UNSAFE_STARTUP_PHASES:
        # `recovery_blocked` already, or something else nothing may continue from.
        return _blocked_without_transition(actual, failure)
    return _abort(store, actual, workspace, context, failure)


def _blocked_without_transition(
    record: RestoreOperationRecord, failure: RestoreFailure
) -> RestoreResult:
    """Report an unsafe durable phase truthfully, changing nothing.

    Used when the durable phase is already unsafe and no authorized transition
    leads anywhere better. Forcing the record into `recovery_blocked` from here
    would be an unauthorized edge, and claiming a phase that is not on disk is
    exactly the dishonesty this result type exists to prevent. The next launcher
    start resumes from the real phase.
    """
    return _result(
        RestoreOutcome.RECOVERY_BLOCKED,
        record.phase,
        record.operation_id,
        failure=RestoreFailure.RECOVERY_BLOCKED,
        record=record,
        normal_startup_allowed=False,
    )


def _abort(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    workspace,
    context: LauncherLifecycleContext,
    failure: RestoreFailure,
) -> RestoreResult:
    """End an operation that never reached the replacement boundary.

    The working database was never touched, so this cleans only launcher-owned
    staging and the one deterministically named replacement artifact this
    operation may have created. A verified safety copy lives in the backup
    directory and is deliberately out of reach of this cleanup.
    """
    published = _publish(store, record, RestorePhase.ABORTED)
    if published.failed:
        actual = store.read_durable_record(record)
        if actual.phase is not RestorePhase.ABORTED:
            # The abort did not stick. Nothing destructive happened, but the
            # operation is still live on disk, so it is reported as-is and the
            # next startup resolves it through the ordinary matrix.
            return _result(
                RestoreOutcome.ABORTED,
                actual.phase,
                actual.operation_id,
                failure=failure,
                record=actual,
            )
        published = _Publication(record=actual)

    aborted = published.record
    workspace.clean_owned_staging(aborted.operation_id)
    workspace.clean_owned_temp_files()
    discard_owned_replacement_artifact(context.database_path, aborted.operation_id)
    return _result(
        RestoreOutcome.ABORTED,
        RestorePhase.ABORTED,
        aborted.operation_id,
        failure=failure,
        record=aborted,
    )


# --------------------------------------------------------------------------
# Rollback
# --------------------------------------------------------------------------


def _enter_rollback(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    workspace,
    context: LauncherLifecycleContext,
    services: RestoreServices,
    failure: RestoreFailure,
) -> RestoreResult:
    """Durably request rollback, then perform it.

    Any partially started backend has already been stopped: the verifier owns and
    terminates its own children in a `finally`, so no process survives the failure
    that brought us here.

    If the request itself cannot be published, **no unauthorized transition is
    attempted**. `replacement_intent → recovery_blocked` is not in the accepted
    graph, and forcing it would raise from inside the launcher boundary. The
    actual durable phase is reported instead, ordinary startup stays blocked, and
    the next launcher start retries recovery from that real phase.
    """
    published = _publish(store, record, RestorePhase.ROLLBACK_IN_PROGRESS)
    if published.failed:
        actual = store.read_durable_record(record)
        if actual.phase is not RestorePhase.ROLLBACK_IN_PROGRESS:
            logger.error(
                "Rollback could not be durably requested; durable phase remains %s.",
                actual.phase.value,
            )
            return _blocked_without_transition(actual, failure)
        published = _Publication(record=actual)

    return perform_rollback(store, published.record, workspace, context, services, failure)


def perform_rollback(
    store: RestoreOperationStateStore,
    record: RestoreOperationRecord,
    workspace,
    context: LauncherLifecycleContext,
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

    database_path = context.database_path
    if not record.safety_copy_filename:
        logger.error("Rollback has no recorded safety copy; recovery is blocked.")
        return _blocked(store, record)
    safety_copy_path = context.backup_dir / record.safety_copy_filename

    try:
        context.require_backend_stopped()
        verify_safety_copy(safety_copy_path)
        quiesce_target_journal(database_path)
        artifact = prepare_replacement_artifact(
            safety_copy_path, database_path, record.operation_id
        )
    except (RestoreLifecycleError, SafetyCopyError, JournalSafetyError, ReplacementError) as exc:
        logger.error("Rollback could not be prepared: %s", type(exc).__name__)
        return _blocked(store, record)

    try:
        commit_replacement(artifact, database_path)
    except ReplacementError as exc:
        if not exc.may_have_replaced:
            discard_replacement_artifact(artifact)
        # A rollback replacement whose durability cannot be proved leaves a
        # working database nothing may be started against.
        logger.error("Rollback replacement failed: %s", type(exc).__name__)
        return _blocked(store, record)

    try:
        startup = services.startup(context.mode, context.paths)
        if Path(getattr(startup, "database_path", database_path)) != database_path:
            raise RestoreEngineError("Rollback startup resolved a different database.")
        services.verify_backend(context.config, context.paths, database_path)
    except Exception as exc:  # noqa: BLE001 - an unverifiable rollback blocks recovery
        logger.error("Rolled-back workspace failed verification: %s", type(exc).__name__)
        return _blocked(store, record)

    published = _publish(store, record, RestorePhase.ROLLED_BACK)
    if published.failed:
        actual = store.read_durable_record(record)
        if actual.phase is not RestorePhase.ROLLED_BACK:
            logger.error("Rollback succeeded but could not be recorded.")
            return _blocked(store, actual)
        published = _Publication(record=actual)
    record = published.record

    # The previous workspace is authoritative again, so this operation's staging
    # may go. The safety copy stays exactly where it is.
    workspace.clean_owned_staging(record.operation_id)
    workspace.clean_owned_temp_files()
    discard_owned_replacement_artifact(database_path, record.operation_id)
    return _result(
        RestoreOutcome.ROLLED_BACK,
        RestorePhase.ROLLED_BACK,
        record.operation_id,
        failure=failure,
        record=record,
    )


def _blocked(
    store: RestoreOperationStateStore, record: RestoreOperationRecord
) -> RestoreResult:
    """End at `recovery_blocked`, preserving every piece of evidence.

    Nothing is cleaned here — not the staged candidate, not the operation record,
    not the safety copy, not the replacement artifact. Only a separately defined
    support procedure moves an installation out of this condition, and it needs
    all of it.

    Only reachable from `rollback_in_progress`, which is the one phase the
    accepted graph allows to enter `recovery_blocked`. If the publication itself
    fails, the durable phase stays `rollback_in_progress` and is reported as
    such — the next launcher start safely repeats the rollback rather than acting
    on a phase that was never written.
    """
    published = _publish(store, record, RestorePhase.RECOVERY_BLOCKED)
    if published.failed:
        actual = store.read_durable_record(record)
        return _result(
            RestoreOutcome.RECOVERY_BLOCKED,
            actual.phase,
            actual.operation_id,
            failure=RestoreFailure.RECOVERY_BLOCKED,
            record=actual,
            normal_startup_allowed=False,
        )
    blocked = published.record
    return _result(
        RestoreOutcome.RECOVERY_BLOCKED,
        RestorePhase.RECOVERY_BLOCKED,
        blocked.operation_id,
        failure=RestoreFailure.RECOVERY_BLOCKED,
        record=blocked,
        normal_startup_allowed=False,
    )
