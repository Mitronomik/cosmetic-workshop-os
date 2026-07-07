from datetime import datetime
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
from app.services.database import initialize_database
from app.services import report_documents as report_documents_module
from app.tests.test_reports import BUSINESS_TABLES


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_report_document_api_endpoints_create_metadata_and_are_safe(monkeypatch, tmp_path):
    db = tmp_path / "report-documents-api.sqlite"
    user_data = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    initialize_database(DatabaseConfig(path=db))
    with sqlite3.connect(db) as con:
        before = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in BUSINESS_TABLES}

    client = TestClient(create_app())
    status = client.get("/api/report-documents/status")
    assert status.status_code == 200
    assert "markdown" in status.json()["available_formats"]
    assert status.json()["documents_count"] == 0

    listing = client.get("/api/report-documents")
    assert listing.status_code == 200
    assert listing.json()["items"] == []

    created = client.post("/api/report-documents/reports/overview", json={"format": "markdown", "reason": "manual"})
    assert created.status_code == 201
    document = created.json()["document"]
    assert document["id"].startswith("workshop-overview-")
    assert document["format"] == "markdown"
    assert (user_data / "exports" / "report-documents" / document["filename"]).exists()
    assert (user_data / "exports" / "report-documents" / document["metadata_filename"]).exists()

    after_listing = client.get("/api/report-documents")
    assert after_listing.status_code == 200
    assert after_listing.json()["total"] == 1
    assert after_listing.json()["items"][0]["id"] == document["id"]

    markdown_download = client.get(f"/api/report-documents/{document['id']}/download")
    assert markdown_download.status_code == 200
    assert markdown_download.text.startswith("# Сводка мастерской")
    assert "text/markdown" in markdown_download.headers["content-type"]
    assert "attachment" in markdown_download.headers["content-disposition"]
    assert document["filename"] in markdown_download.headers["content-disposition"]

    markdown_inline = client.get(f"/api/report-documents/{document['id']}/download?disposition=inline")
    assert markdown_inline.status_code == 200
    assert "attachment" in markdown_inline.headers["content-disposition"]

    monkeypatch.setattr(report_documents_module, "_is_pdf_generation_available", lambda: True)

    def fake_write_pdf_exclusive(path: Path, lines: list[str], *, created_at: datetime) -> None:
        with path.open("xb") as file:
            file.write(b"%PDF-1.4\n% fake test pdf\n%%EOF\n")

    monkeypatch.setattr(report_documents_module, "_write_pdf_exclusive", fake_write_pdf_exclusive)

    pdf_status = client.get("/api/report-documents/status")
    assert pdf_status.status_code == 200
    assert pdf_status.json()["available_formats"] == ["markdown", "pdf"]

    pdf = client.post("/api/report-documents/reports/overview", json={"format": "pdf"})
    assert pdf.status_code == 201
    pdf_document = pdf.json()["document"]
    assert pdf_document["format"] == "pdf"
    assert pdf_document["filename"].endswith(".pdf")
    assert (user_data / "exports" / "report-documents" / pdf_document["filename"]).read_bytes().startswith(b"%PDF-")
    pdf_listing = client.get("/api/report-documents")
    assert pdf_listing.status_code == 200
    assert pdf_listing.json()["total"] == 2
    assert any(item["id"] == pdf_document["id"] and item["format"] == "pdf" for item in pdf_listing.json()["items"])

    pdf_inline = client.get(f"/api/report-documents/{pdf_document['id']}/download?disposition=inline")
    assert pdf_inline.status_code == 200
    assert pdf_inline.content.startswith(b"%PDF-")
    assert pdf_inline.headers["content-type"] == "application/pdf"
    assert "inline" in pdf_inline.headers["content-disposition"]

    unknown = client.get("/api/report-documents/workshop-overview-20990101-000000/download")
    assert unknown.status_code == 404
    assert "Документ отчета не найден" in unknown.json()["detail"]

    bad_disposition = client.get(f"/api/report-documents/{pdf_document['id']}/download?disposition=preview")
    assert bad_disposition.status_code == 422
    assert "Неподдерживаемый режим" in bad_disposition.json()["detail"]

    docx = client.post("/api/report-documents/reports/overview", json={"format": "docx"})
    assert docx.status_code == 422
    assert "DOCX пока не поддерживается" in docx.json()["detail"]

    suspicious = client.post("/api/report-documents/reports/overview", json={"format": "markdown", "reason": "../../bad"})
    assert suspicious.status_code == 201
    suspicious_document = suspicious.json()["document"]
    suspicious_path = (user_data / "exports" / "report-documents" / suspicious_document["filename"]).resolve()
    assert suspicious_path.parent == (user_data / "exports" / "report-documents").resolve()

    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in BUSINESS_TABLES}
    assert after == before
    assert not (user_data / "backups").exists()
    assert list((user_data / "exports").glob("*.json")) == []



@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_report_document_api_uses_saved_workshop_profile(monkeypatch, tmp_path):
    db = tmp_path / "report-documents-profile-api.sqlite"
    user_data = tmp_path / "user-data"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    monkeypatch.setenv(USER_DATA_DIR_ENV, str(user_data))
    initialize_database(DatabaseConfig(path=db))
    client = TestClient(create_app())

    saved = client.put("/api/settings/workshop-profile", json={"workshop_name": "Мастерская API", "master_name": "Мария"})
    assert saved.status_code == 200

    created = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})
    assert created.status_code == 201
    document = created.json()["document"]
    text = (user_data / "exports" / "report-documents" / document["filename"]).read_text(encoding="utf-8")
    assert "## Профиль мастерской" in text
    assert "- Мастерская: Мастерская API" in text
    assert "- Мастер: Мария" in text

    client.put("/api/settings/workshop-profile", json={})
    empty = client.post("/api/report-documents/reports/overview", json={"format": "markdown"})
    assert empty.status_code == 201
    empty_document = empty.json()["document"]
    empty_text = (user_data / "exports" / "report-documents" / empty_document["filename"]).read_text(encoding="utf-8")
    assert "## Профиль мастерской" not in empty_text

def test_report_document_routes_are_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert ("/api/report-documents/status", ("GET",)) in routes
    assert ("/api/report-documents", ("GET",)) in routes
    assert ("/api/report-documents/{document_id}/download", ("GET",)) in routes
    assert ("/api/report-documents/reports/overview", ("POST",)) in routes
