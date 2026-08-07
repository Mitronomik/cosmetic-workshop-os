"""Launcher-owned Restore infrastructure.

C4-I implements the accepted destructive Restore safety state machine from ADR
0016.  C4-II-A1 adds only the separately authorized, non-destructive candidate
preparation core from the post-CR-011 slice plan.  Product Restore remains
``NOT IMPLEMENTED``: there is still no Restore browser screen, control-plane
HTTP surface, native picker integration or destructive confirmation flow.

Destructive entry points still require launcher lifecycle authority::

    context = LauncherLifecycleContext.acquire(config, paths)
    execute_restore(RestoreRequest(selected_source), context)
    recover_incomplete_restore(context)

The A1 validation service is intentionally separate::

    service = RestoreCandidatePreparationService(database_path)
    result = service.prepare_restore_candidate(selected_source)

That service creates no durable Restore operation/phase, no ``before_restore``
safety copy, no working-database mutation and no Restore AuditLog event.  It
reuses C4-I source intake/staging/validation and retains only launcher-private
in-memory source proof after successful validation.
"""

from launcher.restore.context import (
    BackendProcessOwner,
    BackendStopProof,
    LauncherLifecycleContext,
    RestoreLifecycleError,
)
from launcher.restore.contracts import (
    BACKEND_PORT_UNAVAILABLE_MESSAGE,
    COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE,
    RECOVERY_BLOCKED_MESSAGE,
    ROLLED_BACK_MESSAGE,
    SUCCESS_MESSAGE,
    USER_SAFE_MESSAGES,
    RecoveryResult,
    RestoreFailure,
    RestoreOutcome,
    RestoreRequest,
    RestoreResult,
)
from launcher.restore.engine import RestoreServices, execute_restore
from launcher.restore.instance_lock import LauncherAlreadyRunningError, LauncherInstanceLock
from launcher.restore.maintenance_lease import (
    BackendMaintenanceLease,
    MaintenanceLeaseError,
)
from launcher.restore.phases import (
    ALLOWED_TRANSITIONS,
    TERMINAL_PHASES,
    PhaseTransitionError,
    RestorePhase,
)
from launcher.restore.recovery import (
    RestoreStartupPreflight,
    prepare_restore_startup_recovery,
    recover_incomplete_restore,
)
from launcher.restore.validation_session import (
    CANCELLED_MESSAGE,
    TECHNICAL_FAILURE_MESSAGE,
    CandidateCompatibility,
    CandidatePreparationFailure,
    CandidatePreparationResult,
    CandidatePreparationState,
    RestoreCandidatePreparationService,
    RetainedSourceProof,
)
from launcher.restore.verification import RetryableBackendStartError
from launcher.restore.workspace import RestoreWorkspace, resolve_restore_dir

__all__ = [
    "ALLOWED_TRANSITIONS",
    "BACKEND_PORT_UNAVAILABLE_MESSAGE",
    "BackendMaintenanceLease",
    "BackendProcessOwner",
    "BackendStopProof",
    "CANCELLED_MESSAGE",
    "COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE",
    "CandidateCompatibility",
    "CandidatePreparationFailure",
    "CandidatePreparationResult",
    "CandidatePreparationState",
    "LauncherAlreadyRunningError",
    "LauncherInstanceLock",
    "LauncherLifecycleContext",
    "MaintenanceLeaseError",
    "PhaseTransitionError",
    "RECOVERY_BLOCKED_MESSAGE",
    "ROLLED_BACK_MESSAGE",
    "RecoveryResult",
    "RestoreCandidatePreparationService",
    "RestoreFailure",
    "RestoreLifecycleError",
    "RestoreOutcome",
    "RestorePhase",
    "RestoreRequest",
    "RestoreResult",
    "RestoreServices",
    "RestoreStartupPreflight",
    "RestoreWorkspace",
    "RetainedSourceProof",
    "RetryableBackendStartError",
    "SUCCESS_MESSAGE",
    "TECHNICAL_FAILURE_MESSAGE",
    "TERMINAL_PHASES",
    "USER_SAFE_MESSAGES",
    "execute_restore",
    "prepare_restore_startup_recovery",
    "recover_incomplete_restore",
    "resolve_restore_dir",
]
