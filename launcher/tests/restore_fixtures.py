"""Shared helpers for the `C4-I` Restore tests.

Every helper here builds an **isolated temporary workspace**. Nothing in these
tests touches the real `~/Documents/Мастерская косметолога/` directory, the
repository database or any real user data — `docs/pr-testing-and-smoke-rules.md`
§ 15-16 requires exactly that, and Restore is the operation where getting it
wrong would be least recoverable.

The recognizable marker is one `app_settings` row. It is enough to tell workspace
A from workspace B after a replacement, and it is fake data by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import sqlite3

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations

from launcher.restore.contracts import RestoreRequest
from launcher.restore.engine import RestoreServices

MARKER_KEY = "test.workspace_marker"


def build_workspace_database(path: Path, marker: str, *, up_to: str | None = None) -> Path:
    """Create a migrated workshop database carrying one recognizable marker.

    `up_to` truncates the migration chain to an earlier prefix, the same
    technique `launcher/tests/test_runtime_database_continuity.py` already uses,
    so an "older supported schema" candidate is a real one rather than a
    hand-written file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        if up_to is not None:
            cutoff = next(
                index for index, name in enumerate(original) if name.endswith(up_to)
            )
            MIGRATION_MODULES[:] = original[: cutoff + 1]
        apply_migrations(DatabaseConfig(path=path))
    finally:
        MIGRATION_MODULES[:] = original
    # Closed explicitly. `with sqlite3.connect(...)` commits but does *not*
    # close, and a lingering connection would hold a `-shm` that the journal
    # tests are specifically about.
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type, description) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (MARKER_KEY, marker, "string", "Isolated test marker."),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def read_marker(path: Path) -> str | None:
    """The marker a database carries, or `None` when it has none."""
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key = ?", (MARKER_KEY,)
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        connection.close()
    return row[0] if row else None


@dataclass(frozen=True)
class Workspace:
    """An isolated user-data layout, wired to the environment overrides."""

    base_dir: Path
    database_path: Path
    backup_dir: Path
    restore_dir: Path

    def request(self, selected_source: Path, mode: str = "user") -> RestoreRequest:
        return RestoreRequest(
            selected_source=selected_source,
            database_path=self.database_path,
            backup_dir=self.backup_dir,
            restore_dir=self.restore_dir,
            mode=mode,
        )

    def safety_copies(self) -> list[Path]:
        if not self.backup_dir.is_dir():
            return []
        return sorted(self.backup_dir.glob("*-before_restore*.sqlite"))


def make_workspace(monkeypatch, tmp_path: Path, marker: str = "workspace-A") -> Workspace:
    """Build an isolated user-data workspace and point the resolvers at it."""
    base_dir = tmp_path / "user-data"
    database_path = base_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(base_dir))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)
    build_workspace_database(database_path, marker)
    backup_dir = base_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return Workspace(
        base_dir=base_dir,
        database_path=database_path,
        backup_dir=backup_dir,
        restore_dir=base_dir / "restore",
    )


def make_source_backup(tmp_path: Path, marker: str, *, up_to: str | None = None) -> Path:
    """A selectable backup file outside the workspace, with its own marker."""
    source = tmp_path / "chosen" / "20260101T000000000000Z-cosmetic_workshop-manual.sqlite"
    build_workspace_database(source, marker, up_to=up_to)
    return source


# --------------------------------------------------------------------------
# Service stubs
# --------------------------------------------------------------------------
#
# Starting a real uvicorn child in every phase-machine test would make the suite
# minutes long and would prove nothing those tests are about. The real
# collaborators are exercised by the dedicated backend-verification tests and by
# the exact-head smoke runner; everything else substitutes them here.


def migrating_startup(database_path: Path):
    """A startup stand-in that really migrates the exact restored path."""

    def startup(_mode, _paths):
        apply_migrations(DatabaseConfig(path=database_path))
        return SimpleNamespace(database_path=database_path, backup=None)

    return startup


def stub_services(
    database_path: Path,
    *,
    verify=None,
    startup=None,
) -> RestoreServices:
    """Services that migrate for real but verify without a backend process."""
    return RestoreServices(
        verify_backend=verify if verify is not None else (lambda _c, _p, _db: None),
        initialize_startup=startup if startup is not None else migrating_startup(database_path),
    )


def failing_verifier(message: str = "verification refused", *, only_first: bool = True):
    """A verifier that refuses the restored workspace.

    `only_first` is the realistic shape: the restored candidate fails, and the
    rolled-back previous workspace then verifies normally. A verifier that
    refused *every* call would also refuse the rollback verification, which the
    engine correctly escalates to `recovery_blocked` — a different scenario,
    covered by its own tests.
    """
    calls = {"n": 0}

    def verify(_config, _paths, _database_path):
        calls["n"] += 1
        if not only_first or calls["n"] == 1:
            raise RuntimeError(message)
        return None

    return verify


def failing_startup(database_path: Path, message: str = "migration refused"):
    """A startup stand-in that refuses the restored copy, then behaves."""
    calls = {"n": 0}
    healthy = migrating_startup(database_path)

    def startup(mode, paths):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError(message)
        return healthy(mode, paths)

    return startup


DUMMY_CONFIG = SimpleNamespace(backend_url="http://127.0.0.1:0", host="127.0.0.1", backend_port=0)
DUMMY_PATHS = SimpleNamespace()
