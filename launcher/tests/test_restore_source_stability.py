"""Same-size in-place source modification, and the two-pass proof against it.

The finding: stat identity records device, inode, size and file type, and **none
of those change** when a writer rewrites bytes in place without changing the
total length. A source modified that way during staging produces a candidate
holding pages from two different source states — a SQLite file that
`PRAGMA quick_check` will very likely still call `ok`, because every page is
individually well-formed.

Two mechanisms close it, and the tests here separate them deliberately:

- `st_mtime_ns` / `st_ctime_ns` in the identity, which catch the ordinary case
  cheaply;
- **two independent SHA-256 passes over the held descriptor**, which catch it
  regardless of filesystem timestamp resolution.

The digest comparison is the load-bearing one. Timestamps are necessary but not
sufficient, so no test here relies on them alone to prove safety.
"""

from pathlib import Path
import hashlib
import os

import pytest

from launcher.restore.staging import (
    SourceIdentity,
    SourceRejectedError,
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
    """A source large enough that the copy takes more than one chunk read."""
    path = build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "chosen")
    # Pad past the 1 MiB chunk size so a mid-copy rewrite has a window to land in.
    with open(path, "r+b") as stream:
        stream.seek(0, os.SEEK_END)
        stream.write(b"\x00" * (3 * 1024 * 1024))
    return path


def rewrite_in_place(path: Path, offset: int, payload: bytes) -> None:
    """Overwrite bytes without changing the file's total size.

    The whole point: inode, device, type and size all stay identical afterwards.
    """
    before = path.stat().st_size
    with open(path, "r+b") as stream:
        stream.seek(offset)
        stream.write(payload)
    assert path.stat().st_size == before, "the rewrite must not change the size"


def stage(workspace, source, database_path):
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)
    with open_selected_source(source, database_path) as held:
        return operation_id, stage_source(workspace, operation_id, held)


def assert_nothing_published(workspace, operation_id):
    operation_dir = workspace.restore_dir / operation_id
    assert not (operation_dir / STAGED_CANDIDATE_FILENAME).exists()
    leftovers = [p for p in operation_dir.iterdir() if p.name.startswith(OWNED_TEMP_PREFIX)]
    assert leftovers == [], "an interrupted stage left a scratch file behind"


# --------------------------------------------------------------------------
# The identity itself
# --------------------------------------------------------------------------

def test_source_identity_records_both_timestamps(source):
    info = os.stat(source)
    identity = SourceIdentity.from_stat(info)

    assert identity.st_mtime_ns == info.st_mtime_ns
    assert identity.st_ctime_ns == info.st_ctime_ns
    assert set(SourceIdentity.__dataclass_fields__) == {
        "st_dev",
        "st_ino",
        "st_size",
        "st_mode",
        "st_mtime_ns",
        "st_ctime_ns",
    }


def test_a_same_size_rewrite_changes_no_pre_existing_identity_field(source):
    """Exactly why the old identity could not catch this."""
    before = SourceIdentity.from_stat(os.stat(source))

    rewrite_in_place(source, 2 * 1024 * 1024, b"\xff" * 4096)

    after = SourceIdentity.from_stat(os.stat(source))
    assert (after.st_dev, after.st_ino, after.st_size, after.st_mode) == (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mode,
    )
    # Only the timestamps moved — and the digest passes catch it even when a
    # coarse-resolution filesystem would not.
    assert after != before


def test_timestamps_participate_in_the_identity_comparison(source, database_path):
    with open_selected_source(source, database_path) as held:
        rewrite_in_place(source, 1024, b"\xaa" * 512)

        with pytest.raises(SourceRejectedError) as error:
            held.revalidate()

    assert error.value.rejection == "source-identity-changed"


# --------------------------------------------------------------------------
# Rewrites in each staging window
# --------------------------------------------------------------------------

def test_a_same_size_rewrite_during_the_first_pass_is_rejected(
    monkeypatch, workspace, source, database_path
):
    """Bytes already copied are changed while the copy is still running."""
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)
    real_pread = os.pread
    rewritten = {"done": False}

    def rewrite_midway(fd, length, offset):
        if offset > 0 and not rewritten["done"]:
            rewritten["done"] = True
            # Overwrite a region the first chunk already consumed.
            rewrite_in_place(source, 0, b"\x00" * 4096)
        return real_pread(fd, length, offset)

    with open_selected_source(source, database_path) as held:
        monkeypatch.setattr(os, "pread", rewrite_midway)
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert rewritten["done"], "the fixture never rewrote the source"
    assert error.value.rejection == "source-identity-changed"
    assert_nothing_published(workspace, operation_id)


def test_a_same_size_rewrite_between_the_passes_is_rejected(
    monkeypatch, workspace, source, database_path
):
    """The copy finished cleanly; the source moves before verification reads it."""
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)

    from launcher.restore import staging as staging_module

    real_revalidate = staging_module.HeldSource.revalidate
    rewritten = {"done": False}

    def rewrite_on_first_revalidate(self):
        if not rewritten["done"]:
            rewritten["done"] = True
            rewrite_in_place(source, 2 * 1024 * 1024, b"\x5a" * 8192)
        return real_revalidate(self)

    monkeypatch.setattr(staging_module.HeldSource, "revalidate", rewrite_on_first_revalidate)

    with open_selected_source(source, database_path) as held:
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert rewritten["done"]
    assert error.value.rejection == "source-identity-changed"
    assert_nothing_published(workspace, operation_id)


def test_a_same_size_rewrite_during_the_second_pass_is_rejected(
    monkeypatch, workspace, source, database_path
):
    """Caught by the digest comparison and the final stat recheck."""
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)

    from launcher.restore import staging as staging_module

    real_digest = staging_module.HeldSource.digest
    rewritten = {"done": False}

    def rewrite_while_hashing(self):
        if not rewritten["done"]:
            rewritten["done"] = True
            rewrite_in_place(source, 1 * 1024 * 1024, b"\x77" * 8192)
        return real_digest(self)

    monkeypatch.setattr(staging_module.HeldSource, "digest", rewrite_while_hashing)

    with open_selected_source(source, database_path) as held:
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert rewritten["done"]
    assert error.value.rejection == "source-identity-changed"
    assert_nothing_published(workspace, operation_id)


def test_a_digest_mismatch_alone_rejects_even_when_stat_is_unchanged(
    monkeypatch, workspace, source, database_path
):
    """The guarantee that does not depend on timestamp resolution.

    Stat identity is frozen so it cannot contribute, leaving only the two-pass
    digest comparison to catch the change. That is the property a filesystem with
    coarse timestamps would otherwise erode.
    """
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)

    from launcher.restore import staging as staging_module

    with open_selected_source(source, database_path) as held:
        frozen = held.identity
        monkeypatch.setattr(
            staging_module.SourceIdentity, "from_stat", classmethod(lambda _cls, _info: frozen)
        )
        real_digest = staging_module.HeldSource.digest
        monkeypatch.setattr(
            staging_module.HeldSource,
            "digest",
            lambda self: ("0" * 64, self.identity.st_size),
        )

        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert error.value.rejection == "source-identity-changed"
    assert_nothing_published(workspace, operation_id)


def test_a_short_second_pass_is_rejected(monkeypatch, workspace, source, database_path):
    """A truncating writer: the verification read returns fewer bytes."""
    operation_id = new_operation_id()
    workspace.create_operation_dir(operation_id)

    from launcher.restore import staging as staging_module

    with open_selected_source(source, database_path) as held:
        monkeypatch.setattr(
            staging_module.HeldSource,
            "digest",
            lambda self: (hashlib.sha256(b"").hexdigest(), 0),
        )
        with pytest.raises(SourceRejectedError) as error:
            stage_source(workspace, operation_id, held)

    assert error.value.rejection == "source-identity-changed"
    assert_nothing_published(workspace, operation_id)


# --------------------------------------------------------------------------
# A stable source still works
# --------------------------------------------------------------------------

def test_a_stable_source_is_accepted_and_copied_byte_identically(
    workspace, source, database_path
):
    before = digest(source)

    _operation_id, staged = stage(workspace, source, database_path)

    assert digest(staged) == before
    assert digest(source) == before, "the selected source must be untouched"


def test_both_passes_read_the_held_descriptor(workspace, source, database_path):
    """Neither pass may re-open the path — that is the substitution window."""
    import inspect

    from launcher.restore import staging as staging_module

    stage_body = inspect.getsource(staging_module.stage_source)
    digest_body = inspect.getsource(staging_module.HeldSource.digest)

    assert "os.pread(held.fd" in stage_body
    assert "os.pread(self.fd" in digest_body
    for body in (stage_body, digest_body):
        assert "open(self.path" not in body
        assert "open(held.path" not in body


def test_the_verification_pass_writes_nothing(workspace, source, database_path):
    """The second pass hashes; it must not touch the staged scratch file."""
    operation_id = new_operation_id()
    operation_dir = workspace.create_operation_dir(operation_id)

    with open_selected_source(source, database_path) as held:
        staged = stage_source(workspace, operation_id, held)

    # Exactly one file: the published candidate. No second scratch was produced.
    assert [p.name for p in operation_dir.iterdir()] == [STAGED_CANDIDATE_FILENAME]
    assert staged.name == STAGED_CANDIDATE_FILENAME
