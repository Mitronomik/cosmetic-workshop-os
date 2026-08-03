"""The disk-space preflight.

The formula lives in `launcher/restore/capacity.py` and in
`docs/backup-and-restore.md`. What these tests pin down is the behaviour that
formula exists for: every destination filesystem is charged for the artifacts it
will actually hold, destinations that share a device are charged **together**,
the selected source's own filesystem is never charged, and nothing is deleted to
make room.
"""

from pathlib import Path
import shutil

import pytest

from launcher.restore.capacity import (
    OVERHEAD_BYTES,
    InsufficientDiskSpaceError,
    assert_sufficient_disk_space,
    plan_required_space,
)
from launcher.restore.state import STATE_RESERVE_BYTES

SOURCE_SIZE = 40 * 1024 * 1024
WORKING_SIZE = 25 * 1024 * 1024


@pytest.fixture
def layout(tmp_path):
    base = tmp_path / "user-data"
    (base / "data").mkdir(parents=True)
    (base / "backups").mkdir()
    (base / "restore").mkdir()
    return base


def plan(layout, **overrides):
    kwargs = {
        "source_size_bytes": SOURCE_SIZE,
        "working_database_size_bytes": WORKING_SIZE,
        "restore_dir": layout / "restore",
        "database_dir": layout / "data",
        "backup_dir": layout / "backups",
    }
    kwargs.update(overrides)
    return kwargs


def fake_usage(free_bytes: int):
    return lambda _path: shutil._ntuple_diskusage(total=free_bytes, used=0, free=free_bytes)


def test_enough_space_passes(monkeypatch, layout):
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(10 * 1024 * 1024 * 1024))

    requirements = assert_sufficient_disk_space(**plan(layout))

    assert requirements
    assert all(requirement.satisfied for requirement in requirements)


def test_directories_on_one_device_are_charged_together(monkeypatch, layout):
    """The ordinary local install: everything is on one volume.

    Charging each destination in isolation would pass a check that the combined
    write then fails.
    """
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(10 * 1024 * 1024 * 1024))

    requirements = plan_required_space(**plan(layout))

    assert len(requirements) == 1
    expected = (
        SOURCE_SIZE  # staged candidate
        + STATE_RESERVE_BYTES  # operation-state scratch
        + SOURCE_SIZE  # replacement artifact
        + WORKING_SIZE  # before_restore safety copy
        + SOURCE_SIZE  # conservative before_migration allowance
        + OVERHEAD_BYTES
    )
    assert requirements[0].required_bytes == expected


def test_insufficient_space_fails_before_anything_is_created(monkeypatch, layout):
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(1024))

    with pytest.raises(InsufficientDiskSpaceError) as error:
        assert_sufficient_disk_space(**plan(layout))
    assert error.value.free_bytes == 1024
    assert error.value.required_bytes > 1024


def test_a_backup_filesystem_short_of_space_fails_even_when_the_others_are_fine(
    monkeypatch, layout
):
    """Distinct devices are checked separately, not averaged."""
    backups = layout / "backups"

    def per_device(path):
        free = 1024 if Path(path) == backups else 10 * 1024 * 1024 * 1024
        return shutil._ntuple_diskusage(total=free, used=0, free=free)

    monkeypatch.setattr(shutil, "disk_usage", per_device)
    monkeypatch.setattr(
        "launcher.restore.capacity._device_of",
        lambda path: 2 if Path(path) == backups else 1,
    )

    with pytest.raises(InsufficientDiskSpaceError):
        assert_sufficient_disk_space(**plan(layout))


def test_the_older_schema_migration_backup_allowance_is_always_included(monkeypatch, layout):
    """Conservative on purpose: the preflight runs before validation.

    Staging is itself one of the large artifacts, so the preflight cannot wait
    for the candidate's schema level to be known. Over-reserving one
    database-sized allowance is the cheap direction to be wrong in.
    """
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(10 * 1024 * 1024 * 1024))

    requirements = plan_required_space(**plan(layout))
    without_allowance = (
        SOURCE_SIZE + STATE_RESERVE_BYTES + SOURCE_SIZE + WORKING_SIZE + OVERHEAD_BYTES
    )

    assert requirements[0].required_bytes == without_allowance + SOURCE_SIZE


def test_the_selected_source_filesystem_is_never_charged(monkeypatch, layout, tmp_path):
    """The user's backup may sit on a nearly full removable volume."""
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(10 * 1024 * 1024 * 1024))
    requirements = plan_required_space(**plan(layout))

    probed = {requirement.probe_dir for requirement in requirements}
    assert all(layout in path.parents or path == layout for path in probed)
    assert not any("removable" in str(path) for path in probed)


def test_a_directory_that_does_not_exist_yet_is_charged_to_its_parent(monkeypatch, tmp_path):
    """`backups/` and `restore/` are created lazily."""
    base = tmp_path / "fresh"
    (base / "data").mkdir(parents=True)
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(10 * 1024 * 1024 * 1024))

    requirements = plan_required_space(
        source_size_bytes=SOURCE_SIZE,
        working_database_size_bytes=WORKING_SIZE,
        restore_dir=base / "restore",
        database_dir=base / "data",
        backup_dir=base / "backups",
    )

    assert len(requirements) == 1
    assert requirements[0].satisfied


def test_an_unreadable_destination_is_not_a_destination_with_room(monkeypatch, layout):
    def refuse(_path):
        raise OSError("cannot stat")

    monkeypatch.setattr(shutil, "disk_usage", refuse)

    with pytest.raises(InsufficientDiskSpaceError):
        assert_sufficient_disk_space(**plan(layout))


def test_the_preflight_deletes_nothing(monkeypatch, layout):
    """No old user backup is ever removed to make room."""
    old_backup = layout / "backups" / "20250101T000000000000Z-workshop-manual.sqlite"
    old_backup.write_bytes(b"an existing user backup")
    monkeypatch.setattr(shutil, "disk_usage", fake_usage(1024))

    with pytest.raises(InsufficientDiskSpaceError):
        assert_sufficient_disk_space(**plan(layout))

    assert old_backup.exists()
    assert old_backup.read_bytes() == b"an existing user backup"
