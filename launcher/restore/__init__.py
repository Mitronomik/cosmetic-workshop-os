"""Launcher-owned Restore infrastructure.

C4-I implements the accepted destructive Restore safety state machine from ADR
0016. C4-II-A1 adds the merged non-destructive candidate-preparation core. C4-II-
A2 adds the exact-run launcher-owned loopback control plane from ADR 0018. C4-II-
A3 adds only the launcher-owned native macOS source picker. Product Restore remains
``NOT IMPLEMENTED``: there is still no browser Restore screen, no production
browser bootstrap handoff and no destructive confirmation flow.

Destructive entry points still require launcher lifecycle authority::

    context = LauncherLifecycleContext.acquire(config, paths)
    execute_restore(RestoreRequest(selected_source), context)
    recover_incomplete_restore(context)

The non-destructive A1 service remains the only candidate-preparation boundary::

    service = RestoreCandidatePreparationService(database_path)
    result = service.prepare_restore_candidate(selected_source)

A2 wraps that service in an authenticated exact-run local control boundary. A3
production runtime injects ``MacOSNativeSourceSelectionAdapter`` through the
existing launcher-only source-selection seam. Browser bootstrap-fragment handoff
remains A4 scope.
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
from launcher.restore.control_plane import RestoreControlPlane, RestoreControlPlaneError
from launcher.restore.control_protocol import (
    CommandReply,
    ControlSessionError,
    ControlStateSnapshot,
    ControlViewState,
    SourceSelectionAdapter,
    SourceSelectionResult,
    SourceSelectionState,
    UnavailableSourceSelectionAdapter,
)
from launcher.restore.control_session import RestoreControlSession
from launcher.restore.engine import RestoreServices, execute_restore
from launcher.restore.instance_lock import LauncherAlreadyRunningError, LauncherInstanceLock
from launcher.restore.macos_picker import MacOSNativeSourceSelectionAdapter, NativePickerError
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
    "CommandReply",
    "ControlSessionError",
    "ControlStateSnapshot",
    "ControlViewState",
    "LauncherAlreadyRunningError",
    "LauncherInstanceLock",
    "LauncherLifecycleContext",
    "MacOSNativeSourceSelectionAdapter",
    "MaintenanceLeaseError",
    "NativePickerError",
    "PhaseTransitionError",
    "RECOVERY_BLOCKED_MESSAGE",
    "ROLLED_BACK_MESSAGE",
    "RecoveryResult",
    "RestoreCandidatePreparationService",
    "RestoreControlPlane",
    "RestoreControlPlaneError",
    "RestoreControlSession",
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
    "SourceSelectionAdapter",
    "SourceSelectionResult",
    "SourceSelectionState",
    "TECHNICAL_FAILURE_MESSAGE",
    "TERMINAL_PHASES",
    "USER_SAFE_MESSAGES",
    "UnavailableSourceSelectionAdapter",
    "execute_restore",
    "prepare_restore_startup_recovery",
    "recover_incomplete_restore",
    "resolve_restore_dir",
]