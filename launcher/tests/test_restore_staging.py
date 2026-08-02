"""Source intake and the staged read-only candidate.

The property under test is the one `CR-010` § 1 states most plainly: **the
selected source is immutable input.** Every rejection here also happens before
anything destructive could be confirmed, which is what makes a bad selection
harmless rather than merely survivable.
"""

from pathlib import Path
import hashlib
import os

import pytest

from launcher.restore.staging import (
    ACCEPTED_SOURCE_SUFFIXES,
    SourceRejectedError,
    StagingError,
    accept_source_path,
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


# --------------------------------------------------------------------------
# Intake
# --------------------------------------------------------------------------

def test_a_valid_regular_local_backup_is_accepted(source, database_path):
    accepted = accept_source_path(source, database_path)

    assert accepted.path == source
    assert accepted.size_bytes > 0


def test_a_missing_path_is_rejected(tmp_path, database_path):
    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(tmp_path / "nowhere" / "absent.sqlite", database_path)
    assert error.value.rejection == "source-missing"


def test_a_directory_is_rejected(tmp_path, database_path):
    directory = tmp_path / "a-directory.sqlite"
    directory.mkdir()

    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(directory, database_path)
    assert error.value.rejection == "source-is-directory"


def test_a_symlink_is_rejected_even_when_it_points_at_a_valid_backup(
    tmp_path, source, database_path
):
    """The file that must stay byte-identical is the one the user selected."""
    link = tmp_path / "link.sqlite"
    link.symlink_to(source)

    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(link, database_path)
    assert error.value.rejection == "source-is-symlink"


def test_a_non_regular_file_is_rejected(tmp_path, database_path):
    fifo = tmp_path / "pipe.sqlite"
    os.mkfifo(fifo)

    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(fifo, database_path)
    assert error.value.rejection == "source-not-regular-file"


@pytest.mark.parametrize("name", ["export.json", "table.csv", "sheet.xlsx", "report.md", "backup"])
def test_an_unsupported_suffix_is_rejected(tmp_path, database_path, name):
    candidate = tmp_path / name
    candidate.write_bytes(b"not a database")

    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(candidate, database_path)
    assert error.value.rejection == "source-unsupported-suffix"


def test_the_accepted_suffixes_are_exactly_the_sqlite_backup_suffixes():
    assert ACCEPTED_SOURCE_SUFFIXES == {".sqlite", ".db", ".sqlite3"}


def test_an_empty_file_is_rejected(tmp_path, database_path):
    """A zero-byte file is a valid empty SQLite database and passes quick_check."""
    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")

    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(empty, database_path)
    assert error.value.rejection == "source-empty"


def test_a_url_or_non_local_representation_is_rejected(database_path):
    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(object(), database_path)
    assert error.value.rejection == "source-not-local-path"


def test_a_relative_path_is_rejected(database_path):
    with pytest.raises(SourceRejectedError) as error:
        accept_source_path("backups/whatever.sqlite", database_path)
    assert error.value.rejection == "source-not-local-path"


def test_the_current_working_database_cannot_be_selected(database_path):
    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(database_path, database_path)
    assert error.value.rejection == "source-is-working-database"


def test_a_hard_link_alias_of_the_working_database_is_rejected(tmp_path, database_path):
    """Identity, not spelling: `samefile` catches what a string compare misses."""
    alias = tmp_path / "alias.sqlite"
    os.link(database_path, alias)

    with pytest.raises(SourceRejectedError) as error:
        accept_source_path(alias, database_path)
    assert error.value.rejection == "source-is-working-database"


def test_an_unreadable_source_is_rejected(tmp_path, database_path):
    unreadable = build_workspace_database(tmp_path / "locked" / "backup.sqlite", "locked")
    unreadable.chmod(0o000)
    try:
        with pytest.raises(SourceRejectedError) as error:
            accept_source_path(unreadable, database_path)
        assert error.value.rejection == "source-unreadable"
    finally:
        unreadable.chmod(0o600)


# --------------------------------------------------------------------------
# Staging
# --------------------------------------------------------------------------

def test_staging_publishes_a_complete_candidate(workspace, source, database_path):
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)
    accepted = accept_source_path(source, database_path)

    staged = stage_source(workspace, operation_id, accepted)

    assert staged.name == STAGED_CANDIDATE_FILENAME
    assert digest(staged) == digest(source)


def test_staging_leaves_the_source_byte_identical(workspace, source, database_path):
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)
    before = digest(source)
    before_mode = source.stat().st_mode

    stage_source(workspace, operation_id, accept_source_path(source, database_path))

    assert digest(source) == before
    assert source.stat().st_mode == before_mode
    assert source.exists()


def test_an_interrupted_stage_copy_never_becomes_a_valid_candidate(
    workspace, source, database_path, monkeypatch
):
    """The candidate name only ever appears after the copy completed."""
    import shutil

    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)
    accepted = accept_source_path(source, database_path)

    def fail_midway(reader, writer, length=0):
        writer.write(reader.read(64))
        raise OSError(28, "no space left on device")

    monkeypatch.setattr(shutil, "copyfileobj", fail_midway)

    with pytest.raises(StagingError):
        stage_source(workspace, operation_id, accepted)

    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()
    leftovers = [p for p in operation_dir.iterdir() if p.name.startswith(OWNED_TEMP_PREFIX)]
    assert leftovers == []


def test_staging_requires_the_isolated_operation_directory(workspace, source, database_path):
    accepted = accept_source_path(source, database_path)

    with pytest.raises(StagingError):
        stage_source(workspace, new_operation_id(), accepted)


def test_the_operation_directory_is_created_exclusively(workspace):
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)

    from launcher.restore.workspace import RestoreWorkspaceError

    with pytest.raises(RestoreWorkspaceError):
        workspace.create_operation_dir(operation_id)


def test_an_unsafe_operation_identity_cannot_escape_the_boundary(workspace):
    from launcher.restore.workspace import RestoreWorkspaceError

    for unsafe in ("../escape", "a/b", "..", ""):
        with pytest.raises(RestoreWorkspaceError):
            workspace.operation_dir(unsafe)
