"""Finder-visible presentation for non-zero launcher return codes."""

from __future__ import annotations

from types import SimpleNamespace
import socket

import pytest

from macos_package import entrypoint
from macos_package.user_alert import (
    DATA_UNCHANGED_SENTENCE,
    STARTUP_FAILURE_MESSAGES,
    StartupFailure,
)


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture(autouse=True)
def disable_real_alerts(monkeypatch):
    monkeypatch.setenv("COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS", "1")


def _run_with_launcher_result(tmp_path, monkeypatch, launcher_result: int):
    frontend_root = tmp_path / "dist"
    frontend_root.mkdir()
    (frontend_root / "index.html").write_text("<html></html>", encoding="utf-8")

    layout = SimpleNamespace(frontend_dist_dir=frontend_root, is_packaged=True)
    monkeypatch.setattr(entrypoint, "resolve_package_layout", lambda: layout)
    monkeypatch.setattr(entrypoint, "_refuse_incomplete_package", lambda _layout: None)

    import launcher.runtime as launcher_runtime

    monkeypatch.setattr(launcher_runtime, "run_local_runtime", lambda _config: launcher_result)

    reported: list[tuple[StartupFailure, bool, str | None]] = []

    def _record(failure, *, packaged, detail=None):
        reported.append((failure, packaged, detail))

    monkeypatch.setattr(entrypoint, "report_startup_failure", _record)

    code = entrypoint.run_packaged_application(
        [
            "--no-browser",
            "--frontend-port",
            str(_free_loopback_port()),
            "--backend-port",
            str(_free_loopback_port()),
        ]
    )
    return code, reported


def test_zero_launcher_result_remains_silent_success(tmp_path, monkeypatch):
    code, reported = _run_with_launcher_result(tmp_path, monkeypatch, 0)
    assert code == 0
    assert reported == []


def test_restore_blocked_return_is_visible_and_preserves_exit_code(tmp_path, monkeypatch):
    from launcher.runtime import RESTORE_BLOCKED_EXIT_CODE

    code, reported = _run_with_launcher_result(
        tmp_path, monkeypatch, RESTORE_BLOCKED_EXIT_CODE
    )
    assert code == RESTORE_BLOCKED_EXIT_CODE
    assert reported == [
        (
            StartupFailure.SAFE_START_BLOCKED,
            True,
            f"launcher returned {RESTORE_BLOCKED_EXIT_CODE}",
        )
    ]
    message = STARTUP_FAILURE_MESSAGES[StartupFailure.SAFE_START_BLOCKED]
    assert DATA_UNCHANGED_SENTENCE not in message
    assert "восстанов" in message.lower()


@pytest.mark.parametrize("launcher_result", [1, 2, 15, 23])
def test_other_nonzero_returns_are_visible_and_preserve_exact_code(
    tmp_path, monkeypatch, launcher_result
):
    code, reported = _run_with_launcher_result(tmp_path, monkeypatch, launcher_result)
    assert code == launcher_result
    assert reported == [
        (
            StartupFailure.RUNTIME_STOPPED,
            True,
            f"launcher returned {launcher_result}",
        )
    ]
    assert DATA_UNCHANGED_SENTENCE not in STARTUP_FAILURE_MESSAGES[StartupFailure.RUNTIME_STOPPED]
