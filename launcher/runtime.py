from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from launcher.config import RuntimeConfig, RuntimePaths, build_runtime_config, resolve_runtime_paths

BACKEND_MODULE = "app.main:app"


class RuntimeLaunchError(RuntimeError):
    """Raised when local runtime cannot start safely."""


def ensure_backend_import_path(paths: RuntimePaths) -> None:
    backend_path = str(paths.backend_dir)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def initialize_backend_startup(mode: str, paths: RuntimePaths):
    ensure_backend_import_path(paths)
    from app.services.startup import initialize_startup

    return initialize_startup(mode)


def assert_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError as exc:
            raise RuntimeLaunchError(
                f"Порт {port} уже занят. Закройте другое окно приложения или выберите свободный порт."
            ) from exc


def start_backend_process(config: RuntimeConfig, paths: RuntimePaths) -> subprocess.Popen[str]:
    assert_port_available(config.host, config.backend_port)
    env = os.environ.copy()
    python_path_parts = [str(paths.backend_dir)]
    if env.get("PYTHONPATH"):
        python_path_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        BACKEND_MODULE,
        "--host",
        config.host,
        "--port",
        str(config.backend_port),
    ]
    return subprocess.Popen(
        command,
        cwd=paths.backend_dir,
        env=env,
        text=True,
    )


def open_runtime_browser(config: RuntimeConfig) -> None:
    target_url = config.frontend_url or config.backend_url
    webbrowser.open(target_url)


def terminate_process(process: subprocess.Popen[str], timeout_seconds: float = 5.0) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout_seconds)


def run_local_runtime(config: RuntimeConfig | None = None, paths: RuntimePaths | None = None) -> int:
    runtime_config = config or build_runtime_config()
    runtime_paths = paths or resolve_runtime_paths()
    print("Мастерская косметолога: запуск локального режима…")
    print(f"Данные пользователя будут храниться вне кода приложения (режим: {runtime_config.mode}).")
    startup = initialize_backend_startup(runtime_config.mode, runtime_paths)
    print(f"База данных готова: {startup.database_path}")
    if startup.backup is not None:
        print(f"Перед миграцией создана резервная копия: {startup.backup.backup_path}")
    print(f"Запускаю локальный API: {runtime_config.backend_url}")
    process = start_backend_process(runtime_config, runtime_paths)
    try:
        time.sleep(1)
        if process.poll() is not None:
            raise RuntimeLaunchError("Локальный API не запустился. Проверьте зависимости backend runtime.")
        if runtime_config.open_browser:
            open_runtime_browser(runtime_config)
        print("Приложение запущено. Для остановки нажмите Ctrl+C в этом окне.")
        return process.wait()
    except KeyboardInterrupt:
        print("Останавливаю локальное приложение…")
        return 0
    finally:
        terminate_process(process)
