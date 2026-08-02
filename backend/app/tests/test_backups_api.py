from datetime import UTC, datetime
from pathlib import Path
import sqlite3

import pytest
from pydantic import ValidationError

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app
from app.schemas.backups import BackupCreateRequest
from app.services.backup import backup_sqlite_database, list_backup_files
from app.services.database import initialize_database


class _FrozenDatetime(datetime):
    """Fixed clock so a backup filename collision, and therefore the ``-N``
    uniqueness suffix, is reproducible."""

    @classmethod
    def now(cls, tz=None):  # noqa: D102 - mirrors datetime.now
        return datetime(2026, 7, 27, 10, 15, 0, tzinfo=tz or UTC)


def make_database(path: Path, *, rows: int = 3) -> Path:
    """A real, fully migrated application database with identifiable rows.

    CR-004 replaced the raw file copy with the SQLite Online Backup API, so a
    backup source must now actually be a SQLite database. These tests used a
    handful of literal bytes as a stand-in before; that stand-in was only ever
    valid because the old implementation copied bytes without understanding
    them, which is precisely the behaviour ADR 0015 removes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    initialize_database(DatabaseConfig(path=path))
    connection = sqlite3.connect(path)
    try:
        connection.executemany(
            "INSERT INTO ingredients (name, category, default_unit, is_active) VALUES (?, 'base', 'g', 1)",
            [(f"backup-source-{index}",) for index in range(rows)],
        )
        connection.commit()
    finally:
        connection.close()
    return path


def ingredient_names(path: Path) -> set[str]:
    """Read one database independently, without its source WAL or journal."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {row[0] for row in connection.execute("SELECT name FROM ingredients")}
    finally:
        connection.close()


def test_missing_backup_dir_returns_empty_list_without_creating_dir(tmp_path):
    backup_dir = tmp_path / "missing-backups"

    assert list_backup_files(backup_dir) == []
    assert not backup_dir.exists()


def test_existing_backup_files_are_listed_newest_first_and_ignore_non_backups(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    older = backup_dir / "20260705T090000000000Z-cosmetic_workshop-manual.sqlite"
    newer = backup_dir / "20260705T100000000000Z-cosmetic_workshop-before_update.sqlite"
    ignored = backup_dir / "notes.txt"
    older.write_bytes(b"old")
    newer.write_bytes(b"newer")
    ignored.write_text("not a sqlite backup", encoding="utf-8")

    backups = list_backup_files(backup_dir)

    assert [backup.filename for backup in backups] == [newer.name, older.name]
    assert backups[0].reason == "before_update"
    assert backups[0].size_bytes == len(b"newer")


def test_malformed_backup_filename_does_not_crash_listing(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    malformed = backup_dir / "manual-copy.sqlite"
    malformed.write_bytes(b"sqlite bytes")

    backups = list_backup_files(backup_dir)

    assert len(backups) == 1
    assert backups[0].filename == malformed.name
    assert backups[0].created_at is not None
    assert backups[0].reason is None


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_status_is_read_only_and_reports_paths(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "cosmetic_workshop.sqlite"
    user_data_dir = tmp_path / "user-data"
    backup_dir = user_data_dir / "backups"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data_dir))

    client = TestClient(create_app())
    response = client.get("/api/backups/status")

    assert response.status_code == 200
    body = response.json()
    assert body["database_path"] == str(db_path)
    assert body["database_exists"] is False
    assert body["database_size_bytes"] is None
    assert body["backup_dir"] == str(backup_dir)
    assert body["backup_dir_exists"] is False
    assert body["backup_count"] == 0
    assert body["latest_backup"] is None
    assert not db_path.exists()
    assert not backup_dir.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_list_returns_empty_for_missing_dir_without_creating_it(tmp_path, monkeypatch):
    db_path = tmp_path / "dev.sqlite"
    backup_dir = tmp_path / "backups"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.get("/api/backups")

    assert response.status_code == 200
    assert response.json() == {"backups": [], "backup_dir": str(backup_dir)}
    assert not backup_dir.exists()
    assert not db_path.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_backup_creates_unique_backup_without_modifying_source(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    source_rows = ingredient_names(db_path)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    first = client.post("/api/backups", json={"reason": "before_large_edit"})
    second = client.post("/api/backups", json={"reason": "before_large_edit"})

    assert first.status_code == 201
    assert second.status_code == 201
    first_backup = first.json()["backup"]
    second_backup = second.json()["backup"]
    assert first.json()["message"] == "Резервная копия создана."
    assert first.json()["database_path"] == str(db_path)
    assert first_backup["filename"] != second_backup["filename"]
    assert "before_large_edit" in first_backup["filename"]
    # Both snapshots carry the committed business rows. Byte-for-byte equality
    # with the source is deliberately *not* asserted: ADR 0015 accepts a
    # transactionally consistent snapshot, not a file-level clone.
    assert ingredient_names(Path(first_backup["path"])) == source_rows
    assert ingredient_names(Path(second_backup["path"])) == source_rows
    assert first_backup["size_bytes"] == Path(first_backup["path"]).stat().st_size
    assert second_backup["size_bytes"] == Path(second_backup["path"]).stat().st_size
    assert db_path.exists()
    assert ingredient_names(db_path) == source_rows

    listed = client.get("/api/backups").json()["backups"]
    assert [item["filename"] for item in listed] == [second_backup["filename"], first_backup["filename"]]


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_post_backup_with_missing_database_returns_safe_error_without_backup(tmp_path, monkeypatch):
    db_path = tmp_path / "missing.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 404
    assert response.json()["detail"] == "База данных не найдена. Сначала запустите приложение и создайте рабочую базу."
    assert not (tmp_path / "backups").exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    empty = client.post("/api/backups", json={"reason": "   "})
    unsafe = client.post("/api/backups", json={"reason": "before/update ../unsafe"})

    assert empty.status_code == 201
    assert "manual" in empty.json()["backup"]["filename"]
    assert unsafe.status_code == 201
    unsafe_path = Path(unsafe.json()["backup"]["path"])
    assert unsafe_path.parent == tmp_path / "backups"
    assert "before_update_unsafe" in unsafe_path.name


def test_backup_reason_rejects_too_long_values():
    with pytest.raises(ValidationError):
        BackupCreateRequest(reason="x" * 81)


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
@pytest.mark.parametrize(
    ("human_reason", "canonical_reason"),
    [
        ("before-update ../unsafe", "before_update_unsafe"),
        ("before-import", "before_import"),
        ("___before---import___", "before_import"),
        ("перед обновлением", "перед_обновлением"),
        ("123", "reason_123"),
        ("   ", "manual"),
        ("../..", "manual"),
    ],
)
def test_backup_create_list_and_status_report_the_same_canonical_reason(
    tmp_path, monkeypatch, human_reason, canonical_reason
):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    created = client.post("/api/backups", json={"reason": human_reason})

    assert created.status_code == 201
    backup = created.json()["backup"]
    assert backup["reason"] == canonical_reason
    assert canonical_reason in backup["filename"]

    listed = client.get("/api/backups").json()["backups"]
    assert [item["reason"] for item in listed] == [canonical_reason]
    assert listed[0]["filename"] == backup["filename"]

    latest = client.get("/api/backups/status").json()["latest_backup"]
    assert latest["reason"] == canonical_reason
    assert latest["filename"] == backup["filename"]


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_backup_reason_round_trip_survives_a_hyphenated_source_database_stem(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic-workshop-os-2.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    created = client.post("/api/backups", json={"reason": "before-update ../unsafe"})

    assert created.status_code == 201
    backup = created.json()["backup"]
    assert backup["filename"].startswith(f"{backup['filename'].split('-', 1)[0]}-cosmetic-workshop-os-2-")
    assert "before_update_unsafe" in backup["filename"]
    assert backup["reason"] == "before_update_unsafe"
    assert client.get("/api/backups").json()["backups"][0]["reason"] == "before_update_unsafe"
    assert client.get("/api/backups/status").json()["latest_backup"]["reason"] == "before_update_unsafe"


def test_backup_uniqueness_suffix_is_never_reported_as_the_reason(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic-workshop-os.sqlite")
    source_rows = ingredient_names(db_path)
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr("app.services.backup.datetime", _FrozenDatetime)

    first = backup_sqlite_database(db_path, backup_dir, reason="before-update ../unsafe")
    second = backup_sqlite_database(db_path, backup_dir, reason="before-update ../unsafe")
    third = backup_sqlite_database(db_path, backup_dir, reason="before-update ../unsafe")

    assert first.backup_path != second.backup_path != third.backup_path
    assert second.backup_path.name.endswith("-before_update_unsafe-1.sqlite")
    assert third.backup_path.name.endswith("-before_update_unsafe-2.sqlite")
    assert ingredient_names(first.backup_path) == source_rows
    assert ingredient_names(second.backup_path) == source_rows
    assert ingredient_names(db_path) == source_rows

    listed = list_backup_files(backup_dir)
    assert len(listed) == 3
    assert {item.reason for item in listed} == {"before_update_unsafe"}


def test_legacy_backup_files_are_listed_without_rename_delete_or_rewrite(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    legacy = {
        "20260705T090000000000Z-cosmetic_workshop-before_update____unsafe.sqlite": b"legacy repeated underscores",
        "20260705T091000000000Z-cosmetic_workshop-before-import.sqlite": b"legacy hyphen reason",
        "20260705T092000000000Z-cosmetic_workshop-123.sqlite": b"legacy numeric reason",
        "ambiguous.sqlite": b"legacy ambiguous",
    }
    for name, content in legacy.items():
        (backup_dir / name).write_bytes(content)
    before = {path.name: path.read_bytes() for path in backup_dir.iterdir()}

    listed = list_backup_files(backup_dir)

    assert sorted(item.filename for item in listed) == sorted(legacy)
    assert {path.name: path.read_bytes() for path in backup_dir.iterdir()} == before
    for item in listed:
        assert item.path.exists()
        assert item.size_bytes == len(legacy[item.filename])
        assert item.created_at is not None
    by_name = {item.filename: item for item in listed}
    assert by_name["20260705T090000000000Z-cosmetic_workshop-before_update____unsafe.sqlite"].reason == (
        "before_update____unsafe"
    )
    assert by_name["ambiguous.sqlite"].reason is None


# --------------------------------------------------------------------------
# CR-009 B3 — the audited create and status contract
# --------------------------------------------------------------------------

@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_create_returns_recorded_and_describes_the_exact_backup_result(tmp_path, monkeypatch):
    """The create response comes from the engine's own result, never from a re-scan.

    CR-004 measured the previous directory re-list turning a complete, verified
    backup into an HTTP 500, and found it could also raise `StopIteration` or
    describe a different file.
    """
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    response = client.post("/api/backups", json={"reason": "before-update ../unsafe"})

    assert response.status_code == 201
    body = response.json()
    assert body["audit_status"] == "recorded"
    assert body["audit_message"] is None
    backup = body["backup"]
    created = Path(backup["path"])
    assert created.exists()
    assert backup["filename"] == created.name
    assert backup["size_bytes"] == created.stat().st_size
    # The canonical filename-derived reason, never the human request reason.
    assert backup["reason"] == "before_update_unsafe"

    journal = client.get("/api/audit-logs").json()["items"]
    backup_events = [item for item in journal if item["action"] == "backup.created"]
    assert len(backup_events) == 1
    assert backup_events[0]["display_summary"] == "Резервная копия создана"
    assert backup_events[0]["entity_label"] == "Резервная копия"


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_create_does_not_re_list_the_backup_directory(tmp_path, monkeypatch):
    """A directory read failure after a successful backup must not fail the create."""
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
    client = TestClient(create_app())

    import app.api.backups as backups_api

    def fail_if_called(backup_dir):
        raise AssertionError("the create path must not re-list the backup directory")

    monkeypatch.setattr(backups_api, "list_backup_files", fail_if_called)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 201
    assert Path(response.json()["backup"]["path"]).exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_a_failed_audit_returns_pending_201_and_keeps_the_backup(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    from app.services.backup_audit import PENDING_AUDIT_MESSAGE, BackupAuditService

    from app.services.backup_audit import BackupFinalization

    monkeypatch.setattr(
        BackupAuditService,
        "finalize",
        lambda self, operation_id, *, reconciled_after_failure: BackupFinalization("audit_pending"),
    )
    client = TestClient(create_app())
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Резервная копия создана."
    assert body["audit_status"] == "pending"
    assert body["audit_message"] == PENDING_AUDIT_MESSAGE

    created = Path(body["backup"]["path"])
    assert created.exists()
    assert created.name in {item["filename"] for item in client.get("/api/backups").json()["backups"]}
    assert client.get("/api/backups/status").json()["pending_audit_count"] == 1

    # The unresolved operation is finalized exactly once by the next create's
    # bounded pre-create reconciliation pass.
    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
    client = TestClient(create_app())
    second = client.post("/api/backups", json={"reason": "manual"})

    assert second.status_code == 201
    assert client.get("/api/backups/status").json()["pending_audit_count"] == 0
    journal = client.get("/api/audit-logs").json()["items"]
    assert len([item for item in journal if item["action"] == "backup.created"]) == 2


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_preparation_failure_returns_the_exact_safe_500_and_creates_nothing(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    from app.services.backup_audit import BackupAuditService, BackupAuditTrackingUnavailableError

    def failing_prepare(self, *, primary_filename):
        raise BackupAuditTrackingUnavailableError(BackupAuditTrackingUnavailableError.message)

    monkeypatch.setattr(BackupAuditService, "prepare_operation", failing_prepare)
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == {
        "code": "artifact_audit_tracking_unavailable",
        "message": "Не удалось безопасно подготовить создание резервной копии. Резервная копия не создана.",
        "next_action": "Повторите создание резервной копии. Если ошибка повторяется, перезапустите приложение.",
    }
    assert not (tmp_path / "backups").exists() or list((tmp_path / "backups").iterdir()) == []


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_status_reports_the_exact_pending_count_and_stays_read_only(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    from app.services.backup import resolve_backup_paths
    from app.services.backup_audit import BackupAuditService

    client = TestClient(create_app())
    assert client.get("/api/backups/status").json()["pending_audit_count"] == 0

    paths = resolve_backup_paths()
    service = BackupAuditService(paths.backup_dir)
    service.prepare_operation(primary_filename="20260801T101500123456Z-cosmetic_workshop-manual.sqlite")

    status = client.get("/api/backups/status").json()
    assert status["pending_audit_count"] == 1
    # Reading the status must not reconcile it away, nor create anything.
    assert client.get("/api/backups/status").json()["pending_audit_count"] == 1
    assert not paths.backup_dir.exists()


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_a_ledger_read_failure_is_a_safe_500_and_never_a_fabricated_zero(tmp_path, monkeypatch):
    """`0` is a factual claim the frontend clears a standing warning on."""
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    import app.api.backups as backups_api

    def failing_count(backup_dir, config=None):
        raise sqlite3.OperationalError("ledger unavailable")

    monkeypatch.setattr(backups_api, "pending_backup_audit_count", failing_count)
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/api/backups/status")

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Не удалось прочитать сведения о резервных копиях. Данные мастерской не изменялись."
    )


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_status_reports_zero_without_creating_a_database(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "cosmetic_workshop.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app())
    body = client.get("/api/backups/status").json()

    assert body["database_exists"] is False
    assert body["pending_audit_count"] == 0
    assert not db_path.exists()


def test_the_create_response_schema_binds_the_two_audit_fields():
    from app.schemas.backups import BackupCreateResponse
    from app.services.backup_audit import PENDING_AUDIT_MESSAGE

    file_payload = {
        "filename": "20260801T101500123456Z-cosmetic_workshop-manual.sqlite",
        "path": "/local/backups/20260801T101500123456Z-cosmetic_workshop-manual.sqlite",
        "created_at": datetime(2026, 8, 1, 10, 15, tzinfo=UTC),
        "reason": "manual",
        "size_bytes": 4096,
    }
    base = {
        "backup": file_payload,
        "database_path": "/local/cosmetic_workshop.sqlite",
        "backup_dir": "/local/backups",
        "message": "Резервная копия создана.",
    }

    assert BackupCreateResponse(**base, audit_status="recorded", audit_message=None).audit_message is None
    assert (
        BackupCreateResponse(**base, audit_status="pending", audit_message=PENDING_AUDIT_MESSAGE).audit_status
        == "pending"
    )
    with pytest.raises(ValidationError):
        BackupCreateResponse(**base, audit_status="recorded", audit_message="unexpected warning")
    with pytest.raises(ValidationError):
        BackupCreateResponse(**base, audit_status="pending", audit_message=None)
    with pytest.raises(ValidationError):
        BackupCreateResponse(**base, audit_status="pending", audit_message="a different warning")


# --------------------------------------------------------------------------
# Verification failure is not a pending Journal entry
# --------------------------------------------------------------------------

def _workspace(tmp_path, monkeypatch):
    db_path = make_database(tmp_path / "cosmetic_workshop.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
    return db_path


def _backup_events(db_path: Path) -> int:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action = 'backup.created'"
        ).fetchone()[0]
    finally:
        connection.close()


VERIFICATION_FAILED_DETAIL = {
    "code": "backup_verification_failed",
    "message": (
        "Не удалось проверить созданную резервную копию, поэтому она не считается надёжной. "
        "Рабочие данные мастерской не изменялись."
    ),
    "next_action": (
        "Повторите создание резервной копии. Если ошибка повторяется, перезапустите приложение."
    ),
}


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
@pytest.mark.parametrize(
    ("outcome", "reason"),
    [("ambiguous", "embedded-operation-missing"), ("definitely_absent", "backup-absent")],
)
def test_a_non_valid_verification_never_returns_201(tmp_path, monkeypatch, outcome, reason):
    """An artifact that did not verify is not a created backup.

    Reporting it as `201` with a pending Journal entry would tell the user their
    data is safely copied when nothing proved that.
    """
    db_path = _workspace(tmp_path, monkeypatch)
    from app.services.backup_audit import BackupAuditService, BackupVerification

    monkeypatch.setattr(
        BackupAuditService, "verify", lambda self, operation: BackupVerification(outcome, reason)
    )
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    body = response.text
    assert "Резервная копия создана" not in body
    assert "журнал действий пока не добавлена" not in body
    assert _backup_events(db_path) == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_a_verifier_that_raises_never_returns_201(tmp_path, monkeypatch):
    db_path = _workspace(tmp_path, monkeypatch)
    from app.services.backup_audit import BackupAuditService

    def exploding_verify(self, operation):
        raise RuntimeError("verifier defect")

    monkeypatch.setattr(BackupAuditService, "verify", exploding_verify)
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    assert _backup_events(db_path) == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_an_unrelated_sqlite_destination_never_returns_201(tmp_path, monkeypatch):
    """A healthy but foreign database at the reserved path is not our backup."""
    db_path = _workspace(tmp_path, monkeypatch)
    import app.services.backup as backup_service
    from app.db.config import DatabaseConfig as Config
    from app.services.database import initialize_database as init

    original_copy = backup_service._copy_sqlite_database

    def copy_unrelated(source, destination):
        # A complete, valid, fully migrated database — that this operation did
        # not create and cannot claim.
        original_copy(source, destination)
        Path(destination).unlink()
        init(Config(path=Path(destination)))

    monkeypatch.setattr(backup_service, "_copy_sqlite_database", copy_unrelated)
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    assert _backup_events(db_path) == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
@pytest.mark.parametrize(
    "columns",
    [
        {"operation_id": "11111111-1111-4111-8111-111111111111"},
        {"primary_filename": "20260801T101500123456Z-other-manual.sqlite"},
        {"audit_action": "export.created"},
    ],
)
def test_a_wrong_or_missing_embedded_operation_never_returns_201(tmp_path, monkeypatch, columns):
    db_path = _workspace(tmp_path, monkeypatch)
    import app.services.backup as backup_service

    original_copy = backup_service._copy_sqlite_database

    def copy_then_tamper(source, destination):
        original_copy(source, destination)
        connection = sqlite3.connect(destination)
        try:
            connection.execute("PRAGMA ignore_check_constraints = ON")
            assignments = ", ".join(f"{name} = ?" for name in columns)
            connection.execute(
                f"UPDATE artifact_audit_operations SET {assignments}", tuple(columns.values())
            )
            connection.commit()
        finally:
            connection.close()

    monkeypatch.setattr(backup_service, "_copy_sqlite_database", copy_then_tamper)
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    assert _backup_events(db_path) == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_an_unverified_artifact_leaves_the_operation_unresolved_and_counted(tmp_path, monkeypatch):
    """Neither audited nor abandoned: left for diagnosis and bounded reconciliation."""
    db_path = _workspace(tmp_path, monkeypatch)
    from app.services.backup_audit import BackupAuditService, BackupVerification

    monkeypatch.setattr(
        BackupAuditService,
        "verify",
        lambda self, operation: BackupVerification("ambiguous", "embedded-operation-missing"),
    )
    client = TestClient(create_app(), raise_server_exceptions=False)
    assert client.post("/api/backups", json={"reason": "manual"}).status_code == 500

    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        statuses = dict(
            connection.execute(
                "SELECT status, COUNT(*) FROM artifact_audit_operations GROUP BY status"
            ).fetchall()
        )
    finally:
        connection.close()
    assert statuses == {"pending_audit": 1}
    assert TestClient(create_app()).get("/api/backups/status").json()["pending_audit_count"] == 1


# --------------------------------------------------------------------------
# Safe user-facing errors
# --------------------------------------------------------------------------

@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_a_source_that_is_a_directory_returns_a_safe_error_without_any_path(tmp_path, monkeypatch):
    """`BackupError` embeds an absolute path; the API must never propagate it."""
    db_path = tmp_path / "cosmetic_workshop.sqlite"
    db_path.mkdir()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)

    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 409
    body = response.text
    assert str(db_path) not in body
    assert str(tmp_path) not in body
    assert "sqlite" not in body.lower()
    assert "BackupError" not in body
    assert response.json()["detail"]["message"] == (
        "Не удалось создать резервную копию. Рабочие данные мастерской не изменялись."
    )


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_a_busy_source_returns_a_safe_distinct_conflict(tmp_path, monkeypatch):
    db_path = _workspace(tmp_path, monkeypatch)
    import app.services.backup as backup_service
    from app.services.backup import BackupBusyError

    def busy(source, destination):
        raise BackupBusyError(f"The database at {db_path} stayed busy")

    monkeypatch.setattr(backup_service, "_copy_sqlite_database", busy)
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post("/api/backups", json={"reason": "manual"})

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "backup_source_busy"
    assert str(db_path) not in response.text
    assert _backup_events(db_path) == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_the_five_create_failure_modes_stay_distinct(tmp_path, monkeypatch):
    """Source, preparation, creation, verification and audit failures differ.

    Collapsing any two of them into one `BackupError`, one `None` or one HTTP
    result is exactly the defect this slice corrects.
    """
    import app.services.backup as backup_service
    from app.services.backup import BackupBusyError
    from app.services.backup_audit import (
        BackupAuditService,
        BackupAuditTrackingUnavailableError,
        BackupFinalization,
        BackupVerification,
    )

    def observe(setup) -> tuple[int, object]:
        monkeypatch.undo()
        db_path = make_database(tmp_path / f"{setup}.sqlite")
        monkeypatch.setenv(DATABASE_PATH_ENV, str(db_path))
        monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
        if setup == "source":
            monkeypatch.setenv(DATABASE_PATH_ENV, str(tmp_path / "absent.sqlite"))
        elif setup == "preparation":
            monkeypatch.setattr(
                BackupAuditService,
                "prepare_operation",
                lambda self, *, primary_filename: (_ for _ in ()).throw(
                    BackupAuditTrackingUnavailableError("nope")
                ),
            )
        elif setup == "creation":
            monkeypatch.setattr(
                backup_service,
                "_copy_sqlite_database",
                lambda source, destination: (_ for _ in ()).throw(BackupBusyError("busy")),
            )
        elif setup == "verification":
            monkeypatch.setattr(
                BackupAuditService,
                "verify",
                lambda self, operation: BackupVerification("ambiguous", "embedded-operation-missing"),
            )
        elif setup == "audit":
            monkeypatch.setattr(
                BackupAuditService,
                "finalize",
                lambda self, operation_id, *, reconciled_after_failure: BackupFinalization(
                    "audit_pending"
                ),
            )
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.post("/api/backups", json={"reason": "manual"})
        payload = response.json()
        marker = payload.get("audit_status") if response.status_code == 201 else (
            payload["detail"].get("code") if isinstance(payload.get("detail"), dict) else "plain-text"
        )
        return response.status_code, marker

    observed = {name: observe(name) for name in
                ("source", "preparation", "creation", "verification", "audit", "recorded")}

    assert observed["source"] == (404, "plain-text")
    assert observed["preparation"] == (500, "artifact_audit_tracking_unavailable")
    assert observed["creation"] == (409, "backup_source_busy")
    assert observed["verification"] == (500, "backup_verification_failed")
    assert observed["audit"] == (201, "pending")
    assert observed["recorded"] == (201, "recorded")
    # Five failure modes, five distinct outcomes — none collapsed into another.
    assert len(set(observed.values())) == 6
