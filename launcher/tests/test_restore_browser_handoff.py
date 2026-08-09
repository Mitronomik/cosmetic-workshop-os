"""C4-II-A4 launcher-to-browser fragment handoff contract."""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

from launcher.config import build_runtime_config
from launcher.restore.browser_handoff import (
    RestoreBrowserHandoffError,
    runtime_config_with_restore_handoff,
)


TOKEN = "A" * 43


def test_handoff_uses_fragment_only_and_does_not_mutate_original_config():
    config = build_runtime_config(frontend_url="http://127.0.0.1:5173")
    plane = SimpleNamespace(bound_port=43123, bootstrap_capability=TOKEN)

    result = runtime_config_with_restore_handoff(config, plane)

    assert config.frontend_url == "http://127.0.0.1:5173"
    assert result.frontend_url == f"http://127.0.0.1:5173#cw-control=43123:{TOKEN}"
    parsed = urlsplit(result.frontend_url)
    assert parsed.query == ""
    assert parsed.fragment == f"cw-control=43123:{TOKEN}"
    assert TOKEN not in parsed.path
    assert TOKEN not in parsed.query
    assert result.backend_url == config.backend_url


@pytest.mark.parametrize(
    "frontend_url",
    [
        None,
        "http://127.0.0.1:5173/?token=bad",
        "http://127.0.0.1:5173/#already",
        "http://localhost:5173",
        "https://127.0.0.1:5173",
        "http://user@127.0.0.1:5173",
    ],
)
def test_handoff_refuses_non_exact_frontend_origin(frontend_url):
    config = build_runtime_config(frontend_url=frontend_url)
    plane = SimpleNamespace(bound_port=43123, bootstrap_capability=TOKEN)
    with pytest.raises(RestoreBrowserHandoffError):
        runtime_config_with_restore_handoff(config, plane)


@pytest.mark.parametrize(
    ("port", "token"),
    [(0, TOKEN), (65536, TOKEN), (True, TOKEN), (43123, "short"), (43123, "x" * 42 + "+")],
)
def test_handoff_refuses_invalid_control_descriptor(port, token):
    config = build_runtime_config(frontend_url="http://127.0.0.1:5173")
    plane = SimpleNamespace(bound_port=port, bootstrap_capability=token)
    with pytest.raises(RestoreBrowserHandoffError):
        runtime_config_with_restore_handoff(config, plane)
