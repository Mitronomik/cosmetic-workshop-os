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
BACKEND_ENTRYPOINT_MODULE = "app.launcher_backend_entrypoint"
RESTORE_BLOCKED_EXIT_CODE = 3


class RuntimeLaunchError(RuntimeError):
    """Raised when local runtime cannot start safely."""


class BackendPortUnavailableError(RuntimeLaunchError):
    """The configured backend port is occupied by something else."""


def ensure_backend_import_path(paths: RuntimePaths) -> None:
    backend_path = str(paths.backend_dir)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def initialize_backend_startup(mode: str, paths: RuntimePaths):
    ensure_backend_import_path(paths)
    from app.services.startup import initialize_startup

    return initialize_startup(mode)


def assert_port_available(host: str, port: int) -> None:
    """Friendly early probe; the child handshake remains authoritative ownership."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError as exc:
            raise BackendPortUnavailableError(
                f"Порт {port} уже занят. Закройте другое окно приложения или выберите свободный порт."
            ) from exc


def backend_database_path_env(paths: RuntimePaths) -> str:
    ensure_backend_import_path(paths)
    from app.db.config import DATABASE_PATH_ENV

    return DATABASE_PATH_ENV


def backend_liveness_lock_env(paths: RuntimePaths) -> str:
    ensure_backend_import_path(paths)
    from app.services.backend_liveness import BACKEND_LIVENESS_LOCK_ENV

    return BACKEND_LIVENESS_LOCK_ENV


def start_backend_process(
    config: RuntimeConfig,
    paths: RuntimePaths,
    database_path: Path,
    *,
    handshake=None,
) -> subprocess.Popen[str]:
    """Start the API child pinned to the exact startup-selected database path."""

    assert_port_available(config.host, config.backend_port)
    env = os.environ.copy()
    python_path_parts = [str(paths.backend_dir)]
    if env.get("PYTHONPATH"):
        python_path_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
    env[backend_database_path_env(paths)] = str(database_path)

    from launcher.restore.workspace import RestoreWorkspace

    env[backend_liveness_lock_env(paths)] = str(
        RestoreWorkspace.for_database(Path(database_path)).backend_liveness_lock_path
    )
    command = [
        sys.executable,
        "-m",
        BACKEND_ENTRYPOINT_MODULE,
        "--host",
        config.host,
        "--port",
        str(config.backend_port),
    ]
    popen_arguments = {}
    if handshake is not None:
        env.update(handshake.child_environment)
        popen_arguments["pass_fds"] = handshake.pass_fds
    return subprocess.Popen(
        command,
        cwd=paths.backend_dir,
        env=env,
        text=True,
        **popen_arguments,
    )


def start_owned_backend_process(
    config: RuntimeConfig, paths: RuntimePaths, database_path: Path
) -> subprocess.Popen[str]:
    """Return only after the owned child proves liveness-lock and socket ownership."""

    ensure_backend_import_path(paths)
    from launcher.restore.backend_handshake import (
        BackendHandshakeError,
        BackendSocketUnavailableError,
        new_backend_handshake,
    )

    handshake = new_backend_handshake()
    try:
        process = start_backend_process(
            config, paths, database_path, handshake=handshake
        )
    except BaseException:
        handshake.close()
        raise

    handshake.close_child_end()
    try:
        handshake.await_acquisition(process)
    except BackendSocketUnavailableError as exc:
        terminate_process(process)
        raise BackendPortUnavailableError(
            f"Порт {config.backend_port} уже занят. "
            "Закройте другое окно приложения или выберите свободный порт."
        ) from exc
    except BackendHandshakeError:
        terminate_process(process)
        raise
    finally:
        handshake.close()
    return process


def open_runtime_browser(config: RuntimeConfig) -> None:
    """Open the ordinary product URL unchanged; A4 owns bootstrap-fragment handoff."""

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


def acquire_launcher_lifecycle(runtime_config: RuntimeConfig, paths: RuntimePaths):
    """Acquire exact-workspace launcher authority before recovery/startup work."""

    ensure_backend_import_path(paths)
    from launcher.restore import LauncherAlreadyRunningError, LauncherLifecycleContext

    try:
        return LauncherLifecycleContext.acquire(runtime_config, paths)
    except LauncherAlreadyRunningError as exc:
        raise RuntimeLaunchError(
            "Приложение уже запущено. Закройте другое окно приложения и попробуйте снова."
        ) from exc


def resolve_restore_startup_preflight(context):
    from launcher.restore.recovery import prepare_restore_startup_recovery

    return prepare_restore_startup_recovery(context)


def resolve_restore_recovery(context, preflight=None):
    from launcher.restore import recover_incomplete_restore

    return recover_incomplete_restore(context, preflight=preflight)


def start_restore_control_plane(
    config: RuntimeConfig,
    database_path: Path,
):
    """Start A2 control only after launcher authority and proved backend startup.

    Failure is intentionally non-fatal for ordinary workshop use: ADR 0018 allows
    the business product to continue while Restore controls stay unavailable. No
    alternate transport or browser filesystem fallback is created.
    """

    from launcher.restore.control_plane import RestoreControlPlane, RestoreControlPlaneError

    if config.frontend_url is None:
        raise RestoreControlPlaneError(
            "Restore control plane requires the configured local frontend origin."
        )

    plane = None
    try:
        plane = RestoreControlPlane(
            Path(database_path),
            frontend_url=config.frontend_url,
        )
        # This call is safe here because run_local_runtime already holds the
        # canonical launcher instance authority for this workspace.
        plane.cleanup_interrupted_validation_scratch()
        return plane.start()
    except RestoreControlPlaneError:
        if plane is not None:
            plane.close()
        raise
    except Exception as exc:  # noqa: BLE001 - ordinary product may continue safely
        if plane is not None:
            plane.close()
        raise RestoreControlPlaneError(
            "Не удалось запустить локальный канал восстановления."
        ) from exc


def run_local_runtime(
    config: RuntimeConfig | None = None,
    paths: RuntimePaths | None = None,
) -> int:
    runtime_config = config or build_runtime_config()
    runtime_paths = paths or resolve_runtime_paths()
    print("Мастерская косметолога: запуск локального режима…")
    print(
        f"Данные пользователя будут храниться вне кода приложения "
        f"(режим: {runtime_config.mode})."
    )
    context = acquire_launcher_lifecycle(runtime_config, runtime_paths)
    try:
        return _run_locked_runtime(runtime_config, runtime_paths, context)
    finally:
        context.release()


def _run_locked_runtime(
    runtime_config: RuntimeConfig,
    runtime_paths: RuntimePaths,
    context,
) -> int:
    preflight = resolve_restore_startup_preflight(context)
    if preflight.blocked_result is not None:
        print(preflight.blocked_result.message)
        return RESTORE_BLOCKED_EXIT_CODE

    # Port refusal stays before any state-mutating Restore recovery/startup work.
    assert_port_available(runtime_config.host, runtime_config.backend_port)
    recovery = resolve_restore_recovery(context, preflight)
    if not recovery.normal_startup_allowed:
        print(recovery.message)
        return RESTORE_BLOCKED_EXIT_CODE
    if recovery.message:
        print(recovery.message)

    startup = initialize_backend_startup(runtime_config.mode, runtime_paths)
    print(f"База данных готова: {startup.database_path}")
    if startup.backup is not None:
        print(f"Перед миграцией создана резервная копия: {startup.backup.backup_path}")
    print(f"Запускаю локальный API: {runtime_config.backend_url}")

    # Hand the canonical backend-liveness lease to the one owned child.
    context.release_maintenance_lease()
    process = context.backend.start(
        runtime_config,
        runtime_paths,
        startup.database_path,
    )
    control_plane = None
    try:
        # BackendProcessOwner.start() returns only after the exact child proved
        # both liveness-lock and listening-socket ownership. A2 starts after that.
        try:
            control_plane = start_restore_control_plane(
                runtime_config,
                startup.database_path,
            )
        except Exception as exc:  # noqa: BLE001 - product remains usable without Restore control
            from launcher.restore.control_plane import RestoreControlPlaneError

            if not isinstance(exc, RestoreControlPlaneError):
                raise
            print(
                "Восстановление из резервной копии временно недоступно. "
                "Основная мастерская продолжит работу."
            )

        time.sleep(1)
        if process.poll() is not None:
            raise RuntimeLaunchError(
                "Локальный API не запустился. Проверьте зависимости backend runtime."
            )

        # Deliberately unchanged: A2 does not append #cw-control or any bootstrap
        # material. The first production fragment handoff belongs to A4.
        if runtime_config.open_browser:
            open_runtime_browser(runtime_config)
        print("Приложение запущено. Для остановки нажмите Ctrl+C в этом окне.")
        return process.wait()
    except KeyboardInterrupt:
        print("Останавливаю локальное приложение…")
        return 0
    finally:
        # Invalidate browser/control authority and quiesce validation before the
        # ordinary owned backend is stopped and before launcher authority releases.
        if control_plane is not None:
            control_plane.close()
        context.backend.stop()
