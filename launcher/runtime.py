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

# The launcher-managed backend entrypoint. It acquires the backend-liveness lock
# **before** importing `app.main` or anything else that can reach the database,
# then reports that acquisition to this launcher. Running `uvicorn` directly would
# take the lock only once the whole application had already been imported, which
# leaves a window in which a launcher-managed backend is invisible to the check
# that authorizes replacing the database it is about to open.
BACKEND_ENTRYPOINT_MODULE = "app.launcher_backend_entrypoint"

# Returned when an interrupted Restore leaves nothing the launcher can prove is
# safe. Distinct from the generic failure code so a future packaged shell can
# tell "could not start" apart from "must not start".
RESTORE_BLOCKED_EXIT_CODE = 3


class RuntimeLaunchError(RuntimeError):
    """Raised when local runtime cannot start safely."""


class BackendPortUnavailableError(RuntimeLaunchError):
    """The configured port is occupied by something else, right now.

    A **subclass**, so every existing `except RuntimeLaunchError`, every existing
    test and the ordinary user-facing port message are unchanged. What it adds is
    the one distinction Restore recovery cannot make without it: "the environment
    is temporarily busy" is not "the restored database is bad".

    That distinction is load-bearing. A verification backend that cannot bind a
    port has proved nothing about the database, so treating it as a verification
    failure would convert a problem the user fixes by closing another program into
    a terminal `recovery_blocked` that only a support procedure can clear.
    """


def ensure_backend_import_path(paths: RuntimePaths) -> None:
    backend_path = str(paths.backend_dir)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def initialize_backend_startup(mode: str, paths: RuntimePaths):
    ensure_backend_import_path(paths)
    from app.services.startup import initialize_startup

    return initialize_startup(mode)


def assert_port_available(host: str, port: int) -> None:
    """Refuse a port that is already in use, with the message that has always said so.

    The raised type is the narrower :class:`BackendPortUnavailableError`, which is
    a `RuntimeLaunchError`. Callers that only ever wanted "the launcher cannot
    start" are unaffected; the single caller that must tell an occupied port apart
    from a bad database — Restore verification — now can.

    This is a probe, not a reservation, and it is **not** the ownership proof. It
    binds, closes and returns, so the port can be taken between this call and the
    child's own bind. That is a fast, friendly refusal for the common case; the
    authoritative answer is the child's own `bind()`, reported through the
    structured one-run handshake in :func:`start_owned_backend_process`.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError as exc:
            raise BackendPortUnavailableError(
                f"Порт {port} уже занят. Закройте другое окно приложения или выберите свободный порт."
            ) from exc


def backend_database_path_env(paths: RuntimePaths) -> str:
    """The environment key the backend reads its database path from.

    Read from the backend's own constant rather than repeated as a literal here,
    so the launcher and the backend cannot drift apart on the name. The import is
    deferred because `backend/` only joins `sys.path` at runtime, via
    `ensure_backend_import_path`.
    """
    ensure_backend_import_path(paths)
    from app.db.config import DATABASE_PATH_ENV

    return DATABASE_PATH_ENV


def backend_liveness_lock_env(paths: RuntimePaths) -> str:
    """The environment key the backend reads its liveness-lock path from.

    Read from the backend's own constant for the same reason as the database key:
    the launcher and the backend must not be able to drift apart on the name. A
    silently ignored variable here would mean the child never takes the lock, and
    every orphan check would then report "nothing running" — the exact false
    negative the lock exists to prevent.
    """
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
    """Start the API child, pinned to the database startup actually prepared.

    `database_path` is the path `initialize_startup()` selected, backed up,
    migrated and reconciled. Passing it explicitly is what keeps one database
    across the whole user-mode flow. Without it the child calls
    `get_database_config()` on its own and, with no environment value set, falls
    back to the repository default — so it would serve a database that was never
    migrated, while the real user database sat untouched.

    The parameter is **required**, with no default and no `None` branch. Making
    it optional would leave the startup/API split one forgetful call site away
    from returning, and that split is silent: every individual step still looks
    like it succeeded. A caller that cannot name the database has no business
    starting the API, so omitting it is a `TypeError` at the call, not a
    corrupted run.

    An inherited value is deliberately overwritten rather than respected: a stale
    `COSMETIC_WORKSHOP_DB_PATH` left in the parent shell is exactly the case that
    would otherwise split the two processes apart again. The startup result is
    authoritative.

    `handshake`, when supplied, is a one-run pipe and token the child uses to
    report that **it** acquired the backend-liveness lock. Only its descriptor is
    inherited; `pass_fds` clears the inheritable flag on everything else. Callers
    that need the proof use :func:`start_owned_backend_process` rather than
    waiting for it themselves.
    """
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
    """Start a backend child and return only once it **proved** lock and socket.

    Owning a `Popen` says the launcher started a process. It does not say the
    process took the backend-liveness lock, nor that it can actually serve on the
    configured port, and between those facts lie two windows. This closes both:

    ```text
    create a one-run pipe and token
    → spawn the pre-import entrypoint with that pipe inherited
    → the child acquires the lock before importing any application module
    → the child binds and listens on the exact configured socket
    → the child writes `ready:<token>` and closes its end
    → this returns
    ```

    The socket half is what the sixth audit required. `assert_port_available`
    above binds a probe, closes it and returns, which establishes availability at
    an instant and reserves nothing; uvicorn used to perform the real bind *after*
    the child had already reported success, so a program that took the port in
    between produced a child that started and then died. During Restore recovery
    that reads as a verification failure, and a verification failure ends a
    rollback at terminal `recovery_blocked` — over a socket. Now the child owns
    the real listening socket before it reports anything, and uvicorn serves that
    same socket rather than binding a second time.

    Timeout, EOF, an early child exit and a token from some other start are all
    the same answer, and all of them stop the child before returning. A backend
    that cannot be accounted for is never left running: that is how an orphan is
    made, and orphans are the failure this whole mechanism exists to prevent.

    A `port-unavailable:` report is the one refusal that is *not* a handshake
    failure. The handshake worked; what it carried was "somebody else has this
    port". The child bound nothing, imported nothing and opened no database, so it
    is raised as the ordinary :class:`BackendPortUnavailableError` — the same type
    and the same message the early probe uses — and Restore turns that into a
    retryable refusal rather than a verdict about the restored database.
    """
    ensure_backend_import_path(paths)
    from launcher.restore.backend_handshake import (
        BackendHandshakeError,
        BackendSocketUnavailableError,
        new_backend_handshake,
    )

    handshake = new_backend_handshake()
    try:
        process = start_backend_process(config, paths, database_path, handshake=handshake)
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


def start_restore_control_plane(config: RuntimeConfig, database_path: Path):
    """Start A2 control after launcher authority and proved backend startup.

    The allowed Origin is the same URL the ordinary runtime would open:
    `frontend_url` when configured, otherwise the local `backend_url` fallback.
    No alternate Restore transport, picker or browser filesystem fallback exists.
    """
    from launcher.restore.control_plane import RestoreControlPlane, RestoreControlPlaneError

    plane = None
    try:
        plane = RestoreControlPlane(
            Path(database_path),
            frontend_url=config.frontend_url or config.backend_url,
        )
        plane.cleanup_interrupted_validation_scratch()
        return plane.start()
    except RestoreControlPlaneError:
        if plane is not None:
            plane.close()
        raise
    except Exception as exc:  # noqa: BLE001 - convert to fixed safe launcher failure
        if plane is not None:
            plane.close()
        raise RestoreControlPlaneError(
            "Не удалось запустить локальный канал восстановления."
        ) from exc


def run_local_runtime(config: RuntimeConfig | None = None, paths: RuntimePaths | None = None) -> int:
    runtime_config = config or build_runtime_config()
    runtime_paths = paths or resolve_runtime_paths()
    print("Мастерская косметолога: запуск локального режима…")
    print(f"Данные пользователя будут храниться вне кода приложения (режим: {runtime_config.mode}).")
    context = acquire_launcher_lifecycle(runtime_config, runtime_paths)
    try:
        return _run_locked_runtime(runtime_config, runtime_paths, context)
    finally:
        context.release()


def _run_locked_runtime(
    runtime_config: RuntimeConfig, runtime_paths: RuntimePaths, context
) -> int:
    preflight = resolve_restore_startup_preflight(context)
    if preflight.blocked_result is not None:
        print(preflight.blocked_result.message)
        return RESTORE_BLOCKED_EXIT_CODE
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
    context.release_maintenance_lease()
    process = context.backend.start(runtime_config, runtime_paths, startup.database_path)
    control_plane = None
    try:
        try:
            control_plane = start_restore_control_plane(runtime_config, startup.database_path)
        except Exception as exc:  # noqa: BLE001 - ordinary product may continue safely
            from launcher.restore.control_plane import RestoreControlPlaneError

            if not isinstance(exc, RestoreControlPlaneError):
                raise
            print(
                "Восстановление из резервной копии временно недоступно. "
                "Основная мастерская продолжит работу."
            )

        time.sleep(1)
        if process.poll() is not None:
            raise RuntimeLaunchError("Локальный API не запустился. Проверьте зависимости backend runtime.")
        # Deliberately unchanged: the first production #cw-control fragment
        # handoff belongs to A4, after its SPA consumer/removal logic exists.
        if runtime_config.open_browser:
            open_runtime_browser(runtime_config)
        print("Приложение запущено. Для остановки нажмите Ctrl+C в этом окне.")
        return process.wait()
    except KeyboardInterrupt:
        print("Останавливаю локальное приложение…")
        return 0
    finally:
        if control_plane is not None:
            control_plane.close()
        context.backend.stop()