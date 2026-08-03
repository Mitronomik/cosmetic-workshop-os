"""Source intake and the staged read-only candidate.

Two properties dominate this file, and both are about the **original selected
source** rather than the staged copy — which is exactly where an earlier version
of this engine was wrong.

**Self-containment.** Staging copies the main SQLite file and nothing else, so a
source with a live `-wal` beside it would be staged without its newest committed
rows and would still pass `PRAGMA quick_check`. Checking for sidecars beside the
*staged* candidate cannot catch that: by construction the staged copy is alone in
a directory the launcher just made. So the checks here plant real sidecars beside
the real source and drive the real staging path.

**Identity.** The source is opened once and read through that held descriptor. A
path swapped, replaced or symlinked between intake and publication must not be
able to substitute different bytes into `candidate.sqlite`.
"""

from pathlib import Path
import hashlib
import os
import subprocess
import sys

import pytest

from launcher.restore.staging import (
    ACCEPTED_SOURCE_SUFFIXES,
    SOURCE_SIDECAR_SUFFIXES,
    SourceRejectedError,
    StagingError,
    open_selected_source,
    stage_source,
)
from launcher.restore.workspace import (
    OWNED_TEMP_PREFIX,
    STAGED_CANDIDATE_FILENAME,
    RestoreWorkspace,
    new_operation_id,
)

from launcher.tests.restore_fixtures import build_workspace_database


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def workspace(tmp_path):
    return RestoreWorkspace(
        restore_dir=tmp_path / "restore", database_path=tmp_path / "data" / "workshop.sqlite"
    )


@pytest.fixture
def database_path(tmp_path):
    return build_workspace_database(tmp_path / "data" / "workshop.sqlite", "current")


@pytest.fixture
def source(tmp_path):
    return build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "chosen")


def stage(workspace, source, database_path):
    """Drive the real intake → staging path end to end."""
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)
    with open_selected_source(source, database_path) as held:
        return operation_id, stage_source(workspace, operation_id, held)


def run_and_abandon(database: Path, statements: str) -> None:
    """Run SQL in another process and exit without closing the connection.

    SQLite checkpoints and removes the WAL when the *last* connection closes
    cleanly, so a leftover `-wal`/`-shm` can only be produced by a process that
    dies holding it. `os._exit` skips every cleanup handler, which is what leaves
    a real, committed-but-uncheckpointed WAL beside the file.
    """
    script = "\n".join(
        [
            "import os, sqlite3, sys",
            "connection = sqlite3.connect(sys.argv[1], isolation_level=None)",
            statements,
            "os._exit(0)",
        ]
    )
    subprocess.run([sys.executable, "-c", script, str(database)], check=True, timeout=30)


# --------------------------------------------------------------------------
# Intake
# --------------------------------------------------------------------------

def test_a_valid_regular_local_backup_is_accepted(source, database_path):
    with open_selected_source(source, database_path) as held:
        assert held.path == source
        assert held.size_bytes > 0


def test_a_missing_path_is_rejected(tmp_path, database_path):
    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(tmp_path / "nowhere" / "absent.sqlite", database_path)
    assert error.value.rejection == "source-missing"


def test_a_directory_is_rejected(tmp_path, database_path):
    directory = tmp_path / "a-directory.sqlite"
    directory.mkdir()

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(directory, database_path)
    assert error.value.rejection == "source-is-directory"


def test_a_symlink_is_rejected_even_when_it_points_at_a_valid_backup(
    tmp_path, source, database_path
):
    """The file that must stay byte-identical is the one the user selected."""
    link = tmp_path / "link.sqlite"
    link.symlink_to(source)

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(link, database_path)
    assert error.value.rejection == "source-is-symlink"


def test_a_non_regular_file_is_rejected(tmp_path, database_path):
    fifo = tmp_path / "pipe.sqlite"
    os.mkfifo(fifo)

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(fifo, database_path)
    assert error.value.rejection == "source-not-regular-file"


@pytest.mark.parametrize("name", ["export.json", "table.csv", "sheet.xlsx", "report.md", "backup"])
def test_an_unsupported_suffix_is_rejected(tmp_path, database_path, name):
    candidate = tmp_path / name
    candidate.write_bytes(b"not a database")

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(candidate, database_path)
    assert error.value.rejection == "source-unsupported-suffix"


def test_the_accepted_suffixes_are_exactly_the_sqlite_backup_suffixes():
    assert ACCEPTED_SOURCE_SUFFIXES == {".sqlite", ".db", ".sqlite3"}


def test_an_empty_file_is_rejected(tmp_path, database_path):
    """A zero-byte file is a valid empty SQLite database and passes quick_check."""
    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(empty, database_path)
    assert error.value.rejection == "source-empty"


def test_a_url_or_non_local_representation_is_rejected(database_path):
    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(object(), database_path)
    assert error.value.rejection == "source-not-local-path"


def test_a_relative_path_is_rejected(database_path):
    with pytest.raises(SourceRejectedError) as error:
        open_selected_source("backups/whatever.sqlite", database_path)
    assert error.value.rejection == "source-not-local-path"


def test_the_current_working_database_cannot_be_selected(database_path):
    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(database_path, database_path)
    assert error.value.rejection == "source-is-working-database"


def test_a_hard_link_alias_of_the_working_database_is_rejected(tmp_path, database_path):
    """Identity, not spelling: device and inode catch what a string compare misses."""
    alias = tmp_path / "alias.sqlite"
    os.link(database_path, alias)

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(alias, database_path)
    assert error.value.rejection == "source-is-working-database"


def test_an_unreadable_source_is_rejected(tmp_path, database_path):
    unreadable = build_workspace_database(tmp_path / "locked" / "backup.sqlite", "locked")
    unreadable.chmod(0o000)
    try:
        with pytest.raises(SourceRejectedError) as error:
            open_selected_source(unreadable, database_path)
        assert error.value.rejection == "source-unreadable"
    finally:
        unreadable.chmod(0o600)


# --------------------------------------------------------------------------
# Sidecars beside the ORIGINAL source
# --------------------------------------------------------------------------

def test_a_real_committed_wal_source_is_rejected_before_anything_is_staged(
    tmp_path, workspace, database_path
):
    """The defect this check exists for, reproduced end to end.

    The row below is committed and lives in `source.sqlite-wal`. Staging copies
    only the main file, so accepting this source would install a database that is
    silently missing that row — and `quick_check` would still say `ok`.
    """
    source = build_workspace_database(tmp_path / "chosen" / "live.sqlite", "chosen")
    run_and_abandon(
        source,
        'connection.execute("PRAGMA journal_mode = WAL")\n'
        'connection.execute("INSERT INTO app_settings '
        "(key, value, value_type, description) "
        "VALUES ('committed.in.wal', 'present', 'string', '')\")",
    )
    wal = source.with_name(source.name + "-wal")
    assert wal.exists(), "the fixture must leave a real WAL beside the source"
    main_before, wal_before = digest(source), digest(wal)

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(source, database_path)

    assert error.value.rejection == "source-has-wal-sidecar"
    assert error.value.is_sidecar_dependency is True
    # Nothing was staged, and the source and its WAL are untouched.
    assert not workspace.restore_dir.exists()
    assert digest(source) == main_before
    assert digest(wal) == wal_before


def test_a_real_hot_rollback_journal_source_is_rejected_without_being_repaired(
    tmp_path, database_path
):
    """A killed writer leaves a hot journal; opening the file would roll it back.

    That rollback is a *write* to the user's selected source, which the contract
    forbids. The sidecar check runs before the open, so the file is refused while
    both it and its journal stay byte-identical.
    """
    source = build_workspace_database(tmp_path / "chosen" / "hot.sqlite", "before-crash")
    run_and_abandon(
        source,
        'connection.execute("PRAGMA journal_mode = DELETE")\n'
        'connection.execute("BEGIN IMMEDIATE")\n'
        "connection.execute(\"UPDATE app_settings SET value = 'after-crash' "
        "WHERE key = 'test.workspace_marker'\")",
    )
    journal = source.with_name(source.name + "-journal")
    assert journal.exists()
    main_before, journal_before = digest(source), digest(journal)

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(source, database_path)

    assert error.value.rejection == "source-has-journal-sidecar"
    assert digest(source) == main_before, "the source was repaired, which is a write"
    assert digest(journal) == journal_before, "the hot journal was consumed"


@pytest.mark.parametrize("suffix", SOURCE_SIDECAR_SUFFIXES)
def test_every_sidecar_suffix_is_refused(tmp_path, source, database_path, suffix):
    sidecar = source.with_name(source.name + suffix)
    sidecar.write_bytes(b"sidecar content")

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(source, database_path)
    assert error.value.is_sidecar_dependency is True


def test_a_symlinked_sidecar_is_still_a_sidecar(tmp_path, source, database_path):
    """`lexists`, not `exists`: a dangling or symlinked `-wal` still counts."""
    sidecar = source.with_name(source.name + "-wal")
    sidecar.symlink_to(tmp_path / "does-not-exist")

    with pytest.raises(SourceRejectedError) as error:
        open_selected_source(source, database_path)
    assert error.value.rejection == "source-has-wal-sidecar"


def test_a_sidecar_appearing_during_the_copy_is_caught(
    monkeypatch, workspace, source, database_path
):
    """The second check. A source being written to is not a backup artifact."""
    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)
    real_pread = os.pread

    def plant_sidecar_midway(fd, length, offset):
        if offset > 0:
            source.with_name(source.name + "-wal").write_bytes(b"appeared mid-copy")
            monkeypatch.setattr(os, "pread", real_pread)
        return real_pread(fd, length, offset)

    with open_selected_source(source, database_path) as held:
        monkeypatch.setattr(os, "pread", plant_sidecar_midway)
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert error.value.is_sidecar_dependency is True
    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()


# --------------------------------------------------------------------------
# Staging and source identity
# --------------------------------------------------------------------------

def test_staging_publishes_a_complete_candidate(workspace, source, database_path):
    _operation_id, staged = stage(workspace, source, database_path)

    assert staged.name == STAGED_CANDIDATE_FILENAME
    assert digest(staged) == digest(source)


def test_staging_leaves_the_source_byte_identical(workspace, source, database_path):
    before = digest(source)
    before_mode = source.stat().st_mode

    stage(workspace, source, database_path)

    assert digest(source) == before
    assert source.stat().st_mode == before_mode
    assert source.exists()


def test_an_interrupted_stage_copy_never_becomes_a_valid_candidate(
    monkeypatch, workspace, source, database_path
):
    """The candidate name only ever appears after the copy completed."""
    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)

    def fail_midway(_fd, _length, _offset):
        raise OSError(5, "input/output error")

    with open_selected_source(source, database_path) as held:
        monkeypatch.setattr(os, "pread", fail_midway)
        with pytest.raises(StagingError):
            stage_source(workspace, operation_id, held)

    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()
    leftovers = [p for p in operation_dir.iterdir() if p.name.startswith(OWNED_TEMP_PREFIX)]
    assert leftovers == []


def test_the_source_path_being_replaced_after_intake_is_detected(
    workspace, source, database_path, tmp_path
):
    """A different file moved onto the path must not become the candidate."""
    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)
    impostor = build_workspace_database(tmp_path / "impostor" / "other.sqlite", "impostor")

    with open_selected_source(source, database_path) as held:
        os.replace(impostor, source)
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert error.value.rejection == "source-identity-changed"
    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()


def test_a_symlink_substituted_after_intake_is_detected(
    workspace, source, database_path, tmp_path
):
    """The held descriptor keeps pointing at the original inode; `lstat` notices."""
    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)
    elsewhere = build_workspace_database(tmp_path / "elsewhere" / "other.sqlite", "elsewhere")

    with open_selected_source(source, database_path) as held:
        source.unlink()
        source.symlink_to(elsewhere)
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert error.value.rejection == "source-identity-changed"
    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()


def test_the_source_changing_size_during_the_copy_is_detected(
    monkeypatch, workspace, source, database_path
):
    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)
    real_pread = os.pread

    def grow_midway(fd, length, offset):
        if offset > 0:
            with open(source, "ab") as stream:
                stream.write(b"\x00" * 4096)
            monkeypatch.setattr(os, "pread", real_pread)
        return real_pread(fd, length, offset)

    with open_selected_source(source, database_path) as held:
        monkeypatch.setattr(os, "pread", grow_midway)
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert error.value.rejection == "source-identity-changed"
    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()


def test_the_copy_reads_the_held_descriptor_not_the_path(workspace, source, database_path):
    """Reopening the path after validation would be the whole vulnerability.

    The path is unlinked entirely after intake. A copy that re-opened it would
    fail; a copy that reads the held descriptor still sees the original bytes,
    and the identity recheck then refuses to publish them.
    """
    import inspect

    from launcher.restore import staging as staging_module

    body = inspect.getsource(staging_module.stage_source)
    assert "os.pread(held.fd" in body
    assert "open(held.path" not in body
    assert "open(source" not in body


def test_staging_requires_the_isolated_operation_directory(workspace, source, database_path):
    with open_selected_source(source, database_path) as held:
        with pytest.raises(StagingError):
            stage_source(workspace, new_operation_id(), held)


def test_the_operation_directory_is_created_exclusively(workspace):
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)

    from launcher.restore.workspace import RestoreWorkspaceError

    with pytest.raises(RestoreWorkspaceError):
        workspace.create_operation_dir(operation_id)


def test_an_unsafe_operation_identity_cannot_escape_the_boundary(workspace):
    from launcher.restore.workspace import RestoreWorkspaceError

    for unsafe in ("../escape", "a/b", "..", "", "not-a-uuid"):
        with pytest.raises(RestoreWorkspaceError):
            workspace.operation_dir(unsafe)
