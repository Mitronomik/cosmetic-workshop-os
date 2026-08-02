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
    # The child takes this lock for its whole lifetime, so the kernel releases it
    # only when the process actually dies. That is what lets a *later* launcher
    # discover a backend orphaned by a hard crash, which an in-memory process
    # handle cannot survive to report. Derived from the same canonical workspace
    # as the database itself.
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
    """Start a backend child and return only once it **proved** it holds the lock.

    Owning a `Popen` says the launcher started a process. It does not say the
    process took the backend-liveness lock, and between those two facts lies a
    window in which a launcher-managed backend is invisible to the check that
    authorizes replacing the database. This closes it:

    ```text
    create a one-run pipe and token
    → spawn the pre-import entrypoint with that pipe inherited
    → the child acquires the lock before importing any application module
    → the child writes the token and closes its end
    → this returns
    ```

    Timeout, EOF, an early child exit and a token from some other start are all
    the same answer, and all of them stop the child before returning. A backend
    that cannot be accounted for is never left running: that is how an orphan is
    made, and orphans are the failure this whole mechanism exists to prevent.
    """
    ensure_backend_import_path(paths)
    from launcher.restore.backend_handshake import (
        BackendHandshakeError,
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

    # Closed immediately so the pipe reaches EOF if the child dies without
    # writing; while this end stays open the read below could never see that.
    handshake.close_child_end()
    try:
        handshake.await_acquisition(process)
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
    """Take the launcher's authority over one workspace, for the whole run.

    The lifecycle context resolves every canonical path from the existing startup
    and backup resolvers and takes the exclusive instance lock. One boundary
    covers ordinary startup, Restore execution and incomplete-Restore recovery, so
    a second launcher cannot begin recovery while the first is halfway through a
    database replacement.

    The existing port check stays where it is and keeps its own message: a free
    port is not proof that nothing else owns the workspace, least of all during
    Restore, when the backend is stopped by design.
    """
    ensure_backend_import_path(paths)
    from launcher.restore import LauncherAlreadyRunningError, LauncherLifecycleContext

    try:
        return LauncherLifecycleContext.acquire(runtime_config, paths)
    except LauncherAlreadyRunningError as exc:
        raise RuntimeLaunchError(
            "Приложение уже запущено. Закройте другое окно приложения и попробуйте снова."
        ) from exc


def resolve_restore_recovery(context):
    """Resolve any interrupted Restore before ordinary startup may continue.

    This is the `CR-010` § 7.5 gate. It runs before startup migrations, before
    the backend child and before the browser, and its verdict is binding: an
    unsafe persisted phase never falls through to the ordinary startup below.
    """
    from launcher.restore import recover_incomplete_restore

    return recover_incomplete_restore(context)


def run_local_runtime(config: RuntimeConfig | None = None, paths: RuntimePaths | None = None) -> int:
    runtime_config = config or build_runtime_config()
    runtime_paths = paths or resolve_runtime_paths()
    print("Мастерская косметолога: запуск локального режима…")
    assert_port_available(runtime_config.host, runtime_config.backend_port)
    print(f"Данные пользователя будут храниться вне кода приложения (режим: {runtime_config.mode}).")
    context = acquire_launcher_lifecycle(runtime_config, runtime_paths)
    try:
        return _run_locked_runtime(runtime_config, runtime_paths, context)
    finally:
        context.release()


def _run_locked_runtime(
    runtime_config: RuntimeConfig, runtime_paths: RuntimePaths, context
) -> int:
    recovery = resolve_restore_recovery(context)
    if not recovery.normal_startup_allowed:
        # Nothing starts and the browser never opens. The message is the fixed
        # non-technical support-assisted text; every technical detail stayed in
        # the local log.
        print(recovery.message)
        return RESTORE_BLOCKED_EXIT_CODE
    if recovery.message:
        # A recovered previous workspace. Restore failed, and saying so here is
        # the honest result — never "restore succeeded".
        print(recovery.message)
    startup = initialize_backend_startup(runtime_config.mode, runtime_paths)
    print(f"База данных готова: {startup.database_path}")
    if startup.backup is not None:
        print(f"Перед миграцией создана резервная копия: {startup.backup.backup_path}")
    print(f"Запускаю локальный API: {runtime_config.backend_url}")
    # Startup recovery took the retained maintenance lease and ordinary startup
    # migrated the database underneath it. The backend child has to hold that same
    # canonical lock for its own lifetime, so the lease is handed over here — one
    # deliberate release, immediately before the one process allowed to take it.
    context.release_maintenance_lease()
    # The API child must serve the database that was just backed up, migrated and
    # reconciled — not one it resolves for itself. This applies to development
    # mode as well: whatever `initialize_startup()` chose is what gets served.
    #
    # Started *through the owner*, so the launcher holds the exact handle rather
    # than merely having spawned it, and so the child's own lock acquisition is
    # proved before anything treats it as running. Ownership is what a later
    # Restore needs in order to *prove* the backend stopped — a free port proves
    # nothing, and the backend never takes the launcher lock.
    process = context.backend.start(runtime_config, runtime_paths, startup.database_path)
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
        # Through the owner, so the recorded handle is cleared as well as killed.
        context.backend.stop()
