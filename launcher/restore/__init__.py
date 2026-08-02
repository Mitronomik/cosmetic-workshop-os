"""The launcher-owned Restore safety engine (`C4-I`).

Internal infrastructure only. This package implements the accepted `CR-010`
Restore state machine — see ``docs/decisions/0016-launcher-assisted-restore.md``
and ``docs/backup-and-restore.md`` — for a future user-facing launcher flow
(`C4-II`, not authorized). It exposes **no** product Restore button, route,
dialog, CLI command, shell workflow or API endpoint, and the product-level status
of Restore remains `NOT IMPLEMENTED`.

The two entry points a caller needs, both requiring the launcher's authority:

```python
context = LauncherLifecycleContext.acquire(config, paths)
execute_restore(RestoreRequest(selected_source), context)   # one attempt
recover_incomplete_restore(context)                          # before startup
```

`LauncherLifecycleContext` is the gate. It holds the exclusive instance lock,
derives every destructive path from the launcher's own resolvers — the caller
supplies only the selected source — and owns any backend child, which is what
makes "the backend is stopped" provable rather than assumed.

Everything else is a focused collaborator: `phases` owns the twelve-phase graph,
`state` the durable record, `durability` the one safety-critical publication
primitive, `workspace` the isolated operation directory, `instance_lock` the
exclusive launcher boundary, `maintenance_lease` the retained exclusion that
keeps a backend from appearing during destructive work, `backend_handshake` the
bounded proof that an owned child took the liveness lock before importing the
application, `context` the lifecycle authority, `staging` and
`validation` the immutable source and its read-only checks, `capacity` the
disk-space preflight, `safety_copy` the mandatory `before_restore` gate,
`replacement` the journal handling and the atomic boundary, `verification` the
bounded backend checks, `engine` the ordering and `recovery` the startup matrix.
"""

from launcher.restore.context import (
    BackendProcessOwner,
    BackendStopProof,
    LauncherLifecycleContext,
    RestoreLifecycleError,
)
from launcher.restore.contracts import (
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
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.workspace import RestoreWorkspace, resolve_restore_dir

__all__ = [
    "ALLOWED_TRANSITIONS",
    "BackendMaintenanceLease",
    "BackendProcessOwner",
    "BackendStopProof",
    "COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE",
    "LauncherAlreadyRunningError",
    "LauncherInstanceLock",
    "LauncherLifecycleContext",
    "MaintenanceLeaseError",
    "PhaseTransitionError",
    "RestoreLifecycleError",
    "RECOVERY_BLOCKED_MESSAGE",
    "ROLLED_BACK_MESSAGE",
    "RecoveryResult",
    "RestoreFailure",
    "RestoreOutcome",
    "RestorePhase",
    "RestoreRequest",
    "RestoreResult",
    "RestoreServices",
    "RestoreWorkspace",
    "SUCCESS_MESSAGE",
    "TERMINAL_PHASES",
    "USER_SAFE_MESSAGES",
    "execute_restore",
    "recover_incomplete_restore",
    "resolve_restore_dir",
]
