"""Conservative disk-space preflight, run before any large artifact is created.

Restore transiently needs several full-size copies of a database that may be
large — ADR 0016 § Consequences accepts that cost explicitly. Discovering the
disk is full *after* the working database has been replaced is exactly the
failure the phase machine exists to survive, and it is much better not to reach
it.

## The formula

Five artifacts, each charged to the filesystem that will actually hold it:

```text
staged candidate        → the Restore operation directory   : source_size
replacement artifact    → the working-database directory    : source_size
operation-state scratch → the Restore directory             : STATE_RESERVE_BYTES (1 MiB)
before_restore copy     → the backup directory              : working_database_size
before_migration copy   → the backup directory              : source_size
```

Requirements are then **grouped by filesystem device** (`st_dev`) and compared
once per device against `shutil.disk_usage(...).free`, plus a fixed
`OVERHEAD_BYTES` per device. Grouping matters because in the ordinary local
install all four directories are on one volume, and charging each in isolation
would pass a check that the combined write then fails.

Two deliberate conservatisms:

- **The `before_migration` allowance is always charged.** It is only actually
  taken when the candidate is at an older supported schema, but the preflight
  runs *before* validation has established the candidate's schema level — that
  ordering is required, because staging is itself one of the large artifacts.
  Over-reserving one database-sized allowance is the cheap direction to be wrong
  in.
- **The selected source's filesystem is never charged.** Restore writes nothing
  there, and the user's backup may sit on a nearly-full removable volume. Relying
  on that volume having room for application-owned artifacts is what § 11 of the
  task contract forbids.

Nothing here deletes anything. Old user backups are never removed to make room.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil

from launcher.restore.state import STATE_RESERVE_BYTES

# Bounded, documented headroom per device: filesystem metadata, SQLite page
# rounding and the small journal a backup destination may create while it is
# being written. A fixed bound rather than a percentage, so the reservation
# cannot grow without limit on a large workspace.
OVERHEAD_BYTES = 16 * 1024 * 1024


class InsufficientDiskSpaceError(RuntimeError):
    """Raised when a destination filesystem cannot hold the required artifacts.

    The message names byte counts for local technical logs only. The user-facing
    text comes from the fixed category vocabulary, never from here.
    """

    def __init__(self, required_bytes: int, free_bytes: int) -> None:
        super().__init__(
            f"Restore needs {required_bytes} bytes on a destination filesystem "
            f"that has {free_bytes} bytes free."
        )
        self.required_bytes = required_bytes
        self.free_bytes = free_bytes


@dataclass(frozen=True)
class DeviceRequirement:
    """One filesystem's total requirement, after grouping."""

    device: int
    probe_dir: Path
    required_bytes: int
    free_bytes: int

    @property
    def satisfied(self) -> bool:
        return self.free_bytes >= self.required_bytes


def _existing_ancestor(directory: Path) -> Path:
    """The nearest existing ancestor of a directory that may not exist yet.

    `backups/` and `restore/` are created lazily, so the preflight often has to
    ask about a path that is not there. Its parent is on the same filesystem in
    every layout this product creates, so the answer is the same.
    """
    candidate = Path(directory)
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            return candidate
        candidate = parent
    return candidate


def _device_of(directory: Path) -> int | None:
    try:
        return os.stat(_existing_ancestor(directory)).st_dev
    except OSError:
        return None


def _free_bytes(directory: Path) -> int | None:
    try:
        return shutil.disk_usage(_existing_ancestor(directory)).free
    except OSError:
        return None


def plan_required_space(
    *,
    source_size_bytes: int,
    working_database_size_bytes: int,
    restore_dir: Path,
    database_dir: Path,
    backup_dir: Path,
) -> list[DeviceRequirement]:
    """Group every Restore artifact onto the device that will hold it.

    A directory whose device or free space cannot be read contributes a
    requirement that is reported as unsatisfied, rather than being skipped. An
    unreadable destination is not a destination with room.
    """
    charges: list[tuple[Path, int]] = [
        # Staged candidate and operation-state scratch, both under `restore/`.
        (restore_dir, source_size_bytes + STATE_RESERVE_BYTES),
        # The launcher-owned replacement artifact, staged beside the working
        # database so the replacement can be an atomic same-filesystem rename.
        (database_dir, source_size_bytes),
        # The mandatory `before_restore` safety copy, plus the conservative
        # `before_migration` allowance for a restored older schema.
        (backup_dir, working_database_size_bytes + source_size_bytes),
    ]

    grouped: dict[int | None, tuple[Path, int]] = {}
    for directory, required in charges:
        device = _device_of(directory)
        probe, total = grouped.get(device, (directory, 0))
        grouped[device] = (probe, total + required)

    requirements: list[DeviceRequirement] = []
    for device, (probe_dir, required) in grouped.items():
        free = _free_bytes(probe_dir)
        requirements.append(
            DeviceRequirement(
                device=device if device is not None else -1,
                probe_dir=probe_dir,
                required_bytes=required + OVERHEAD_BYTES,
                free_bytes=free if free is not None else 0,
            )
        )
    return requirements


def assert_sufficient_disk_space(
    *,
    source_size_bytes: int,
    working_database_size_bytes: int,
    restore_dir: Path,
    database_dir: Path,
    backup_dir: Path,
) -> list[DeviceRequirement]:
    """Fail safely before any large artifact exists when capacity is short."""
    requirements = plan_required_space(
        source_size_bytes=source_size_bytes,
        working_database_size_bytes=working_database_size_bytes,
        restore_dir=restore_dir,
        database_dir=database_dir,
        backup_dir=backup_dir,
    )
    for requirement in requirements:
        if not requirement.satisfied:
            raise InsufficientDiskSpaceError(
                requirement.required_bytes, requirement.free_bytes
            )
    return requirements
