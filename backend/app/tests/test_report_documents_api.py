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
    assert status.json()["available_formats"] == ["markdown", "pdf"]
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


def test_report_document_routes_are_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert ("/api/report-documents/status", ("GET",)) in routes
    assert ("/api/report-documents", ("GET",)) in routes
    assert ("/api/report-documents/reports/overview", ("POST",)) in routes
