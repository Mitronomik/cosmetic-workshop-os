"""The packaged application's entrypoint: prove, serve, then hand over.

What a packaged start adds to an ordinary start is small and deliberately so:

```text
1. resolve this package's own resources
2. refuse if any of them is missing, or if the bundled runtime is not the one running
3. start the local production-frontend listener (no Node)
4. hand over to the existing launcher user-mode flow, unchanged
5. stop the listener when the launcher returns, however it returns
6. make every fatal packaged outcome visible to a user who has no terminal
```

Step 4 is the point of the whole module. Everything the product actually does —
the backend child and its lock/socket handshake, startup migrations and the
mandatory backup before them, the Restore control plane and picker, the owner
loop, the browser — belongs to `launcher.runtime.run_local_runtime`, and this
module calls it rather than reproducing any of it. There is no second
supervisor here, no second Restore path, and no business logic. When the
launcher returns a non-zero code, that exact code remains the packaged
application's exit code; D3 adds only the fixed Finder-visible explanation that
stdout/stderr alone cannot provide to a double-click user.

`SIGTERM` is caught for one reason: Finder and the Dock stop an application by
sending it, and the default action would kill this process outright, leaving the
launcher no chance to stop the backend child or release the workspace lock. It
is converted to `KeyboardInterrupt`, which is exactly the shutdown the launcher
already handles on `Ctrl+C`, so quitting from the Dock takes the same graceful
path as quitting from a terminal.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import signal
import sys
import traceback

from macos_package.frontend_server import (
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_PORT,
    FrontendPortUnavailableError,
    FrontendRootMissingError,
    FrontendServerConfig,
    FrontendServerError,
    LocalFrontendServer,
)
from macos_package.package_paths import (
    PackageLayout,
    bundled_runtime_owns_interpreter,
    missing_package_resources,
    resolve_package_layout,
)
from macos_package.user_alert import StartupFailure, report_startup_failure

# Package-specific exit codes. Chosen above the launcher's own range — its
# generic failure is `2` and `RESTORE_BLOCKED_EXIT_CODE` is `3` — so a packaged
# refusal never collides with, or masquerades as, a launcher verdict.
EXIT_MISSING_RESOURCES = 10
EXIT_RUNTIME_MISSING = 11
EXIT_FRONTEND_PORT_UNAVAILABLE = 12
EXIT_FRONTEND_FAILED = 13
EXIT_BACKEND_PORT_UNAVAILABLE = 14
EXIT_LAUNCHER_REFUSED = 15
EXIT_UNEXPECTED = 16
EXIT_UPDATE_STOPPED_BEFORE_COMMIT = 17
EXIT_UPDATE_COMPLETION_UNCERTAIN = 18


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Ordinary double-click needs no arguments; verification needs a few.

    The defaults are the product: user mode, the configured frontend origin, the
    browser opens. The flags exist so an automated package smoke can run the
    real packaged product without a browser and on isolated ports, without any
    separate "test mode" code path inside the application.
    """
    parser = argparse.ArgumentParser(
        prog="CosmeticWorkshopOS",
        description="Packaged local runtime for Мастерская косметолога.",
    )
    parser.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT)
    parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args(argv)


def _install_sigterm_handler():
    previous = signal.getsignal(signal.SIGTERM)

    def _raise_interrupt(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _raise_interrupt)
    return previous


def run_packaged_application(argv: list[str] | None = None) -> int:
    """Start the packaged product, or refuse in a way the user can act on."""
    arguments = parse_args(argv)
    layout = resolve_package_layout()

    refusal = _refuse_incomplete_package(layout)
    if refusal is not None:
        return refusal

    server = LocalFrontendServer(
        FrontendServerConfig(
            root=layout.frontend_dist_dir,
            port=arguments.frontend_port,
            backend_port=arguments.backend_port,
        )
    )
    try:
        server.start()
    except FrontendPortUnavailableError as exc:
        # Nothing was started and nothing was written, so there is nothing to
        # clean up and no user data to be concerned about. The foreign process
        # holding the port is left strictly alone.
        report_startup_failure(
            StartupFailure.FRONTEND_PORT_BUSY, packaged=layout.is_packaged, detail=str(exc)
        )
        return EXIT_FRONTEND_PORT_UNAVAILABLE
    except (FrontendRootMissingError, FrontendServerError) as exc:
        report_startup_failure(
            StartupFailure.MISSING_RESOURCES
            if isinstance(exc, FrontendRootMissingError)
            else StartupFailure.UNEXPECTED,
            packaged=layout.is_packaged,
            detail=str(exc),
        )
        return EXIT_FRONTEND_FAILED

    previous_sigterm = _install_sigterm_handler()
    try:
        return _run_launcher(layout, server, arguments)
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        # Runs on every path, including the refusals above this line and the
        # launcher's own failures. The listener must not survive the launcher as
        # an orphan holding the frontend port.
        server.stop()


def _refuse_incomplete_package(layout: PackageLayout) -> int | None:
    """Prove the package carries what it needs, before anything is started.

    There is no repair and no substitution here. A package missing its frontend
    build or its backend modules cannot be completed from a developer checkout —
    that would mean the artifact under verification was never the thing that
    ran — so the only answer is a clear refusal.
    """
    missing = missing_package_resources(layout)
    if missing:
        report_startup_failure(
            StartupFailure.MISSING_RESOURCES,
            packaged=layout.is_packaged,
            detail=f"missing packaged resources: {', '.join(missing)}",
        )
        return EXIT_MISSING_RESOURCES
    if layout.is_packaged and not bundled_runtime_owns_interpreter(layout):
        # The package declares a bundled interpreter but something else is
        # running it. Continuing would silently make the user's own Python a
        # dependency — the exact thing this package exists to remove.
        report_startup_failure(
            StartupFailure.RUNTIME_MISSING,
            packaged=True,
            detail="the bundled runtime is not the interpreter executing the package",
        )
        return EXIT_RUNTIME_MISSING
    return None


def _classify_update_exception(exc: Exception) -> tuple[StartupFailure, int] | None:
    """Map backend-owned update truth to the two fixed D4-C package outcomes."""
    try:
        from app.services.update_safety import UpdateSafetyError, classify_update_failure_for_user
    except ImportError:
        return None
    if not isinstance(exc, UpdateSafetyError):
        return None
    if classify_update_failure_for_user(exc) == "before_commit":
        return StartupFailure.UPDATE_STOPPED_BEFORE_COMMIT, EXIT_UPDATE_STOPPED_BEFORE_COMMIT
    return StartupFailure.UPDATE_COMPLETION_UNCERTAIN, EXIT_UPDATE_COMPLETION_UNCERTAIN


def _run_launcher(
    layout: PackageLayout, server: LocalFrontendServer, arguments: argparse.Namespace
) -> int:
    """Call the existing launcher user-mode flow and make its verdict visible."""
    from launcher.config import build_runtime_config
    from launcher.runtime import (
        RESTORE_BLOCKED_EXIT_CODE,
        BackendPortUnavailableError,
        RuntimeLaunchError,
        run_local_runtime,
    )

    try:
        config = build_runtime_config(
            backend_port=arguments.backend_port,
            # The exact local frontend origin the Restore control plane checks.
            # It is the listener's own origin rather than a repeated literal, so
            # the two cannot drift apart and quietly break the ADR 0018 handoff.
            frontend_url=server.origin,
            mode="user",
            open_browser=not arguments.no_browser,
        )
    except ValueError as exc:
        report_startup_failure(
            StartupFailure.UNEXPECTED, packaged=layout.is_packaged, detail=str(exc)
        )
        return EXIT_UNEXPECTED

    try:
        result = run_local_runtime(config)
        if result == 0:
            return 0
        if result == RESTORE_BLOCKED_EXIT_CODE:
            report_startup_failure(
                StartupFailure.SAFE_START_BLOCKED,
                packaged=layout.is_packaged,
                detail=f"launcher returned {result}",
            )
            return result
        report_startup_failure(
            StartupFailure.RUNTIME_STOPPED,
            packaged=layout.is_packaged,
            detail=f"launcher returned {result}",
        )
        return result
    except KeyboardInterrupt:
        # Ctrl+C in developer mode, or Quit from the Dock in packaged mode. The
        # launcher's own `finally` has already stopped the backend child.
        return 0
    except BackendPortUnavailableError as exc:
        report_startup_failure(
            StartupFailure.BACKEND_PORT_BUSY, packaged=layout.is_packaged, detail=str(exc)
        )
        return EXIT_BACKEND_PORT_UNAVAILABLE
    except (RuntimeLaunchError, ValueError) as exc:
        report_startup_failure(
            StartupFailure.LAUNCHER_REFUSED, packaged=layout.is_packaged, detail=str(exc)
        )
        return EXIT_LAUNCHER_REFUSED
    except Exception as exc:  # noqa: BLE001 - a packaged crash must not be a silent exit
        update_failure = _classify_update_exception(exc)
        if update_failure is not None:
            failure, exit_code = update_failure
            report_startup_failure(
                failure,
                packaged=layout.is_packaged,
                # Keep the developer log useful without leaking an internal
                # category, filesystem path or traceback into the user dialogue.
                detail="D4-C classified startup-owned update failure",
            )
            return exit_code
        # The traceback is developer evidence and goes to stderr and the system
        # log. The user gets the fixed non-technical message instead.
        report_startup_failure(
            StartupFailure.UNEXPECTED,
            packaged=layout.is_packaged,
            detail=traceback.format_exc(),
        )
        return EXIT_UNEXPECTED


def main(argv: list[str] | None = None) -> int:
    return run_packaged_application(argv)


if __name__ == "__main__":  # pragma: no cover - process entry point
    # The packaged bootstrap puts the application root on `sys.path`; this keeps
    # a direct `python macos_package/entrypoint.py` working too.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
