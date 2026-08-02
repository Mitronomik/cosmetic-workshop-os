"""The launcher-owned Restore safety engine (`C4-I`).

Internal infrastructure only. This package implements the accepted `CR-010`
Restore state machine — see ``docs/decisions/0016-launcher-assisted-restore.md``
and ``docs/backup-and-restore.md`` — for a future user-facing launcher flow
(`C4-II`, not authorized). It exposes **no** product Restore button, route,
dialog, CLI command, shell workflow or API endpoint, and the product-level status
of Restore remains `NOT IMPLEMENTED`.

The two entry points a caller needs:

```python
execute_restore(request, config, paths)          # run one Restore attempt
recover_incomplete_restore(db, backups, cfg, p)  # resolve state before startup
```

Everything else is a focused collaborator: `phases` owns the twelve-phase graph,
`state` the durable record and its atomic publication, `workspace` the isolated
operation directory, `instance_lock` the exclusive launcher boundary, `staging`
and `validation` the immutable source and its read-only candidate checks,
`capacity` the disk-space preflight, `safety_copy` the mandatory `before_restore`
gate, `replacement` the journal handling and the atomic boundary, `verification`
the bounded backend checks, `engine` the ordering and `recovery` the startup
matrix.
"""

from launcher.restore.contracts import (
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
    "LauncherAlreadyRunningError",
    "LauncherInstanceLock",
    "PhaseTransitionError",
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
