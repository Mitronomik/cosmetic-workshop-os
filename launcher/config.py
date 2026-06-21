from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

RuntimeMode = Literal["development", "user"]
ALLOWED_RUNTIME_MODES: tuple[RuntimeMode, ...] = ("development", "user")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_URL = "http://127.0.0.1:5173"


class RuntimeConfigError(ValueError):
    """Raised when launcher runtime configuration is unsafe or invalid."""


@dataclass(frozen=True)
class RuntimePaths:
    project_root: Path
    backend_dir: Path
    frontend_dir: Path


def resolve_runtime_paths(project_root: Path | None = None) -> RuntimePaths:
    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    return RuntimePaths(
        project_root=root,
        backend_dir=root / "backend",
        frontend_dir=root / "frontend",
    )


@dataclass(frozen=True)
class RuntimeConfig:
    host: str = DEFAULT_HOST
    backend_port: int = DEFAULT_BACKEND_PORT
    frontend_url: str | None = DEFAULT_FRONTEND_URL
    mode: RuntimeMode = "user"
    open_browser: bool = True

    @property
    def backend_url(self) -> str:
        return f"http://{self.host}:{self.backend_port}"


def validate_runtime_mode(mode: str) -> RuntimeMode:
    if mode not in ALLOWED_RUNTIME_MODES:
        allowed = ", ".join(ALLOWED_RUNTIME_MODES)
        raise RuntimeConfigError(f"Unsupported runtime mode {mode!r}. Allowed modes: {allowed}.")
    return cast(RuntimeMode, mode)


def validate_runtime_config(config: RuntimeConfig) -> RuntimeConfig:
    if config.host != DEFAULT_HOST:
        raise RuntimeConfigError(
            "Local runtime must listen on 127.0.0.1 only. Change the host back to 127.0.0.1."
        )
    if not (1 <= config.backend_port <= 65535):
        raise RuntimeConfigError(
            f"Backend port {config.backend_port!r} is invalid. Use a port from 1 to 65535."
        )
    validate_runtime_mode(config.mode)
    return config


def build_runtime_config(
    *,
    host: str = DEFAULT_HOST,
    backend_port: int = DEFAULT_BACKEND_PORT,
    frontend_url: str | None = DEFAULT_FRONTEND_URL,
    mode: str = "user",
    open_browser: bool = True,
) -> RuntimeConfig:
    return validate_runtime_config(
        RuntimeConfig(
            host=host,
            backend_port=backend_port,
            frontend_url=frontend_url,
            mode=validate_runtime_mode(mode),
            open_browser=open_browser,
        )
    )
