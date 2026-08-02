"""The complete startup recovery matrix, resolved before ordinary startup.

`CR-010` § 7.5. Every one of the twelve phases has exactly one required
behaviour, and this module implements that table — not an equivalent of its own
choosing. An interrupted Restore may never be ignored, and no unsafe phase may
fall through to ordinary startup, startup migrations or the browser.

The four groups:

| Phases | Behaviour |
|---|---|
| `prepared`, `source_staged`, `candidate_validated`, `safety_copy_verified` | Never replaced anything. Transition to `aborted`, clean only owned staging, allow normal startup. A verified safety copy is retained. |
| `replacement_intent`, `replacement_committed`, `verification_in_progress` | Block startup. Durably enter `rollback_in_progress`, restore and verify the safety copy, end at `rolled_back` or `recovery_blocked`. |
| `rollback_in_progress` | Block startup. Continue or safely repeat the rollback. |
| `completed`, `aborted`, `rolled_back` | Terminal and safe. Confirm the record is readable, retain the safety copy, clean only owned staging, allow normal startup. |
| `recovery_blocked` | Nothing starts. All evidence preserved. One fixed non-technical result. |

A record that exists but cannot be read is **not** treated as "no operation".
That is the one case where the launcher knows something happened and cannot tell
what, and the accepted answer is `recovery_blocked`, not an optimistic start.
"""

from __future__ import annotations

from pathlib import Path
import logging

from launcher.restore.contracts import (
    RECOVERY_BLOCKED_MESSAGE,
    ROLLED_BACK_MESSAGE,
    RecoveryResult,
    RestoreOutcome,
    RestoreRequest,
)
from launcher.restore.engine import RestoreServices, perform_rollback
from launcher.restore.phases import (
    ABORTABLE_PHASES,
    ROLLBACK_REQUIRED_PHASES,
    RestorePhase,
)
from launcher.restore.state import RestoreOperationStateStore, RestoreStateError
from launcher.restore.workspace import RestoreWorkspace

logger = logging.getLogger(__name__)


def _allowed(phase: RestorePhase, operation_id: str | None, outcome: RestoreOutcome) -> RecoveryResult:
    return RecoveryResult(
        normal_startup_allowed=True, phase=phase, outcome=outcome, operation_id=operation_id
    )


def _blocked_result(
    phase: RestorePhase, operation_id: str | None, message: str
) -> RecoveryResult:
    return RecoveryResult(
        normal_startup_allowed=False,
        phase=phase,
        outcome=RestoreOutcome.RECOVERY_BLOCKED,
        operation_id=operation_id,
        message=message,
    )


def recover_incomplete_restore(
    database_path: Path,
    backup_dir: Path,
    config,
    paths,
    *,
    mode: str = "user",
    services: RestoreServices | None = None,
) -> RecoveryResult:
    """Resolve any persisted Restore operation before the backend may start.

    Returns a :class:`RecoveryResult` whose `normal_startup_allowed` is the only
    thing the launcher needs to branch on. `no_operation` is the ordinary case:
    no Restore has ever run here, so the launcher proceeds exactly as it did
    before `C4-I`.
    """
    active_services = services or RestoreServices()
    workspace = RestoreWorkspace.for_database(Path(database_path))
    store = RestoreOperationStateStore(workspace)

    if not store.has_record():
        return RecoveryResult(normal_startup_allowed=True, no_operation=True)

    try:
        record = store.read()
    except RestoreStateError as exc:
        # Present but unreadable. Nothing may be inferred from a record that
        # cannot be parsed, and "there is no operation" is not what this is.
        logger.error("Restore operation record is unreadable: %s", type(exc).__name__)
        return _blocked_result(RestorePhase.RECOVERY_BLOCKED, None, RECOVERY_BLOCKED_MESSAGE)
    if record is None:
        return RecoveryResult(normal_startup_allowed=True, no_operation=True)

    phase = record.phase

    # ------------------------------------------------ terminal blocked state
    if phase is RestorePhase.RECOVERY_BLOCKED:
        logger.error("Startup blocked: a previous Restore ended in recovery_blocked.")
        return _blocked_result(phase, record.operation_id, RECOVERY_BLOCKED_MESSAGE)

    # ------------------------------------------------- terminal safe states
    if phase in (RestorePhase.COMPLETED, RestorePhase.ABORTED, RestorePhase.ROLLED_BACK):
        # The record was readable, which is the confirmation the matrix asks for.
        # Only launcher-owned staging is cleaned; the safety copy is retained.
        workspace.clean_owned_staging(record.operation_id)
        workspace.clean_owned_temp_files()
        outcome = {
            RestorePhase.COMPLETED: RestoreOutcome.COMPLETED,
            RestorePhase.ABORTED: RestoreOutcome.ABORTED,
            RestorePhase.ROLLED_BACK: RestoreOutcome.ROLLED_BACK,
        }[phase]
        result = _allowed(phase, record.operation_id, outcome)
        if phase is RestorePhase.ROLLED_BACK:
            # Restore remains failed. Startup continues against the recovered
            # previous workspace, and the message says so rather than implying a
            # successful Restore.
            return RecoveryResult(
                normal_startup_allowed=True,
                phase=phase,
                outcome=RestoreOutcome.ROLLED_BACK,
                operation_id=record.operation_id,
                message=ROLLED_BACK_MESSAGE,
            )
        return result

    # ------------------------------------------------- pre-replacement states
    if phase in ABORTABLE_PHASES:
        # Nothing was replaced, so nothing is rolled back and the replacement is
        # never executed automatically. The operation is closed out and ordinary
        # startup continues against the existing working database.
        try:
            aborted = store.transition(record, RestorePhase.ABORTED)
        except RestoreStateError:
            logger.error("An interrupted Restore could not be closed out.")
            return _blocked_result(
                RestorePhase.RECOVERY_BLOCKED, record.operation_id, RECOVERY_BLOCKED_MESSAGE
            )
        workspace.clean_owned_staging(aborted.operation_id)
        workspace.clean_owned_temp_files()
        return _allowed(RestorePhase.ABORTED, aborted.operation_id, RestoreOutcome.ABORTED)

    # ------------------------------------------------ rollback-required states
    request = RestoreRequest(
        # Recovery never touches the selected source, and the durable record
        # deliberately does not store its path. The staged candidate is preserved
        # evidence; rollback restores from the safety copy alone.
        selected_source=Path(database_path),
        database_path=Path(database_path),
        backup_dir=Path(backup_dir),
        restore_dir=workspace.restore_dir,
        mode=mode,
    )

    if phase in ROLLBACK_REQUIRED_PHASES:
        try:
            record = store.transition(record, RestorePhase.ROLLBACK_IN_PROGRESS)
        except RestoreStateError:
            logger.error("Rollback could not be durably requested during recovery.")
            return _blocked_result(
                RestorePhase.RECOVERY_BLOCKED, record.operation_id, RECOVERY_BLOCKED_MESSAGE
            )

    # `rollback_in_progress` arrives here either from the transition above or
    # from a crash during a previous rollback. Both continue the same way, which
    # is what makes rollback safely repeatable.
    result = perform_rollback(
        store, record, workspace, request, config, paths, active_services
    )
    if result.outcome is RestoreOutcome.ROLLED_BACK:
        return RecoveryResult(
            normal_startup_allowed=True,
            phase=RestorePhase.ROLLED_BACK,
            outcome=RestoreOutcome.ROLLED_BACK,
            operation_id=result.operation_id,
            message=ROLLED_BACK_MESSAGE,
        )
    return _blocked_result(
        RestorePhase.RECOVERY_BLOCKED, result.operation_id, RECOVERY_BLOCKED_MESSAGE
    )
