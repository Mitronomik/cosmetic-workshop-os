"""The candidate-validation contract, and what it refuses.

The headline case is `test_quick_check_ok_alone_does_not_pass`: `CR-004` proved
that an empty file, a WAL-era copy missing every committed row and an unrelated
healthy database all return `ok`, so structural health is a necessary condition
and never a sufficient one. Everything else here is the rest of ADR 0016 § 3.

Validation must also leave the candidate exactly as it found it — no writes, no
migration table created, no silent repair.
"""

from pathlib import Path
import hashlib
import sqlite3

import pytest

from app.db.migrations import MIGRATION_TABLE, expected_migration_ids

from launcher.restore.validation import CandidateRejectedError, validate_staged_candidate

from launcher.tests.restore_fixtures import build_workspace_database


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rewrite_history(path: Path, migration_ids: list[str]) -> None:
    """Replace the recorded migration history, leaving the schema alone."""
    with sqlite3.connect(path) as connection:
        connection.execute(f"DELETE FROM {MIGRATION_TABLE}")
        connection.executemany(
            f"INSERT INTO {MIGRATION_TABLE} (migration_id) VALUES (?)",
            [(migration_id,) for migration_id in migration_ids],
        )


@pytest.fixture
def current(tmp_path):
    return build_workspace_database(tmp_path / "current.sqlite", "current")


# --------------------------------------------------------------------------
# Accepted
# --------------------------------------------------------------------------

def test_the_current_schema_is_accepted(current):
    validated = validate_staged_candidate(current)

    assert list(validated.applied_migration_ids) == expected_migration_ids()
    assert validated.is_current_head is True


def test_a_known_older_prefix_is_accepted(tmp_path):
    older = build_workspace_database(
        tmp_path / "older.sqlite", "older", up_to="0018_demo_data_tracking"
    )

    validated = validate_staged_candidate(older)

    assert validated.is_current_head is False
    assert validated.applied_migration_ids[-1] == "0018_demo_data_tracking"
    assert "0020_artifact_audit_operations" not in validated.applied_migration_ids


# --------------------------------------------------------------------------
# Rejected
# --------------------------------------------------------------------------

def test_a_newer_schema_is_rejected_as_newer(current):
    rewrite_history(current, expected_migration_ids() + ["0021_from_the_future"])

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "schema-newer-than-application"
    assert error.value.is_newer_schema is True


def test_an_unknown_migration_id_is_rejected(current):
    rewrite_history(current, expected_migration_ids()[:5] + ["0006_invented_by_hand"])

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "unknown-migration-id"
    assert error.value.is_newer_schema is False


def test_a_skipped_migration_id_is_rejected(current):
    expected = expected_migration_ids()
    rewrite_history(current, expected[:3] + expected[4:6])

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "skipped-migration-id"


def test_a_reordered_migration_id_is_rejected(current):
    expected = expected_migration_ids()[:6]
    rewrite_history(current, [expected[0], expected[2], expected[1]] + expected[3:])

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "reordered-migration-id"


def test_a_duplicate_migration_id_is_rejected(current):
    expected = expected_migration_ids()[:4]
    with sqlite3.connect(current) as connection:
        connection.execute(f"DELETE FROM {MIGRATION_TABLE}")
        # `migration_id` is the primary key, so the duplicate has to be produced
        # in a table without that constraint — which is exactly the shape a
        # hand-edited or foreign history can have.
        connection.execute(f"DROP TABLE {MIGRATION_TABLE}")
        connection.execute(
            f"CREATE TABLE {MIGRATION_TABLE} (migration_id TEXT, applied_at TEXT)"
        )
        connection.executemany(
            f"INSERT INTO {MIGRATION_TABLE} (migration_id, applied_at) VALUES (?, '')",
            [(value,) for value in expected + [expected[1]]],
        )

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "duplicate-migration-id"


def test_a_missing_migration_table_is_rejected(current):
    with sqlite3.connect(current) as connection:
        connection.execute(f"DROP TABLE {MIGRATION_TABLE}")

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "migration-table-missing"


def test_a_malformed_migration_table_is_rejected(current):
    with sqlite3.connect(current) as connection:
        connection.execute(f"DROP TABLE {MIGRATION_TABLE}")
        connection.execute(f"CREATE TABLE {MIGRATION_TABLE} (whatever TEXT)")
        connection.execute(f"INSERT INTO {MIGRATION_TABLE} VALUES ('0001_infrastructure')")

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "migration-table-shape-unexpected"


def test_an_empty_migration_history_is_rejected(current):
    rewrite_history(current, [])

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "migration-history-empty"


def test_a_missing_required_application_table_is_rejected(current):
    """A recorded history is a claim; the file has to back it up."""
    with sqlite3.connect(current) as connection:
        connection.execute("DROP TABLE production_batch_packaging")

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "candidate-missing-required-table"


def test_an_arbitrary_healthy_sqlite_database_is_rejected(tmp_path):
    foreign = tmp_path / "someone-elses.sqlite"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
        connection.execute("INSERT INTO notes (body) VALUES ('perfectly healthy')")
    with sqlite3.connect(f"file:{foreign}?mode=ro", uri=True) as check:
        assert check.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(foreign)
    assert error.value.rejection == "migration-table-missing"


def test_a_database_with_a_migration_table_but_no_workshop_identity_is_rejected(tmp_path):
    """`schema_migrations` alone does not make a file this application's workspace."""
    impostor = tmp_path / "impostor.sqlite"
    with sqlite3.connect(impostor) as connection:
        connection.execute(
            f"CREATE TABLE {MIGRATION_TABLE} "
            "(migration_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.execute(
            f"INSERT INTO {MIGRATION_TABLE} (migration_id) VALUES ('0001_infrastructure')"
        )

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(impostor)
    assert error.value.rejection == "candidate-not-a-workshop-database"


def test_an_empty_sqlite_file_is_rejected(tmp_path):
    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(empty)
    assert error.value.rejection == "candidate-empty"


def test_quick_check_ok_alone_does_not_pass(tmp_path):
    """CR-004's counter-examples, restated as a validation test.

    Both of these return `ok`. Neither is an acceptable Restore candidate, and
    the checks that reject them are the lineage and identity ones — never
    `quick_check`.
    """
    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")
    foreign = tmp_path / "foreign.sqlite"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE anything (x INTEGER)")
    with sqlite3.connect(f"file:{foreign}?mode=ro", uri=True) as check:
        assert check.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    for candidate in (empty, foreign):
        with pytest.raises(CandidateRejectedError):
            validate_staged_candidate(candidate)


def test_a_corrupt_candidate_is_rejected(tmp_path, current):
    corrupt = tmp_path / "corrupt.sqlite"
    payload = bytearray(current.read_bytes())
    # Damage well past the header, so the file still opens as SQLite and has to
    # be caught by the structural check rather than by failing to open.
    for offset in range(4096, min(len(payload), 65536)):
        payload[offset] = payload[offset] ^ 0xFF
    corrupt.write_bytes(bytes(payload))

    with pytest.raises(CandidateRejectedError):
        validate_staged_candidate(corrupt)


def test_a_candidate_depending_on_an_external_wal_is_rejected(tmp_path, current):
    current.with_name(current.name + "-wal").write_bytes(b"pretend wal frames")

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "candidate-external-journal-dependency"


def test_a_candidate_depending_on_an_external_rollback_journal_is_rejected(tmp_path, current):
    current.with_name(current.name + "-journal").write_bytes(b"pretend journal")

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(current)
    assert error.value.rejection == "candidate-external-journal-dependency"


def test_a_symlinked_candidate_is_rejected(tmp_path, current):
    link = tmp_path / "linked.sqlite"
    link.symlink_to(current)

    with pytest.raises(CandidateRejectedError) as error:
        validate_staged_candidate(link)
    assert error.value.rejection == "candidate-is-symlink"


# --------------------------------------------------------------------------
# Validation changes nothing
# --------------------------------------------------------------------------

def test_validation_performs_no_writes(current):
    before = digest(current)

    validate_staged_candidate(current)

    assert digest(current) == before


def test_validation_never_creates_the_migration_table(tmp_path):
    """The reason this module exists instead of reusing `applied_migration_ids`."""
    foreign = tmp_path / "foreign.sqlite"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE notes (x INTEGER)")
    before = digest(foreign)

    with pytest.raises(CandidateRejectedError):
        validate_staged_candidate(foreign)

    assert digest(foreign) == before
    with sqlite3.connect(f"file:{foreign}?mode=ro", uri=True) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert MIGRATION_TABLE not in tables


def test_validation_never_migrates_the_candidate(tmp_path):
    older = build_workspace_database(
        tmp_path / "older.sqlite", "older", up_to="0018_demo_data_tracking"
    )
    before = digest(older)

    validate_staged_candidate(older)

    assert digest(older) == before
    with sqlite3.connect(f"file:{older}?mode=ro", uri=True) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert "artifact_audit_operations" not in tables


def test_validation_leaves_no_sidecar_beside_the_candidate(current):
    validate_staged_candidate(current)

    for suffix in ("-wal", "-shm", "-journal"):
        assert not current.with_name(current.name + suffix).exists()
