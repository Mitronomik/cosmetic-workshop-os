"""C4-II-A3 production runtime wires the native picker into the closed A2 plane."""

from __future__ import annotations

from pathlib import Path

from launcher import runtime
from launcher.config import build_runtime_config
from launcher.restore import control_plane as control_plane_module
from launcher.restore import macos_picker as picker_module


def test_start_restore_control_plane_uses_production_native_picker(monkeypatch, tmp_path: Path):
    captured = {}

    class FakePicker:
        pass

    class FakePlane:
        def __init__(self, database_path, *, frontend_url, picker_adapter):
            captured["database_path"] = Path(database_path)
            captured["frontend_url"] = frontend_url
            captured["picker_adapter"] = picker_adapter
            self.cleaned = False
            self.started = False

        def cleanup_interrupted_validation_scratch(self):
            self.cleaned = True
            return 0

        def start(self):
            self.started = True
            return self

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(picker_module, "MacOSNativeSourceSelectionAdapter", FakePicker)
    monkeypatch.setattr(control_plane_module, "RestoreControlPlane", FakePlane)

    database = tmp_path / "working.sqlite"
    config = build_runtime_config(frontend_url="http://127.0.0.1:5173")
    plane = runtime.start_restore_control_plane(config, database)

    assert isinstance(captured["picker_adapter"], FakePicker)
    assert captured["database_path"] == database
    assert captured["frontend_url"] == "http://127.0.0.1:5173"
    assert plane.cleaned is True
    assert plane.started is True
