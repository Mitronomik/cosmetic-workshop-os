"""The shared safety-critical publication primitive, boundary by boundary.

`CR-010` § 7.3 requires faults injected at **every** publication boundary. This
file is that matrix, tested against the primitive directly rather than through a
caller, so each stage classification is pinned independently of what any caller
does with it.

The classification is the product here. `BEFORE_REPLACE` means nothing was
published and the caller may treat the operation as not having happened;
`DURING_REPLACE` and `AFTER_REPLACE` both mean the caller must not assume that —
one is ambiguous, the other is certain, and the safe response is the same.
"""

from pathlib import Path
import errno
import os

import pytest

from launcher.restore import durability
from launcher.restore.durability import (
    FULL_SYNC,
    PLAIN_FSYNC,
    DurabilityError,
    PublicationStage,
    flush_directory,
    flush_file,
    flush_path,
    publish_atomically,
    write_and_publish_bytes,
)


def explode(*_args, **_kwargs):
    raise OSError(errno.EIO, "injected fault")


@pytest.fixture
def published(tmp_path):
    """An existing published file plus an exclusive scratch beside it."""
    target = tmp_path / "record.json"
    target.write_bytes(b"OLD")
    scratch = tmp_path / ".scratch.tmp"
    fd = os.open(scratch, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    return target, scratch


# --------------------------------------------------------------------------
# The happy path
# --------------------------------------------------------------------------

def test_a_complete_publication_replaces_the_target(published):
    target, scratch = published

    write_and_publish_bytes(b"NEW", target, scratch)

    assert target.read_bytes() == b"NEW"
    assert not scratch.exists(), "the scratch name is consumed by the rename"


def test_publication_is_atomic_within_one_directory(published, monkeypatch):
    target, scratch = published
    renames: list[tuple[str, str]] = []
    real = durability._atomic_rename

    def watched(source, destination):
        renames.append((str(source), str(destination)))
        return real(source, destination)

    monkeypatch.setattr(durability, "_atomic_rename", watched)
    write_and_publish_bytes(b"NEW", target, scratch)

    assert len(renames) == 1
    assert Path(renames[0][0]).parent == Path(renames[0][1]).parent


# --------------------------------------------------------------------------
# Stage classification, boundary by boundary
# --------------------------------------------------------------------------

@pytest.mark.parametrize("boundary", ["_open_scratch_for_write", "flush_file"])
def test_a_write_side_fault_is_before_replace(published, monkeypatch, boundary):
    """Nothing was published, and the old content is intact."""
    target, scratch = published
    monkeypatch.setattr(durability, boundary, explode)

    with pytest.raises(DurabilityError) as error:
        write_and_publish_bytes(b"NEW", target, scratch)

    assert error.value.stage is PublicationStage.BEFORE_REPLACE
    assert error.value.may_have_published is False
    assert target.read_bytes() == b"OLD"


def test_a_rename_fault_is_during_replace(published, monkeypatch):
    """Ambiguous by construction, so it is never reported as "did not happen"."""
    target, scratch = published
    monkeypatch.setattr(durability, "_atomic_rename", explode)

    with pytest.raises(DurabilityError) as error:
        publish_atomically(scratch, target)

    assert error.value.stage is PublicationStage.DURING_REPLACE
    assert error.value.may_have_published is True


def test_a_target_flush_fault_is_after_replace(published, monkeypatch):
    target, scratch = published
    scratch.write_bytes(b"NEW")
    monkeypatch.setattr(durability, "flush_path", explode)

    with pytest.raises(DurabilityError) as error:
        publish_atomically(scratch, target)

    assert error.value.stage is PublicationStage.AFTER_REPLACE
    assert error.value.may_have_published is True
    # The rename really did land, which is precisely why it may not be denied.
    assert target.read_bytes() == b"NEW"


@pytest.mark.parametrize("boundary", ["_open_for_flush", "_fsync_fd"])
def test_a_parent_directory_flush_fault_is_after_replace(published, monkeypatch, boundary):
    """The mandatory flush. Never swallowed, and never misclassified.

    Treating this as harmless — as an earlier version did — is what could let the
    working database come back replaced while the operation record reverted to a
    phase saying nothing was replaced.
    """
    target, scratch = published
    scratch.write_bytes(b"NEW")
    # Both boundaries sit after the rename — `_open_for_flush` and `_fsync_fd`
    # are used by the published-target flush and the parent-directory flush, and
    # which of the two reaches them first is a platform detail (on macOS the file
    # takes the `F_FULLFSYNC` path instead). The stage is the same either way,
    # which is exactly the property under test.
    monkeypatch.setattr(durability, boundary, explode)

    with pytest.raises(DurabilityError) as error:
        publish_atomically(scratch, target)

    assert error.value.stage is PublicationStage.AFTER_REPLACE
    assert error.value.may_have_published is True
    assert target.read_bytes() == b"NEW"


def test_the_parent_directory_flush_actually_runs(published, monkeypatch):
    """Proof it is part of the primitive rather than documented aspiration."""
    target, scratch = published
    flushed: list[Path] = []
    real = durability.flush_directory

    def watched(path):
        flushed.append(Path(path))
        return real(path)

    monkeypatch.setattr(durability, "flush_directory", watched)
    write_and_publish_bytes(b"NEW", target, scratch)

    assert flushed == [target.parent]


# --------------------------------------------------------------------------
# What the flush actually is
# --------------------------------------------------------------------------

def test_the_strongest_supported_file_flush_is_used(tmp_path):
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")

    method = flush_path(probe)

    if durability.IS_MACOS:
        assert method is FULL_SYNC
        assert method.full_device_flush is True
    else:
        assert method is PLAIN_FSYNC


@pytest.mark.parametrize("code", [errno.ENOTSUP, errno.EINVAL, errno.EOPNOTSUPP])
def test_an_unsupported_full_flush_falls_back_and_says_so(tmp_path, monkeypatch, code):
    """The returned method is the honest claim, not the intended one."""
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")
    monkeypatch.setattr(
        durability,
        "_full_device_flush",
        lambda _fd: (_ for _ in ()).throw(OSError(code, "unsupported")),
    )

    method = flush_path(probe)

    assert method is PLAIN_FSYNC
    assert method.full_device_flush is False


def test_a_real_io_error_during_the_full_flush_is_not_downgraded(tmp_path, monkeypatch):
    """Only the unsupported-class errors fall back; an I/O failure propagates."""
    if not durability.IS_MACOS:
        pytest.skip("F_FULLFSYNC fallback is a macOS behaviour")
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")
    monkeypatch.setattr(
        durability,
        "_full_device_flush",
        lambda _fd: (_ for _ in ()).throw(OSError(errno.EIO, "device failure")),
    )

    with pytest.raises(OSError):
        flush_path(probe)


def test_directories_are_flushed_without_attempting_a_full_device_flush(tmp_path, monkeypatch):
    """`F_FULLFSYNC` is not supported on a directory descriptor and is not tried."""
    attempts: list[int] = []
    monkeypatch.setattr(durability, "_full_device_flush", lambda fd: attempts.append(fd))

    flush_directory(tmp_path)

    assert attempts == []


def test_a_directory_flush_failure_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(durability, "_fsync_fd", explode)

    with pytest.raises(OSError):
        flush_directory(tmp_path)


def test_flush_file_reports_the_method_that_ran(tmp_path):
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"x")
    fd = os.open(probe, os.O_RDONLY)
    try:
        method = flush_file(fd)
    finally:
        os.close(fd)

    assert method in (FULL_SYNC, PLAIN_FSYNC)
    assert method.full_device_flush is (method is FULL_SYNC)
