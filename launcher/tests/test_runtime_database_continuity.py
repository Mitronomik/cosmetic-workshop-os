"""One database across startup and the API child.

User-mode startup selects a database under the user-data directory, backs it up,
migrates it and reconciles unresolved CR-009 operations against it. If the
uvicorn child then resolves its own database, every one of those steps was
applied to a file the user never sees: the API would serve an unmigrated
database while the real one sat untouched, and `pending_audit_count` would be
answered from the wrong ledger.

These tests prove the launcher hands the exact startup-selected path down, that
a stale inherited value cannot win, and — most importantly — that the continuity
is observable in the database itself rather than merely asserted about an
environment key.
"""

import sqlite3
import subprocess
from pathlib import Path

import pytest

from app.db.config import DATABASE_PATH_ENV, DEFAULT_DATABASE_PATH, DatabaseConfig, get_database_config
from app.db.paths import USER_DATA_DIR_ENV
from launcher import runtime
from launcher.config import build_runtime_config, resolve_runtime_paths

USER_DATA_ENV = "COSMETIC_WORKSHOP_USER_DATA_DIR"


class RecordedPopen:
    """A stand-in for the backend child that captures what it was launched with.

    It also completes the launcher's lock-acquisition handshake. The real child
    takes the backend-liveness lock before importing anything and reports that
    over the inherited pipe; a stand-in that stayed silent would not be a
    simplified child, it would be a child the launcher is right to refuse — and
    every test here would fail on a bounded timeout that proves nothing.
    """

    instances: list["RecordedPopen"] = []

    def __init__(self, command, cwd=None, env=None, text=None, pass_fds=()):
        self.command = command
        self.cwd = cwd
        self.env = dict(env or {})
        self.pass_fds = tuple(pass_fds)
        self.handshake_written = self._complete_handshake()
        RecordedPopen.instances.append(self)

    def _complete_handshake(self) -> bool:
        """Report the liveness lock exactly as the real entrypoint does."""
        import os

        from app.launcher_backend_entrypoint import (
            HANDSHAKE_ACQUIRED_PREFIX,
            HANDSHAKE_FD_ENV,
            HANDSHAKE_TOKEN_ENV,
        )

        raw_fd = self.env.get(HANDSHAKE_FD_ENV)
        token = self.env.get(HANDSHAKE_TOKEN_ENV)
        if not raw_fd or not token:
            return False
        os.write(int(raw_fd), f"{HANDSHAKE_ACQUIRED_PREFIX}{token}\n".encode("utf-8"))
        return True

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0

    def send_signal(self, _signal):
        return None

    def kill(self):
        return None


@pytest.fixture
def recorded_child(monkeypatch):
    RecordedPopen.instances = []
    monkeypatch.setattr(subprocess, "Popen", RecordedPopen)
    return RecordedPopen


def free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def table_names(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def applied_migrations(database_path: Path) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        return [row[0] for row in connection.execute("SELECT migration_id FROM schema_migrations")]


def run_launcher(monkeypatch, mode: str):
    """Run the real `run_local_runtime` with the child process stubbed out."""
    monkeypatch.setattr(runtime, "open_runtime_browser", lambda _config: None)
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)
    config = build_runtime_config(backend_port=free_port(), mode=mode, open_browser=False)
    runtime.run_local_runtime(config, resolve_runtime_paths())
    assert len(RecordedPopen.instances) == 1
    return RecordedPopen.instances[0]


# --------------------------------------------------------------------------
# The environment the child is actually given
# --------------------------------------------------------------------------

def test_user_mode_child_receives_the_exact_startup_database_path(monkeypatch, tmp_path, recorded_child):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    child = run_launcher(monkeypatch, "user")

    expected = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    assert child.env[DATABASE_PATH_ENV] == str(expected)
    assert expected.exists()
    # Not the repository default, which is what the child would otherwise pick.
    assert child.env[DATABASE_PATH_ENV] != str(DEFAULT_DATABASE_PATH)


def test_development_mode_child_receives_the_startup_database_path(monkeypatch, tmp_path, recorded_child):
    development_database = tmp_path / "development" / "workshop.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(development_database))
    monkeypatch.delenv(USER_DATA_ENV, raising=False)

    child = run_launcher(monkeypatch, "development")

    assert child.env[DATABASE_PATH_ENV] == str(development_database)
    assert development_database.exists()


def test_a_stale_inherited_database_path_is_overridden_in_user_mode(monkeypatch, tmp_path, recorded_child):
    """The startup result wins over whatever the parent shell happened to hold.

    A leftover `COSMETIC_WORKSHOP_DB_PATH` from an earlier development session is
    exactly the case that would otherwise split the two processes apart while
    every individual step looked correct.
    """
    user_data_dir = tmp_path / "user-data"
    stale = tmp_path / "stale" / "wrong.sqlite"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"")
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.setenv(DATABASE_PATH_ENV, str(stale))

    child = run_launcher(monkeypatch, "user")

    expected = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    assert child.env[DATABASE_PATH_ENV] == str(expected)
    assert child.env[DATABASE_PATH_ENV] != str(stale)
    # The stale file was never migrated.
    assert table_names(stale) == set()


def test_the_child_keeps_its_existing_pythonpath_host_port_and_cwd(monkeypatch, tmp_path, recorded_child):
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    monkeypatch.setenv("PYTHONPATH", "/existing/entry")
    paths = resolve_runtime_paths()

    child = run_launcher(monkeypatch, "user")

    assert child.cwd == paths.backend_dir
    assert str(paths.backend_dir) in child.env["PYTHONPATH"]
    assert "/existing/entry" in child.env["PYTHONPATH"]
    # The launcher-managed entrypoint, not `uvicorn` directly: it takes the
    # backend-liveness lock before importing `app.main`, so a launcher-managed
    # child is never invisible to the check that authorizes replacing the
    # database it is about to open.
    assert child.command[:3] == [
        runtime.sys.executable,
        "-m",
        runtime.BACKEND_ENTRYPOINT_MODULE,
    ]
    assert "uvicorn" not in child.command
    assert "--host" in child.command and "127.0.0.1" in child.command


def test_start_backend_process_requires_a_database_path(monkeypatch, tmp_path, recorded_child):
    """The path is mandatory, so the startup/API split cannot silently return.

    An optional parameter would leave this defect one forgetful call site away,
    and it fails silently: startup migrates one database, the API serves
    another, and every individual step still reports success. Requiring it turns
    that into an immediate, loud `TypeError` at the call.
    """
    import inspect

    signature = inspect.signature(runtime.start_backend_process)
    parameter = signature.parameters["database_path"]

    assert parameter.default is inspect.Parameter.empty, "database_path must have no default"
    assert parameter.annotation in (Path, "Path"), "database_path must be a plain Path, not Path | None"

    config = build_runtime_config(backend_port=free_port(), mode="user", open_browser=False)
    with pytest.raises(TypeError):
        runtime.start_backend_process(config, resolve_runtime_paths())


def test_start_backend_process_pins_the_database_environment_unconditionally(monkeypatch, tmp_path, recorded_child):
    """Every start pins the key — there is no branch that can skip it."""
    import inspect

    source = inspect.getsource(runtime.start_backend_process)
    assert "if database_path is not None" not in source
    assert "database_path or " not in source

    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    chosen = tmp_path / "chosen" / "workshop.sqlite"
    config = build_runtime_config(backend_port=free_port(), mode="user", open_browser=False)

    runtime.start_backend_process(config, resolve_runtime_paths(), chosen)

    assert RecordedPopen.instances[-1].env[DATABASE_PATH_ENV] == str(chosen)


def test_no_production_call_site_starts_the_api_without_a_database_path():
    """Every real caller supplies the startup-selected path.

    Both spawning functions are checked. `start_owned_backend_process` is the one
    production startup uses — it adds the lock-acquisition handshake — and it
    forwards to `start_backend_process`, so a call site that named no database
    would be just as silent a defect through either name.
    """
    import ast
    import inspect

    # Parsed rather than grepped: the call spans several lines now, and a textual
    # check would have quietly stopped covering it.
    tree = ast.parse(inspect.getsource(runtime))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in ("start_backend_process", "start_owned_backend_process")
    ]

    assert calls, "expected at least one production call site"
    for call in calls:
        supplied = [ast.unparse(argument) for argument in call.args]
        assert any("database_path" in argument for argument in supplied), ast.unparse(call)

    launcher_source = inspect.getsource(runtime._run_locked_runtime)
    assert "startup.database_path" in launcher_source


def test_the_launcher_reads_the_database_environment_key_from_the_backend(monkeypatch, tmp_path):
    """The key is not duplicated as a literal in the launcher.

    If the backend ever renames it, the launcher follows automatically instead of
    silently writing an ignored variable.
    """
    assert runtime.backend_database_path_env(resolve_runtime_paths()) == DATABASE_PATH_ENV


# --------------------------------------------------------------------------
# Observable continuity, not just an environment key
# --------------------------------------------------------------------------

def test_the_api_database_config_resolves_to_the_startup_database(monkeypatch, tmp_path, recorded_child):
    """Applying the child's environment must make the backend open that database.

    This closes the loop: it is not enough that the launcher sets a variable —
    the backend's own resolver has to agree, which is what the real child does at
    import time.
    """
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    child = run_launcher(monkeypatch, "user")

    for key, value in child.env.items():
        if key in (DATABASE_PATH_ENV, USER_DATA_ENV):
            monkeypatch.setenv(key, value)
    assert get_database_config().path == user_data_dir / "data" / "cosmetic_workshop.sqlite"


def test_backup_migration_reconciliation_and_api_all_use_one_database(monkeypatch, tmp_path, recorded_child):
    """The whole user-mode chain lands on a single file.

    Proven through the database rather than the environment: the startup-selected
    database is the one that gets migration `0020`, the one a document created
    through the API writes its ledger row and AuditLog event into, and the one a
    later restart reconciles. The repository default must stay untouched.
    """
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    user_database = user_data_dir / "data" / "cosmetic_workshop.sqlite"

    # A pre-existing database at the previous migration level, so a backup and a
    # real migration both have to happen.
    from app.db.migrations import MIGRATION_MODULES, apply_migrations

    user_database.parent.mkdir(parents=True)
    original = list(MIGRATION_MODULES)
    try:
        cutoff = next(i for i, name in enumerate(original) if name.endswith("0020_artifact_audit_operations"))
        MIGRATION_MODULES[:] = original[:cutoff]
        apply_migrations(DatabaseConfig(path=user_database))
    finally:
        MIGRATION_MODULES[:] = original
    assert "artifact_audit_operations" not in table_names(user_database)

    default_existed = DEFAULT_DATABASE_PATH.exists()
    default_tables_before = table_names(DEFAULT_DATABASE_PATH) if default_existed else None

    child = run_launcher(monkeypatch, "user")

    # The launcher migrated the user database and told the child to use it.
    assert child.env[DATABASE_PATH_ENV] == str(user_database)
    assert "0020_artifact_audit_operations" in applied_migrations(user_database)
    assert "artifact_audit_operations" in table_names(user_database)
    assert (user_data_dir / "backups").exists()
    assert list((user_data_dir / "backups").glob("*.sqlite"))

    # Now act as the child does, and create a document through the API.
    for key, value in child.env.items():
        if key in (DATABASE_PATH_ENV, USER_DATA_ENV):
            monkeypatch.setenv(key, value)
    from app.schemas.report_documents import ReportOverviewDocumentCreateRequest
    from app.services.report_documents import ReportDocumentService

    service = ReportDocumentService()
    assert service.config.path == user_database
    response = service.create_overview_document(ReportOverviewDocumentCreateRequest(format="markdown"))
    assert response.audit_status == "recorded"

    # The ledger row and the AuditLog event are in the startup-selected database.
    with sqlite3.connect(user_database) as connection:
        operations = connection.execute(
            "SELECT status, audit_log_id FROM artifact_audit_operations"
        ).fetchall()
        actions = [row[0] for row in connection.execute("SELECT action FROM audit_logs")]
    assert len(operations) == 1
    assert operations[0][0] == "audited"
    assert operations[0][1] is not None
    assert actions == ["report_document.created"]

    # And the status endpoint reads that same ledger.
    assert service.status().pending_audit_count == 0

    # The repository default database was never used for any of this.
    if default_existed:
        assert table_names(DEFAULT_DATABASE_PATH) == default_tables_before
        with sqlite3.connect(DEFAULT_DATABASE_PATH) as connection:
            if "artifact_audit_operations" in (default_tables_before or set()):
                assert connection.execute("SELECT COUNT(*) FROM artifact_audit_operations").fetchone()[0] == 0
    else:
        assert not DEFAULT_DATABASE_PATH.exists()


def test_a_restart_reconciles_the_same_database_the_api_wrote_to(monkeypatch, tmp_path, recorded_child):
    """Startup reconciliation must find what the API left behind."""
    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)
    user_database = user_data_dir / "data" / "cosmetic_workshop.sqlite"

    child = run_launcher(monkeypatch, "user")
    for key, value in child.env.items():
        if key in (DATABASE_PATH_ENV, USER_DATA_ENV):
            monkeypatch.setenv(key, value)

    # Create a document whose Journal entry cannot be written.
    from app.repositories.audit import AuditLogRepository
    from app.schemas.report_documents import ReportOverviewDocumentCreateRequest
    from app.services.report_documents import ReportDocumentService

    def failing_create_log(*_args, **_kwargs):
        raise sqlite3.OperationalError("audit insert refused")

    monkeypatch.setattr(AuditLogRepository, "create_log", failing_create_log)
    response = ReportDocumentService().create_overview_document(
        ReportOverviewDocumentCreateRequest(format="markdown")
    )
    assert response.audit_status == "pending"
    monkeypatch.undo()
    monkeypatch.setenv(USER_DATA_ENV, str(user_data_dir))
    monkeypatch.setenv(DATABASE_PATH_ENV, str(user_database))
    monkeypatch.setattr(subprocess, "Popen", RecordedPopen)
    monkeypatch.setattr(runtime, "open_runtime_browser", lambda _config: None)
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)

    with sqlite3.connect(user_database) as connection:
        assert connection.execute(
            "SELECT status FROM artifact_audit_operations"
        ).fetchone()[0] == "pending_audit"

    # Restart through the launcher: reconciliation runs against that database.
    RecordedPopen.instances = []
    restart_config = build_runtime_config(backend_port=free_port(), mode="user", open_browser=False)
    runtime.run_local_runtime(restart_config, resolve_runtime_paths())

    with sqlite3.connect(user_database) as connection:
        status_row = connection.execute("SELECT status, audit_log_id FROM artifact_audit_operations").fetchone()
        actions = [row[0] for row in connection.execute("SELECT action FROM audit_logs")]
    assert status_row[0] == "audited"
    assert status_row[1] is not None
    assert actions == ["report_document.created"]
    assert ReportDocumentService().status().pending_audit_count == 0
