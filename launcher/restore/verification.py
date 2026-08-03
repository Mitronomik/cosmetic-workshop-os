"""Bounded post-restore backend verification, including restartability.

`CR-010` § 9. Passing every check here is what authorizes the durable transition
to `completed`, and `completed` is what unblocks the ordinary browser. Anything
short of that is a failed Restore that rolls back.

The backend is started through the **existing** launcher/backend boundary —
`launcher.runtime.start_backend_process`, pinned to an explicit
`COSMETIC_WORKSHOP_DB_PATH` — so no second uvicorn implementation exists and the
child cannot resolve a fallback database of its own. Readiness is *polled* within
an explicit timeout rather than slept for: a fixed sleep either wastes time or
declares success before the process is listening.

Restartability is proved, not assumed: the whole cycle runs twice against the
exact same path, with a graceful stop in between. A database that serves one
start and fails the next is not a restored workspace.

Each of those cycles is one **exact owned-backend lifetime**, and the launcher's
maintenance lease is handed over for that lifetime and taken back at the end of
it. This module does not implement the handover: it is given a
`run_backend_cycle` callable — in production
:meth:`LauncherLifecycleContext.run_owned_backend_cycle` — and calls it once per
cycle. That is what makes "the lease is reacquired between cycle 1 and cycle 2"
true by construction rather than by convention, and it is why the parameter has
no default: a caller that cannot name who owns the lease has no business starting
a backend against a database mid-Restore.

Response bodies never reach ordinary user output. They are checked here and
discarded; only the fixed category vocabulary is reported outward.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from urllib.error import URLError
import hashlib
import json
import time
import urllib.request

# The bounded representative read-only endpoints. Health proves the process is
# serving; the two settings reads prove the restored database can actually be
# opened and queried through the ordinary application stack.
HEALTH_ENDPOINT = "/api/health"
REPRESENTATIVE_READ_ENDPOINTS: tuple[str, ...] = (
    "/api/settings/status",
    "/api/settings/workshop-profile",
)

READINESS_TIMEOUT_SECONDS = 30.0
READINESS_POLL_INTERVAL_SECONDS = 0.2
REQUEST_TIMEOUT_SECONDS = 10.0
GRACEFUL_STOP_TIMEOUT_SECONDS = 10.0

# Two full start/verify/stop cycles: the second one is the restartability proof.
VERIFICATION_CYCLES = 2


class BackendVerificationError(RuntimeError):
    """Raised when the restored workspace failed a required post-restore check.

    Carries an internal reason for local technical logs only.
    """


@dataclass(frozen=True)
class BackendVerificationReport:
    """What verification actually proved, for local logging and tests."""

    database_path: Path
    cycles_completed: int
    endpoints_checked: tuple[str, ...]


def _get_json(url: str) -> object:
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise BackendVerificationError(f"Endpoint returned HTTP {response.status}.")
        return json.loads(response.read().decode("utf-8"))


def wait_for_backend_ready(base_url: str, process, *, timeout_seconds: float) -> object:
    """Poll health until it answers, the process dies, or the bound expires.

    The liveness check inside the loop matters: a child that exited immediately
    would otherwise keep this polling until the full timeout for no reason, and
    the honest answer — the backend did not start — is already available.
    """
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise BackendVerificationError("The restored backend process exited during startup.")
        try:
            return _get_json(f"{base_url}{HEALTH_ENDPOINT}")
        except (URLError, OSError, ValueError) as exc:
            last_error = exc
            time.sleep(READINESS_POLL_INTERVAL_SECONDS)
    raise BackendVerificationError(
        f"The restored backend did not become ready within the bound: {type(last_error).__name__}"
        if last_error is not None
        else "The restored backend did not become ready within the bound."
    )


def _assert_health_payload(payload: object) -> None:
    if not isinstance(payload, dict) or not payload:
        raise BackendVerificationError("The health payload was not a valid object.")
    status = payload.get("status")
    if not isinstance(status, str) or not status:
        raise BackendVerificationError("The health payload carried no status.")


def _check_representative_reads(base_url: str) -> None:
    for endpoint in REPRESENTATIVE_READ_ENDPOINTS:
        try:
            payload = _get_json(f"{base_url}{endpoint}")
        except (URLError, OSError, ValueError) as exc:
            raise BackendVerificationError(
                f"A representative read failed: {type(exc).__name__}"
            ) from exc
        if not isinstance(payload, dict):
            raise BackendVerificationError("A representative read returned an unexpected shape.")


def fallback_database_fingerprint() -> tuple[bool, int, int, int, str]:
    """A content fingerprint of the repository fallback database.

    Existence, size and mtime are not enough. A same-size write within one
    filesystem timestamp granularity leaves all three unchanged, and "the child
    quietly opened and migrated the repository database" is precisely a
    same-directory, same-name modification. The SHA-256 makes the claim
    "neither created nor modified" a statement about content.

    Stat identity is included as well, so a fallback that was replaced by a
    different file with identical content is still noticed.
    """
    from app.db.config import DEFAULT_DATABASE_PATH

    if not DEFAULT_DATABASE_PATH.exists():
        return (False, 0, 0, 0, "")
    info = DEFAULT_DATABASE_PATH.stat()
    digest = hashlib.sha256()
    with open(DEFAULT_DATABASE_PATH, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return (True, info.st_size, info.st_dev, info.st_ino, digest.hexdigest())


def _run_one_verification_cycle(config, paths, target: Path, base_url: str, cycle: int) -> None:
    """One exact owned-backend lifetime: start, check, stop, prove stopped.

    A fresh owner per cycle: the child is started, recorded, checked and then
    stopped by handle. No PID is ever discovered by port or by name.

    The stop runs in a `finally`, including on the failure path — so a
    verification failure can never leave a backend holding the database the
    caller is about to roll back. The caller's `run_backend_cycle` then waits for
    the lock to be released and takes the maintenance lease back, which is why
    this function returning is enough for the next cycle to be safe.
    """
    # Deferred: `launcher.runtime` imports this package for the startup recovery
    # gate, so importing it at module scope would be circular.
    from launcher.restore.context import BackendProcessOwner

    owner = BackendProcessOwner()
    try:
        process = owner.start(config, paths, target)
        payload = wait_for_backend_ready(
            base_url, process, timeout_seconds=READINESS_TIMEOUT_SECONDS
        )
        _assert_health_payload(payload)
        _check_representative_reads(base_url)
    except BackendVerificationError:
        raise
    except Exception as exc:
        raise BackendVerificationError(
            f"The restored backend failed verification cycle {cycle + 1}: "
            f"{type(exc).__name__}"
        ) from exc
    finally:
        proof = owner.stop(timeout_seconds=GRACEFUL_STOP_TIMEOUT_SECONDS)
        if not proof.confirmed_stopped:
            raise BackendVerificationError(
                "A verification backend could not be stopped within its bound."
            )


def verify_restored_backend(
    config, paths, database_path: Path, *, run_backend_cycle
) -> BackendVerificationReport:
    """Start, check, stop, restart, check and stop again — all bounded.

    `database_path` is the exact path the launcher prepared. It is passed to the
    child explicitly, and the repository default database is fingerprinted
    throughout: if it appears or changes, the child resolved its own database and
    the continuity this whole slice depends on was not preserved.

    `run_backend_cycle` is the launcher's owned-backend window, invoked **once
    per cycle**. Each invocation releases the maintenance lease, runs the one
    child, and takes the lease back before returning — so between cycle 1 and
    cycle 2 the launcher holds the lock again and no separate backend can slip
    into the gap. It is keyword-only and has no default: a lease handed over for
    two starts at once is the defect this shape exists to make unrepresentable.
    """
    target = Path(database_path)
    if not target.is_file():
        raise BackendVerificationError("The restored database file is missing.")

    fallback_before = fallback_database_fingerprint()
    base_url = config.backend_url

    for cycle in range(VERIFICATION_CYCLES):
        run_backend_cycle(
            partial(_run_one_verification_cycle, config, paths, target, base_url, cycle)
        )

    if fallback_database_fingerprint() != fallback_before:
        raise BackendVerificationError(
            "The repository fallback database was created or modified during verification."
        )
    if not target.is_file():
        raise BackendVerificationError("The restored database file disappeared during verification.")

    return BackendVerificationReport(
        database_path=target,
        cycles_completed=VERIFICATION_CYCLES,
        endpoints_checked=(HEALTH_ENDPOINT,) + REPRESENTATIVE_READ_ENDPOINTS,
    )
