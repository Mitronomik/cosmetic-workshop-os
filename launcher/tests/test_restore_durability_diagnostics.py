"""The durability method that actually ran, recorded rather than asserted.

The finding: `flush_file()` returned a `FlushMethod`, production callers dropped
it, and the documentation nonetheless said the `F_FULLFSYNC` fallback was
"recorded". It was not. A claim that a stronger primitive is used "where
supported" is only honest if a reader can check which one ran on their machine.

So every safety-critical flush now reports its category, whether the target was a
file or a directory, the platform, and the method. These tests hold two lines:

1. the recorded method is the one that really ran, including the fallback and
   including the separate directory flush;
2. the diagnostics carry **no** path, filename, database content or user data —
   a fixed category enum, a target kind, a platform string and a method name.
"""

import errno
import json
import logging

import pytest

from launcher.restore import durability
from launcher.restore.durability import (
    DIRECTORY_FSYNC,
    DURABILITY_DIAGNOSTICS,
    FULL_SYNC,
    PLAIN_FSYNC,
    DurabilityDiagnostics,
    PublicationCategory,
    flush_directory,
    flush_path,
    write_and_publish_bytes,
)

from launcher.tests.restore_fixtures import (
    make_source_backup,
    make_workspace,
    request_for,
    stub_services,
)


@pytest.fixture(autouse=True)
def clean_diagnostics():
    DURABILITY_DIAGNOSTICS.clear()
    yield
    DURABILITY_DIAGNOSTICS.clear()


# --------------------------------------------------------------------------
# The method actually used
# --------------------------------------------------------------------------

def test_a_file_flush_records_the_method_that_ran(tmp_path):
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")

    method = flush_path(probe, category=PublicationCategory.OPERATION_RECORD)

    observations = DURABILITY_DIAGNOSTICS.observations
    assert len(observations) == 1
    assert observations[0].category == "operation_record"
    assert observations[0].target == "file"
    assert observations[0].method == method.name
    if durability.IS_MACOS:
        assert method is FULL_SYNC
        assert observations[0].method == "F_FULLFSYNC"
        assert observations[0].full_device_flush is True
    else:
        assert method is PLAIN_FSYNC


@pytest.mark.parametrize("code", [errno.ENOTSUP, errno.EINVAL, errno.EOPNOTSUPP])
def test_an_unsupported_full_flush_records_the_fallback(tmp_path, monkeypatch, code):
    """The claim being made honest: the fallback is visible when it happens."""
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")
    monkeypatch.setattr(
        durability,
        "_full_device_flush",
        lambda _fd: (_ for _ in ()).throw(OSError(code, "unsupported")),
    )

    method = flush_path(probe, category=PublicationCategory.STAGED_CANDIDATE)

    assert method is PLAIN_FSYNC
    observation = DURABILITY_DIAGNOSTICS.observations[-1]
    assert observation.method == "fsync"
    assert observation.full_device_flush is False, (
        "a fallback must never be recorded as a full-device flush"
    )


def test_a_directory_flush_is_recorded_separately(tmp_path):
    """Never conflated with a full-device file flush."""
    flush_directory(tmp_path, category=PublicationCategory.OPERATION_RECORD)

    observation = DURABILITY_DIAGNOSTICS.observations[-1]
    assert observation.target == "directory"
    assert observation.method == DIRECTORY_FSYNC.name == "directory_fsync"
    assert observation.full_device_flush is False


def test_an_unexpected_io_error_is_never_downgraded_or_recorded(tmp_path, monkeypatch):
    """A real failure fails; it does not become a quietly recorded fallback."""
    if not durability.IS_MACOS:
        pytest.skip("the F_FULLFSYNC fallback path is a macOS behaviour")
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")
    monkeypatch.setattr(
        durability,
        "_full_device_flush",
        lambda _fd: (_ for _ in ()).throw(OSError(errno.EIO, "device failure")),
    )

    with pytest.raises(OSError):
        flush_path(probe, category=PublicationCategory.OPERATION_RECORD)

    assert DURABILITY_DIAGNOSTICS.observations == (), (
        "a failed flush must not be recorded as if it succeeded"
    )


# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------

def test_the_category_vocabulary_covers_every_safety_critical_publication():
    assert {category.value for category in PublicationCategory} >= {
        "operation_record",
        "record_durability_confirmation",
        "staged_candidate",
        "replacement_artifact",
        "working_database_replacement",
        "rollback_replacement",
    }


def test_a_publication_records_both_its_file_and_its_directory_flush(tmp_path):
    import os

    target = tmp_path / "record.json"
    target.write_bytes(b"OLD")
    scratch = tmp_path / ".scratch.tmp"
    os.close(os.open(scratch, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))

    write_and_publish_bytes(
        b"NEW", target, scratch, category=PublicationCategory.OPERATION_RECORD
    )

    targets = [o.target for o in DURABILITY_DIAGNOSTICS.observations]
    assert targets.count("directory") == 1, "the mandatory directory flush is recorded"
    assert targets.count("file") >= 1
    assert all(o.category == "operation_record" for o in DURABILITY_DIAGNOSTICS.observations)


def test_a_real_restore_records_every_publication_category(monkeypatch, tmp_path):
    """End to end: the categories a completed Restore actually produces."""
    from launcher.restore.engine import execute_restore

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    DURABILITY_DIAGNOSTICS.clear()
    try:
        execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    recorded = {o.category for o in DURABILITY_DIAGNOSTICS.observations}
    assert "operation_record" in recorded
    assert "staged_candidate" in recorded
    assert "working_database_replacement" in recorded
    # Every observation names a category from the closed vocabulary.
    known = {category.value for category in PublicationCategory}
    assert recorded <= known


# --------------------------------------------------------------------------
# Privacy
# --------------------------------------------------------------------------

def test_diagnostics_carry_no_path_or_business_data(monkeypatch, tmp_path):
    from launcher.restore.engine import execute_restore

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    DURABILITY_DIAGNOSTICS.clear()
    try:
        execute_restore(
            request_for(source), context, services=stub_services(workspace.database_path)
        )
    finally:
        context.release()

    serialized = json.dumps(DURABILITY_DIAGNOSTICS.snapshot(), ensure_ascii=False)
    assert str(tmp_path) not in serialized
    assert "cosmetic_workshop" not in serialized
    assert ".sqlite" not in serialized
    assert "/" not in serialized
    # Exactly five keys, all of them fixed vocabulary or platform metadata.
    for entry in DURABILITY_DIAGNOSTICS.snapshot():
        assert set(entry) == {
            "category",
            "target",
            "platform",
            "method",
            "full_device_flush",
        }


def test_the_technical_log_line_carries_no_path(tmp_path, caplog):
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"content")

    with caplog.at_level(logging.DEBUG, logger="launcher.restore.durability"):
        flush_path(probe, category=PublicationCategory.REPLACEMENT_ARTIFACT)

    messages = [record.getMessage() for record in caplog.records]
    assert messages, "the flush method must reach the technical log"
    joined = " ".join(messages)
    assert "replacement_artifact" in joined
    assert str(tmp_path) not in joined
    assert "probe.bin" not in joined


# --------------------------------------------------------------------------
# The collector itself
# --------------------------------------------------------------------------

def test_the_collector_is_narrow_and_resettable():
    diagnostics = DurabilityDiagnostics()

    diagnostics.record(PublicationCategory.ROLLBACK_REPLACEMENT, "file", FULL_SYNC)
    diagnostics.record(PublicationCategory.ROLLBACK_REPLACEMENT, "directory", DIRECTORY_FSYNC)

    assert diagnostics.methods_for(PublicationCategory.ROLLBACK_REPLACEMENT) == [
        "F_FULLFSYNC",
        "directory_fsync",
    ]
    assert diagnostics.methods_for(PublicationCategory.OPERATION_RECORD) == []

    diagnostics.clear()
    assert diagnostics.observations == ()


def test_the_flush_method_is_not_part_of_the_authoritative_record():
    """It is evidence about a write, not a lifecycle fact."""
    from launcher.restore.state import ALLOWED_RECORD_FIELDS

    for forbidden in ("flush_method", "durability", "full_device_flush", "fsync"):
        assert not any(forbidden in field for field in ALLOWED_RECORD_FIELDS)
