"""The backend-liveness lock: proof that no application backend is still running.

Durable contract: ``docs/backup-and-restore.md`` § 16.3 and `CR-010` § 2.

Restore may not replace the working database while a backend can still write to
it. The launcher proves that by owning the child's process handle — but an
in-memory handle dies with the launcher. After a **hard launcher crash**:

```text
launcher is killed (SIGKILL, power loss, panic)
→ the in-memory Popen handle is gone
→ the uvicorn child keeps running and keeps the database open
→ the next launcher owns no process
→ "nothing was running" — which is false
```

A PID file cannot close that gap: PIDs are reused, so a recorded PID that is
alive today may belong to something else entirely. A listening port cannot close
it either — a port is evidence about a socket, not about which process holds a
database, and during Restore the port is free by design.

What does close it is a lock **held by the backend process itself** for its whole
lifetime. The kernel releases an `fcntl.flock` when the holding process dies, for
any reason, without needing any cleanup code to run. So:

```text
lock is held   → an application backend is alive, whoever started it
lock is free   → no application backend is alive
```

That is a fact about the operating system's process table, not about anything
this application remembered to write down.

## The contract

The launcher passes an exact lock path in `COSMETIC_WORKSHOP_BACKEND_LIVENESS_LOCK`
and the backend takes the lock during startup, holding the descriptor open until
the process exits. When the variable is **absent** — the ordinary test client, a
developer importing the app directly — no lock is taken and nothing is claimed;
the launcher is the only thing that sets it, and the launcher is the only thing
that consumes it.

When the variable is present and the lock **cannot** be taken, startup fails.
That means another backend is already alive against this workspace, and serving a
second one would put two writers on one SQLite database.

This module holds one descriptor and nothing else. It is not a process
supervisor, not a daemon, and it has no domain coupling: no route, no table, no
AuditLog event, no migration.
"""

from __future__ import annotations

from pathlib import Path
import fcntl
import os

# The exact lock path, supplied by the launcher. Absent means "not launcher-managed".
BACKEND_LIVENESS_LOCK_ENV = "COSMETIC_WORKSHOP_BACKEND_LIVENESS_LOCK"


class BackendLivenessError(RuntimeError):
    """Raised when the backend cannot establish its expected liveness contract."""


# The held descriptor, kept at module scope for the process lifetime. Deliberately
# never closed by ordinary code: the kernel releasing it on process exit *is* the
# signal, and closing it early would announce that the backend had stopped while
# it was still serving.
_LIVENESS_FD: int | None = None


def configured_liveness_lock_path() -> Path | None:
    """The lock path the launcher assigned, or `None` when unmanaged."""
    configured = os.environ.get(BACKEND_LIVENESS_LOCK_ENV)
    return Path(configured) if configured else None


def holds_liveness_lock() -> bool:
    return _LIVENESS_FD is not None


def acquire_backend_liveness_lock() -> Path | None:
    """Take the liveness lock for this process's whole lifetime.

    Returns the lock path when one was taken, or `None` when this backend is not
    launcher-managed. Raises :class:`BackendLivenessError` when the launcher
    assigned a lock that could not be taken — which means another application
    backend is already alive against this workspace.

    Idempotent: a second call while the lock is held is a no-op, so an app
    created twice in one process does not fight itself.
    """
    global _LIVENESS_FD

    lock_path = configured_liveness_lock_path()
    if lock_path is None:
        return None
    if _LIVENESS_FD is not None:
        return lock_path

    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError as exc:
        raise BackendLivenessError(
            f"The backend liveness lock could not be opened: {type(exc).__name__}"
        ) from exc

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        os.close(fd)
        raise BackendLivenessError(
            "Another application backend is already running against this workspace."
        ) from exc

    try:
        # Diagnostic only. Nothing reads this back as authority — the held lock is
        # the authority, and a PID written here would be exactly the reusable
        # identifier this design exists to avoid depending on.
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("ascii"))
    except OSError:
        pass

    _LIVENESS_FD = fd
    return lock_path


def release_backend_liveness_lock() -> None:
    """Release the lock explicitly.

    Only for tests and for a process that is deliberately standing down while
    staying alive. Ordinary shutdown does **not** need this: process exit releases
    the lock, which is the property the whole design rests on.
    """
    global _LIVENESS_FD

    fd, _LIVENESS_FD = _LIVENESS_FD, None
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        os.close(fd)
