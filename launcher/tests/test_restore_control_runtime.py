"""Launcher lifetime wiring for the C4-II-A2/A4 Restore control plane."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from launcher import runtime
from launcher.config import build_runtime_config, resolve_runtime_paths
from launcher.restore.control_plane import RestoreControlPlaneError


BOOTSTRAP_TOKEN = "A" * 43


class FakeProcess:
    def poll(self):
        return None

    def wait(self, timeout=None):
        del timeout
        return 0


class FakeBackendOwner:
    def __init__(self, events):
        self.events = events

    def start(self, config, paths, database_path):
        del config, paths
        self.events.append(("backend_start", Path(database_path)))
        return FakeProcess()

    def stop(self):
        self.events.append(("backend_stop", None))


class FakeContext:
    def __init__(self, events):
        self.events = events
        self.backend = FakeBackendOwner(events)

    def release_maintenance_lease(self):
        self.events.append(("lease_release", None))


class FakeControlPlane:
    def __init__(self, events, *, bootstrap_capability=BOOTSTRAP_TOKEN):
        self.events = events
        self.bound_port = 43123
        self.bootstrap_capability = bootstrap_capability

    def close(self):
        self.events.append(("control_close", None))


def _patch_successful_startup(monkeypatch, tmp_path, events):
    database = tmp_path / "workshop.sqlite"
    monkeypatch.setattr(runtime, "assert_port_available", lambda *_args: events.append(("port", None)))
    monkeypatch.setattr(
        runtime,
        "resolve_restore_startup_preflight",
        lambda _context: SimpleNamespace(blocked_result=None),
    )
    monkeypatch.setattr(
        runtime,
        "resolve_restore_recovery",
        lambda _context, _preflight: SimpleNamespace(
            normal_startup_allowed=True,
            message="",
        ),
    )
    monkeypatch.setattr(
        runtime,
        "initialize_backend_startup",
        lambda _mode, _paths: SimpleNamespace(database_path=database, backup=None),
    )
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)
    return database


def test_control_plane_starts_after_owned_backend_and_closes_before_backend(monkeypatch, tmp_path):
    events = []
    database = _patch_successful_startup(monkeypatch, tmp_path, events)
    context = FakeContext(events)
    opened = []

    def start_control(_config, path):
        assert Path(path) == database
        events.append(("control_start", Path(path)))
        return FakeControlPlane(events)

    monkeypatch.setattr(runtime, "start_restore_control_plane", start_control)
    monkeypatch.setattr(
        runtime,
        "open_runtime_browser",
        lambda config: (events.append(("browser", None)), opened.append(config.frontend_url)),
    )

    config = build_runtime_config(open_browser=True)
    result = runtime._run_locked_runtime(config, resolve_runtime_paths(), context)

    assert result == 0
    names = [name for name, _value in events]
    assert names.index("backend_start") < names.index("control_start") < names.index("browser")
    assert names.index("control_close") < names.index("backend_stop")
    assert opened == [f"http://127.0.0.1:5173#cw-control=43123:{BOOTSTRAP_TOKEN}"]
    assert config.frontend_url == "http://127.0.0.1:5173"


def test_control_plane_failure_keeps_ordinary_product_available(monkeypatch, tmp_path, capsys):
    events = []
    _patch_successful_startup(monkeypatch, tmp_path, events)
    context = FakeContext(events)
    opened = []

    def fail_control(_config, _path):
        events.append(("control_failed", None))
        raise RestoreControlPlaneError("expected test refusal")

    monkeypatch.setattr(runtime, "start_restore_control_plane", fail_control)
    monkeypatch.setattr(
        runtime,
        "open_runtime_browser",
        lambda config: (events.append(("browser", None)), opened.append(config.frontend_url)),
    )

    result = runtime._run_locked_runtime(
        build_runtime_config(open_browser=True),
        resolve_runtime_paths(),
        context,
    )

    assert result == 0
    names = [name for name, _value in events]
    assert "control_failed" in names
    assert "browser" in names
    assert names[-1] == "backend_stop"
    assert opened == ["http://127.0.0.1:5173"]
    assert "Основная мастерская продолжит работу" in capsys.readouterr().out


def test_invalid_handoff_closes_control_and_opens_ordinary_product(monkeypatch, tmp_path, capsys):
    events = []
    _patch_successful_startup(monkeypatch, tmp_path, events)
    context = FakeContext(events)
    opened = []

    monkeypatch.setattr(
        runtime,
        "start_restore_control_plane",
        lambda _config, _path: FakeControlPlane(events, bootstrap_capability="bad"),
    )
    monkeypatch.setattr(
        runtime,
        "open_runtime_browser",
        lambda config: opened.append(config.frontend_url),
    )

    result = runtime._run_locked_runtime(
        build_runtime_config(open_browser=True),
        resolve_runtime_paths(),
        context,
    )

    assert result == 0
    assert opened == ["http://127.0.0.1:5173"]
    assert [name for name, _value in events].count("control_close") == 1
    assert "Основная мастерская продолжит работу" in capsys.readouterr().out
