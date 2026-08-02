"""The CR-009 B1 report-document HTTP contract and startup ordering.

Three outcomes have to stay distinguishable to a caller, and the whole point of
the accepted decision is that the middle one exists at all:

- the document was created and recorded  -> `201`, `recorded`
- the document was created, the Journal entry was not -> `201`, `pending`
- tracking could not be prepared, so nothing was created -> `500`, no files

These tests also pin the read-only half: status, list, download and Journal GETs
must never reconcile, audit or mutate anything.
"""

from datetime import datetime
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
from app.services import report_document_audit as audit_module
from app.services import report_documents as report_documents_module
from app.services.report_document_audit import (
    PENDING_AUDIT_MESSAGE,
    ReportDocumentAuditTrackingUnavailableError,
)

pytestmark = pytest.mark.skipif(
    TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment."
)

TRACKING_FAILURE_DETAIL = {
    "code": "artifact_audit_tracking_unavailable",
    "message": "Не удалось безопасно подготовить создание документа. Документ не создан.",
    "next_action": "Повторите создание документа. Если ошибка повторяется, перезапустите приложение.",
}

# The exact fixed contract for a pair that exists but did not verify. Written out
# literally rather than imported, so a change to the constant cannot silently
# change what the user is promised.
VERIFICATION_FAILED_DETAIL = {
    "code": "report_document_verification_failed",
    "message": (
        "Не удалось проверить созданный документ отчета, поэтому он не считается надёжным. "
        "Данные мастерской не изменялись."
    ),
    "next_action": "Повторите создание документа. Если ошибка повторяется, перезапустите приложение.",
}


def environment(monkeypatch, tmp_path):
    database_path = tmp_path / "report-documents-audit.sqlite"
    user_data = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    initialize_database(DatabaseConfig(path=database_path))
    documents_dir = user_data / "exports" / "report-documents"
    return DatabaseConfig(path=database_path), documents_dir, TestClient(create_app())


def user_mode_environment(monkeypatch, tmp_path):
    """An environment whose API database is the one user-mode startup will open.

    User mode resolves its own path under the user-data directory, so a test that
    creates documents through the API and then restarts must point both at the
    same file — otherwise startup reconciles an empty database and proves nothing.
    """
    user_data = tmp_path / "user-data"
    database_path = user_data / "data" / "cosmetic_workshop.sqlite"
    database_path.parent.mkdir(parents=True)
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    initialize_database(DatabaseConfig(path=database_path))
    return DatabaseConfig(path=database_path), user_data / "exports" / "report-documents", TestClient(create_app())


def enable_fake_pdf(monkeypatch):
    monkeypatch.setattr(report_documents_module, "_is_pdf_generation_available", lambda: True)

    def fake_write_pdf_exclusive(path: Path, lines: list[str], *, created_at: datetime) -> None:
        with path.open("xb") as file:
            file.write(b"%PDF-1.4\n% fake test pdf\n%%EOF\n")

    monkeypatch.setattr(report_documents_module, "_write_pdf_exclusive", fake_write_pdf_exclusive)


def audit_actions(config):
    with sqlite3.connect(config.path) as connection:
        return [row[0] for row in connection.execute("SELECT action FROM audit_logs ORDER BY id")]


def operations(config):
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT operation_id, status, audit_log_id, primary_filename, companion_filename"
            " FROM artifact_audit_operations ORDER BY created_at, operation_id"
        ).fetchall()


# --------------------------------------------------------------------------
# Recorded success
# --------------------------------------------------------------------------

def test_a_recorded_creation_returns_201_with_the_additive_audit_fields(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 201
    body = response.json()
    # Existing fields are preserved exactly.
    assert body["message"] == "Документ отчета создан."
    document = body["document"]
    assert document["id"].startswith("workshop-overview-")
    assert document["format"] == "markdown"
    assert document["filename"].endswith(".md")
    assert document["metadata_filename"].endswith(".json")
    # Additive fields.
    assert body["audit_status"] == "recorded"
    assert body["audit_message"] is None

    assert (documents_dir / document["filename"]).exists()
    assert (documents_dir / document["metadata_filename"]).exists()
    assert audit_actions(config) == ["report_document.created"]
    rows = operations(config)
    assert len(rows) == 1
    assert rows[0]["status"] == "audited"
    assert rows[0]["audit_log_id"] is not None
    assert rows[0]["primary_filename"] == document["filename"]
    assert rows[0]["companion_filename"] == document["metadata_filename"]
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 0


def test_a_recorded_pdf_creation_uses_the_same_contract(monkeypatch, tmp_path):
    config, _documents_dir, client = environment(monkeypatch, tmp_path)
    enable_fake_pdf(monkeypatch)

    response = client.post("/api/report-documents/reports/overview", json={"format": "pdf"})

    assert response.status_code == 201
    assert response.json()["audit_status"] == "recorded"
    assert response.json()["audit_message"] is None
    assert audit_actions(config) == ["report_document.created"]


# --------------------------------------------------------------------------
# Preparation failure
# --------------------------------------------------------------------------

def test_preparation_failure_returns_the_exact_500_and_creates_nothing(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_prepare(*_args, **_kwargs):
        raise sqlite3.OperationalError("ledger unavailable")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "prepare_operation", failing_prepare)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 500
    assert response.json()["detail"] == TRACKING_FAILURE_DETAIL
    # No artifact, no sidecar, no AuditLog row, no committed ledger row.
    assert not documents_dir.exists() or list(documents_dir.iterdir()) == []
    assert audit_actions(config) == []
    assert operations(config) == []
    assert client.get("/api/report-documents").json()["total"] == 0
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 0


def test_the_preparation_failure_detail_leaks_no_technical_information(monkeypatch, tmp_path):
    _config, _documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_prepare(*_args, **_kwargs):
        raise sqlite3.OperationalError("no such table: artifact_audit_operations")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "prepare_operation", failing_prepare)

    body = client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).text

    for forbidden in ("no such table", "sqlite", "SQLite", "Traceback", "INSERT", "artifact_audit_operations"):
        assert forbidden not in body


def test_an_unreadable_ledger_during_identity_reservation_is_a_preparation_failure(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_identity(*_args, **_kwargs):
        raise sqlite3.OperationalError("ledger unreadable")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "has_active_identity", failing_identity)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 500
    assert response.json()["detail"] == TRACKING_FAILURE_DETAIL
    assert not documents_dir.exists() or list(documents_dir.iterdir()) == []
    assert audit_actions(config) == []
    assert operations(config) == []


def test_existing_validation_precedence_is_unchanged(monkeypatch, tmp_path):
    """A rejected format is still rejected before anything is prepared."""
    config, _documents_dir, client = environment(monkeypatch, tmp_path)

    docx = client.post("/api/report-documents/reports/overview", json={"format": "docx"})

    assert docx.status_code == 422
    assert "DOCX пока не поддерживается" in docx.json()["detail"]
    assert operations(config) == []
    assert audit_actions(config) == []


# --------------------------------------------------------------------------
# Artifact creation failure
# --------------------------------------------------------------------------

def test_a_document_write_failure_keeps_its_existing_error_and_writes_no_success_event(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_write(path: Path, text: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(report_documents_module, "_write_text_exclusive", failing_write)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Не удалось создать документ отчета. Данные мастерской не изменялись."
    assert list(documents_dir.iterdir()) == []
    assert audit_actions(config) == []
    # The prepared operation is resolved rather than left to be reconciled.
    rows = operations(config)
    assert len(rows) == 1
    assert rows[0]["status"] == "abandoned"
    assert rows[0]["audit_log_id"] is None
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 0


# --------------------------------------------------------------------------
# Pending success
# --------------------------------------------------------------------------

def fail_audit_insert(monkeypatch):
    def failing_create_log(*_args, **_kwargs):
        raise sqlite3.OperationalError("audit insert refused")

    monkeypatch.setattr(AuditLogRepository, "create_log", failing_create_log)


def test_a_failed_journal_write_still_returns_201_with_the_exact_pending_warning(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Документ отчета создан."
    assert body["audit_status"] == "pending"
    assert body["audit_message"] == PENDING_AUDIT_MESSAGE
    document = body["document"]

    # The artifact is authoritative: both files survive and stay reachable.
    assert (documents_dir / document["filename"]).exists()
    assert (documents_dir / document["metadata_filename"]).exists()
    listing = client.get("/api/report-documents").json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == document["id"]
    download = client.get(f"/api/report-documents/{document['id']}/download")
    assert download.status_code == 200
    assert download.text.startswith("# Сводка мастерской")

    # The missing event is remembered rather than forgotten.
    assert audit_actions(config) == []
    rows = operations(config)
    assert len(rows) == 1
    assert rows[0]["status"] == "pending_audit"
    assert rows[0]["audit_log_id"] is None
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 1


def test_a_pending_response_is_not_a_failure_and_leaks_nothing(monkeypatch, tmp_path):
    _config, _documents_dir, client = environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code not in (409, 500)
    for forbidden in ("sqlite", "SQLite", "Traceback", "artifact_audit_operations", "operation_id", "INSERT"):
        assert forbidden not in response.text


def test_a_later_reconciliation_completes_the_pending_event_exactly_once(monkeypatch, tmp_path):
    """The second document's pre-create pass finishes the first one's event."""
    config, _documents_dir, client = environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)
    first = client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).json()
    assert first["audit_status"] == "pending"

    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))

    second = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert second.status_code == 201
    assert second.json()["audit_status"] == "recorded"
    # One event for the recovered document, one for the new one — never three.
    assert audit_actions(config) == ["report_document.created", "report_document.created"]
    rows = operations(config)
    assert [row["status"] for row in rows] == ["audited", "audited"]
    assert len({row["audit_log_id"] for row in rows}) == 2
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 0


def test_repeated_creates_never_duplicate_an_event(monkeypatch, tmp_path):
    config, _documents_dir, client = environment(monkeypatch, tmp_path)

    for _ in range(3):
        assert client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).status_code == 201

    assert audit_actions(config) == ["report_document.created"] * 3
    rows = operations(config)
    assert len(rows) == 3
    assert {row["status"] for row in rows} == {"audited"}
    assert len({row["audit_log_id"] for row in rows}) == 3
    assert len({row["operation_id"] for row in rows}) == 3


# --------------------------------------------------------------------------
# Read-only endpoints
# --------------------------------------------------------------------------

def test_status_list_download_and_journal_gets_never_reconcile_or_mutate(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)
    document = client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).json()["document"]
    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))

    document_path = documents_dir / document["filename"]
    sidecar_path = documents_dir / document["metadata_filename"]
    before_bytes = (document_path.read_bytes(), sidecar_path.read_bytes())
    before_rows = [tuple(row) for row in operations(config)]

    def forbidden(*_args, **_kwargs):
        raise AssertionError("A read-only endpoint must not reconcile.")

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "reconcile", forbidden)

    for _ in range(3):
        assert client.get("/api/report-documents/status").status_code == 200
        assert client.get("/api/report-documents").status_code == 200
        assert client.get(f"/api/report-documents/{document['id']}/download").status_code == 200
        assert client.get("/api/audit-logs").status_code == 200

    # Nothing moved: no event, no ledger transition, no changed bytes.
    assert audit_actions(config) == []
    assert [tuple(row) for row in operations(config)] == before_rows
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before_bytes
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 1


def test_the_status_response_keeps_every_existing_field(monkeypatch, tmp_path):
    _config, _documents_dir, client = environment(monkeypatch, tmp_path)

    body = client.get("/api/report-documents/status").json()

    assert set(body) == {
        "documents_dir",
        "available_formats",
        "available_document_types",
        "can_create",
        "documents_count",
        "message",
        "pending_audit_count",
    }
    assert body["available_document_types"] == ["workshop_overview"]
    assert body["can_create"] is True
    assert body["documents_count"] == 0
    assert "вручную" in body["message"]
    assert body["pending_audit_count"] == 0


def test_status_never_reports_a_fabricated_zero_when_the_ledger_cannot_be_read(monkeypatch, tmp_path):
    """An unreadable ledger is an error, not a count of zero.

    `pending_audit_count: 0` is a factual claim that nothing is awaiting a
    Journal entry, and the frontend acts on it by clearing a standing warning.
    Publishing it when the ledger could not actually be read would convert "I
    don't know" into "definitely nothing" and silently erase a true warning —
    the exact audit gap CR-009 exists to prevent.

    The correct production answer to an unmigrated database is that the launcher
    migrates the database it is about to serve, which
    `launcher/tests/test_runtime_database_continuity.py` proves.
    """
    config, _documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_count(*_args, **_kwargs):
        raise sqlite3.OperationalError("no such table: artifact_audit_operations")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "count_unresolved", failing_count)

    response = client.get("/api/report-documents/status")

    assert response.status_code == 500
    assert "pending_audit_count" not in response.text
    # A safe fixed Russian message, with no technical detail behind it.
    assert response.json()["detail"] == "Не удалось прочитать сведения о документах отчетов. Данные мастерской не изменялись."
    for forbidden in ("no such table", "sqlite", "SQLite", "Traceback", "SELECT", "COUNT(", "artifact_audit_operations"):
        assert forbidden not in response.text, forbidden
    # Still read-only: nothing was reconciled, audited or mutated.
    assert audit_actions(config) == []
    assert operations(config) == []


def test_a_filesystem_failure_opening_the_ledger_is_also_safely_translated(monkeypatch, tmp_path):
    """`OSError` is a real path here, not a hypothetical one.

    Opening the database goes through `ensure_database_parent`, whose `mkdir`
    raises `OSError` when the user-data directory cannot be created — a full or
    read-only volume, for instance. It must reach the user as the same safe
    availability answer as a SQLite failure.
    """
    config, _documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_count(*_args, **_kwargs):
        raise PermissionError("[Errno 13] Permission denied: '/private/data'")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "count_unresolved", failing_count)

    response = client.get("/api/report-documents/status")

    assert response.status_code == 500
    assert response.json()["detail"] == "Не удалось прочитать сведения о документах отчетов. Данные мастерской не изменялись."
    assert "pending_audit_count" not in response.text
    for forbidden in ("Permission denied", "Errno", "/private/data", "Traceback"):
        assert forbidden not in response.text, forbidden
    assert audit_actions(config) == []
    assert operations(config) == []


@pytest.mark.parametrize(
    "defect",
    [
        TypeError("programming defect"),
        AttributeError("programming defect"),
        RuntimeError("programming defect"),
        AssertionError("programming defect"),
    ],
)
def test_an_unexpected_programming_defect_is_not_disguised_as_ledger_unavailability(tmp_path, defect):
    """A bug must not be reported as the known "ledger unavailable" condition.

    The safe status error means something specific and recoverable: the ledger
    could not be read, try again. Translating a `TypeError` into it would hand
    the user a reassuring Russian sentence about a problem they do not have,
    while the real defect disappears without a trace and without a stack.

    Asserted at the service layer, where the distinction is observable. At the
    API layer such a defect becomes the framework's generic 500 — which is
    correct, and is deliberately *not* the known availability response.
    """
    from app.db.config import DatabaseConfig
    from app.services.report_documents import (
        ReportDocumentService,
        ReportDocumentStatusUnavailableError,
    )

    database_path = tmp_path / "defect.sqlite"
    initialize_database(DatabaseConfig(path=database_path))
    service = ReportDocumentService(DatabaseConfig(path=database_path), documents_dir=tmp_path / "documents")

    def raising_pending_count():
        raise defect

    service.audit_service.pending_count = raising_pending_count

    with pytest.raises(type(defect)) as raised:
        service.status()

    # The original defect propagates unchanged, not wrapped in the safe error.
    assert raised.value is defect
    assert not isinstance(raised.value, ReportDocumentStatusUnavailableError)
    assert "Не удалось прочитать сведения" not in str(raised.value)


def test_an_unexpected_defect_reserving_an_identity_is_not_disguised_as_tracking_unavailable(monkeypatch, tmp_path):
    """The create path must not dress a bug up as "tracking unavailable" either.

    Identity reservation runs before either file is written, so letting an
    unexpected defect propagate costs nothing: the create fails with nothing on
    disk either way. What it buys is that a real bug is not reported to the user
    as the specific, recoverable condition it is not.
    """
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    def defective_identity(*_args, **_kwargs):
        raise TypeError("programming defect")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "has_active_identity", defective_identity)

    # The defect surfaces as itself rather than as the tracking-unavailable
    # contract. `TestClient` re-raises server exceptions, which is exactly the
    # observable difference: a translated error would have returned a response.
    with pytest.raises(TypeError, match="programming defect") as raised:
        client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert not isinstance(raised.value, ReportDocumentAuditTrackingUnavailableError)
    assert "Не удалось безопасно подготовить создание документа" not in str(raised.value)
    # Still nothing created, and nothing recorded.
    assert not documents_dir.exists() or list(documents_dir.iterdir()) == []
    assert audit_actions(config) == []
    assert operations(config) == []


def test_a_completed_document_survives_an_unexpected_defect_in_finalization(monkeypatch, tmp_path):
    """After both files exist, no failure may become a total failure.

    This pins the deliberately broad protection on the post-artifact path. A
    defect raised while finalizing must degrade to `pending` — HTTP 201, artifact
    intact, operation counted — never an HTTP 500 that tells the user their
    document was not created when it plainly was.
    """
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    def defective_finalizer(*_args, **_kwargs):
        raise RuntimeError("programming defect during finalization")

    monkeypatch.setattr(
        audit_module.ReportDocumentAuditService, "_commit_finalization", defective_finalizer
    )

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 201
    body = response.json()
    assert body["audit_status"] == "pending"
    assert body["audit_message"] == PENDING_AUDIT_MESSAGE
    document = body["document"]
    assert (documents_dir / document["filename"]).exists()
    assert (documents_dir / document["metadata_filename"]).exists()
    assert client.get(f"/api/report-documents/{document['id']}/download").status_code == 200
    # Unresolved and counted, not lost.
    assert audit_actions(config) == []
    assert [row["status"] for row in operations(config)] == ["pending_audit"]
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 1


def test_the_status_exception_boundary_is_narrow_by_construction():
    """No broad catch may be reintroduced around the pending-count read."""
    import inspect

    from app.services import report_documents as module

    source = inspect.getsource(module.ReportDocumentService.status)

    assert "except (sqlite3.Error, OSError)" in source
    assert "except Exception" not in source
    assert "except BaseException" not in source


def test_status_reports_an_exact_zero_only_when_the_ledger_really_is_empty(monkeypatch, tmp_path):
    _config, _documents_dir, client = environment(monkeypatch, tmp_path)

    response = client.get("/api/report-documents/status")

    assert response.status_code == 200
    assert response.json()["pending_audit_count"] == 0


def test_status_reports_the_exact_positive_count_of_unresolved_operations(monkeypatch, tmp_path):
    config, _documents_dir, client = environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)
    for _ in range(2):
        assert client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).status_code == 201
    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))

    response = client.get("/api/report-documents/status")

    assert response.status_code == 200
    assert response.json()["pending_audit_count"] == 2


def test_the_pending_audit_count_excludes_audited_and_abandoned(monkeypatch, tmp_path):
    config, _documents_dir, client = environment(monkeypatch, tmp_path)
    client.post("/api/report-documents/reports/overview", json={"format": "markdown"})
    fail_audit_insert(monkeypatch)
    client.post("/api/report-documents/reports/overview", json={"format": "markdown"})
    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))

    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO artifact_audit_operations"
            " (operation_id, artifact_kind, primary_filename, companion_filename, status, audit_action)"
            " VALUES ('99999999-9999-4999-8999-999999999999', 'report_document', 'gone.md', 'gone.json',"
            " 'abandoned', 'report_document.created')"
        )

    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 1


# --------------------------------------------------------------------------
# Journal read surface
# --------------------------------------------------------------------------

def test_the_journal_shows_safe_russian_wording_and_no_internal_identity(monkeypatch, tmp_path):
    config, _documents_dir, client = environment(monkeypatch, tmp_path)
    document = client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).json()["document"]

    response = client.get("/api/audit-logs")

    assert response.status_code == 200
    items = response.json()["items"]
    entry = next(item for item in items if item["action_label"] == "Документ отчёта создан")
    assert entry["entity_label"] == "Документ отчёта"
    assert entry["display_summary"] == "Документ отчёта создан"
    # The read model still suppresses raw summary, metadata and entity ID.
    assert "summary" not in entry
    assert "metadata_json" not in entry
    assert "entity_id" not in entry

    with sqlite3.connect(config.path) as connection:
        operation_id = connection.execute("SELECT entity_id FROM audit_logs").fetchone()[0]
    for forbidden in (operation_id, document["filename"], document["metadata_filename"], "Report document created"):
        assert forbidden not in response.text


def test_report_document_created_is_not_in_the_suffix_allowlist():
    from app.domain.audit_log_presentation import SUFFIX_PREFIXES, display_summary

    assert "report_document.created" not in SUFFIX_PREFIXES
    # A poisoned persisted summary can contribute nothing.
    assert display_summary("report_document.created", "Report document created: секрет.md") == "Документ отчёта создан"


def test_no_journal_details_route_was_added():
    paths = {getattr(route, "path", "") for route in create_app().routes}

    assert "/api/audit-logs" in paths
    assert not any(path.startswith("/api/audit-logs/") for path in paths)


# --------------------------------------------------------------------------
# Startup
# --------------------------------------------------------------------------

def test_startup_reconciliation_completes_a_pending_event_after_migrations(monkeypatch, tmp_path):
    config, documents_dir, client = user_mode_environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)
    document = client.post("/api/report-documents/reports/overview", json={"format": "markdown"}).json()["document"]
    monkeypatch.undo()
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))
    document_path = documents_dir / document["filename"]
    sidecar_path = documents_dir / document["metadata_filename"]
    before_bytes = (document_path.read_bytes(), sidecar_path.read_bytes())

    from app.services.startup import initialize_startup

    result = initialize_startup("user")

    assert result.report_document_audit_reconciliation is not None
    assert result.report_document_audit_reconciliation.audited == 1
    assert audit_actions(config) == ["report_document.created"]
    assert [row["status"] for row in operations(config)] == ["audited"]
    # The recovered event is marked as such, and the files are untouched.
    with sqlite3.connect(config.path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM audit_logs").fetchone()[0])
    assert metadata["reconciled_after_failure"] is True
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before_bytes

    # Restarting again must not create a second event.
    initialize_startup("user")
    assert audit_actions(config) == ["report_document.created"]


def test_startup_completes_even_when_one_reconciliation_item_cannot_be_finalized(monkeypatch, tmp_path):
    config, _documents_dir, client = user_mode_environment(monkeypatch, tmp_path)
    fail_audit_insert(monkeypatch)
    client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    from app.services.startup import initialize_startup

    # The AuditLog insert is still failing when startup runs.
    result = initialize_startup("user")

    assert result.database_path.exists()
    assert result.report_document_audit_reconciliation is not None
    assert result.report_document_audit_reconciliation.unresolved == 1
    assert audit_actions(config) == []
    assert [row["status"] for row in operations(config)] == ["pending_audit"]


def test_startup_does_not_hide_an_independent_migration_failure(monkeypatch, tmp_path):
    """Audit recovery is forgiving; migrations are not."""
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    from app.services import startup as startup_module

    def failing_initialize_database(*_args, **_kwargs):
        raise sqlite3.OperationalError("migration failed")

    monkeypatch.setattr(startup_module, "initialize_database", failing_initialize_database)

    with pytest.raises(sqlite3.OperationalError, match="migration failed"):
        startup_module.initialize_startup("user")


def test_startup_reconciliation_runs_after_migrations_not_before(monkeypatch, tmp_path):
    """Ordering matters: the ledger table does not exist until `0020` runs."""
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(tmp_path / "user-data"))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    from app.services import startup as startup_module

    order: list[str] = []
    real_initialize = startup_module.initialize_database
    real_reconcile = startup_module.reconcile_report_documents

    def traced_initialize(*args, **kwargs):
        order.append("migrations")
        return real_initialize(*args, **kwargs)

    def traced_reconcile(*args, **kwargs):
        order.append("reconciliation")
        return real_reconcile(*args, **kwargs)

    monkeypatch.setattr(startup_module, "initialize_database", traced_initialize)
    monkeypatch.setattr(startup_module, "reconcile_report_documents", traced_reconcile)

    startup_module.initialize_startup("user")

    assert order == ["migrations", "reconciliation"]


def test_startup_reconciliation_does_not_backfill_legacy_documents(monkeypatch, tmp_path):
    user_data = tmp_path / "user-data"
    documents_dir = user_data / "exports" / "report-documents"
    documents_dir.mkdir(parents=True)
    (documents_dir / "workshop-overview-20250101-000000.md").write_text("# Старый\n", encoding="utf-8")
    (documents_dir / "workshop-overview-20250101-000000.json").write_text('{"id": "x"}', encoding="utf-8")
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    from app.services.startup import initialize_startup

    result = initialize_startup("user")
    config = DatabaseConfig(path=result.database_path)

    assert result.report_document_audit_reconciliation.examined == 0
    assert audit_actions(config) == []
    assert operations(config) == []


# --------------------------------------------------------------------------
# An unverified document is never a created document
#
# The correction this slice makes. `POST /api/report-documents/reports/overview`
# previously mapped every non-recorded finalization to `201` with `audit_status:
# pending`, so a document that failed mandatory verification was presented to the
# user as created with only its Journal entry outstanding. Verification failure
# and Journal failure are now different answers, and only the second is a
# success.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", ["ambiguous", "definitely_absent"])
def test_a_non_valid_verification_never_returns_201(monkeypatch, tmp_path, outcome):
    config, documents_dir, client = environment(monkeypatch, tmp_path)
    monkeypatch.setattr(
        audit_module.ReportDocumentAuditService,
        "verify",
        lambda self, operation: audit_module.ReportDocumentVerification(outcome, "injected"),
    )

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code != 201
    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == VERIFICATION_FAILED_DETAIL
    # Not a success in any form: no create message, and no pending-Journal pair.
    serialized = json.dumps(body, ensure_ascii=False)
    assert "Документ отчета создан." not in serialized
    assert "audit_status" not in body
    assert PENDING_AUDIT_MESSAGE not in serialized
    # No event written, and the pair is preserved rather than deleted.
    assert audit_actions(config) == []
    assert len(list(documents_dir.glob("*.md"))) == 1
    assert len(list(documents_dir.glob("*.json"))) == 1
    # Unresolved and counted.
    assert [row["status"] for row in operations(config)] in (["prepared"], ["pending_audit"])
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 1


def test_a_real_corruption_between_write_and_finalization_never_returns_201(monkeypatch, tmp_path):
    """A genuine verifier verdict, not an injected outcome, reaches the same result."""
    config, documents_dir, client = environment(monkeypatch, tmp_path)
    original = audit_module.ReportDocumentAuditService.finalize

    def corrupt_then_finalize(self, operation_id, *, reconciled_after_failure):
        # The recorded size no longer matches the bytes on disk.
        for path in documents_dir.glob("*.md"):
            path.write_text("truncated", encoding="utf-8")
        return original(self, operation_id, reconciled_after_failure=reconciled_after_failure)

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "finalize", corrupt_then_finalize)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 500
    assert response.json()["detail"] == VERIFICATION_FAILED_DETAIL
    assert audit_actions(config) == []
    assert len(list(documents_dir.glob("*.md"))) == 1


def test_the_verification_error_leaks_no_filename_path_reason_or_sqlite_detail(monkeypatch, tmp_path):
    config, documents_dir, client = environment(monkeypatch, tmp_path)
    captured = {}

    def leaky_verify(self, operation):
        captured["primary"] = operation.primary_filename
        captured["companion"] = operation.companion_filename
        captured["operation_id"] = operation.operation_id
        raise sqlite3.OperationalError("database disk image is malformed")

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "verify", leaky_verify)

    response = client.post(
        "/api/report-documents/reports/overview",
        json={"format": "markdown", "reason": "квартальная сводка"},
    )

    assert response.status_code == 500
    serialized = json.dumps(response.json(), ensure_ascii=False)
    for forbidden in [
        captured["primary"],
        captured["companion"],
        captured["operation_id"],
        str(documents_dir),
        "workshop-overview",
        "квартальная сводка",
        "database disk image is malformed",
        "sqlite",
        "Traceback",
        "size-mismatch",
    ]:
        assert forbidden not in serialized
    assert set(response.json()["detail"]) == {"code", "message", "next_action"}


def test_a_transient_verifier_fault_is_finalized_once_by_a_later_reconciliation(monkeypatch, tmp_path):
    """The refused create leaves a recoverable operation, not a lost document."""
    config, documents_dir, client = environment(monkeypatch, tmp_path)
    original_verify = audit_module.ReportDocumentAuditService.verify

    def defective(*_args, **_kwargs):
        raise TypeError("injected transient verifier fault")

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "verify", defective)
    first = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})
    assert first.status_code == 500
    assert audit_actions(config) == []
    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "verify", original_verify)

    # The next create runs one bounded pre-create reconciliation pass first.
    second = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert second.status_code == 201
    assert audit_actions(config) == ["report_document.created", "report_document.created"]
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 0


def test_a_verified_document_with_a_failed_journal_write_is_still_201_pending(monkeypatch, tmp_path):
    """The other half of the correction: a Journal failure is still a success."""
    config, documents_dir, client = environment(monkeypatch, tmp_path)

    def failing_create_log(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected AuditLog failure")

    monkeypatch.setattr(AuditLogRepository, "create_log", failing_create_log)

    response = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Документ отчета создан."
    assert body["audit_status"] == "pending"
    assert body["audit_message"] == PENDING_AUDIT_MESSAGE
    assert audit_actions(config) == []
    assert client.get("/api/report-documents/status").json()["pending_audit_count"] == 1
    # The document is listable and downloadable: it is the authoritative result.
    assert client.get("/api/report-documents").json()["total"] == 1
