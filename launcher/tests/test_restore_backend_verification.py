"""Bounded post-restore verification against a real backend child.

These are the only Restore tests that start uvicorn, and they are the ones that
have to: everything the accepted contract calls "verification" — the exact
database path reaching the child, the health payload, the representative reads,
the graceful stop and the second start — is a property of the real process
boundary, not of a stub.

They are deliberately few. The phase machine, the fault matrix and the recovery
table are proved elsewhere without paying for a process start each.
"""

from pathlib import Path
import socket
import sqlite3

import pytest

from app.db.config import DEFAULT_DATABASE_PATH

from launcher.config import build_runtime_config, resolve_runtime_paths
from launcher.restore.verification import (
    HEALTH_ENDPOINT,
    REPRESENTATIVE_READ_ENDPOINTS,
    VERIFICATION_CYCLES,
    BackendVerificationError,
    verify_restored_backend,
)

from launcher.tests.restore_fixtures import build_workspace_database


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def restored(monkeypatch, tmp_path):
    base = tmp_path / "user-data"
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(base))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)
    database = build_workspace_database(
        base / "data" / "cosmetic_workshop.sqlite", "restored-workspace"
    )
    return database


def test_the_bounded_verification_starts_checks_and_restarts_the_backend(restored):
    """The complete accepted check set, twice, against the exact restored path."""
    config = build_runtime_config(backend_port=free_port(), open_browser=False)

    report = verify_restored_backend(config, resolve_runtime_paths(), restored)

    assert report.database_path == restored
    assert report.cycles_completed == VERIFICATION_CYCLES == 2
    assert report.endpoints_checked == (
        HEALTH_ENDPOINT,
        "/api/settings/status",
        "/api/settings/workshop-profile",
    )


def test_the_verified_endpoints_are_the_accepted_read_only_ones():
    assert HEALTH_ENDPOINT == "/api/health"
    assert REPRESENTATIVE_READ_ENDPOINTS == (
        "/api/settings/status",
        "/api/settings/workshop-profile",
    )


def test_no_repository_fallback_database_is_created_or_modified(restored):
    """Continuity, proved by what did *not* happen to the repository default."""
    existed = DEFAULT_DATABASE_PATH.exists()
    before = DEFAULT_DATABASE_PATH.stat().st_mtime_ns if existed else None
    config = build_runtime_config(backend_port=free_port(), open_browser=False)

    verify_restored_backend(config, resolve_runtime_paths(), restored)

    if existed:
        assert DEFAULT_DATABASE_PATH.stat().st_mtime_ns == before
    else:
        assert not DEFAULT_DATABASE_PATH.exists()


def test_the_backend_serves_the_exact_restored_database(restored):
    """Observable in the database itself, not merely in an environment key."""
    config = build_runtime_config(backend_port=free_port(), open_browser=False)

    verify_restored_backend(config, resolve_runtime_paths(), restored)

    connection = sqlite3.connect(f"file:{restored}?mode=ro", uri=True)
    try:
        value = connection.execute(
            "SELECT value FROM app_settings WHERE key = 'test.workspace_marker'"
        ).fetchone()
    finally:
        connection.close()
    assert value[0] == "restored-workspace"


def test_no_backend_process_survives_verification(restored):
    """Graceful termination on both cycles, so the port is free afterwards."""
    port = free_port()
    config = build_runtime_config(backend_port=port, open_browser=False)

    verify_restored_backend(config, resolve_runtime_paths(), restored)

    # A successful bind proves the child released it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", port))


def test_a_missing_restored_database_fails_before_any_process_starts(tmp_path):
    config = build_runtime_config(backend_port=free_port(), open_browser=False)

    with pytest.raises(BackendVerificationError):
        verify_restored_backend(config, resolve_runtime_paths(), tmp_path / "absent.sqlite")


def test_readiness_polling_is_bounded_rather_than_a_fixed_sleep(monkeypatch, restored):
    """A child that never becomes ready fails inside the bound, not forever."""
    from launcher.restore import verification as verification_module

    monkeypatch.setattr(verification_module, "READINESS_TIMEOUT_SECONDS", 1.0)
    monkeypatch.setattr(verification_module, "READINESS_POLL_INTERVAL_SECONDS", 0.05)

    class NeverReady:
        def poll(self):
            return None

    with pytest.raises(BackendVerificationError):
        verification_module.wait_for_backend_ready(
            "http://127.0.0.1:1", NeverReady(), timeout_seconds=0.5
        )


def test_a_child_that_exits_immediately_is_reported_without_waiting(restored):
    """The honest answer is already available; the bound is not spent on it."""
    from launcher.restore import verification as verification_module

    class Exited:
        def poll(self):
            return 1

    with pytest.raises(BackendVerificationError, match="exited"):
        verification_module.wait_for_backend_ready(
            "http://127.0.0.1:1", Exited(), timeout_seconds=30
        )


def test_an_invalid_health_payload_is_refused():
    from launcher.restore.verification import _assert_health_payload

    for payload in ({}, {"status": ""}, [], "ok", {"other": 1}):
        with pytest.raises(BackendVerificationError):
            _assert_health_payload(payload)
