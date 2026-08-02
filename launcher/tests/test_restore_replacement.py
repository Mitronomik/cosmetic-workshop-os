"""The replacement target, its SQLite sidecars, and the atomic boundary.

The sidecar tests are the ones that matter most. Replacing a main database while
a `-wal` or `-journal` survives beside it produces a file that every structural
check calls `ok` and that SQLite will happily corrupt by applying another
database's transaction state to it.

The rule the implementation follows: settle the journal through SQLite's own
lifecycle, then **verify**. Never unlink a sidecar the launcher cannot account
for — committed WAL data is real user data.
"""

from pathlib import Path
import hashlib
import sqlite3

import pytest

from launcher.restore.replacement import (
    JournalSafetyError,
    ReplacementError,
    ReplacementTargetError,
    assert_replaceable_target,
    commit_replacement,
    discard_replacement_artifact,
    existing_target_sidecars,
    prepare_replacement_artifact,
    quiesce_target_journal,
    target_sidecar_paths,
)
from launcher.restore.workspace import OWNED_TEMP_PREFIX

from launcher.tests.restore_fixtures import MARKER_KEY, build_workspace_database, read_marker


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def target(tmp_path):
    return build_workspace_database(tmp_path / "data" / "workshop.sqlite", "workspace-A")


@pytest.fixture
def candidate(tmp_path):
    return build_workspace_database(tmp_path / "staged" / "candidate.sqlite", "workspace-B")


# --------------------------------------------------------------------------
# Target identity
# --------------------------------------------------------------------------

def test_the_exact_configured_database_is_the_only_accepted_target(target):
    assert assert_replaceable_target(target, target) == target


def test_a_foreign_path_is_never_accepted_as_the_target(target, tmp_path):
    with pytest.raises(ReplacementTargetError):
        assert_replaceable_target(tmp_path / "somewhere-else.sqlite", target)


def test_a_symlinked_database_path_is_refused(tmp_path, target):
    """Replacing a symlink would leave the real database untouched."""
    link = tmp_path / "data" / "linked.sqlite"
    link.symlink_to(target)

    with pytest.raises(ReplacementTargetError):
        assert_replaceable_target(link, link)


def test_a_missing_target_is_refused(tmp_path):
    absent = tmp_path / "absent.sqlite"

    with pytest.raises(ReplacementTargetError):
        assert_replaceable_target(absent, absent)


# --------------------------------------------------------------------------
# Sidecars
# --------------------------------------------------------------------------

def test_the_sidecar_paths_are_exact_and_named(target):
    names = [path.name for path in target_sidecar_paths(target)]

    assert names == [
        "workshop.sqlite-wal",
        "workshop.sqlite-shm",
        "workshop.sqlite-journal",
    ]


def run_and_abandon(database: Path, statements: str) -> None:
    """Run SQL in another process and exit without closing the connection.

    SQLite checkpoints and removes the WAL when the *last* connection closes
    cleanly, so a leftover `-wal`/`-shm` can only be produced by a process that
    dies holding it — which is exactly the case the launcher has to survive
    (a backend killed mid-session). `os._exit` skips every cleanup handler.
    """
    import subprocess
    import sys

    script = "\n".join(
        [
            "import os, sqlite3, sys",
            "connection = sqlite3.connect(sys.argv[1], isolation_level=None)",
            statements,
            "os._exit(0)",
        ]
    )
    subprocess.run([sys.executable, "-c", script, str(database)], check=True, timeout=30)


def test_committed_wal_data_survives_the_journal_settlement(tmp_path):
    """The checkpoint preserves committed rows; it does not discard them.

    This is the `CR-004` failure mode in the opposite direction: a WAL whose
    committed frames were never checkpointed is real user data, and the
    settlement must fold it into the main file rather than drop it.
    """
    database = build_workspace_database(tmp_path / "data" / "wal.sqlite", "wal-workspace")
    run_and_abandon(
        database,
        'connection.execute("PRAGMA journal_mode = WAL")\n'
        'connection.execute("INSERT INTO app_settings '
        "(key, value, value_type, description) "
        "VALUES ('committed.in.wal', 'present', 'string', '')\")",
    )
    assert database.with_name(database.name + "-wal").exists()

    quiesce_target_journal(database)

    assert existing_target_sidecars(database) == []
    reader = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        row = reader.execute(
            "SELECT value FROM app_settings WHERE key = 'committed.in.wal'"
        ).fetchone()
    finally:
        reader.close()
    assert row[0] == "present", "a committed WAL row must survive the settlement"
    assert read_marker(database) == "wal-workspace"


def test_an_existing_wal_mode_database_leaves_no_sidecar_behind(tmp_path):
    database = build_workspace_database(tmp_path / "data" / "wal.sqlite", "wal")
    run_and_abandon(
        database,
        'connection.execute("PRAGMA journal_mode = WAL")\nconnection.execute("SELECT 1")',
    )

    quiesce_target_journal(database)

    assert existing_target_sidecars(database) == []


def test_a_stale_owned_wal_and_shm_are_removed_through_sqlite(tmp_path):
    database = build_workspace_database(tmp_path / "data" / "stale.sqlite", "stale")
    run_and_abandon(
        database,
        'connection.execute("PRAGMA journal_mode = WAL")\n'
        'connection.execute("SELECT COUNT(*) FROM app_settings")',
    )
    assert database.with_name(database.name + "-shm").exists()
    assert database.with_name(database.name + "-wal").exists()

    quiesce_target_journal(database)

    assert not database.with_name(database.name + "-shm").exists()
    assert not database.with_name(database.name + "-wal").exists()


def test_a_real_hot_rollback_journal_is_recovered_and_removed(tmp_path):
    """A killed writer leaves a hot journal; SQLite rolls it back on open.

    Produced by an actual interrupted transaction in a separate process rather
    than by writing a fake file, because only the real thing exercises the
    recovery path.
    """
    import subprocess
    import sys
    import textwrap

    database = build_workspace_database(tmp_path / "data" / "hot.sqlite", "before-crash")
    script = textwrap.dedent(
        """
        import os, sqlite3, sys
        connection = sqlite3.connect(sys.argv[1], isolation_level=None)
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "UPDATE app_settings SET value = 'after-crash' WHERE key = ?", (sys.argv[2],)
        )
        os._exit(0)
        """
    )
    subprocess.run(
        [sys.executable, "-c", script, str(database), MARKER_KEY], check=True, timeout=30
    )
    assert database.with_name(database.name + "-journal").exists()

    quiesce_target_journal(database)

    assert existing_target_sidecars(database) == []
    # Rolled back, not applied: the uncommitted write never existed.
    assert read_marker(database) == "before-crash"


def test_a_sidecar_that_cannot_be_handled_safely_blocks_replacement(tmp_path, target, monkeypatch):
    """No blind unlink: the operation stops instead."""
    import launcher.restore.replacement as replacement_module

    # A sidecar SQLite's own lifecycle did not resolve. The launcher must refuse
    # rather than reach for `unlink`, so the check is stubbed to report one that
    # survives the settlement.
    stubborn = tmp_path / "data" / "unresolvable-sidecar"
    stubborn.write_bytes(b"not something the launcher can account for")
    monkeypatch.setattr(
        replacement_module, "existing_target_sidecars", lambda _path: [stubborn]
    )

    with pytest.raises(JournalSafetyError):
        quiesce_target_journal(target)

    assert stubborn.exists(), "an unaccountable sidecar is never deleted"


def test_journal_settlement_does_not_change_the_business_data(target):
    before = read_marker(target)

    quiesce_target_journal(target)

    assert read_marker(target) == before


def test_no_active_connection_remains_after_settlement(target):
    """The last handle this process holds is released before replacement."""
    quiesce_target_journal(target)

    # An exclusive lock proves nothing else in this process still has it open.
    connection = sqlite3.connect(target, timeout=1.0)
    try:
        connection.execute("PRAGMA locking_mode = EXCLUSIVE")
        connection.execute("BEGIN EXCLUSIVE")
        connection.execute("ROLLBACK")
    finally:
        connection.close()


# --------------------------------------------------------------------------
# The boundary
# --------------------------------------------------------------------------

def test_the_replacement_artifact_is_staged_beside_the_target(target, candidate):
    artifact = prepare_replacement_artifact(candidate, target)

    assert artifact.parent == target.parent
    assert artifact.name.startswith(OWNED_TEMP_PREFIX)
    assert digest(artifact) == digest(candidate)
    discard_replacement_artifact(artifact)


def test_the_replacement_is_one_atomic_same_filesystem_rename(target, candidate, monkeypatch):
    import launcher.restore.replacement as replacement_module

    renames: list[tuple[str, str]] = []
    real_replace = replacement_module.os.replace

    def watched(src, dst):
        renames.append((str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(replacement_module.os, "replace", watched)
    artifact = prepare_replacement_artifact(candidate, target)
    commit_replacement(artifact, target)

    assert len(renames) == 1
    assert renames[0][1] == str(target)
    assert read_marker(target) == "workspace-B"


def test_the_staged_candidate_is_preserved_as_evidence(target, candidate):
    before = digest(candidate)

    artifact = prepare_replacement_artifact(candidate, target)
    commit_replacement(artifact, target)

    assert candidate.exists()
    assert digest(candidate) == before


def test_a_failed_artifact_write_leaves_nothing_behind(target, tmp_path, monkeypatch):
    import shutil

    source = build_workspace_database(tmp_path / "src" / "c.sqlite", "src")

    def fail(_reader, _writer, length=0):
        raise OSError(28, "no space left on device")

    monkeypatch.setattr(shutil, "copyfileobj", fail)

    with pytest.raises(ReplacementError):
        prepare_replacement_artifact(source, target)

    leftovers = [p for p in target.parent.iterdir() if p.name.startswith(OWNED_TEMP_PREFIX)]
    assert leftovers == []


def test_discard_only_removes_launcher_owned_artifacts(target, tmp_path):
    foreign = tmp_path / "data" / "not-ours.sqlite"
    foreign.write_bytes(b"keep me")

    discard_replacement_artifact(foreign)

    assert foreign.exists()


def test_a_replacement_failure_is_reported_rather_than_guessed(target, candidate, monkeypatch):
    import launcher.restore.replacement as replacement_module

    monkeypatch.setattr(
        replacement_module.os,
        "replace",
        lambda *_a: (_ for _ in ()).throw(OSError(18, "cross-device link")),
    )
    artifact = prepare_replacement_artifact(candidate, target)

    with pytest.raises(ReplacementError):
        commit_replacement(artifact, target)
    discard_replacement_artifact(artifact)
