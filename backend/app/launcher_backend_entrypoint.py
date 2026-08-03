"""The launcher-managed backend entrypoint: lock **and socket** before the app.

Durable contract: ``docs/backup-and-restore.md`` § 16.3 and `CR-010` § 2.

Two ownership facts have to be established before this process may touch the
application, and both of them have to be established *before* the launcher is
told the child started.

## The lock, before any application import

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
replacing the database it is about to open. So the lock is acquired **before any
application module is imported**, and a child that cannot take it exits without
ever reaching `app.main`.

## The listening socket, before the readiness report

The launcher probes the configured port before spawning this child, but a probe
binds, closes and returns — it establishes availability at an instant and
reserves nothing. Another program can take the port between that probe and the
moment uvicorn binds. Previously uvicorn performed that bind *after* this module
had already reported a successful start, which made a temporary socket conflict
indistinguishable from a real failure:

```text
parent probes the port          ← free
parent spawns the child
child takes the liveness lock
child reports "started"         ← the launcher now believes the backend is up
another program takes the port
child imports uvicorn
uvicorn tries to bind           ← EADDRINUSE, far too late to classify
child exits
```

The launcher then saw a child that started and then died, which during Restore
recovery is a *verification failure* — and a verification failure ends a rollback
at terminal `recovery_blocked`. A busy socket must never be able to do that.

So this module binds the real configured socket itself, before reporting
anything, and uvicorn serves **that already-bound socket**. There is no second
bind, and therefore no window between the proof and the serving.

The order is the whole point, so it is written out literally:

```text
1. parse the launcher's arguments                          stdlib only
2. acquire the backend liveness lock                       ← before any import
3. bind and listen on the exact configured host and port   ← before any import
4a. bind refused with EADDRINUSE:
       report `port-unavailable:<token>` and exit          ← before any import
4b. lock and socket both owned:
       report `ready:<token>`
5. only now import uvicorn and app.main
6. serve the application through the socket bound in step 3
```

A successful readiness report therefore means exactly this, and nothing weaker:

```text
this exact child owns the canonical backend-liveness lock
AND
this exact child owns the actual configured listening socket
```

Steps 4a and 4b are a bounded handshake over an inherited pipe the launcher
created for this one start. The launcher owns the `Popen`, so it can already say
"this child is mine"; the handshake is what lets it also say "this child holds
the lock and the socket", which no health endpoint, PID file or port scan can
establish.

`EADDRINUSE` is the only refusal reported as a port collision. An invalid host,
an unusable address family, a permission failure or any other socket error is a
real startup failure and keeps its ordinary meaning — classifying every socket
problem as "somebody else has the port" would hide genuine misconfiguration
behind a retry instruction. Nothing here parses uvicorn output to infer anything:
the structured, one-run handshake is the authority.

Nothing here discovers, signals or supervises any other process. It is one
process's own startup order, and it exits rather than continuing when the order
cannot be honoured.
"""

from __future__ import annotations

import argparse
import errno
import os
import socket
import sys

# Exit codes a launcher can distinguish. Deliberately outside the range uvicorn
# itself uses for ordinary shutdown, and never reused as a success value. They are
# **secondary** evidence: the structured handshake is what the launcher classifies
# on, because an exit code alone cannot say *which* start it belonged to.
LOCK_REFUSED_EXIT_CODE = 21
HANDSHAKE_FAILED_EXIT_CODE = 22
PORT_UNAVAILABLE_EXIT_CODE = 23
SOCKET_FAILED_EXIT_CODE = 24

# The inherited write end of the launcher's one-run handshake pipe, and the
# one-run token that proves the write came from the child the launcher started.
# Both are set by the launcher for exactly one spawn; neither survives it.
HANDSHAKE_FD_ENV = "COSMETIC_WORKSHOP_BACKEND_HANDSHAKE_FD"
HANDSHAKE_TOKEN_ENV = "COSMETIC_WORKSHOP_BACKEND_HANDSHAKE_TOKEN"

# The two structured results this child can report. Each carries the one-run
# token, so a reader can tell a complete report from a truncated one and this
# start's report from some other start's.
HANDSHAKE_READY_PREFIX = "ready:"
HANDSHAKE_PORT_UNAVAILABLE_PREFIX = "port-unavailable:"

# uvicorn's own default, used here so moving the bind into this module changes
# nothing observable about how the socket behaves.
LISTEN_BACKLOG = 2048


class ConfiguredPortUnavailableError(RuntimeError):
    """The exact configured port is held by something else, right now.

    Raised **only** for `EADDRINUSE`. Every other socket failure keeps its own
    identity, because "another program has the port" is a retry instruction and
    "this host is not usable" is not.
    """


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


def bind_configured_socket(host: str, port: int) -> socket.socket:
    """Own the exact configured listening socket, or refuse.

    Returned open and listening, and kept open for the whole process lifetime:
    this is the socket uvicorn will serve, not a reservation that gets closed and
    re-taken. Closing it between the proof and the serving would leave open
    exactly the race this function exists to eliminate.

    `SO_REUSEADDR` is set, matching what uvicorn's own `bind_socket` does, so a
    restart is not refused by a lingering `TIME_WAIT`. It does **not** weaken the
    collision check: a live listener on the same address still yields
    `EADDRINUSE`. `SO_REUSEPORT` is deliberately **not** set — two simultaneous
    listeners on one port is precisely the outcome this must never report as
    success.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(LISTEN_BACKLOG)
    except OSError as exc:
        server.close()
        if exc.errno == errno.EADDRINUSE:
            raise ConfiguredPortUnavailableError(
                "The configured port is already in use."
            ) from exc
        # An invalid host, an unusable family, a permission refusal. Not a
        # collision, and not something a user fixes by closing another program.
        raise
    return server


def _report(prefix: str) -> bool:
    """Write one structured result to the launcher's one-run pipe.

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
    payload = f"{prefix}{token}\n".encode("utf-8")
    try:
        os.write(fd, payload)
    finally:
        # Closed even on a failed write: a descriptor kept open would leave the
        # launcher waiting on a pipe that will never carry anything else.
        os.close(fd)
    return True


def signal_ready() -> bool:
    """Tell the parent launcher this child owns **both** the lock and the socket.

    Only ever called with both already in hand. Sending this earlier would make
    the word "ready" mean "the process exists", which is the weaker claim the
    launcher used to act on.
    """
    return _report(HANDSHAKE_READY_PREFIX)


def signal_port_unavailable() -> bool:
    """Tell the parent launcher the exact configured port was already taken.

    A *structured* refusal, so the launcher classifies it as an environment
    problem rather than inferring anything from an exit code, from stderr or from
    uvicorn's own log text.
    """
    return _report(HANDSHAKE_PORT_UNAVAILABLE_PREFIX)


def run_backend(server_socket: socket.socket, host: str, port: int) -> int:
    """Import the application and serve it through the socket already owned.

    Only ever called with the liveness lock held and `server_socket` bound and
    listening. The import lives inside this function rather than at module scope
    so the ordering above is enforced by control flow rather than by a convention
    a future edit could quietly break.

    `Server.run(sockets=[...])` hands the existing socket to
    `loop.create_server(sock=...)`, so uvicorn never binds again. The high-level
    `uvicorn.run(host=..., port=...)` path is deliberately not used: it would
    perform its own bind *after* readiness was reported, which is the whole
    defect this arrangement removes. `host` and `port` are still passed to the
    config so logging and generated URLs describe the socket accurately.
    """
    import uvicorn

    config = uvicorn.Config("app.main:app", host=host, port=port)
    server = uvicorn.Server(config)
    server.run(sockets=[server_socket])
    return 0


def main(argv: list[str] | None = None) -> int:
    """Acquire, bind, report, then serve — and refuse to reorder those steps."""
    parser = argparse.ArgumentParser(
        prog="app.launcher_backend_entrypoint",
        description="Start the launcher-managed backend owning its lock and socket first.",
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
        server_socket = bind_configured_socket(arguments.host, arguments.port)
    except ConfiguredPortUnavailableError:
        # Reported as a *structured* result, before any application module is
        # imported and before the database is opened. The launcher turns this into
        # its ordinary port-collision error, and Restore turns that into a
        # retryable refusal rather than a verdict about the restored database.
        try:
            signal_port_unavailable()
        except OSError:
            return HANDSHAKE_FAILED_EXIT_CODE
        return PORT_UNAVAILABLE_EXIT_CODE
    except OSError:
        # Not a collision: an invalid host, an unusable address family, a
        # permission refusal. It keeps its ordinary meaning, which is a child that
        # could not start rather than a port somebody else is using.
        print("Не удалось открыть локальный сетевой порт приложения.", file=sys.stderr)
        return SOCKET_FAILED_EXIT_CODE

    try:
        signal_ready()
    except OSError:
        server_socket.close()
        print("Не удалось подтвердить запуск локального API.", file=sys.stderr)
        return HANDSHAKE_FAILED_EXIT_CODE

    return run_backend(server_socket, arguments.host, arguments.port)


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
