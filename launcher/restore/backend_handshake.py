"""The bounded proof that *this exact child* acquired the backend liveness lock.

Owning a `Popen` proves the launcher started a process. It does not prove that
the process took the liveness lock, and the gap between those two facts is a real
window: a child exists for some time before it holds anything, and during that
window every liveness check reports "no backend is alive" about a backend that is
very much on its way.

What is deliberately **not** used to close that gap:

`a PID file`
    PIDs are reused, and a file written by a previous run is indistinguishable
    from one written by this one.
`a listening port`
    A port describes a socket. It says nothing about which process holds a
    database, and during Restore the port is free by design.
`a process name or command line`
    Matching on either would mean acting on a process this launcher did not
    start, which is a second failure mode rather than a safety measure.
`the health endpoint`
    Health proves the application is serving, which happens *after* the import
    this handshake exists to gate. It is checked as well, never instead.

What is used is an ordinary anonymous pipe, created by the launcher for exactly
one spawn and inherited by exactly one child, carrying a token generated for that
same spawn. Both halves are one-run values:

- a pipe from a previous start is closed and gone, so no stale evidence exists
  for a later child to benefit from;
- a token from a previous start does not match this start's expected value, so
  even a replayed payload is refused;
- the child closes its end immediately, so a child that dies before writing gives
  the launcher EOF rather than a hang.

Every wait is bounded. Timeout, EOF, a mismatched token and an early child exit
are all the same answer: this child is not proved to hold the lock, so it is
stopped, no browser opens and Restore does not proceed.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import secrets
import select
import time


def _entrypoint():
    """The backend's own entrypoint module, imported lazily.

    Deferred for the same reason every other backend import in this package is:
    `backend/` only joins `sys.path` at runtime through
    `launcher.runtime.ensure_backend_import_path`. Reading the variable names and
    the payload prefix from the backend rather than restating them here is what
    keeps the two halves of the handshake from drifting apart — a renamed
    variable on one side would otherwise become a silent timeout on the other.
    """
    from app import launcher_backend_entrypoint

    return launcher_backend_entrypoint


# Generous enough for a cold Python start on a slow disk, bounded so a wedged
# child can never hold the launcher — or a Restore — open indefinitely.
HANDSHAKE_TIMEOUT_SECONDS = 60.0

# The pipe carries one short line. Reading more than this would mean the child
# wrote something this protocol does not define, which is itself a refusal.
_MAX_HANDSHAKE_BYTES = 512


class BackendHandshakeError(RuntimeError):
    """Raised when a started child could not be proved to hold the liveness lock."""


@dataclass
class PendingBackendHandshake:
    """One spawn's handshake: a private pipe and a one-run token.

    Created before the child, consumed once, and closed either way. Not reusable
    and not shared between starts — that is what makes "stale evidence cannot
    satisfy a new start" a property of the mechanism rather than a rule someone
    has to remember.
    """

    read_fd: int
    write_fd: int
    token: str
    _closed: bool = False

    @property
    def child_environment(self) -> dict[str, str]:
        """The two variables the child reads, and nothing else."""
        entrypoint = _entrypoint()
        return {
            entrypoint.HANDSHAKE_FD_ENV: str(self.write_fd),
            entrypoint.HANDSHAKE_TOKEN_ENV: self.token,
        }

    @property
    def pass_fds(self) -> tuple[int, ...]:
        """The descriptors `Popen` must let the child inherit."""
        return (self.write_fd,)

    def close_child_end(self) -> None:
        """Close the launcher's copy of the write end, right after the spawn.

        Required, not tidiness. While the launcher still holds a write end the
        pipe never reaches EOF, so a child that died before writing would leave
        the read below waiting for the full timeout instead of reporting the
        failure it can already see.
        """
        if self.write_fd < 0:
            return
        fd, self.write_fd = self.write_fd, -1
        try:
            os.close(fd)
        except OSError:
            pass

    def await_acquisition(
        self, process, *, timeout_seconds: float = HANDSHAKE_TIMEOUT_SECONDS
    ) -> str:
        """Block, bounded, until this child reports the lock — or fail.

        Four distinct failures, one answer. The child exited before reporting;
        the pipe reached EOF without a complete line; the payload did not carry
        this start's token; the bound expired. None of them may be treated as a
        started backend, so each raises.

        The token comparison uses a constant-time helper. Not because an attacker
        is modelled here, but because "compare the whole value, always" is the
        habit that keeps a partial match from ever being accepted.
        """
        deadline = time.monotonic() + timeout_seconds
        buffer = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BackendHandshakeError(
                    "The backend child did not report the liveness lock within its bound."
                )
            try:
                ready, _, _ = select.select([self.read_fd], [], [], min(remaining, 0.2))
            except OSError as exc:
                raise BackendHandshakeError(
                    f"The backend handshake could not be read: {type(exc).__name__}"
                ) from exc

            if ready:
                try:
                    chunk = os.read(self.read_fd, _MAX_HANDSHAKE_BYTES)
                except OSError as exc:
                    raise BackendHandshakeError(
                        f"The backend handshake could not be read: {type(exc).__name__}"
                    ) from exc
                if not chunk:
                    raise BackendHandshakeError(
                        "The backend child closed the handshake without reporting the lock."
                    )
                buffer.extend(chunk)
                if b"\n" in buffer:
                    return self._accept(bytes(buffer))
                if len(buffer) >= _MAX_HANDSHAKE_BYTES:
                    raise BackendHandshakeError(
                        "The backend child wrote an unrecognized handshake payload."
                    )
                continue

            # Nothing readable. A child that has already exited is never going to
            # write, so that is reported now rather than at the deadline.
            if process is not None and process.poll() is not None:
                raise BackendHandshakeError(
                    "The backend child exited before reporting the liveness lock."
                )

    def _accept(self, payload: bytes) -> str:
        prefix = _entrypoint().HANDSHAKE_ACQUIRED_PREFIX
        try:
            line = payload.decode("utf-8").splitlines()[0]
        except (UnicodeDecodeError, IndexError) as exc:
            raise BackendHandshakeError(
                "The backend child wrote an unreadable handshake payload."
            ) from exc
        if not line.startswith(prefix):
            raise BackendHandshakeError(
                "The backend child wrote an unrecognized handshake payload."
            )
        reported = line[len(prefix) :]
        if not secrets.compare_digest(reported, self.token):
            # A token from some other start. Stale or replayed evidence is exactly
            # what this value exists to refuse.
            raise BackendHandshakeError(
                "The backend handshake carried a token from a different start."
            )
        return reported

    def close(self) -> None:
        """Release both descriptors. Safe to call more than once."""
        if self._closed:
            return
        self._closed = True
        self.close_child_end()
        fd, self.read_fd = self.read_fd, -1
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass


def new_backend_handshake() -> PendingBackendHandshake:
    """One fresh pipe and one fresh token, for exactly one child start."""
    read_fd, write_fd = os.pipe()
    # Inherited on purpose, and only this one descriptor: `Popen(pass_fds=...)`
    # clears the inheritable flag on everything else.
    os.set_inheritable(write_fd, True)
    return PendingBackendHandshake(
        read_fd=read_fd, write_fd=write_fd, token=secrets.token_hex(16)
    )
