"""The launcher-managed backend entrypoint: the lock is taken before the app.

Durable contract: ``docs/backup-and-restore.md`` § 16.3 and `CR-010` § 2.

The backend-liveness lock proves that no application backend is alive. That proof
is only as good as the moment the lock is taken, and taking it in the FastAPI
lifespan takes it **too late**:

```text
launcher spawns the child
→ Python starts, imports uvicorn, imports app.main
→ app.main imports every router, every service, the database layer
→ only then does the lifespan run and take the lock
→ the launcher dies hard somewhere inside that window
→ the next launcher sees a free lock and begins destructive work
→ the delayed child finishes importing and opens the database underneath it
```

Everything between "the process exists" and "the lock is held" is a window in
which a launcher-managed backend is invisible to the very check that authorizes
replacing the database it is about to open. This module closes it: the lock is
acquired **before any application module is imported**, and a child that cannot
take it exits without ever reaching `app.main`.

The order is the whole point, so it is written out literally:

```text
1. read the launcher-assigned lock path from the environment
2. acquire the backend liveness lock                       ← before any import
3. signal the parent launcher that *this exact child* took it
4. only now import uvicorn and app.main, and start serving
```

Step 3 is a bounded handshake over an inherited pipe the launcher created for
this one start. The launcher owns the `Popen`, so it can already say "this child
is mine"; the handshake is what lets it also say "this child holds the lock",
which no health endpoint, PID file or listening port can establish.

Nothing here discovers, signals or supervises any other process. It is one
process's own startup order, and it exits rather than continuing when the order
cannot be honoured.
"""

from __future__ import annotations

import argparse
import os
import sys

# Exit codes a launcher can distinguish. Deliberately outside the range uvicorn
# itself uses for ordinary shutdown, and never reused as a success value.
LOCK_REFUSED_EXIT_CODE = 21
HANDSHAKE_FAILED_EXIT_CODE = 22

# The inherited write end of the launcher's one-run handshake pipe, and the
# one-run token that proves the write came from the child the launcher started.
# Both are set by the launcher for exactly one spawn; neither survives it.
HANDSHAKE_FD_ENV = "COSMETIC_WORKSHOP_BACKEND_HANDSHAKE_FD"
HANDSHAKE_TOKEN_ENV = "COSMETIC_WORKSHOP_BACKEND_HANDSHAKE_TOKEN"

# What the child writes once the lock is held. The token follows it, so a reader
# can tell a complete acquisition report from a truncated one.
HANDSHAKE_ACQUIRED_PREFIX = "lock-acquired:"


def acquire_lock_before_import():
    """Take the backend liveness lock, importing nothing from the application.

    Returns the lock path when the launcher assigned one, or `None` when this
    process is not launcher-managed — a developer running the module directly,
    for instance, claims nothing and is claimed by nothing.

    The only import here is `app.services.backend_liveness`, which holds one file
    descriptor and has no domain, database or FastAPI coupling. Importing
    anything wider would reintroduce the window this module exists to close.

    Raises :class:`~app.services.backend_liveness.BackendLivenessError` when a
    lock was assigned and could not be taken. That means another backend — or a
    launcher holding a maintenance lease over a database replacement — owns this
    workspace, and continuing would put a second writer on one SQLite database.
    """
    from app.services.backend_liveness import acquire_backend_liveness_lock

    return acquire_backend_liveness_lock()


def signal_lock_acquired() -> bool:
    """Tell the parent launcher that *this* child holds the lock.

    Written to an inherited pipe descriptor rather than to a file: a pipe created
    for one spawn cannot be left behind by a previous run, so there is no stale
    evidence a later child could inherit the benefit of. The token is generated
    per start for the same reason, and the descriptor is closed immediately so
    the launcher sees EOF if this process later dies.

    Returns `False` when no handshake was requested, which is the ordinary
    unmanaged case. A requested handshake that cannot be written is a failure the
    caller must not paper over: the launcher is waiting on it and will otherwise
    time out with a child it cannot account for.
    """
    raw_fd = os.environ.get(HANDSHAKE_FD_ENV)
    token = os.environ.get(HANDSHAKE_TOKEN_ENV)
    if not raw_fd or not token:
        return False
    fd = int(raw_fd)
    payload = f"{HANDSHAKE_ACQUIRED_PREFIX}{token}\n".encode("utf-8")
    try:
        os.write(fd, payload)
    finally:
        # Closed even on a failed write: a descriptor kept open would leave the
        # launcher waiting on a pipe that will never carry anything else.
        os.close(fd)
    return True


def run_backend(host: str, port: int) -> int:
    """Import the application and serve it. Only ever called with the lock held.

    The import lives inside this function rather than at module scope so the
    ordering above is enforced by control flow rather than by a convention a
    future edit could quietly break.
    """
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Acquire, report, then serve — and refuse to reorder those three steps."""
    parser = argparse.ArgumentParser(
        prog="app.launcher_backend_entrypoint",
        description="Start the launcher-managed backend with the liveness lock held first.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args(argv)

    from app.services.backend_liveness import BackendLivenessError

    try:
        acquire_lock_before_import()
    except BackendLivenessError:
        # No traceback and no application import. Another backend, or a launcher
        # holding the maintenance lease over a destructive interval, owns this
        # workspace; the honest response is to exit before touching anything.
        print(
            "Другое окно приложения уже использует эти данные. "
            "Закройте его и попробуйте снова.",
            file=sys.stderr,
        )
        return LOCK_REFUSED_EXIT_CODE

    try:
        signal_lock_acquired()
    except OSError:
        print("Не удалось подтвердить запуск локального API.", file=sys.stderr)
        return HANDSHAKE_FAILED_EXIT_CODE

    return run_backend(arguments.host, arguments.port)


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
