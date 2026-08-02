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

## The backend must be provably stopped

A held launcher lock does not prove Uvicorn is stopped: the backend child never
takes that lock. A free port proves even less — during Restore the port is free
*by design*. The only sound proof is process ownership: the launcher either has
not started the backend yet, or it holds the exact `Popen` handle it started and
has watched that handle die.

`BackendProcessOwner` is that handle. It terminates **only** the process it
recorded, escalating to `kill()` on the same handle after a bounded wait, and
confirms `poll()` is no longer `None` before returning a proof. Nothing here
discovers processes by port, by name or by command-line pattern, and `pkill`,
`lsof` and pattern matching are deliberately absent — killing a process this
launcher did not start is not a safety measure, it is a second failure mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
import logging

from launcher.restore.instance_lock import LauncherInstanceLock
from launcher.restore.workspace import RestoreWorkspace, resolve_restore_dir

logger = logging.getLogger(__name__)

# How long a backend gets to shut down gracefully before the owned handle is
# killed. Generous enough for uvicorn's own shutdown, bounded so Restore cannot
# hang on a wedged child.
BACKEND_GRACEFUL_STOP_SECONDS = 10.0
BACKEND_KILL_WAIT_SECONDS = 5.0


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
        """Start the ordinary backend child and record the handle.

        Deferred import: `launcher.runtime` imports this package for the startup
        recovery gate, so a module-scope import would be circular.
        """
        from launcher.runtime import start_backend_process

        process = start_backend_process(config, paths, Path(database_path))
        self.adopt(process)
        return process

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

    def stop_backend(self) -> BackendStopProof:
        """Stop any launcher-owned backend and record the proof.

        Called once, before anything that could touch the working database. The
        proof is kept so later stages can assert it rather than re-deriving it —
        and so `require_backend_stopped()` fails loudly if it was never taken.
        """
        self.require_authority()
        proof = self.backend.stop()
        self._backend_stop_proof = proof
        if not proof.confirmed_stopped:
            raise RestoreLifecycleError(
                "The launcher-owned backend could not be proved stopped."
            )
        return proof

    def require_backend_stopped(self) -> BackendStopProof:
        """Assert the backend-stop proof exists and still holds.

        Re-checks liveness rather than trusting the earlier proof: between the
        stop and the replacement boundary the only thing that could start a
        backend is this launcher, and if it somehow did, the proof is stale.
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
        return proof

    # ---------------------------------------------------------------- cleanup

    def release(self) -> None:
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
