"""The launcher lifecycle context: the only gate into destructive Restore work.

Two independent findings are closed here, and they belong together because both
are about *who is allowed to say what*.

## Canonical paths are derived, never supplied

`CR-010` § 2 makes the launcher the owner of the Restore lifecycle. If a caller
could hand in the database path, the backup directory and the Restore directory,
then a caller could take the lock and write operation state for one location
while replacing a database somewhere else — and every individual check would
still pass, because each was asked about a path the caller chose.

So exactly one value comes from the future Restore caller: **the selected
source**. Everything destructive or application-owned is resolved here, from the
existing repository resolvers:

```text
database path    ← app.services.startup.startup_database_config(mode)
backup directory ← app.services.backup.resolve_backup_dir(config)
Restore directory← RestoreWorkspace.for_database(database path)
lock path        ← the same workspace
```

One database identity produces the lock, the operation record, the safety copy
and the replacement target. `verify_derived_paths()` re-derives all of them and
compares, so a context mutated after construction is refused before any staging.

## The backend must be provably stopped, and must stay stopped

A held launcher lock does not prove Uvicorn is stopped: the backend child never
takes that lock. A free port proves even less — during Restore the port is free
*by design*. The only sound proof is process ownership: the launcher either has
not started the backend yet, or it holds the exact `Popen` handle it started and
has watched that handle die.

Ownership answers "is *my* backend gone". It does not answer "can another one
appear", and neither does a momentary liveness check: proving the lock was free
at one instant leaves the whole destructive interval afterwards unprotected. So
the launcher takes the same canonical backend-liveness lock and **retains** it —
a :class:`~launcher.restore.maintenance_lease.BackendMaintenanceLease` — for
every step that reads or writes the working database. While it is held no backend
can start against this workspace, because the child's own lock acquisition is the
thing that would have to succeed.

The lease is released for exactly one reason: an owned backend genuinely has to
run, for ordinary startup or for a verification cycle. It is reacquired before
anything destructive resumes, and a reacquisition that fails blocks rather than
continues.

`BackendProcessOwner` is that handle. It terminates **only** the process it
recorded, escalating to `kill()` on the same handle after a bounded wait, and
confirms `poll()` is no longer `None` before returning a proof. Nothing here
discovers processes by port, by name or by command-line pattern, and `pkill`,
`lsof` and pattern matching are deliberately absent — killing a process this
launcher did not start is not a safety measure, it is a second failure mode.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
import fcntl
import logging
import os
import time

from launcher.restore.instance_lock import LauncherInstanceLock
from launcher.restore.maintenance_lease import (
    BackendMaintenanceLease,
    MaintenanceLeaseError,
)
from launcher.restore.workspace import RestoreWorkspace, resolve_restore_dir

logger = logging.getLogger(__name__)

# How long a backend gets to shut down gracefully before the owned handle is
# killed. Generous enough for uvicorn's own shutdown, bounded so Restore cannot
# hang on a wedged child.
BACKEND_GRACEFUL_STOP_SECONDS = 10.0
BACKEND_KILL_WAIT_SECONDS = 5.0

# How long to wait for a stopped child to actually release its liveness lock.
BACKEND_LIVENESS_WAIT_SECONDS = 10.0
BACKEND_LIVENESS_POLL_SECONDS = 0.05


def backend_liveness_lock_is_free(lock_path: Path) -> bool:
    """Whether **no** application backend currently holds the liveness lock.

    The proof is a non-blocking exclusive `flock` that is released immediately.
    Taking it means nobody else had it; failing to take it means a live process
    does, whichever launcher started that process and whether or not this launcher
    remembers it.

    That last part is the whole point. After a hard launcher crash the in-memory
    `Popen` is gone but the orphaned backend is still running and still holding
    this lock, because the kernel only releases it when the holding process dies.
    A PID file could not say this — PIDs are reused — and a listening port could
    not either, since a port describes a socket rather than who holds a database.

    Acquiring and releasing is deliberate: this call proves availability, it does
    not reserve it. The launcher instance lock is what keeps a second launcher
    from racing in between, and the backend this launcher starts next needs to be
    able to take the liveness lock itself.
    """
    path = Path(lock_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError:
        # An unreadable lock path cannot prove absence, and this function is only
        # ever consulted for permission to do something destructive.
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return True
    finally:
        os.close(fd)


class RestoreLifecycleError(RuntimeError):
    """Raised when the launcher lifecycle cannot authorize destructive work."""


@dataclass(frozen=True)
class BackendStopProof:
    """Evidence that no launcher-owned backend is running.

    `confirmed_stopped` is the only field the engine gates on. `was_running` and
    `pid` exist so a test — and a local log — can show *which* process was
    stopped, which is what distinguishes this from "nothing was running, so
    nothing needed stopping".
    """

    pid: int | None
    was_running: bool
    graceful: bool
    confirmed_stopped: bool


class BackendProcessOwner:
    """Owns at most one launcher-started backend child, by handle.

    Not a process supervisor and not a generic manager: it can hold one handle,
    stop that handle, and say whether it is dead. Anything broader would be the
    generic framework `CR-010` refuses for a bounded problem.
    """

    def __init__(self) -> None:
        self._process = None
        self._pid: int | None = None

    @property
    def pid(self) -> int | None:
        return self._pid

    @property
    def has_process(self) -> bool:
        return self._process is not None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def adopt(self, process) -> None:
        """Record a backend child this launcher started.

        Refuses to replace a live handle. Losing track of a running child is
        exactly how an unowned process survives Restore, and overwriting the
        handle is how that happens silently.
        """
        if self.is_running:
            raise RestoreLifecycleError(
                "A launcher-owned backend process is already being tracked."
            )
        self._process = process
        self._pid = getattr(process, "pid", None)

    def start(self, config, paths, database_path: Path):
        """Start an owned backend child that has **proved** it holds the lock.

        The child runs the launcher-managed entrypoint, which acquires the
        backend-liveness lock before importing any application module and then
        reports that acquisition over a one-run inherited pipe. This returns only
        after that report arrives, so "the backend started" and "the backend holds
        the lock" are the same fact rather than two hopefully-related ones.

        A child that cannot take the lock, exits early, or does not report within
        the bound is stopped here and raises: the launcher never carries on with a
        process it cannot account for.

        Deferred import: `launcher.runtime` imports this package for the startup
        recovery gate, so a module-scope import would be circular.
        """
        from launcher.runtime import start_owned_backend_process

        process = start_owned_backend_process(config, paths, Path(database_path))
        self.adopt(process)
        return process

    def wait_until_liveness_lock_released(
        self, lock_path: Path, *, timeout_seconds: float = BACKEND_LIVENESS_WAIT_SECONDS
    ) -> bool:
        """Wait, bounded, for the backend-liveness lock to become free.

        `poll()` reports that *our* child has exited; it does not report that the
        child has finished releasing its descriptors. On a normal stop those are
        microseconds apart, but Restore is about to replace a database on the
        strength of that lock being free, so it waits for the lock itself rather
        than assuming process exit is instantaneous.
        """
        deadline = time.monotonic() + timeout_seconds
        while True:
            if backend_liveness_lock_is_free(lock_path):
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(BACKEND_LIVENESS_POLL_SECONDS)

    def stop(self, timeout_seconds: float = BACKEND_GRACEFUL_STOP_SECONDS) -> BackendStopProof:
        """Stop the owned child, and prove it is gone.

        Graceful `SIGTERM` first; on timeout, `kill()` on **the same handle** —
        never a PID looked up by port or name. Returns only after `poll()` shows
        the process has actually exited, because "we asked it to stop" is not
        proof that it did.
        """
        from launcher.runtime import terminate_process

        process = self._process
        if process is None:
            # The launcher never started a backend in this lifecycle, so there is
            # nothing that could hold the database open on its behalf.
            return BackendStopProof(
                pid=None, was_running=False, graceful=True, confirmed_stopped=True
            )

        pid = self._pid
        was_running = process.poll() is None
        graceful = True
        if was_running:
            try:
                terminate_process(process, timeout_seconds=timeout_seconds)
            except Exception as exc:  # noqa: BLE001 - reported through the proof
                logger.error("Backend termination raised: %s", type(exc).__name__)
            graceful = process.poll() == 0 or process.poll() is not None

        confirmed = process.poll() is not None
        if not confirmed:
            # `terminate_process` already escalates to `kill()` on this handle.
            # Reaching here means even that did not take effect within the bound,
            # and the honest answer is that the backend is not proved stopped.
            logger.error("The launcher-owned backend did not stop within its bound.")
        else:
            self._process = None
        return BackendStopProof(
            pid=pid,
            was_running=was_running,
            graceful=graceful,
            confirmed_stopped=confirmed,
        )


@dataclass
class LauncherLifecycleContext:
    """One launcher instance's authority over one workspace.

    Constructed by :meth:`acquire`, which is what makes the lock, the canonical
    paths and the process ownership arrive together. A caller cannot assemble
    partial authority: without this object the engine refuses to run at all.
    """

    config: object
    paths: object
    mode: str
    database_path: Path
    backup_dir: Path
    workspace: RestoreWorkspace
    lock: LauncherInstanceLock
    maintenance_lease: BackendMaintenanceLease
    backend: BackendProcessOwner = field(default_factory=BackendProcessOwner)
    _backend_stop_proof: BackendStopProof | None = field(default=None, repr=False)

    # ------------------------------------------------------------ construction

    @classmethod
    def acquire(cls, config, paths) -> "LauncherLifecycleContext":
        """Resolve every canonical path, then take the exclusive launcher lock.

        `startup_database_config` only computes a path — it creates no directory,
        database or migration — so this is safe to call before the port check has
        even decided whether startup may continue.
        """
        from launcher.runtime import ensure_backend_import_path

        ensure_backend_import_path(paths)
        from app.services.backup import resolve_backup_dir
        from app.services.startup import startup_database_config

        mode = getattr(config, "mode", "user")
        database_config = startup_database_config(mode)
        database_path = Path(database_config.path)
        backup_dir = Path(resolve_backup_dir(database_config))
        workspace = RestoreWorkspace.for_database(database_path)

        context = cls(
            config=config,
            paths=paths,
            mode=mode,
            database_path=database_path,
            backup_dir=backup_dir,
            workspace=workspace,
            lock=LauncherInstanceLock.for_workspace(workspace),
            maintenance_lease=BackendMaintenanceLease.for_workspace(workspace),
        )
        context.verify_derived_paths()
        context.lock.acquire()
        return context

    # -------------------------------------------------------------- authority

    def verify_derived_paths(self) -> None:
        """Re-derive every canonical path and refuse a context that disagrees.

        The paths were derived from the resolvers at construction, so this can
        only fail if the context was mutated afterwards — which is exactly the
        tampering it exists to catch. Cheap, and it runs before staging on every
        destructive entry point.
        """
        from app.db.config import DatabaseConfig
        from app.services.backup import resolve_backup_dir

        expected_backup_dir = Path(resolve_backup_dir(DatabaseConfig(path=self.database_path)))
        if self.backup_dir != expected_backup_dir:
            raise RestoreLifecycleError(
                "The Restore backup directory is not the one this database resolves to."
            )
        expected_restore_dir = resolve_restore_dir(self.database_path)
        if self.workspace.restore_dir != expected_restore_dir:
            raise RestoreLifecycleError(
                "The Restore operation directory is not the one this database resolves to."
            )
        if self.workspace.database_path != self.database_path:
            raise RestoreLifecycleError(
                "The Restore workspace does not describe the canonical database."
            )
        if self.lock.lock_path != self.workspace.lock_path:
            raise RestoreLifecycleError(
                "The launcher lock does not guard the canonical Restore directory."
            )
        if self.maintenance_lease.lock_path != self.workspace.backend_liveness_lock_path:
            # A lease over some other path would keep a backend out of a workspace
            # this Restore is not about, while leaving the real target unguarded.
            raise RestoreLifecycleError(
                "The maintenance lease does not guard the canonical backend-liveness lock."
            )

    def require_authority(self) -> None:
        """Refuse destructive work without a held lock and canonical paths."""
        if not self.lock.held:
            raise RestoreLifecycleError(
                "Restore requires the exclusive launcher instance lock to be held."
            )
        self.verify_derived_paths()

    # -------------------------------------------------------- backend stopping

    @property
    def backend_stop_proof(self) -> BackendStopProof | None:
        return self._backend_stop_proof

    @property
    def backend_liveness_lock_path(self) -> Path:
        return self.workspace.backend_liveness_lock_path

    def no_backend_is_alive(self) -> bool:
        """Whether **no** application backend can be holding the working database.

        Two ways to be true, and the first is stronger. When this launcher holds
        the retained maintenance lease, the answer is yes by construction: the
        lease *is* the backend-liveness lock, so no backend can hold it. Otherwise
        the lock is probed momentarily, which answers availability only — it says
        the lock was free at that instant and reserves nothing.
        """
        if self.maintenance_lease.held:
            return True
        return backend_liveness_lock_is_free(self.backend_liveness_lock_path)

    def stop_backend(self) -> BackendStopProof:
        """Stop any launcher-owned backend and **take** the maintenance lease.

        Three facts, and none of them implies the next:

        1. the child *this* launcher owns has exited — proved by its handle;
        2. no application backend at all holds the liveness lock — proved by
           taking that lock, which an orphan from a previously crashed launcher
           would still be holding even though this process owns nothing;
        3. no application backend can appear during what follows — proved by
           **keeping** the lock rather than releasing it.

        The third is the one a momentary check could never give. Acquiring and
        immediately releasing establishes availability at an instant and reserves
        nothing, so a backend starting one millisecond later would be holding the
        database through journal settlement and replacement while every individual
        check had reported success.

        An orphan is never killed: this launcher did not start it, so it has
        detection but no authority, and the safe response is to refuse rather than
        to signal a process it cannot account for.
        """
        self.require_authority()
        proof = self.backend.stop()
        self._backend_stop_proof = proof
        if not proof.confirmed_stopped:
            raise RestoreLifecycleError(
                "The launcher-owned backend could not be proved stopped."
            )

        # A child that just exited may still be milliseconds from releasing its
        # descriptors, so this waits for the lock rather than assuming.
        if proof.was_running:
            self.backend.wait_until_liveness_lock_released(self.backend_liveness_lock_path)

        self.acquire_maintenance_lease()
        return proof

    # ------------------------------------------------------ maintenance lease

    def acquire_maintenance_lease(self) -> None:
        """Take and retain exclusive use of the workspace, or refuse.

        A failure here is never "try harder": the lock is held by an application
        backend this launcher does not own, and the accepted answer to that is to
        stop, not to clear the way.
        """
        try:
            self.maintenance_lease.acquire_with_retry()
        except MaintenanceLeaseError as exc:
            raise RestoreLifecycleError(
                "Another application backend is still running against this workspace."
            ) from exc

    def release_maintenance_lease(self) -> None:
        """Give the workspace back so an owned backend may start."""
        self.maintenance_lease.release()

    @contextmanager
    def owned_backend_window(self):
        """Release the lease for one owned-backend interval, then take it back.

        The exact accepted cycle, in one place so no call site can implement half
        of it:

        ```text
        release the maintenance lease
        → start the owned child through the pre-import lock entrypoint
        → wait for that exact child's lock-acquired handshake
        → verify
        → stop the child by its owned handle
        → wait for the lock to be released
        → reacquire the maintenance lease
        → only then continue, replace or roll back
        ```

        The lease is reacquired on the failure path too, because the failure path
        leads to rollback and rollback replaces the working database. When the
        reacquisition itself fails, that is raised — a rollback without the lease
        is precisely the destructive work this object exists to gate.
        """
        self.release_maintenance_lease()
        try:
            yield self
        finally:
            self.backend.wait_until_liveness_lock_released(
                self.backend_liveness_lock_path
            )
            self.acquire_maintenance_lease()

    def require_backend_stopped(self) -> BackendStopProof:
        """Assert the backend is stopped **and still excluded**, right now.

        Re-checks every fact rather than trusting the earlier proof: a launcher
        that started a backend since, and — the part a momentary check cannot
        give — that this launcher still holds the retained maintenance lease. A
        lease that was released, or was never taken, means the workspace is
        unreserved, and an unreserved workspace is not authority for destructive
        work no matter how free the lock looked a moment ago.
        """
        proof = self._backend_stop_proof
        if proof is None or not proof.confirmed_stopped:
            raise RestoreLifecycleError(
                "Restore may not touch the working database without backend-stop proof."
            )
        if self.backend.is_running:
            raise RestoreLifecycleError(
                "A launcher-owned backend is running again; Restore cannot continue."
            )
        try:
            self.maintenance_lease.require_held(
                "Touching the working database"
            )
        except MaintenanceLeaseError as exc:
            raise RestoreLifecycleError(
                "Restore does not hold the retained backend maintenance lease; "
                "the working database may not be touched."
            ) from exc
        return proof

    # ---------------------------------------------------------------- cleanup

    def release(self) -> None:
        self.maintenance_lease.release()
        self.lock.release()

    def __enter__(self) -> "LauncherLifecycleContext":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
