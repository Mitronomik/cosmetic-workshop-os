"""The CR-009 B2 JSON-export HTTP contract, plus the CR-006 create correction.

Three outcomes have to stay distinguishable to a caller, and the whole point of
the accepted decision is that the middle one exists at all:

- the export was created and recorded          -> `201`, `recorded`
- the export was created, the Journal entry was not -> `201`, `pending`
- tracking could not be prepared, so nothing was created -> `500`, no file

The CR-006 half is the other thing pinned here: `POST /api/exports` describes the
export from the creator's exact `ExportResult` and never from a directory
re-scan, and its `reason` is the canonical filename-derived slug rather than the
human manifest reason.
"""

import json
from pathlib import Path
import sqlite3

import pytest

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.paths import USER_DATA_DIR_ENV
from app.main import create_app
from app.repositories.artifact_audit_operations import ArtifactAuditOperationRepository
from app.repositories.audit import AuditLogRepository
from app.services.database import initialize_database
from app.services import export as export_module
from app.services import export_audit as audit_module
from app.services import export_creation as creation_module
from app.services.export_audit import PENDING_AUDIT_MESSAGE
from app.services.startup import initialize_startup

pytestmark = pytest.mark.skipif(
    TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment."
)

TRACKING_FAILURE_DETAIL = {
    "code": "artifact_audit_tracking_unavailable",
    "message": "Не удалось безопасно подготовить создание экспорта. Экспорт не создан.",
    "next_action": "Повторите создание экспорта. Если ошибка повторяется, перезапустите приложение.",
}

# The exact fixed contract for an export that exists but did not verify. Written
# out literally rather than imported, so a change to the constant cannot silently
# change what the user is promised.
VERIFICATION_FAILED_DETAIL = {
    "code": "export_verification_failed",
    "message": (
        "Не удалось проверить созданный экспорт, поэтому он не считается надёжным. "
        "Данные мастерской не изменялись."
    ),
    "next_action": "Повторите создание экспорта. Если ошибка повторяется, перезапустите приложение.",
}


def environment(monkeypatch, tmp_path):
    database_path = tmp_path / "exports-audit.sqlite"
    user_data = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    initialize_database(DatabaseConfig(path=database_path))
    return DatabaseConfig(path=database_path), user_data / "exports", TestClient(create_app())


def audit_rows(config):
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT id, action, entity_type, entity_id, summary, metadata_json FROM audit_logs ORDER BY id"
        ).fetchall()


# --------------------------------------------------------------------------
# Recorded success and the CR-006 create-response correction
# --------------------------------------------------------------------------


def test_a_recorded_creation_returns_201_with_the_additive_audit_fields(monkeypatch, tmp_path):
    config, export_dir, client = environment(monkeypatch, tmp_path)

    response = client.post("/api/exports", json={"reason": "before_import"})

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Экспорт создан."
    assert body["audit_status"] == "recorded"
    assert body["audit_message"] is None
    # Every existing field is preserved.
    assert set(body) == {
        "export",
        "database_path",
        "export_dir",
        "entity_counts",
        "message",
        "audit_status",
        "audit_message",
    }
    assert set(body["export"]) == {"filename", "path", "created_at", "reason", "size_bytes"}
    exported = Path(body["export"]["path"])
    assert exported.exists()
    assert body["export"]["size_bytes"] == exported.stat().st_size
    assert body["export"]["reason"] == "before_import"
    assert body["export_dir"] == str(export_dir)

    rows = audit_rows(config)
    assert [row["action"] for row in rows] == ["export.created"]
    assert json.loads(rows[0]["metadata_json"])["reconciled_after_failure"] is False


def test_the_create_response_reason_is_canonical_not_the_human_manifest_reason(monkeypatch, tmp_path):
    """The exact CR-006 defect: `ExportResult.reason` must never be the API reason."""
    _config, _export_dir, client = environment(monkeypatch, tmp_path)

    response = client.post("/api/exports", json={"reason": "before-update ../unsafe"})

    assert response.status_code == 201
    export = response.json()["export"]
    assert export["reason"] == "before_update_unsafe"
    assert "../" not in export["reason"]
    # The manifest keeps the human reason; CR-005 is not reopened.
    manifest = json.loads(Path(export["path"]).read_text(encoding="utf-8"))["manifest"]
    assert manifest["reason"] == "before-update ../unsafe"
    # Create, list and status agree on the canonical slug for the same file.
    listed = client.get("/api/exports").json()["exports"][0]
    status_latest = client.get("/api/exports/status").json()["latest_export"]
    assert listed["reason"] == status_latest["reason"] == "before_update_unsafe"


def test_the_create_path_never_re_lists_the_export_directory(monkeypatch, tmp_path):
    """A completed operation must not depend on an unrelated secondary read.

    ADR 0014 8.4b/8.6: a directory scan that raises turned a fully successful
    creation into a generic `500`. Removing the scan removes that outcome.
    """
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    calls: list[int] = []

    def forbidden(*_args, **_kwargs):
        calls.append(1)
        raise OSError(13, "the create path must not list the export directory")

    monkeypatch.setattr("app.api.exports.list_export_files", forbidden)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 201
    assert response.json()["audit_status"] == "recorded"
    assert calls == []


def test_the_uniqueness_suffix_never_enters_the_reported_reason(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)

    first = client.post("/api/exports", json={"reason": "before_large_edit"}).json()
    second = client.post("/api/exports", json={"reason": "before_large_edit"}).json()

    assert first["export"]["filename"] != second["export"]["filename"]
    assert first["export"]["reason"] == second["export"]["reason"] == "before_large_edit"


def test_repeated_creates_never_duplicate_an_event(monkeypatch, tmp_path):
    config, _export_dir, client = environment(monkeypatch, tmp_path)

    for _ in range(3):
        assert client.post("/api/exports", json={"reason": "manual"}).status_code == 201

    rows = audit_rows(config)
    assert len(rows) == 3
    assert len({row["entity_id"] for row in rows}) == 3


# --------------------------------------------------------------------------
# Preparation failure — nothing is created
# --------------------------------------------------------------------------


def test_preparation_failure_returns_the_exact_500_and_creates_nothing(monkeypatch, tmp_path):
    config, export_dir, client = environment(monkeypatch, tmp_path)

    def failing_prepare(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger write failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "prepare_operation", failing_prepare)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == TRACKING_FAILURE_DETAIL
    assert not export_dir.exists() or list(export_dir.iterdir()) == []
    assert audit_rows(config) == []
    assert ArtifactAuditOperationRepository(config).count_unresolved("json_export") == 0


def test_the_preparation_failure_detail_leaks_no_technical_information(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)

    def failing_prepare(*_args, **_kwargs):
        raise sqlite3.OperationalError("no such table: artifact_audit_operations")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "prepare_operation", failing_prepare)

    detail = json.dumps(client.post("/api/exports", json={"reason": "manual"}).json(), ensure_ascii=False)

    for forbidden in ["sqlite", "SQL", "artifact_audit_operations", "Traceback", "no such table"]:
        assert forbidden not in detail


def test_an_unreadable_ledger_during_identity_reservation_is_a_preparation_failure(monkeypatch, tmp_path):
    config, export_dir, client = environment(monkeypatch, tmp_path)

    def failing_identity(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "has_active_identity", failing_identity)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == TRACKING_FAILURE_DETAIL
    assert not export_dir.exists() or list(export_dir.iterdir()) == []
    assert audit_rows(config) == []


def test_an_unexpected_defect_reserving_an_identity_is_not_disguised_as_tracking_unavailable(monkeypatch, tmp_path):
    """A programming defect must not be dressed up as a recoverable condition."""
    _config, _export_dir, client = environment(monkeypatch, tmp_path)

    def defective(*_args, **_kwargs):
        raise TypeError("injected programming defect")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "has_active_identity", defective)

    with pytest.raises(TypeError):
        client.post("/api/exports", json={"reason": "manual"})


def test_existing_source_error_precedence_is_unchanged(monkeypatch, tmp_path):
    """A missing database still returns `404`, and leaves no prepared operation."""
    database_path = tmp_path / "missing.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.delenv(USER_DATA_DIR_ENV, raising=False)
    client = TestClient(create_app())

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 404
    assert response.json()["detail"].startswith("База данных не найдена.")
    assert not database_path.exists()
    assert not (tmp_path / "exports").exists()


# --------------------------------------------------------------------------
# Pending partial success
# --------------------------------------------------------------------------


def failing_journal(monkeypatch):
    """Break only the AuditLog insert, and return how to repair just that.

    `monkeypatch.undo()` would also revert the environment variables this
    module's `environment()` set, silently pointing a later assertion at the
    developer's real database. The restore callable is deliberately narrow.
    """
    original = AuditLogRepository.create_log

    def failing_create_log(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected AuditLog failure")

    monkeypatch.setattr(AuditLogRepository, "create_log", failing_create_log)
    return lambda: monkeypatch.setattr(AuditLogRepository, "create_log", original)


def test_a_failed_journal_write_still_returns_201_with_the_exact_pending_warning(monkeypatch, tmp_path):
    config, _export_dir, client = environment(monkeypatch, tmp_path)
    failing_journal(monkeypatch)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Экспорт создан."
    assert body["audit_status"] == "pending"
    assert body["audit_message"] == PENDING_AUDIT_MESSAGE
    assert body["audit_message"] == (
        "Экспорт создан, но запись в журнал действий пока не добавлена. "
        "Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта."
    )

    # The export is the authoritative result: present, listable, unchanged.
    exported = Path(body["export"]["path"])
    assert exported.exists()
    assert body["export"]["size_bytes"] == exported.stat().st_size
    assert audit_rows(config) == []
    assert ArtifactAuditOperationRepository(config).count_unresolved("json_export") == 1


def test_a_pending_export_stays_listable_and_byte_identical(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    failing_journal(monkeypatch)

    body = client.post("/api/exports", json={"reason": "manual"}).json()
    exported = Path(body["export"]["path"])
    content = exported.read_bytes()

    listed = client.get("/api/exports").json()["exports"]
    status = client.get("/api/exports/status").json()

    assert [item["filename"] for item in listed] == [body["export"]["filename"]]
    assert status["export_count"] == 1
    assert status["pending_audit_count"] == 1
    assert exported.read_bytes() == content


def test_a_pending_response_is_not_a_failure_and_leaks_nothing(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    failing_journal(monkeypatch)

    warning = client.post("/api/exports", json={"reason": "manual"}).json()["audit_message"]

    for forbidden in ["sqlite", "SQL", "operation_id", ".json", "/", "artifact_audit_operations"]:
        assert forbidden not in warning
    assert "не создан" not in warning


def test_a_later_reconciliation_completes_the_pending_event_exactly_once(monkeypatch, tmp_path):
    config, _export_dir, client = environment(monkeypatch, tmp_path)
    restore_journal = failing_journal(monkeypatch)
    first = client.post("/api/exports", json={"reason": "manual"}).json()
    assert first["audit_status"] == "pending"
    restore_journal()

    # The next create runs one bounded pre-create reconciliation pass first.
    second = client.post("/api/exports", json={"reason": "manual"}).json()

    assert second["audit_status"] == "recorded"
    rows = audit_rows(config)
    assert len(rows) == 2
    recovered = [row for row in rows if json.loads(row["metadata_json"])["reconciled_after_failure"] is True]
    assert len(recovered) == 1
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 0


def test_a_completed_export_survives_an_unexpected_defect_in_finalization(monkeypatch, tmp_path):
    """A defect that prevented verification must not be reported as a success.

    The name is the merged baseline's and is kept deliberately: what this test
    protects — the written export survives an unexpected finalization defect and
    the raw defect never reaches the user — is unchanged. What changed is the
    *conclusion*. The baseline asserted `201` with `audit_status: pending`, which
    presented an unverified export as created; it is now the fixed safe `500`,
    with the file-preservation and no-event assertions preserved verbatim.

    The written file is still never deleted and the raw defect never reaches the
    user — but the export was never verified, so it is not an authoritative
    result. Returning `201 pending` here would tell the user their export exists
    and is trustworthy when nothing established that.
    """
    config, export_dir, client = environment(monkeypatch, tmp_path)

    def defective(*_args, **_kwargs):
        raise TypeError("injected programming defect")

    monkeypatch.setattr(audit_module.ExportAuditService, "verify", defective)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    # The file is preserved: this operation could not prove it owns the path, so
    # deleting it could destroy a file belonging to something else.
    assert len(list(export_dir.glob("*.json"))) == 1
    assert audit_rows(config) == []
    # Unresolved and counted, so the standing warning still surfaces it.
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 1


def test_an_export_is_never_deleted_because_the_journal_write_failed(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    failing_journal(monkeypatch)

    exported = Path(client.post("/api/exports", json={"reason": "manual"}).json()["export"]["path"])

    assert exported.exists()
    payload = json.loads(exported.read_text(encoding="utf-8"))
    assert set(payload) == {"manifest", "data"}


# --------------------------------------------------------------------------
# Status: read-only, exact, never a fabricated zero
# --------------------------------------------------------------------------


def test_the_status_response_keeps_every_existing_field(monkeypatch, tmp_path):
    _config, export_dir, client = environment(monkeypatch, tmp_path)
    client.post("/api/exports", json={"reason": "manual"})

    body = client.get("/api/exports/status").json()

    assert set(body) == {
        "database_path",
        "database_exists",
        "database_size_bytes",
        "export_dir",
        "export_dir_exists",
        "export_count",
        "latest_export",
        "pending_audit_count",
    }
    assert body["export_dir"] == str(export_dir)
    assert body["export_count"] == 1
    assert body["pending_audit_count"] == 0


def test_status_reports_the_exact_positive_count_of_unresolved_operations(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    restore_journal = failing_journal(monkeypatch)
    client.post("/api/exports", json={"reason": "manual"})
    client.post("/api/exports", json={"reason": "manual"})
    restore_journal()

    assert client.get("/api/exports/status").json()["pending_audit_count"] == 2


def test_the_pending_audit_count_excludes_other_kinds_audited_and_abandoned(monkeypatch, tmp_path):
    config, _export_dir, client = environment(monkeypatch, tmp_path)
    repository = ArtifactAuditOperationRepository(config)
    client.post("/api/exports", json={"reason": "recorded_one"})
    repository.prepare_operation(
        operation_id="11111111-2222-3333-4444-555555555555",
        artifact_kind="report_document",
        primary_filename="workshop-overview-20260801-101112.md",
        companion_filename="workshop-overview-20260801-101112.json",
        audit_action="report_document.created",
    )
    repository.prepare_operation(
        operation_id="66666666-7777-8888-9999-aaaaaaaaaaaa",
        artifact_kind="manual_backup",
        primary_filename="20260801T101112131415Z-cosmetic_workshop-backup-manual.sqlite",
        companion_filename=None,
        audit_action="backup.created",
    )
    abandoned = "cccccccc-dddd-eeee-ffff-000000000000"
    repository.prepare_operation(
        operation_id=abandoned,
        artifact_kind="json_export",
        primary_filename="20250101T000000000000Z-cosmetic_workshop-export-gone.json",
        companion_filename=None,
        audit_action="export.created",
    )
    repository.mark_abandoned(abandoned)

    assert client.get("/api/exports/status").json()["pending_audit_count"] == 0


def test_status_never_reports_a_fabricated_zero_when_the_ledger_cannot_be_read(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    client.post("/api/exports", json={"reason": "manual"})

    def failing_count(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "count_unresolved", failing_count)

    response = client.get("/api/exports/status")

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "Не удалось прочитать сведения об экспортах. Данные мастерской не изменялись."
    for forbidden in ["sqlite", "SQL", "artifact_audit_operations", "Traceback"]:
        assert forbidden not in detail


def test_a_filesystem_failure_opening_the_ledger_is_also_safely_translated(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)

    def failing_count(*_args, **_kwargs):
        raise OSError(13, "injected permission failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "count_unresolved", failing_count)

    assert client.get("/api/exports/status").status_code == 500


@pytest.mark.parametrize("defect", [TypeError, AttributeError, ValueError])
def test_an_unexpected_programming_defect_is_not_disguised_as_ledger_unavailability(monkeypatch, tmp_path, defect):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)

    def defective(*_args, **_kwargs):
        raise defect("injected programming defect")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "count_unresolved", defective)

    with pytest.raises(defect):
        client.get("/api/exports/status")


def test_status_and_list_never_reconcile_audit_or_mutate(monkeypatch, tmp_path):
    config, _export_dir, client = environment(monkeypatch, tmp_path)
    restore_journal = failing_journal(monkeypatch)
    client.post("/api/exports", json={"reason": "manual"})
    restore_journal()

    def forbidden(*_args, **_kwargs):  # pragma: no cover - the assertion is that this never runs
        raise AssertionError("A read endpoint must never reconcile.")

    monkeypatch.setattr(audit_module.ExportAuditService, "reconcile", forbidden)

    assert client.get("/api/exports/status").status_code == 200
    assert client.get("/api/exports").status_code == 200
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 1
    assert audit_rows(config) == []
    assert ArtifactAuditOperationRepository(config).count_unresolved("json_export") == 1


def test_a_status_read_never_creates_the_database_or_the_export_directory(monkeypatch, tmp_path):
    """A GET that creates a database file is not a read."""
    database_path = tmp_path / "data" / "cosmetic_workshop.sqlite"
    user_data = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    client = TestClient(create_app())

    body = client.get("/api/exports/status").json()

    assert body["database_exists"] is False
    # No database means no ledger, so this zero is a conclusive read.
    assert body["pending_audit_count"] == 0
    assert not database_path.exists()
    assert not (user_data / "exports").exists()


# --------------------------------------------------------------------------
# Journal privacy and startup ordering
# --------------------------------------------------------------------------


def test_the_journal_shows_safe_russian_wording_and_no_internal_identity(monkeypatch, tmp_path):
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    created = client.post("/api/exports", json={"reason": "before-update ../unsafe"}).json()

    entries = client.get("/api/audit-logs").json()["items"]
    entry = next(item for item in entries if item["action"] == "export.created")

    assert entry["display_summary"] == "Экспорт создан"
    serialized = json.dumps(entries, ensure_ascii=False)
    for forbidden in [
        created["export"]["filename"],
        created["export"]["path"],
        "before_update_unsafe",
        "before-update ../unsafe",
        "operation_id",
        "metadata",
    ]:
        assert forbidden not in serialized
    # The read API keeps excluding raw summary, metadata and entity ID.
    assert "summary" not in entry or entry.get("summary") != "JSON export created"


def test_startup_reconciliation_completes_a_pending_event_after_migrations(monkeypatch, tmp_path):
    config, _export_dir, client = environment(monkeypatch, tmp_path)
    restore_journal = failing_journal(monkeypatch)
    body = client.post("/api/exports", json={"reason": "manual"}).json()
    assert body["audit_status"] == "pending"
    restore_journal()

    result = initialize_startup("development")

    assert result.json_export_audit_reconciliation.audited == 1
    rows = audit_rows(config)
    assert len(rows) == 1
    assert json.loads(rows[0]["metadata_json"])["reconciled_after_failure"] is True
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 0
    assert Path(body["export"]["path"]).exists()


def test_startup_reconciles_report_documents_and_exports_in_a_fixed_order(monkeypatch, tmp_path):
    _config, _export_dir, _client = environment(monkeypatch, tmp_path)
    order: list[str] = []

    monkeypatch.setattr(
        "app.services.startup.initialize_database", lambda *_a, **_k: (order.append("migrations"), [])[1]
    )
    monkeypatch.setattr(
        "app.services.startup.reconcile_report_documents",
        lambda *_a, **_k: order.append("report_documents"),
    )
    monkeypatch.setattr(
        "app.services.startup.reconcile_json_exports", lambda *_a, **_k: order.append("json_exports")
    )

    initialize_startup("development")

    assert order == ["migrations", "report_documents", "json_exports"]


def test_startup_completes_even_when_export_reconciliation_fails(monkeypatch, tmp_path):
    _config, _export_dir, _client = environment(monkeypatch, tmp_path)

    def failing_list(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "list_unresolved", failing_list)

    result = initialize_startup("development")

    assert result.json_export_audit_reconciliation.failed == 1
    assert result.database_path.exists()


def test_startup_reconciliation_does_not_backfill_legacy_exports(monkeypatch, tmp_path):
    config, export_dir, _client = environment(monkeypatch, tmp_path)
    export_dir.mkdir(parents=True, exist_ok=True)
    legacy = export_dir / "20250101T000000000000Z-cosmetic_workshop-export-manual.json"
    legacy.write_text(
        json.dumps({"manifest": {"export_schema_version": 1, "reason": "manual", "source": "cosmetic-workshop-os", "tables": {}}, "data": {}}),
        encoding="utf-8",
    )
    before = legacy.read_bytes()

    result = initialize_startup("development")

    assert result.json_export_audit_reconciliation.examined == 0
    assert audit_rows(config) == []
    assert legacy.read_bytes() == before


def test_startup_and_the_api_resolve_the_same_export_directory(monkeypatch, tmp_path):
    config, export_dir, client = environment(monkeypatch, tmp_path)

    assert export_module.resolve_export_dir(config) == export_dir
    assert client.get("/api/exports/status").json()["export_dir"] == str(export_dir)


def test_the_create_orchestration_uses_one_filename_selection_algorithm(monkeypatch, tmp_path):
    """The reserved name and the written name must be the same name."""
    _config, _export_dir, client = environment(monkeypatch, tmp_path)
    reserved: list[str] = []
    real_reserve = creation_module.reserve_export_path

    def tracking_reserve(*args, **kwargs):
        path = real_reserve(*args, **kwargs)
        reserved.append(path.name)
        return path

    monkeypatch.setattr(creation_module, "reserve_export_path", tracking_reserve)

    body = client.post("/api/exports", json={"reason": "manual"}).json()

    assert reserved == [body["export"]["filename"]]
    operation = ArtifactAuditOperationRepository(_config).list_unresolved("json_export")
    assert operation == []


# --------------------------------------------------------------------------
# An unverified export is never a created export
#
# The correction this slice makes. `POST /api/exports` previously mapped every
# non-recorded finalization to `201` with `audit_status: pending`, so an export
# that failed mandatory verification was presented to the user as created with
# only its Journal entry outstanding. Verification failure and Journal failure
# are now different answers, and only the second is a success.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", ["ambiguous", "definitely_absent"])
def test_a_non_valid_verification_never_returns_201(monkeypatch, tmp_path, outcome):
    config, export_dir, client = environment(monkeypatch, tmp_path)
    monkeypatch.setattr(
        audit_module.ExportAuditService,
        "verify",
        lambda self, operation: audit_module.ExportVerification(outcome, "injected"),
    )

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code != 201
    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == VERIFICATION_FAILED_DETAIL
    # Not a success in any form: no create message, and no pending-Journal pair.
    serialized = json.dumps(body, ensure_ascii=False)
    assert "Экспорт создан." not in serialized
    assert "audit_status" not in body
    assert PENDING_AUDIT_MESSAGE not in serialized
    # No event, file preserved, operation unresolved and counted.
    assert audit_rows(config) == []
    assert len(list(export_dir.glob("*.json"))) == 1
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 1


def test_a_real_corruption_between_write_and_finalization_never_returns_201(monkeypatch, tmp_path):
    """A genuine verifier verdict, not an injected outcome, reaches the same result."""
    config, export_dir, client = environment(monkeypatch, tmp_path)
    original = audit_module.ExportAuditService.finalize

    def corrupt_then_finalize(self, operation_id, *, reconciled_after_failure):
        for path in export_dir.glob("*.json"):
            path.write_text("{not json", encoding="utf-8")
        return original(self, operation_id, reconciled_after_failure=reconciled_after_failure)

    monkeypatch.setattr(audit_module.ExportAuditService, "finalize", corrupt_then_finalize)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    assert audit_rows(config) == []
    assert len(list(export_dir.glob("*.json"))) == 1


def test_the_verification_error_leaks_no_filename_path_reason_or_sqlite_detail(monkeypatch, tmp_path):
    config, export_dir, client = environment(monkeypatch, tmp_path)
    captured = {}

    def leaky_verify(self, operation):
        captured["name"] = operation.primary_filename
        captured["operation_id"] = operation.operation_id
        raise sqlite3.OperationalError("database disk image is malformed")

    monkeypatch.setattr(audit_module.ExportAuditService, "verify", leaky_verify)

    response = client.post("/api/exports", json={"reason": "квартальная выгрузка"})

    assert response.status_code == 500
    serialized = json.dumps(response.json(), ensure_ascii=False)
    for forbidden in [
        captured["name"],
        captured["operation_id"],
        str(export_dir),
        "cosmetic_workshop",
        "квартальная выгрузка",
        "kvartalnaya",
        "database disk image is malformed",
        "sqlite",
        "Traceback",
        "ingredients",
        "export_schema_version",
    ]:
        assert forbidden not in serialized
    assert set(response.json()["detail"]) == {"code", "message", "next_action"}


def test_a_transient_verifier_fault_is_finalized_once_by_a_later_reconciliation(monkeypatch, tmp_path):
    """The refused create leaves a recoverable operation, not a lost export."""
    config, export_dir, client = environment(monkeypatch, tmp_path)
    original_verify = audit_module.ExportAuditService.verify

    def defective(*_args, **_kwargs):
        raise TypeError("injected transient verifier fault")

    monkeypatch.setattr(audit_module.ExportAuditService, "verify", defective)
    assert client.post("/api/exports", json={"reason": "manual"}).status_code == 500
    assert audit_rows(config) == []
    monkeypatch.setattr(audit_module.ExportAuditService, "verify", original_verify)

    # The next create runs one bounded pre-create reconciliation pass first.
    second = client.post("/api/exports", json={"reason": "manual"})

    assert second.status_code == 201
    rows = audit_rows(config)
    assert [row["action"] for row in rows] == ["export.created", "export.created"]
    recovered = [row for row in rows if json.loads(row["metadata_json"])["reconciled_after_failure"] is True]
    assert len(recovered) == 1
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 0


def test_a_verified_export_with_a_failed_journal_write_is_still_201_pending(monkeypatch, tmp_path):
    """The other half of the correction: a Journal failure is still a success."""
    config, export_dir, client = environment(monkeypatch, tmp_path)
    failing_journal(monkeypatch)

    response = client.post("/api/exports", json={"reason": "manual"})

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Экспорт создан."
    assert body["audit_status"] == "pending"
    assert body["audit_message"] == PENDING_AUDIT_MESSAGE
    assert Path(body["export"]["path"]).exists()
    assert audit_rows(config) == []
    assert client.get("/api/exports/status").json()["pending_audit_count"] == 1
