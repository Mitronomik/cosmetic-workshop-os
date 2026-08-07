"""A2 control Origin must match the URL ordinary runtime navigation would open."""

from __future__ import annotations

from pathlib import Path

from launcher import runtime
from launcher.config import build_runtime_config


def test_control_plane_uses_backend_origin_when_frontend_url_is_none(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class FakeControlPlane:
        def __init__(self, database_path: Path, *, frontend_url: str):
            captured["database_path"] = Path(database_path)
            captured["frontend_url"] = frontend_url
            captured["cleanup"] = False
            captured["started"] = False

        def cleanup_interrupted_validation_scratch(self) -> int:
            captured["cleanup"] = True
            return 0

        def start(self):
            captured["started"] = True
            return self

        def close(self) -> None:
            captured["closed"] = True

    from launcher.restore import control_plane as module

    monkeypatch.setattr(module, "RestoreControlPlane", FakeControlPlane)

    database_path = tmp_path / "workshop.sqlite"
    config = build_runtime_config(
        backend_port=8123,
        frontend_url=None,
        open_browser=False,
    )

    plane = runtime.start_restore_control_plane(config, database_path)

    assert plane is not None
    assert captured["database_path"] == database_path
    assert captured["frontend_url"] == config.backend_url
    assert captured["frontend_url"] == "http://127.0.0.1:8123"
    assert captured["cleanup"] is True
    assert captured["started"] is True
