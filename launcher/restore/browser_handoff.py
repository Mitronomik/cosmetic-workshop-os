"""A4 launcher-to-browser one-use Restore bootstrap handoff.

Only the launch URL fragment carries the control-plane port and bootstrap
capability. The fragment is browser presentation transport, never backend or
filesystem authority, and callers must never log the returned URL.
"""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit

from launcher.config import RuntimeConfig

_BOOTSTRAP_TOKEN = re.compile(r"[A-Za-z0-9_-]{43,256}\Z")


class RestoreBrowserHandoffError(RuntimeError):
    """Raised when A4 cannot construct the exact local browser handoff safely."""


class RestoreControlHandoffSource(Protocol):
    @property
    def bound_port(self) -> int: ...

    @property
    def bootstrap_capability(self) -> str: ...


def runtime_config_with_restore_handoff(
    config: RuntimeConfig,
    control_plane: RestoreControlHandoffSource,
) -> RuntimeConfig:
    """Return a browser-only config carrying one A4 bootstrap URL fragment."""

    if config.frontend_url is None:
        raise RestoreBrowserHandoffError("restore_browser_frontend_origin_missing")
    parsed = urlsplit(config.frontend_url)
    try:
        frontend_port = parsed.port
    except ValueError as exc:
        raise RestoreBrowserHandoffError("restore_browser_frontend_origin_invalid") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or frontend_port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise RestoreBrowserHandoffError("restore_browser_frontend_origin_invalid")

    control_port = control_plane.bound_port
    capability = control_plane.bootstrap_capability
    if isinstance(control_port, bool) or not isinstance(control_port, int) or not (1 <= control_port <= 65535):
        raise RestoreBrowserHandoffError("restore_browser_control_port_invalid")
    if not isinstance(capability, str) or _BOOTSTRAP_TOKEN.fullmatch(capability) is None:
        raise RestoreBrowserHandoffError("restore_browser_bootstrap_invalid")

    fragment = f"cw-control={control_port}:{capability}"
    target_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", fragment))
    return replace(config, frontend_url=target_url)
