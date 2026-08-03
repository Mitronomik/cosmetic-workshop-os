"""The retained launcher maintenance lease over the backend-liveness lock.

Authoritative contract: ``docs/backup-and-restore.md`` § 16.4 and
``docs/decisions/0016-launcher-assisted-restore.md`` § 2.

## Why a momentary check is not enough

The earlier proof opened the canonical backend-liveness lock, took a non-blocking
exclusive `flock`, released it and closed the descriptor. That answers exactly one
question — *was the lock free at that instant?* — and Restore needs a different
one, which is *will it stay free for the whole destructive interval?*

```text
launcher checks the lock            ← free
launcher releases the lock
another backend acquires it         ← nothing prevented this
launcher settles the SQLite journal
launcher replaces the working database
```

Every individual step still reported success, and a live writer was holding the
database the whole way through. Availability is not reservation.

## What the lease is

The same canonical `backend-liveness.lock`, taken by the launcher and **kept**
for the whole interval in which the working database may be read or written. It
is the identical primitive the backend child uses for its own lifetime, which is
what makes the two mutually exclusive without a second coordination mechanism:

```text
lease held by the launcher → no backend can start against this workspace
lock held by a backend     → the launcher cannot take the lease
```

Held through safety-copy creation, journal settlement, replacement-artifact
preparation, the replacement itself, rollback replacement and post-replacement
verification of the file. Released only when an owned backend genuinely has to
run — startup, or a verification cycle — and reacquired before anything
destructive resumes.

## What it is not

Not a supervisor, not a daemon, not a registry. It holds one descriptor and
answers one question. It never discovers, signals or terminates any process: a
lease that cannot be taken means somebody else owns this workspace, and the
response to that is to refuse, never to clear the way.
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
import fcntl
import logging
import os
import time

logger = logging.getLogger(__name__)

# How long to keep retrying the lease after an owned backend was stopped. A child
# that has exited may still be milliseconds from having its descriptors reaped,
# and failing the reacquisition over that would block a recovery that is fine.
LEASE_REACQUIRE_TIMEOUT_SECONDS = 15.0
LEASE_REACQUIRE_POLL_SECONDS = 0.05


class MaintenanceLeaseError(RuntimeError):
    """Raised when the launcher cannot hold exclusive use of the workspace."""


class BackendMaintenanceLease:
    """A retained exclusive lease on one workspace's backend-liveness lock.

    Idempotent to acquire and to release, because the lifecycle around it is a
    sequence of nested intervals rather than a single balanced pair: startup
    recovery may already hold what a Restore attempt then needs, and neither
    should have to know whether the other ran first.
    """

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = Path(lock_path)
        self._fd: int | None = None

    @classmethod
    def for_workspace(cls, workspace) -> "BackendMaintenanceLease":
        """The lease over the canonical lock of one Restore workspace."""
        return cls(workspace.backend_liveness_lock_path)

    @property
    def held(self) -> bool:
        return self._fd is not None

    def acquire(self) -> "BackendMaintenanceLease":
        """Take and **keep** the lock. Raises when anything else holds it.

        Already holding it is a no-op rather than an error: the destructive
        interval is entered from more than one place, and re-entering an interval
        that is already open is not a conflict.
        """
        if self._fd is not None:
            return self

        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as exc:
            # A lock path that cannot even be opened cannot prove anything, and
            # this class is only ever consulted for permission to do something
            # destructive.
            raise MaintenanceLeaseError(
                f"The backend maintenance lease could not be opened: {type(exc).__name__}"
            ) from exc

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise MaintenanceLeaseError(
                "Another application backend holds this workspace; "
                "the maintenance lease cannot be taken."
            ) from exc

        try:
            # Diagnostic only, exactly as in the instance lock and the backend's
            # own liveness lock. Nothing reads this back as authority — the held
            # flock is the authority, and a PID would be the reusable identifier
            # this whole design avoids depending on.
            os.ftruncate(fd, 0)
            os.write(fd, f"launcher-maintenance {os.getpid()}\n".encode("ascii"))
        except OSError:
            pass

        self._fd = fd
        return self

    def acquire_with_retry(
        self,
        *,
        timeout_seconds: float = LEASE_REACQUIRE_TIMEOUT_SECONDS,
        poll_seconds: float = LEASE_REACQUIRE_POLL_SECONDS,
    ) -> "BackendMaintenanceLease":
        """Reacquire after an owned backend was stopped, within a bound.

        `poll()` reports that the child exited; it does not report that the kernel
        has finished releasing its descriptors. Retrying briefly is the difference
        between a normal verification cycle and a spurious `recovery_blocked`.
        Still bounded: a lock that stays held belongs to something this launcher
        does not own, and waiting forever on that is not a recovery strategy.
        """
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                return self.acquire()
            except MaintenanceLeaseError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(poll_seconds)

    def release(self) -> None:
        """Give the lock back so an owned backend can take it.

        Deliberately *not* called at the end of every destructive step. The lease
        is released for exactly one reason — an owned backend must run — and the
        caller that releases it is the caller responsible for reacquiring it
        before the next destructive step.
        """
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            os.close(fd)

    def require_held(self, what: str) -> None:
        """Refuse an operation that needs exclusive use but does not have it."""
        if not self.held:
            raise MaintenanceLeaseError(
                f"{what} requires the retained backend maintenance lease."
            )

    def __enter__(self) -> "BackendMaintenanceLease":
        return self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
