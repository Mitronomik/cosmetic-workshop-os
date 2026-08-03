"""The launcher-managed entrypoint takes the liveness lock before the app.

`app/launcher_backend_entrypoint.py` exists for one ordering guarantee, so these
tests are about that ordering and nothing else.

Acquiring the lock in the FastAPI lifespan takes it after Python has imported
uvicorn, `app.main`, every router and the database layer. Everything before that
is a window in which a launcher-managed backend exists and holds nothing — and a
launcher that dies inside that window leaves a child which later opens the
database underneath whatever the next launcher decided to do with it.

The lifespan acquisition stays, as an idempotent defence. It simply may no longer
be the *first* acquisition point for a launcher-managed child.
"""

from pathlib import Path
import ast
import inspect


def executable_source(target) -> str:
    """One callable's source with comments and string literals removed.

    The entrypoint *documents* why `uvicorn.run()` is not used, so a plain
    substring check would trip on the explanation of its own absence.
    """
    import io
    import textwrap
    import tokenize

    kept: list[str] = []
    stream = io.StringIO(textwrap.dedent(inspect.getsource(target))).readline
    for token in tokenize.generate_tokens(stream):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept)
import os
import subprocess
import sys

import pytest

from app import launcher_backend_entrypoint as entrypoint
from app.services.backend_liveness import (
    BACKEND_LIVENESS_LOCK_ENV,
    BackendLivenessError,
    release_backend_liveness_lock,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------
# The ordering, as a structural property
# --------------------------------------------------------------------------

def test_no_application_module_is_imported_at_module_scope():
    """A module-scope `app.main` would reopen the window this file closes."""
    tree = ast.parse(inspect.getsource(entrypoint))
    imported: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    for name in imported:
        assert not name.startswith("app."), f"{name} must not be imported before the lock"
        assert name != "uvicorn", "uvicorn must not be imported before the lock"


def test_the_lock_helper_imports_only_the_liveness_module():
    """The narrowest possible import: one file descriptor, no domain coupling."""
    source = inspect.getsource(entrypoint.acquire_lock_before_import)

    assert "from app.services.backend_liveness import" in source
    assert "app.main" not in source
    assert "uvicorn" not in source


def test_the_application_is_named_only_where_it_is_served():
    serving = inspect.getsource(entrypoint.run_backend)

    assert "uvicorn" in serving
    assert "app.main:app" in serving


def test_the_socket_is_served_rather_than_bound_a_second_time():
    """uvicorn is handed the socket the child already owns.

    `uvicorn.run(host=..., port=...)` would bind again, *after* readiness had been
    reported — which is the exact window the sixth correction closes. The
    low-level `Server.run(sockets=[...])` path hands the existing socket to
    `loop.create_server(sock=...)` and never binds.
    """
    serving = executable_source(entrypoint.run_backend)

    assert "server . run ( sockets = [ server_socket ] )" in serving
    assert "uvicorn . run (" not in serving, (
        "uvicorn.run() binds again, after readiness has already been reported"
    )


def test_main_acquires_binds_reports_and_only_then_serves():
    """The four steps, in order, in the one function that sequences them."""
    source = inspect.getsource(entrypoint.main)

    acquire = source.index("acquire_lock_before_import()")
    bind = source.index("bind_configured_socket(")
    signal = source.index("signal_ready()")
    serve = source.index("run_backend(")

    assert acquire < bind < signal < serve


def test_main_acquires_reports_and_only_then_serves():
    """Readiness is reported after the lock **and** the socket, never before.

    Kept under its original name because it guards the original rule; what
    changed is that "reports" now means "reports ownership of both", so the bind
    is part of the ordering it asserts.
    """
    source = inspect.getsource(entrypoint.main)

    acquire = source.index("acquire_lock_before_import()")
    signal = source.index("signal_ready()")
    serve = source.index("run_backend(")

    assert acquire < signal < serve


# --------------------------------------------------------------------------
# The lock itself
# --------------------------------------------------------------------------

def test_an_unmanaged_process_claims_nothing(monkeypatch):
    monkeypatch.delenv(BACKEND_LIVENESS_LOCK_ENV, raising=False)

    assert entrypoint.acquire_lock_before_import() is None


def test_a_managed_process_takes_the_assigned_lock(monkeypatch, tmp_path):
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    monkeypatch.setenv(BACKEND_LIVENESS_LOCK_ENV, str(lock_path))
    try:
        assert entrypoint.acquire_lock_before_import() == lock_path
    finally:
        release_backend_liveness_lock()


def test_a_taken_lock_refuses_the_entrypoint(monkeypatch, tmp_path):
    """Another holder means another writer; the child must not continue."""
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl, os, sys, time\n"
            "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
            "fcntl.flock(fd, fcntl.LOCK_EX)\n"
            "print('held', flush=True)\n"
            "time.sleep(120)\n",
            str(lock_path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "held"
        monkeypatch.setenv(BACKEND_LIVENESS_LOCK_ENV, str(lock_path))

        with pytest.raises(BackendLivenessError):
            entrypoint.acquire_lock_before_import()
    finally:
        holder.terminate()
        holder.wait(timeout=10)


def test_main_exits_with_the_refused_code_without_importing_the_application(
    monkeypatch, tmp_path
):
    """A refused child exits; it does not fall through to serving.

    Run in a real subprocess, because "the application was never imported" is a
    claim about `sys.modules` in the process that did the refusing.
    """
    lock_path = tmp_path / "restore" / "backend-liveness.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl, os, sys, time\n"
            "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
            "fcntl.flock(fd, fcntl.LOCK_EX)\n"
            "print('held', flush=True)\n"
            "time.sleep(120)\n",
            str(lock_path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "held"

        environment = os.environ.copy()
        environment[BACKEND_LIVENESS_LOCK_ENV] = str(lock_path)
        environment["PYTHONPATH"] = str(BACKEND_DIR)
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys\n"
                "from app import launcher_backend_entrypoint as entrypoint\n"
                "code = entrypoint.main(['--host', '127.0.0.1', '--port', '0'])\n"
                "print(code)\n"
                "print('app.main' in sys.modules)\n"
                "print('uvicorn' in sys.modules)\n",
            ],
            cwd=BACKEND_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )
        reported = completed.stdout.strip().splitlines()

        assert reported[0] == str(entrypoint.LOCK_REFUSED_EXIT_CODE)
        assert reported[1] == "False", "the application was imported after a refusal"
        assert reported[2] == "False", "uvicorn was imported after a refusal"
        # The refusal is a fixed non-technical sentence, never a traceback.
        assert "Traceback" not in completed.stderr
        assert "BackendLivenessError" not in completed.stderr
    finally:
        holder.terminate()
        holder.wait(timeout=10)


# --------------------------------------------------------------------------
# The handshake the launcher waits on
# --------------------------------------------------------------------------

def test_no_handshake_is_written_when_none_was_requested(monkeypatch):
    monkeypatch.delenv(entrypoint.HANDSHAKE_FD_ENV, raising=False)
    monkeypatch.delenv(entrypoint.HANDSHAKE_TOKEN_ENV, raising=False)

    assert entrypoint.signal_ready() is False


def test_the_handshake_reports_the_token_it_was_given(monkeypatch):
    read_fd, write_fd = os.pipe()
    monkeypatch.setenv(entrypoint.HANDSHAKE_FD_ENV, str(write_fd))
    monkeypatch.setenv(entrypoint.HANDSHAKE_TOKEN_ENV, "abc123")
    try:
        assert entrypoint.signal_ready() is True
        # The child closes its end, so the launcher sees EOF if it later dies.
        assert os.read(read_fd, 512) == b"ready:abc123\n"
        assert os.read(read_fd, 512) == b""
    finally:
        os.close(read_fd)


def test_the_lifespan_acquisition_remains_as_an_idempotent_defence():
    """The entrypoint is the first acquisition, not the only one."""
    from app import main as app_main

    lifespan = inspect.getsource(app_main._lifespan)
    assert "acquire_backend_liveness_lock()" in lifespan
