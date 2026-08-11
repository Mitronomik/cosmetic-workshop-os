"""Synchronous C4-II-B2 Restore execution on the main launcher runtime path.

This module creates no thread and owns no HTTP surface. The control session may
queue one launcher-private :class:`RestoreExecutionIntent`; the main runtime is
the only caller of :func:`execute_restore_intent`, so C4-I backend stop/restart
ownership stays serialized with launcher lifetime management.

C4-I imports are intentionally deferred until execution. Importing the control
session from an HTTP worker therefore does not import or acquire the destructive
engine as an execution dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from launcher.runtime import RuntimeLaunchError
from launcher.restore.contracts import ExpectedSourceProof
from launcher.restore.control_protocol import ControlViewState

BACKEND_RESTART_BLOCKED_MESSAGE = (
    "После операции восстановления не удалось снова запустить приложение. "
    "Закройте и снова откройте приложение. Все данные сохранены."
)
MAINTENANCE_EXCLUSION_BLOCKED_MESSAGE = (
    "Приложение не может безопасно продолжить работу после восстановления. "
    "Закройте и снова откройте приложение. Все данные сохранены."
)


class RestoreExecutionSafetyError(RuntimeLaunchError):
    """B2 cannot prove the workspace is safely excluded for continued runtime."""


@dataclass(frozen=True)
class RestoreExecutionIntent:
    """One launcher-private, in-memory transfer of accepted A1/B1 authority."""

    run_id: str
    request_id: str
    command_seq: int
    generation: int
    selected_source: Path
    expected_source_proof: ExpectedSourceProof


PublishResult = Callable[..., bool]
ExecuteRestore = Callable[..., object]


def _publish_blocked(
    publish_result: PublishResult,
    intent: RestoreExecutionIntent,
    *,
    message: str,
    failure: str,
) -> None:
    publish_result(
        intent,
        state=ControlViewState.RESTORE_BLOCKED,
        message=message,
        failure=failure,
    )


def _require_maintenance_exclusion(context) -> None:
    """Require retained canonical exclusion or raise so runtime cleanup fails closed."""

    if context.maintenance_lease.held:
        return
    try:
        context.acquire_maintenance_lease()
    except Exception as exc:  # noqa: BLE001 - converted to one fixed launcher failure
        raise RestoreExecutionSafetyError(MAINTENANCE_EXCLUSION_BLOCKED_MESSAGE) from exc
    if not context.maintenance_lease.held:
        raise RestoreExecutionSafetyError(MAINTENANCE_EXCLUSION_BLOCKED_MESSAGE)


def execute_restore_intent(
    intent: RestoreExecutionIntent,
    context,
    runtime_config,
    runtime_paths,
    publish_result: PublishResult,
    *,
    execute_restore_fn: ExecuteRestore | None = None,
):
    """Run one accepted intent synchronously and return the restarted backend.

    ``None`` means C4-I truth is safely excluded but ordinary startup is blocked;
    the same launcher/control-plane run may remain alive to expose the fixed final
    state. Failure to prove maintenance exclusion raises instead, causing main
    runtime cleanup to close control authority and stop any launcher-owned backend.
    """

    from launcher.restore.contracts import (
        BACKEND_PORT_UNAVAILABLE_MESSAGE,
        ProofBoundRestoreRequest,
        RestoreFailure,
        RestoreOutcome,
    )
    from launcher.restore.engine import execute_restore
    from launcher.restore.verification import RetryableBackendStartError

    active_execute_restore = execute_restore_fn or execute_restore
    request = ProofBoundRestoreRequest(
        selected_source=Path(intent.selected_source),
        expected_source_proof=intent.expected_source_proof,
    )

    try:
        result = active_execute_restore(request, context)
    except RetryableBackendStartError:
        _require_maintenance_exclusion(context)
        _publish_blocked(
            publish_result,
            intent,
            message=BACKEND_PORT_UNAVAILABLE_MESSAGE,
            failure=RestoreFailure.BACKEND_PORT_UNAVAILABLE.value,
        )
        return None

    if not result.normal_startup_allowed:
        _require_maintenance_exclusion(context)
        _publish_blocked(
            publish_result,
            intent,
            message=result.message,
            failure=(result.failure.value if result.failure else "restore_blocked"),
        )
        return None

    _require_maintenance_exclusion(context)
    context.release_maintenance_lease()
    try:
        process = context.backend.start(
            runtime_config,
            runtime_paths,
            context.database_path,
        )
    except Exception:  # noqa: BLE001 - never expose process/handshake details
        _require_maintenance_exclusion(context)
        _publish_blocked(
            publish_result,
            intent,
            message=BACKEND_RESTART_BLOCKED_MESSAGE,
            failure="backend_restart_failed",
        )
        return None

    state = (
        ControlViewState.RESTORE_COMPLETED
        if result.outcome is RestoreOutcome.COMPLETED
        else ControlViewState.RESTORE_FAILED
    )
    publish_result(
        intent,
        state=state,
        message=result.message,
        failure=result.failure.value if result.failure else None,
    )
    return process
