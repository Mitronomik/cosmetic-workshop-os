"""CR-004 regressions: the backup engine and the generated-filename grammar.

Durable contract:
``docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md``.

Every consistency test here reproduces one behaviour the CR-004 diagnostic
measured on merged `main` and that the accepted contract now forbids. They use
barriers and explicit transaction boundaries rather than sleeps, so none of them
depends on timing to be meaningful.
"""

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
import threading

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations
from app.db.paths import USER_DATA_DIR_ENV
from app.services.backup import (
    BACKUP_BUSY_TIMEOUT_SECONDS,
    BackupPaths,
    BackupBusyError,
    BackupError,
    BackupSourceMissingError,
    backup_sqlite_database,
    canonical_backup_reason,
    is_generated_backup_filename,
    list_backup_files,
    parse_generated_backup_filename,
    reserve_backup_path,
)
import app.services.backup as backup_service
from app.services.database import initialize_database
from app.services.startup import initialize_startup

FIXED_TIME = datetime(2026, 8, 1, 10, 15, 0, 123456, tzinfo=UTC)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def migrated_database(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    initialize_database(DatabaseConfig(path=path))
    return path


def supported_older_database(path: Path) -> Path:
    """Build the exact known prefix immediately before current head."""
    path.parent.mkdir(parents=True, exist_ok=True)
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-1]
        apply_migrations(DatabaseConfig(path=path))
    finally:
        MIGRATION_MODULES[:] = original
    return path


def insert_ingredients(connection: sqlite3.Connection, labels) -> None:
    connection.executemany(
        "INSERT INTO ingredients (name, category, default_unit, is_active) VALUES (?, 'base', 'g', 1)",
        [(label,) for label in labels],
    )


def read_names(path: Path, prefix: str) -> set[str]:
    """Open one database independently, without any source WAL or journal."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {
            row[0]
            for row in connection.execute("SELECT name FROM ingredients WHERE name LIKE ?", (f"{prefix}%",))
        }
    finally:
        connection.close()


def quick_check(path: Path) -> str:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return connection.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        connection.close()


def isolated_copy(source: Path, destination: Path) -> Path:
    """Move the bytes somewhere with no sibling WAL, journal or shm file.

    This is what proves independence. A backup read next to the source's own
    `-wal` can borrow committed pages from it and look complete when it is not.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    return destination


# --------------------------------------------------------------------------
# CR-004 §7.2 — WAL committed but uncheckpointed state
# --------------------------------------------------------------------------

def test_wal_committed_uncheckpointed_rows_are_present_in_the_backup(tmp_path):
    """The decisive CR-004 finding, inverted into a guarantee.

    On merged `main` this produced a `quick_check = ok`, fully migrated database
    that contained **none** of the committed rows. Structural validity was never
    the question; transactional completeness was.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    writer = sqlite3.connect(database)
    try:
        writer.execute("PRAGMA journal_mode = WAL")
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        insert_ingredients(writer, [f"wal-committed-{index}" for index in range(50)])
        writer.commit()
        assert (database.parent / f"{database.name}-wal").stat().st_size > 0

        result = backup_sqlite_database(database, tmp_path / "backups", reason="manual")
        independent = isolated_copy(result.backup_path, tmp_path / "independent.sqlite")
    finally:
        writer.close()

    assert read_names(independent, "wal-committed-") == {
        f"wal-committed-{index}" for index in range(50)
    }
    assert quick_check(independent) == "ok"


def test_backup_of_a_wal_source_opens_without_the_source_wal(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    writer = sqlite3.connect(database)
    try:
        writer.execute("PRAGMA journal_mode = WAL")
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        insert_ingredients(writer, ["independent-row"])
        writer.commit()
        result = backup_sqlite_database(database, tmp_path / "backups", reason="manual")
    finally:
        writer.close()

    # Deleting the whole source, WAL included, must not affect the backup.
    moved = isolated_copy(result.backup_path, tmp_path / "elsewhere" / "backup.sqlite")
    assert read_names(moved, "independent-row") == {"independent-row"}


# --------------------------------------------------------------------------
# CR-004 §7.5 — uncommitted data must never appear
# --------------------------------------------------------------------------

def test_uncommitted_rows_are_excluded_and_committed_rows_are_kept(tmp_path):
    """On merged `main` this leaked 465 never-committed rows and lost 506 real ones."""
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    seed = sqlite3.connect(database)
    try:
        insert_ingredients(seed, [f"committed-{index}" for index in range(30)])
        seed.commit()
    finally:
        seed.close()

    holder = sqlite3.connect(database, timeout=30)
    try:
        holder.execute("BEGIN IMMEDIATE")
        insert_ingredients(holder, [f"UNCOMMITTED-{index}" for index in range(30)])
        result = backup_sqlite_database(database, tmp_path / "backups", reason="manual")
    finally:
        holder.rollback()
        holder.close()

    independent = isolated_copy(result.backup_path, tmp_path / "independent.sqlite")
    assert read_names(independent, "committed-") == {f"committed-{index}" for index in range(30)}
    assert read_names(independent, "UNCOMMITTED-") == set()
    assert quick_check(independent) == "ok"


# --------------------------------------------------------------------------
# CR-004 §7.4 — concurrent committed writers, paired atomicity
# --------------------------------------------------------------------------

def test_a_concurrent_transaction_is_never_half_represented(tmp_path):
    """Each writer transaction inserts a matched pair into two tables.

    A snapshot holding one half without the other has captured part of one
    SQLite transaction. The writer is driven by explicit events, so the backup
    always runs while a transaction is genuinely open.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    mid_transaction = threading.Event()
    backup_done = threading.Event()
    failures: list[str] = []

    def writer() -> None:
        connection = sqlite3.connect(database, timeout=30)
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO ingredients (name, category, default_unit, is_active) VALUES ('pair-1', 'base', 'g', 1)"
            )
            connection.execute(
                "INSERT INTO catalog_tags (scope, name, slug) VALUES ('ingredient', 'pair-1', 'pair-1')"
            )
            mid_transaction.set()
            backup_done.wait(timeout=30)
            connection.commit()
        except sqlite3.Error as failure:  # pragma: no cover - surfaced through `failures`
            failures.append(f"{type(failure).__name__}: {failure}")
        finally:
            connection.close()

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        assert mid_transaction.wait(timeout=30)
        result = backup_sqlite_database(database, tmp_path / "backups", reason="manual")
    finally:
        backup_done.set()
        thread.join(timeout=30)
    assert failures == []

    independent = isolated_copy(result.backup_path, tmp_path / "independent.sqlite")
    connection = sqlite3.connect(f"file:{independent}?mode=ro", uri=True)
    try:
        ingredients = {row[0] for row in connection.execute("SELECT name FROM ingredients WHERE name LIKE 'pair-%'")}
        tags = {row[0] for row in connection.execute("SELECT name FROM catalog_tags WHERE name LIKE 'pair-%'")}
    finally:
        connection.close()

    # Either both halves or neither — never one.
    assert ingredients == tags
    assert quick_check(independent) == "ok"


def test_backup_does_not_modify_source_business_data(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    seed = sqlite3.connect(database)
    try:
        insert_ingredients(seed, [f"stable-{index}" for index in range(10)])
        seed.commit()
    finally:
        seed.close()
    before = read_names(database, "stable-")

    backup_sqlite_database(database, tmp_path / "backups", reason="manual")

    assert read_names(database, "stable-") == before


# --------------------------------------------------------------------------
# The engine's own contract
# --------------------------------------------------------------------------

def test_missing_source_raises_before_creating_the_backup_directory(tmp_path):
    with pytest.raises(BackupSourceMissingError):
        backup_sqlite_database(tmp_path / "absent.sqlite", tmp_path / "backups", reason="manual")
    assert not (tmp_path / "backups").exists()


def test_source_that_is_not_a_file_is_refused(tmp_path):
    directory = tmp_path / "not-a-file.sqlite"
    directory.mkdir()
    with pytest.raises(BackupError):
        backup_sqlite_database(directory, tmp_path / "backups", reason="manual")
    assert not (tmp_path / "backups").exists()


def test_a_locked_source_fails_within_the_bounded_wait(tmp_path):
    """The bound itself.

    CPython retries `sqlite3_backup_step` for as long as it reports busy, so the
    plain call never returned while the source stayed locked. One busy wait, then
    a truthful refusal — and no file left behind.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    seed = sqlite3.connect(database)
    try:
        seed.executemany(
            "INSERT INTO ingredients (name, category, default_unit, is_active, notes) VALUES (?, 'base', 'g', 1, ?)",
            [(f"row-{index}", "O" * 400) for index in range(4000)],
        )
        seed.commit()
    finally:
        seed.close()

    locked = threading.Event()
    release = threading.Event()

    def hold_exclusive_lock() -> None:
        connection = sqlite3.connect(database, timeout=60)
        try:
            # A small cache forces the open transaction to spill pages, which is
            # what makes SQLite take a real EXCLUSIVE lock on the main file.
            connection.execute("PRAGMA cache_size = 16")
            connection.execute("BEGIN EXCLUSIVE")
            connection.execute("UPDATE ingredients SET notes = 'LOCKED' WHERE id <= 4000")
            locked.set()
            release.wait(timeout=60)
        finally:
            connection.rollback()
            connection.close()

    thread = threading.Thread(target=hold_exclusive_lock)
    thread.start()
    try:
        assert locked.wait(timeout=30)
        with pytest.raises(BackupBusyError):
            backup_sqlite_database(database, tmp_path / "backups", reason="manual")
    finally:
        release.set()
        thread.join(timeout=60)

    # Refusing must not leave a partial artifact: an empty file is a valid empty
    # SQLite database and would otherwise be listed as a backup.
    assert list_backup_files(tmp_path / "backups") == []


def test_the_bounded_wait_is_the_repository_connection_timeout():
    assert BACKUP_BUSY_TIMEOUT_SECONDS == 5.0


def test_a_failure_before_publication_leaves_nothing_behind(tmp_path, monkeypatch):
    """A copy that never completes publishes nothing and leaves no scratch file.

    The engine writes into a file it exclusively created and only then links that
    content onto the reserved name, so a failure during the copy cannot leave a
    half-written artifact under a name the listing would show.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"

    def failing_copy(source, destination):
        # The scratch file already exists at this point; the copy into it fails.
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(backup_service, "_copy_sqlite_database", failing_copy)
    with pytest.raises(BackupError):
        backup_sqlite_database(database, backup_dir, reason="manual")
    monkeypatch.undo()

    assert list_backup_files(backup_dir) == []
    assert list(backup_dir.iterdir()) == []


def test_an_interrupted_copy_never_leaves_a_listable_partial(tmp_path, monkeypatch):
    """Even if the scratch file survives, it can never look like a backup."""
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    leaked: dict[str, Path] = {}

    def failing_copy(source, destination):
        leaked["partial"] = Path(destination)
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(backup_service, "_copy_sqlite_database", failing_copy)
    # Removing the scratch file is what normally cleans up; suppress it so the
    # crash-equivalent leftover is the thing under test.
    monkeypatch.setattr(Path, "unlink", lambda self, **kwargs: None)
    with pytest.raises(BackupError):
        backup_sqlite_database(database, backup_dir, reason="manual")
    monkeypatch.undo()

    partial = leaked["partial"]
    assert partial.exists()
    assert partial.suffix == backup_service.PARTIAL_BACKUP_SUFFIX
    assert partial.suffix not in backup_service.SQLITE_BACKUP_SUFFIXES
    # A crash therefore cannot leave a misleading successful-looking backup.
    assert list_backup_files(backup_dir) == []


def test_a_scratch_size_read_failure_publishes_nothing(tmp_path, monkeypatch):
    """The size is read from the scratch file, so its failure is a real failure.

    Moving that read before publication is what makes publication the commit
    point. It also means the read can still fail — and when it does, nothing has
    been published, so reporting failure is truthful.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    original_stat = Path.stat

    def failing_stat(self, *args, **kwargs):
        if self.suffix == backup_service.PARTIAL_BACKUP_SUFFIX:
            raise OSError("simulated scratch size read failure")
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", failing_stat)
    with pytest.raises(BackupError):
        backup_sqlite_database(database, backup_dir, reason="manual")
    monkeypatch.undo()

    assert list_backup_files(backup_dir) == []
    # No final backup was published, and the scratch file was cleaned up.
    assert list(backup_dir.iterdir()) == []


def test_the_engine_never_stats_the_final_path_after_publication(tmp_path, monkeypatch):
    """Nothing fallible may run after the artifact is committed.

    A `stat` of the published path would let a transient metadata failure turn a
    completed backup into a reported failure — a false total failure that invites
    the user to make a second copy of the same thing.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    reserved = reserve_backup_path(backup_dir, database, FIXED_TIME, "manual")

    published = {"value": False}
    stats_after_publication: list[str] = []
    original_stat = Path.stat
    original_publish = backup_service._publish_without_replacing

    def recording_stat(self, *args, **kwargs):
        if published["value"] and self == reserved:
            stats_after_publication.append(str(self))
        return original_stat(self, *args, **kwargs)

    def publish_then_watch(partial_path, backup_path):
        original_publish(partial_path, backup_path)
        published["value"] = True

    monkeypatch.setattr(backup_service, "_publish_without_replacing", publish_then_watch)
    monkeypatch.setattr(Path, "stat", recording_stat)
    result = backup_sqlite_database(
        database, backup_dir, reason="manual", reserved_backup_path=reserved
    )
    published["value"] = False
    monkeypatch.undo()

    assert stats_after_publication == []
    assert result.backup_path == reserved


def test_the_reported_size_is_the_published_file_size(tmp_path):
    """The scratch and final paths are links to one inode, so the size is exact."""
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    seed = sqlite3.connect(database)
    try:
        insert_ingredients(seed, [f"sized-{index}" for index in range(200)])
        seed.commit()
    finally:
        seed.close()
    backup_dir = tmp_path / "backups"

    result = backup_sqlite_database(database, backup_dir, reason="manual")

    assert result.size_bytes == result.backup_path.stat().st_size
    assert result.size_bytes > 0


def test_a_published_backup_never_fails_on_unavailable_final_metadata(tmp_path, monkeypatch):
    """Once published, no filesystem metadata read can make this a failure."""
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    reserved = reserve_backup_path(backup_dir, database, FIXED_TIME, "manual")

    published = {"value": False}
    original_stat = Path.stat
    original_publish = backup_service._publish_without_replacing

    def failing_final_stat(self, *args, **kwargs):
        # Every read of the *final* path fails from publication onwards.
        if published["value"] and self == reserved:
            raise OSError("final path metadata unavailable")
        return original_stat(self, *args, **kwargs)

    def publish_then_break(partial_path, backup_path):
        original_publish(partial_path, backup_path)
        published["value"] = True

    monkeypatch.setattr(backup_service, "_publish_without_replacing", publish_then_break)
    monkeypatch.setattr(Path, "stat", failing_final_stat)
    result = backup_sqlite_database(
        database, backup_dir, reason="manual", reserved_backup_path=reserved
    )
    published["value"] = False
    monkeypatch.undo()

    # A completed, published backup — reported as the success it is.
    assert result.backup_path == reserved
    assert result.size_bytes > 0
    assert quick_check(reserved) == "ok"
    assert [item.filename for item in list_backup_files(backup_dir)] == [reserved.name]


def test_the_correction_creates_exactly_one_backup(tmp_path):
    """No duplicate artifact is produced by the pre-publication size read."""
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"

    result = backup_sqlite_database(database, backup_dir, reason="manual")

    assert [p.name for p in backup_dir.iterdir()] == [result.backup_path.name]
    assert len(list_backup_files(backup_dir)) == 1


def test_backup_never_overwrites_an_existing_file(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    reserved = reserve_backup_path(backup_dir, database, FIXED_TIME, "manual")
    reserved.write_bytes(b"an existing backup")

    with pytest.raises(BackupError):
        backup_sqlite_database(
            database, backup_dir, reason="manual", reserved_backup_path=reserved
        )

    assert reserved.read_bytes() == b"an existing backup"


def test_reserved_path_is_used_exactly_and_dates_the_result(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    reserved = reserve_backup_path(backup_dir, database, FIXED_TIME, "before-import")

    result = backup_sqlite_database(
        database, backup_dir, reason="before-import", reserved_backup_path=reserved
    )

    assert result.backup_path == reserved
    # The reserved name, not the clock, dates the result: the ledger row, the
    # filename and the create response must all agree.
    assert result.created_at == FIXED_TIME
    assert canonical_backup_reason(result.backup_path) == "before_import"


def test_a_reserved_path_outside_the_backup_directory_is_refused(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    reserved = reserve_backup_path(elsewhere, database, FIXED_TIME, "manual")

    with pytest.raises(BackupError):
        backup_sqlite_database(database, backup_dir, reason="manual", reserved_backup_path=reserved)


def test_a_reserved_path_outside_the_grammar_is_refused(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    with pytest.raises(BackupError):
        backup_sqlite_database(
            database,
            backup_dir,
            reason="manual",
            reserved_backup_path=backup_dir / "chosen-by-hand.sqlite",
        )
    assert list(backup_dir.iterdir()) == []


def test_automatic_startup_backup_uses_the_safe_engine(tmp_path, monkeypatch):
    """The automatic `before_migration` backup runs before migrations, unaudited.

    It must still be a consistent snapshot — it is the copy a user falls back on
    when a migration goes wrong — but it creates no ledger row and no Journal
    event, and it cannot depend on the ledger table existing.
    """
    user_data_dir = tmp_path / "user-data"
    database = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    supported_older_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE legacy_marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO legacy_marker (value) VALUES ('before migration')")

    result = initialize_startup("user")

    assert result.backup is not None
    assert result.backup.reason == "before_migration"
    assert quick_check(result.backup.backup_path) == "ok"

    snapshot = sqlite3.connect(f"file:{result.backup.backup_path}?mode=ro", uri=True)
    try:
        assert snapshot.execute("SELECT value FROM legacy_marker").fetchone()[0] == "before migration"
        assert (
            snapshot.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='artifact_audit_operations'"
            ).fetchone()
            is None
        )
    finally:
        snapshot.close()

    live = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        assert live.execute("SELECT COUNT(*) FROM artifact_audit_operations").fetchone()[0] == 0
        assert (
            live.execute("SELECT COUNT(*) FROM audit_logs WHERE action = 'backup.created'").fetchone()[0]
            == 0
        )
    finally:
        live.close()


# --------------------------------------------------------------------------
# The strict generated-filename grammar
# --------------------------------------------------------------------------

def generated_name(stem: str = "cosmetic_workshop", reason: str = "before_import", suffix=None) -> str:
    tail = f"-{suffix}" if suffix is not None else ""
    return f"20260801T101500123456Z-{stem}-{reason}{tail}.sqlite"


@pytest.mark.parametrize(
    "name",
    [
        generated_name(),
        generated_name(suffix=1),
        generated_name(suffix=12),
        generated_name(stem="cosmetic-workshop-os-2"),
        generated_name(stem="Мастерская"),
        generated_name(reason="перед_обновлением"),
        generated_name(reason="reason_123"),
        generated_name(reason="manual", suffix=3),
        "20260801T101500123456Z-cosmetic_workshop-manual.db",
        "20260801T101500123456Z-cosmetic_workshop-manual.sqlite3",
    ],
)
def test_the_grammar_accepts_every_name_the_generator_produces(name):
    parsed = parse_generated_backup_filename(name)
    assert parsed is not None
    # A round trip through the one generator is the actual contract.
    assert generated_name(parsed.source_stem, parsed.reason, parsed.suffix).replace(
        ".sqlite", parsed.extension
    ) == name


@pytest.mark.parametrize(
    ("name", "why"),
    [
        ("2026-08-01-cosmetic_workshop-manual.sqlite", "malformed timestamp"),
        ("cosmetic_workshop-manual.sqlite", "missing timestamp"),
        ("20260801T101500123456Z-manual.sqlite", "no source stem"),
        ("20260801T101500123456Z--manual.sqlite", "empty source stem"),
        ("20260801T101500123456Z-cosmetic_workshop-before import.sqlite", "noncanonical space reason"),
        ("20260801T101500123456Z-cosmetic_workshop-Before_Import_.sqlite", "trailing separator in reason"),
        ("20260801T101500123456Z-cosmetic_workshop-123.sqlite", "digits-only reason"),
        ("20260801T101500123456Z-cosmetic_workshop-manual-01.sqlite", "leading-zero suffix"),
        ("20260801T101500123456Z-cosmetic_workshop-manual-1.5.sqlite", "malformed suffix"),
        ("20260801T101500123456Z-cosmetic_workshop-manual.txt", "wrong extension"),
        ("20260801T101500123456Z-cosmetic_workshop-manual.sqlite.bak", "double extension"),
        ("", "empty"),
        ("20260801T101500123456Z-cosmetic_workshop-manual", "no extension"),
    ],
)
def test_the_grammar_rejects_names_the_generator_could_not_produce(name, why):
    assert parse_generated_backup_filename(name) is None, why
    assert not is_generated_backup_filename(name), why
    assert canonical_backup_reason(Path(name)) is None, why


@pytest.mark.parametrize(
    "name",
    [
        "../20260801T101500123456Z-cosmetic_workshop-manual.sqlite",
        "sub/20260801T101500123456Z-cosmetic_workshop-manual.sqlite",
        "/20260801T101500123456Z-cosmetic_workshop-manual.sqlite",
    ],
)
def test_the_grammar_rejects_anything_that_is_not_a_plain_filename(name):
    """A path is not a name.

    This is the check the ledger depends on: a stored `primary_filename` is later
    joined onto a real directory, so a value carrying a separator or `..` must
    never parse as a generated name.
    """
    assert parse_generated_backup_filename(name) is None
    assert not is_generated_backup_filename(name)


def test_the_grammar_is_ambiguous_between_a_hyphenated_stem_and_reason():
    """CR-005 recorded this ambiguity, and it is why the filename is not identity.

    `...-cosmetic_workshop-before-import.sqlite` is genuinely a name this
    generator can produce — from a database called `cosmetic_workshop-before`
    with reason `import`. The grammar cannot tell that apart from a hyphenated
    reason, and it is not asked to: a backup proves whose it is through the
    ledger row embedded in the snapshot, never through its filename.
    """
    parsed = parse_generated_backup_filename(
        "20260801T101500123456Z-cosmetic_workshop-before-import.sqlite"
    )

    assert parsed is not None
    assert (parsed.source_stem, parsed.reason) == ("cosmetic_workshop-before", "import")


def test_the_grammar_is_not_applied_to_legacy_listing(tmp_path):
    """Legacy listing stays best-effort; CR-005 accepted exactly that."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    legacy = backup_dir / "20260705T090000000000Z-cosmetic_workshop-before-import.sqlite"
    legacy.write_bytes(b"legacy")
    ambiguous = backup_dir / "ambiguous.sqlite"
    ambiguous.write_bytes(b"legacy")

    listed = {item.filename for item in list_backup_files(backup_dir)}

    assert listed == {legacy.name, ambiguous.name}
    assert parse_generated_backup_filename(ambiguous.name) is None


def test_the_uniqueness_suffix_is_never_part_of_the_reason():
    parsed = parse_generated_backup_filename(generated_name(reason="before_import", suffix=7))
    assert parsed is not None
    assert parsed.reason == "before_import"
    assert parsed.suffix == 7


def test_a_hyphenated_source_stem_round_trips(tmp_path):
    database = migrated_database(tmp_path / "cosmetic-workshop-os-2.sqlite")
    reserved = reserve_backup_path(tmp_path / "backups", database, FIXED_TIME, "before-update ../unsafe")

    parsed = parse_generated_backup_filename(reserved.name)

    assert parsed is not None
    assert parsed.source_stem == "cosmetic-workshop-os-2"
    assert parsed.reason == "before_update_unsafe"
    assert parsed.suffix is None


def test_reservation_advances_past_an_active_ledger_identity(tmp_path):
    """A `prepared` operation owns its filename before that file exists."""
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    taken = {reserve_backup_path(backup_dir, database, FIXED_TIME, "manual").name}

    second = reserve_backup_path(
        backup_dir, database, FIXED_TIME, "manual", is_identity_active=lambda name: name in taken
    )

    assert second.name not in taken
    assert second.name.endswith("-manual-1.sqlite")


# --------------------------------------------------------------------------
# startup ordering
# --------------------------------------------------------------------------

def test_startup_reconciles_manual_backups_after_migrations_and_after_exports(tmp_path, monkeypatch):
    """The accepted order, asserted as an order rather than as a set of calls.

    `automatic before_migration backup → migrations → report documents → JSON
    exports → manual backups → API`. The automatic backup must be recorded
    before migrations run, and manual-backup reconciliation must come after the
    migration that creates the ledger table it reads.
    """
    user_data_dir = tmp_path / "user-data"
    database = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))
    supported_older_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE legacy_marker (value TEXT NOT NULL)")

    import app.services.startup as startup_module

    order: list[str] = []
    originals = {
        name: getattr(startup_module, name)
        for name in (
            "backup_sqlite_database",
            "initialize_database",
            "reconcile_report_documents",
            "reconcile_json_exports",
            "reconcile_manual_backups",
        )
    }

    def record(name):
        def wrapper(*args, **kwargs):
            order.append(name)
            return originals[name](*args, **kwargs)

        return wrapper

    for name in originals:
        monkeypatch.setattr(startup_module, name, record(name))

    result = startup_module.initialize_startup("user")

    assert order == [
        "backup_sqlite_database",
        "initialize_database",
        "reconcile_report_documents",
        "reconcile_json_exports",
        "reconcile_manual_backups",
    ]
    assert result.manual_backup_audit_reconciliation is not None
    assert result.manual_backup_audit_reconciliation.examined == 0
    # The automatic backup is not routed through the audited orchestration.
    assert result.backup is not None
    assert result.backup.reason == "before_migration"


# --------------------------------------------------------------------------
# Destination ownership under a race
# --------------------------------------------------------------------------

def test_a_foreign_file_appearing_after_the_check_is_never_overwritten(tmp_path, monkeypatch):
    """The no-overwrite guarantee must survive a TOCTOU race.

    `exists()` followed by an open is not ownership: another process can create
    the destination in between. Here a foreign, perfectly valid SQLite database
    appears at the reserved path *after* the early check and *before* publication.
    The engine must fail without touching it.
    """
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    reserved = reserve_backup_path(backup_dir, database, FIXED_TIME, "manual")

    foreign_bytes: dict[str, bytes] = {}
    original_copy = backup_service._copy_sqlite_database

    def copy_then_race(source, destination):
        original_copy(source, destination)
        # The race window: the destination was free at the early check, and a
        # different process creates it before this operation publishes.
        initialize_database(DatabaseConfig(path=reserved))
        foreign_bytes["content"] = reserved.read_bytes()

    monkeypatch.setattr(backup_service, "_copy_sqlite_database", copy_then_race)
    with pytest.raises(BackupError):
        backup_sqlite_database(
            database, backup_dir, reason="manual", reserved_backup_path=reserved
        )
    monkeypatch.undo()

    # The foreign file is untouched, byte for byte.
    assert reserved.exists()
    assert reserved.read_bytes() == foreign_bytes["content"]
    assert quick_check(reserved) == "ok"
    # Cleanup removed only the engine's own scratch file.
    assert [p.name for p in backup_dir.iterdir()] == [reserved.name]


def test_publication_refuses_rather_than_replacing_an_existing_destination(tmp_path):
    """`os.link` is what refuses; a plain rename would silently replace."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    partial = backup_dir / "scratch.partial"
    partial.write_bytes(b"engine-owned content")
    occupied = backup_dir / "20260801T101500123456Z-cosmetic_workshop-manual.sqlite"
    occupied.write_bytes(b"a foreign file")

    with pytest.raises(BackupError):
        backup_service._publish_without_replacing(partial, occupied)

    assert occupied.read_bytes() == b"a foreign file"
    assert partial.read_bytes() == b"engine-owned content"


def test_a_racing_foreign_destination_leaves_the_ledger_unresolved(tmp_path, monkeypatch):
    """The audited create must not audit anything when publication is refused."""
    from app.services.backup_audit import BackupAuditService
    from app.services.backup_creation import create_audited_backup

    database = tmp_path / "data" / "cosmetic_workshop.sqlite"
    database.parent.mkdir(parents=True)
    config = DatabaseConfig(path=database)
    initialize_database(config)
    paths = BackupPaths(database_path=database, backup_dir=tmp_path / "backups")

    original_publish = backup_service._publish_without_replacing

    def occupy_then_publish(partial_path, backup_path):
        # The race window, at its narrowest: a foreign process creates the exact
        # reserved path in the instant before this operation publishes onto it.
        initialize_database(DatabaseConfig(path=Path(backup_path)))
        original_publish(partial_path, backup_path)

    monkeypatch.setattr(backup_service, "_publish_without_replacing", occupy_then_publish)
    with pytest.raises(BackupError):
        create_audited_backup(paths, "manual", config=config)
    monkeypatch.undo()

    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action = 'backup.created'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM artifact_audit_operations WHERE status = 'audited'"
        ).fetchone()[0] == 0
    finally:
        connection.close()
    # The unresolved operation stays counted for bounded reconciliation.
    assert BackupAuditService(paths.backup_dir, config).pending_count() == 1
    # Only the foreign file remains; the scratch file was cleaned up.
    assert len(list(paths.backup_dir.iterdir())) == 1


def test_the_successful_path_publishes_exactly_the_reserved_filename(tmp_path):
    database = migrated_database(tmp_path / "data" / "cosmetic_workshop.sqlite")
    backup_dir = tmp_path / "backups"
    reserved = reserve_backup_path(backup_dir, database, FIXED_TIME, "before-import")

    result = backup_sqlite_database(
        database, backup_dir, reason="before-import", reserved_backup_path=reserved
    )

    assert result.backup_path == reserved
    assert result.backup_path.exists()
    # Exactly one file: the published backup, with no scratch file left over.
    assert [p.name for p in backup_dir.iterdir()] == [reserved.name]
    assert quick_check(reserved) == "ok"
