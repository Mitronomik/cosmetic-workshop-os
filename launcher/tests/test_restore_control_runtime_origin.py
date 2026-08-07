"""A2 control requires the configured local frontend Origin from ADR 0018."""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher import runtime
from launcher.config import build_runtime_config
from launcher.restore.control_plane import RestoreControlPlaneError


def test_missing_configured_frontend_origin_fails_restore_control_closed(monkeypatch, tmp_path):
    constructed = []

    class ShouldNotConstruct:
        def __init__(self, *_args, **_kwargs):
            constructed.append(True)
            raise AssertionError("control plane must not construct without configured frontend Origin")

    from launcher.restore import control_plane as module

    monkeypatch.setattr(module, "RestoreControlPlane", ShouldNotConstruct)
    config = build_runtime_config(
        backend_port=8123,
        frontend_url=None,
        open_browser=False,
    )

    with pytest.raises(RestoreControlPlaneError):
        runtime.start_restore_control_plane(config, Path(tmp_path / "workshop.sqlite"))

    assert constructed == []
