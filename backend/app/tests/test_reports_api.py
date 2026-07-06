import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.main import create_app
from app.services.database import initialize_database


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_report_api_endpoints_return_generated_at_warnings_and_are_read_only(monkeypatch, tmp_path):
    db = tmp_path / "reports-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    with sqlite3.connect(db) as con:
        before = {row[0]: con.execute(f"SELECT COUNT(*) FROM {row[0]}").fetchone()[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    client = TestClient(create_app())
    for path in ("overview", "inventory", "orders", "production", "finance"):
        response = client.get(f"/api/reports/{path}")
        assert response.status_code == 200
        body = response.json()
        assert body["generated_at"]
        assert "warnings" in body
        if path == "finance":
            assert "complete_finance_record_count" in body
            assert "incomplete_margin_count" in body
        if path == "overview":
            assert "complete_finance_record_count" in body["finance_summary"]
            assert "incomplete_margin_count" in body["finance_summary"]
    with sqlite3.connect(db) as con:
        after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert after == before


def test_reports_routes_are_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert ("/api/reports/overview", ("GET",)) in routes
    assert ("/api/reports/inventory", ("GET",)) in routes
    assert ("/api/reports/orders", ("GET",)) in routes
    assert ("/api/reports/production", ("GET",)) in routes
    assert ("/api/reports/finance", ("GET",)) in routes
