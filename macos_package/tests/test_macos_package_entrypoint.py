"""The packaged entrypoint: what it proves before starting, and what it delegates.

The entrypoint's whole value is that it adds as little as possible. These tests
pin both halves of that:

```text
it refuses an incomplete package instead of falling back to a checkout
it refuses when the bundled runtime is not the interpreter running it
it starts the frontend listener and always stops it again
it calls the existing launcher rather than reimplementing any of it
it passes the listener's exact origin as the local frontend origin
it returns the launcher's own code, including non-zero ones
every fatal refusal is a fixed, human-readable, non-technical message
```
"""

from __future__ import annotations

import json
from pathlib import Path
import socket
import sys

import pytest

from macos_package import entrypoint
from macos_package.package_paths import (
    bundled_runtime_owns_interpreter,
    missing_package_resources,
    resolve_package_layout,
)
from macos_package.user_alert import (
    DATA_UNCHANGED_SENTENCE,
    PRE_MUTATION_FAILURES,
    STARTUP_FAILURE_MESSAGES,
    StartupFailure,
    show_alert,
)
from packaging_fixtures import build_frontend_dist, free_loopback_port


@pytest.fixture(autouse=True)
def never_open_a_real_dialog(monkeypatch):
    """A modal alert in an unattended test run would hang the suite."""
    monkeypatch.setenv("COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS", "1")


@pytest.fixture
def reported(monkeypatch):
    """Capture the failure reports instead of writing them to stderr."""
    captured: list[tuple[StartupFailure, bool, str | None]] = []

    def _record(failure, *, packaged, detail=None):
        captured.append((failure, packaged, detail))

    monkeypatch.setattr(entrypoint, "report_startup_failure", _record)
    return captured


def make_application_root(tmp_path: Path, *, packaged: bool = False, complete: bool = True) -> Path:
    """Build a tree shaped like the packaged application root."""
    root = tmp_path / "app"
    (root / "launcher").mkdir(parents=True, exist_ok=True)
    (root / "launcher" / "main.py").write_text("# launcher\n", encoding="utf-8")
    if complete:
        backend = root / "backend" / "app"
        backend.mkdir(parents=True, exist_ok=True)
        (backend / "launcher_backend_entrypoint.py").write_text("# backend\n", encoding="utf-8")
        build_frontend_dist(root)
    if packaged:
        runtime = tmp_path / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        (root / "package-runtime.json").write_text(
            json.dumps(
                {
                    "python_version": "3.12.13",
                    "architecture": "arm64",
                    "runtime_root_relative_to_app": "../runtime",
                }
            ),
            encoding="utf-8",
        )
    return root


@pytest.fixture
def use_layout(monkeypatch):
    def _use(root: Path):
        layout = resolve_package_layout(root)
        monkeypatch.setattr(entrypoint, "resolve_package_layout", lambda: layout)
        return layout

    return _use


@pytest.fixture
def launcher_spy(monkeypatch):
    """Stand in for `launcher.runtime.run_local_runtime` and record its config."""
    import launcher.runtime as launcher_runtime

    calls: list = []

    def _spy(config):
        calls.append(config)
        return _spy.result

    _spy.result = 0
    monkeypatch.setattr(launcher_runtime, "run_local_runtime", _spy)
    return _spy, calls


def run(argv: list[str] | None = None) -> int:
    return entrypoint.run_packaged_application(
        argv or ["--no-browser", "--frontend-port", str(free_loopback_port())]
    )


# -- resource resolution ---------------------------------------------------


def test_source_tree_resolves_the_repository_as_the_application_root():
    """The same `__file__`-relative rule answers in both places the code runs."""
    layout = resolve_package_layout()
    assert layout.application_root == Path(__file__).resolve().parents[2]
    assert layout.launcher_dir.name == "launcher"
    assert layout.backend_app_dir.is_dir()
    assert not layout.is_packaged


def test_packaged_tree_is_recognised_by_its_own_manifest(tmp_path):
    root = make_application_root(tmp_path, packaged=True)
    layout = resolve_package_layout(root)
    assert layout.is_packaged
    assert layout.bundled_runtime_dir == (tmp_path / "runtime").resolve()
    assert missing_package_resources(layout) == []


def test_an_unparseable_manifest_is_not_a_crash(tmp_path):
    root = make_application_root(tmp_path, packaged=True)
    (root / "package-runtime.json").write_text("{ not json", encoding="utf-8")
    assert resolve_package_layout(root).is_packaged is False


@pytest.mark.parametrize(
    "removed,expected",
    [
        ("frontend/dist/index.html", "frontend_index"),
        ("backend/app/launcher_backend_entrypoint.py", "backend"),
        ("launcher/main.py", "launcher"),
    ],
)
def test_each_missing_resource_is_named(tmp_path, removed, expected):
    root = make_application_root(tmp_path)
    (root / removed).unlink()
    assert expected in missing_package_resources(resolve_package_layout(root))


def test_a_half_copied_frontend_build_is_missing_assets_not_just_an_index(tmp_path):
    """index.html without assets renders a blank page — the silent packaging bug."""
    root = make_application_root(tmp_path)
    for asset in (root / "frontend" / "dist" / "assets").iterdir():
        asset.unlink()
    assert "frontend_assets" in missing_package_resources(resolve_package_layout(root))


# -- refusals --------------------------------------------------------------


def test_incomplete_package_refuses_and_never_starts_the_launcher(
    tmp_path, use_layout, launcher_spy, reported
):
    """No fallback to a developer checkout: the artifact under test must be what runs."""
    _spy, calls = launcher_spy
    use_layout(make_application_root(tmp_path, complete=False))
    assert run() == entrypoint.EXIT_MISSING_RESOURCES
    assert calls == []
    assert reported[0][0] is StartupFailure.MISSING_RESOURCES


def test_packaged_run_refuses_when_the_bundled_runtime_is_not_running_it(
    tmp_path, use_layout, launcher_spy, reported
):
    """Otherwise the user's own Python silently becomes a dependency."""
    _spy, calls = launcher_spy
    root = make_application_root(tmp_path, packaged=True)
    layout = use_layout(root)
    # The test interpreter is nowhere near `tmp_path/runtime`.
    assert not bundled_runtime_owns_interpreter(layout)
    assert run() == entrypoint.EXIT_RUNTIME_MISSING
    assert calls == []
    assert reported[0][0] is StartupFailure.RUNTIME_MISSING


def test_packaged_run_accepts_an_interpreter_inside_the_bundle(tmp_path, monkeypatch):
    root = make_application_root(tmp_path, packaged=True)
    layout = resolve_package_layout(root)
    fake_interpreter = tmp_path / "runtime" / "bin" / "python3.12"
    fake_interpreter.parent.mkdir(parents=True, exist_ok=True)
    fake_interpreter.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(fake_interpreter))
    assert bundled_runtime_owns_interpreter(layout)


def test_occupied_frontend_port_refuses_without_touching_the_holder(
    tmp_path, use_layout, launcher_spy, reported
):
    _spy, calls = launcher_spy
    use_layout(make_application_root(tmp_path))
    port = free_loopback_port()
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    holder.bind(("127.0.0.1", port))
    holder.listen(1)
    try:
        code = entrypoint.run_packaged_application(
            ["--no-browser", "--frontend-port", str(port)]
        )
        assert code == entrypoint.EXIT_FRONTEND_PORT_UNAVAILABLE
        assert calls == []
        assert reported[0][0] is StartupFailure.FRONTEND_PORT_BUSY
        # The foreign process is still there and still listening.
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
    finally:
        holder.close()


# -- delegation ------------------------------------------------------------


def test_calls_the_existing_launcher_with_the_listener_origin(
    tmp_path, use_layout, launcher_spy
):
    """The frontend origin is the listener's own, not a repeated literal.

    ADR 0018 makes the Restore control plane check this origin exactly, so the
    two must be incapable of drifting apart.
    """
    _spy, calls = launcher_spy
    use_layout(make_application_root(tmp_path))
    frontend_port, backend_port = free_loopback_port(), free_loopback_port()
    code = entrypoint.run_packaged_application(
        [
            "--no-browser",
            "--frontend-port",
            str(frontend_port),
            "--backend-port",
            str(backend_port),
        ]
    )
    assert code == 0
    assert len(calls) == 1
    config = calls[0]
    assert config.frontend_url == f"http://127.0.0.1:{frontend_port}"
    assert config.backend_port == backend_port
    assert config.host == "127.0.0.1"
    assert config.mode == "user"
    assert config.open_browser is False


def test_default_launch_opens_the_ordinary_browser(tmp_path, use_layout, launcher_spy):
    """The browser is the product surface; the packaged default must not change that."""
    _spy, calls = launcher_spy
    use_layout(make_application_root(tmp_path))
    entrypoint.run_packaged_application(["--frontend-port", str(free_loopback_port())])
    assert calls[0].open_browser is True


def test_the_frontend_listener_is_running_while_the_launcher_runs(
    tmp_path, use_layout, monkeypatch
):
    import launcher.runtime as launcher_runtime

    observed: dict = {}
    port = free_loopback_port()

    def _probe(config):
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            observed["listening"] = True
        return 0

    monkeypatch.setattr(launcher_runtime, "run_local_runtime", _probe)
    use_layout(make_application_root(tmp_path))
    assert entrypoint.run_packaged_application(
        ["--no-browser", "--frontend-port", str(port)]
    ) == 0
    assert observed["listening"] is True
    # And it is gone once the launcher returned — no orphan holds the port.
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.5)


@pytest.mark.parametrize("launcher_result", [1, 2, 3, 15])
def test_a_non_zero_launcher_result_is_propagated_unchanged(
    tmp_path, use_layout, launcher_spy, launcher_result
):
    """A launcher refusal — including `restore_blocked` (3) — is never a success."""
    spy, _calls = launcher_spy
    spy.result = launcher_result
    use_layout(make_application_root(tmp_path))
    assert run() == launcher_result


def test_a_launcher_port_refusal_becomes_the_backend_port_message(
    tmp_path, use_layout, monkeypatch, reported
):
    import launcher.runtime as launcher_runtime

    def _refuse(_config):
        raise launcher_runtime.BackendPortUnavailableError("Порт 8000 уже занят.")

    monkeypatch.setattr(launcher_runtime, "run_local_runtime", _refuse)
    use_layout(make_application_root(tmp_path))
    assert run() == entrypoint.EXIT_BACKEND_PORT_UNAVAILABLE
    assert reported[0][0] is StartupFailure.BACKEND_PORT_BUSY


def test_a_generic_launcher_refusal_is_reported_as_a_refusal(
    tmp_path, use_layout, monkeypatch, reported
):
    import launcher.runtime as launcher_runtime

    def _refuse(_config):
        raise launcher_runtime.RuntimeLaunchError("Приложение уже запущено.")

    monkeypatch.setattr(launcher_runtime, "run_local_runtime", _refuse)
    use_layout(make_application_root(tmp_path))
    assert run() == entrypoint.EXIT_LAUNCHER_REFUSED
    assert reported[0][0] is StartupFailure.LAUNCHER_REFUSED


def test_an_unexpected_crash_keeps_the_traceback_out_of_the_user_message(
    tmp_path, use_layout, monkeypatch, reported
):
    import launcher.runtime as launcher_runtime

    def _explode(_config):
        raise ZeroDivisionError("internal detail nobody should read")

    monkeypatch.setattr(launcher_runtime, "run_local_runtime", _explode)
    use_layout(make_application_root(tmp_path))
    assert run() == entrypoint.EXIT_UNEXPECTED
    failure, _packaged, detail = reported[0]
    assert failure is StartupFailure.UNEXPECTED
    # The traceback goes to the log side only.
    assert "ZeroDivisionError" in detail
    assert "ZeroDivisionError" not in STARTUP_FAILURE_MESSAGES[failure]


def test_the_listener_is_stopped_even_when_the_launcher_crashes(
    tmp_path, use_layout, monkeypatch, reported
):
    import launcher.runtime as launcher_runtime

    port = free_loopback_port()
    monkeypatch.setattr(
        launcher_runtime, "run_local_runtime", lambda _c: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    use_layout(make_application_root(tmp_path))
    entrypoint.run_packaged_application(["--no-browser", "--frontend-port", str(port)])
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.5)


def test_keyboard_interrupt_is_a_clean_shutdown(tmp_path, use_layout, monkeypatch):
    """Quit from the Dock arrives as SIGTERM, which becomes this."""
    import launcher.runtime as launcher_runtime

    monkeypatch.setattr(
        launcher_runtime,
        "run_local_runtime",
        lambda _c: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    use_layout(make_application_root(tmp_path))
    assert run() == 0


# -- user-facing message safety --------------------------------------------


def test_every_startup_message_is_non_technical_and_actionable():
    """Readable, free of internals, and offering the user a next step."""
    for failure, message in STARTUP_FAILURE_MESSAGES.items():
        assert message.strip(), failure
        for forbidden in (
            "Traceback",
            "Error",
            "Exception",
            "/Users/",
            "sys.",
            "None",
            "sqlite",
            "SQLite",
            "migration",
            "5173",
            "8000",
        ):
            assert forbidden not in message, (failure, forbidden)
        # Every message ends by telling the user what to do next.
        assert any(word in message for word in ("Закройте", "Удалите", "Попробуйте")), failure


def test_only_proven_pre_mutation_failures_promise_that_data_is_unchanged():
    """The reassurance must track the control flow, not the mood of the message.

    By the time a launcher-stage failure is reported, the launcher may already
    have created the user-data directory, created the database, taken a
    `before_migration` backup and applied migrations. Promising an untouched
    database there would be a false statement about the user's records.
    """
    for failure, message in STARTUP_FAILURE_MESSAGES.items():
        claims = DATA_UNCHANGED_SENTENCE in message
        assert claims == (failure in PRE_MUTATION_FAILURES), (
            f"{failure} {'claims' if claims else 'does not claim'} unchanged data "
            f"but is {'' if failure in PRE_MUTATION_FAILURES else 'not '}a proven "
            "pre-mutation refusal"
        )


@pytest.mark.parametrize(
    "failure",
    [StartupFailure.LAUNCHER_REFUSED, StartupFailure.UNEXPECTED, StartupFailure.BACKEND_PORT_BUSY],
)
def test_post_launcher_failures_make_no_data_immutability_promise(failure):
    """These are all reachable after `initialize_backend_startup()` has run.

    `BACKEND_PORT_BUSY` is included deliberately. `BackendPortUnavailableError`
    is raised both by the launcher's early probe (before anything is written)
    and by the backend child losing a race for the port *after* migrations have
    been applied. Both arrive here as the same exception type, so the packaged
    entrypoint cannot tell them apart and must not promise what only one of them
    guarantees.
    """
    message = STARTUP_FAILURE_MESSAGES[failure]
    assert DATA_UNCHANGED_SENTENCE not in message
    for forbidden in ("ничего не изменив", "база данных не", "не была изменена"):
        assert forbidden not in message, (failure, forbidden)


def test_pre_mutation_set_matches_the_entrypoint_paths_that_precede_the_launcher():
    """The set is only trustworthy if it names refusals that really do precede it.

    Each of these is returned by the packaged entrypoint before
    `run_local_runtime` is called, so no launcher code has executed and the
    user-data directory has not been opened.
    """
    assert PRE_MUTATION_FAILURES == {
        StartupFailure.MISSING_RESOURCES,
        StartupFailure.RUNTIME_MISSING,
        StartupFailure.FRONTEND_PORT_BUSY,
    }


def test_a_generic_launcher_failure_is_presented_without_a_data_promise(
    tmp_path, use_layout, monkeypatch
):
    """End-to-end regression: the message a real launcher crash would show.

    Simulates a failure raised *after* the launcher would have completed startup
    work, and asserts the text the user is shown neither reassures them falsely
    nor leaks the internals of what went wrong.
    """
    import launcher.runtime as launcher_runtime

    shown: list[str] = []
    monkeypatch.setattr("macos_package.user_alert.show_alert", lambda message: shown.append(message))
    monkeypatch.delenv("COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS", raising=False)

    def _fail_after_startup_work(_config):
        raise sqlite3_like_failure()

    def sqlite3_like_failure():
        return RuntimeError("database is locked: /Users/someone/Documents/data.sqlite")

    monkeypatch.setattr(launcher_runtime, "run_local_runtime", _fail_after_startup_work)
    root = make_application_root(tmp_path, packaged=True)
    layout = resolve_package_layout(root)
    monkeypatch.setattr(entrypoint, "resolve_package_layout", lambda: layout)
    monkeypatch.setattr(
        "macos_package.entrypoint.bundled_runtime_owns_interpreter", lambda _layout: True
    )

    code = entrypoint.run_packaged_application(
        ["--no-browser", "--frontend-port", str(free_loopback_port())]
    )
    assert code == entrypoint.EXIT_UNEXPECTED
    assert shown == [STARTUP_FAILURE_MESSAGES[StartupFailure.UNEXPECTED]]
    displayed = shown[0]
    assert DATA_UNCHANGED_SENTENCE not in displayed
    # Nothing from the exception reaches the user-visible text.
    for leaked in ("database is locked", "/Users/someone", ".sqlite", "RuntimeError"):
        assert leaked not in displayed


def test_only_catalogue_messages_can_ever_be_displayed(monkeypatch):
    """The invariant that keeps composed text away from AppleScript."""
    monkeypatch.delenv("COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS", raising=False)
    called: list = []
    monkeypatch.setattr("macos_package.user_alert.subprocess.run", lambda *a, **k: called.append(a))
    assert show_alert("\" & (do shell script \"rm -rf /\") & \"") is False
    assert show_alert("/Users/someone/Documents/Мастерская косметолога/data") is False
    assert called == []
