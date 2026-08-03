"""The complete candidate-validation contract, run against the staged copy only.

`CR-010` § 3: the staged candidate must pass **all** of this before any mutation,
replacement, deletion, migration, checkpoint or journal cleanup touches the
current working database. Nothing here writes, migrates or repairs anything.

The one rule worth restating: **`PRAGMA quick_check = ok` alone is never
sufficient.** `CR-004` produced `ok` from an empty file, from a WAL-era raw copy
missing every committed row, and from a copy holding two transaction states at
once — and an unrelated healthy SQLite database returns `ok` as well. So
`quick_check` is one condition among many here, and the conditions that actually
identify the file are the migration lineage and the required-table check that
follows it.

Schema lineage is read through `app.db.migration_lineage`, a read-only backend
helper. The launcher does not carry its own migration list; the expected chain
stays in `app.db.migrations`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import sqlite3

CandidateRejection = Literal[
    "candidate-missing",
    "candidate-is-symlink",
    "candidate-not-regular-file",
    "candidate-empty",
    "candidate-external-journal-dependency",
    "candidate-not-openable",
    "candidate-quick-check-failed",
    "candidate-structure-unreadable",
    "candidate-not-a-workshop-database",
    "candidate-missing-required-table",
    "migration-table-missing",
    "migration-table-shape-unexpected",
    "migration-history-empty",
    "migration-history-unreadable",
    "duplicate-migration-id",
    "unknown-migration-id",
    "reordered-migration-id",
    "skipped-migration-id",
    "schema-newer-than-application",
]

# The rejections that mean "this file is from a newer application", which the
# user-facing vocabulary reports differently from "this file is not valid".
NEWER_SCHEMA_REJECTIONS: frozenset[str] = frozenset({"schema-newer-than-application"})

# Sidecar suffixes a candidate must not depend on. A backup that needs one of
# these to be complete is not a self-contained snapshot, and the sidecar is not
# something Restore may carry along: `CR-004` settled that `-wal`, `-shm` and
# `-journal` files are never copied or guessed at.
EXTERNAL_JOURNAL_SUFFIXES: tuple[str, ...] = ("-wal", "-shm", "-journal")

SQLITE_TIMEOUT_SECONDS = 5.0


class CandidateRejectedError(RuntimeError):
    """Raised when the staged candidate fails the accepted validation contract."""

    def __init__(self, rejection: CandidateRejection) -> None:
        super().__init__(f"Restore candidate rejected: {rejection}")
        self.rejection: CandidateRejection = rejection

    @property
    def is_newer_schema(self) -> bool:
        return self.rejection in NEWER_SCHEMA_REJECTIONS


@dataclass(frozen=True)
class ValidatedCandidate:
    """A staged candidate that passed the complete contract.

    `is_current_head` decides one thing downstream: whether restored startup will
    take the ordinary `before_migration` backup. It is not used to skip any check.
    """

    path: Path
    applied_migration_ids: tuple[str, ...]
    is_current_head: bool


def _assert_no_external_journal_dependency(candidate: Path) -> None:
    """Refuse a candidate that has a sidecar beside it.

    The staged candidate lives alone in an isolated directory this launcher
    created, so a sidecar here means the stage copy brought a dependency along or
    something else wrote into the directory. Either way the file is not the
    self-contained snapshot the contract requires.
    """
    for suffix in EXTERNAL_JOURNAL_SUFFIXES:
        if candidate.with_name(candidate.name + suffix).exists():
            raise CandidateRejectedError("candidate-external-journal-dependency")


def _open_read_only(candidate: Path) -> sqlite3.Connection:
    """Open the staged candidate through a read-only URI.

    `mode=ro` is what makes "validation performs no mutation" a property of the
    connection rather than a promise about the queries below. `immutable=1` is
    deliberately *not* used: a truncated or partially written candidate must be
    allowed to fail honestly rather than be read through a promise it does not
    keep. This is the same reasoning the accepted backup verification applies.
    """
    try:
        return sqlite3.connect(
            f"file:{candidate}?mode=ro", uri=True, timeout=SQLITE_TIMEOUT_SECONDS
        )
    except sqlite3.Error as exc:
        raise CandidateRejectedError("candidate-not-openable") from exc


def validate_workspace_snapshot(snapshot_path: Path) -> ValidatedCandidate:
    """The complete read-only workspace-validation contract for one SQLite file.

    Shared by the staged Restore candidate and by the `before_restore` safety
    copy, because the two need the *same* proof: that a file on disk is a
    self-contained, structurally sound, recognizably `cosmetic-workshop-os`
    workspace whose recorded migration history is a known ordered prefix that the
    file actually backs up.

    Extracting it rather than writing a second checker is the point. A safety
    copy verified more weakly than a candidate is a recovery point that might not
    be one, and that is the artifact the entire destructive boundary rests on.

    Ordered cheapest-and-most-fundamental first, so a foreign file is refused
    before this process opens a SQLite connection to it.
    """
    candidate = Path(snapshot_path)

    # 1-3: it is an owned regular file, not a symlink, and not empty. The size
    # check has to precede every structural one, because a zero-byte file is a
    # valid empty SQLite database that passes `quick_check`.
    if candidate.is_symlink():
        raise CandidateRejectedError("candidate-is-symlink")
    if not candidate.exists():
        raise CandidateRejectedError("candidate-missing")
    if not candidate.is_file():
        raise CandidateRejectedError("candidate-not-regular-file")
    try:
        if candidate.stat().st_size == 0:
            raise CandidateRejectedError("candidate-empty")
    except OSError as exc:
        raise CandidateRejectedError("candidate-not-regular-file") from exc

    # 4: no external journal dependency.
    _assert_no_external_journal_dependency(candidate)

    # 5: SQLite opens it read-only.
    connection = _open_read_only(candidate)
    try:
        # 6: structural health. Necessary, nowhere near sufficient — everything
        # below is what makes the difference.
        try:
            quick_check = connection.execute("PRAGMA quick_check").fetchone()
        except sqlite3.DatabaseError as exc:
            raise CandidateRejectedError("candidate-not-openable") from exc
        if not quick_check or quick_check[0] != "ok":
            raise CandidateRejectedError("candidate-quick-check-failed")

        # 7-13: the migration-history table exists with the expected shape, and
        # its IDs form an exact known ordered prefix — no unknown, duplicated,
        # reordered or skipped ID, and nothing newer than this application.
        # Read without creating or modifying the migration table.
        from app.db.migration_lineage import (
            WORKSPACE_IDENTITY_TABLES,
            inspect_migration_lineage,
            missing_required_tables,
            table_exists,
        )

        lineage = inspect_migration_lineage(connection)
        if not lineage.is_known_prefix:
            raise CandidateRejectedError(lineage.rejection or "candidate-structure-unreadable")

        # 14: recognizably a `cosmetic-workshop-os` workspace rather than an
        # arbitrary SQLite database that happens to carry a `schema_migrations`
        # table. Checked separately from the required-table mapping so the
        # user-facing category can say "not this application's backup".
        try:
            identity_present = all(
                table_exists(connection, name) for name in sorted(WORKSPACE_IDENTITY_TABLES)
            )
        except sqlite3.Error as exc:
            raise CandidateRejectedError("candidate-structure-unreadable") from exc
        if not identity_present:
            raise CandidateRejectedError("candidate-not-a-workshop-database")

        # 15: every table the recorded prefix promises is actually present. A
        # recorded history is a claim; this is the check that the file backs it.
        try:
            missing = missing_required_tables(connection, lineage.applied_ids)
        except sqlite3.Error as exc:
            raise CandidateRejectedError("candidate-structure-unreadable") from exc
        if missing:
            raise CandidateRejectedError("candidate-missing-required-table")

        return ValidatedCandidate(
            path=candidate,
            applied_migration_ids=lineage.applied_ids,
            is_current_head=lineage.is_current_head,
        )
    finally:
        connection.close()


def validate_staged_candidate(candidate_path: Path) -> ValidatedCandidate:
    """Validate the staged Restore candidate.

    Currently exactly the shared workspace contract. It stays a named entry point
    because the candidate and the safety copy are validated for different reasons
    at different moments, and a future candidate-only condition belongs here
    rather than in the shared checker where it would silently tighten safety-copy
    verification too.
    """
    return validate_workspace_snapshot(candidate_path)
