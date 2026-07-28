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


FINANCE_SNAPSHOT_FIELDS = (
    "known_tax",
    "tax_snapshot_record_count",
    "missing_tax_snapshot_count",
    "margin_snapshot_record_count",
    "missing_margin_snapshot_count",
)


def seed_snapshot_batch(db, *, sale_price, total_cost, tax, margin, margin_percent):
    with sqlite3.connect(db) as con:
        client = con.execute("INSERT INTO clients (full_name) VALUES ('Анна')").lastrowid
        template = con.execute("INSERT INTO recipe_templates (name, product_type) VALUES ('Крем', 'cream')").lastrowid
        version = con.execute("INSERT INTO recipe_versions (recipe_template_id, version_number, title, status) VALUES (?, 1, 'v1', 'draft')", (template,)).lastrowid
        order = con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status, sale_price) VALUES (?, ?, 'Крем', '50', 'g', 'produced', ?)", (client, version, sale_price)).lastrowid
        con.execute("INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, other_cost, total_cost, sale_price, tax, margin, margin_percent) VALUES (?, ?, '50.000', 'g', '0.00', ?, ?, ?, ?, ?)", (order, version, total_cost, sale_price, tax, margin, margin_percent))


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_finance_and_overview_expose_the_same_snapshot_backed_finance_dto(monkeypatch, tmp_path):
    db = tmp_path / "finance-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    seed_snapshot_batch(db, sale_price="1000.00", total_cost="400.00", tax="60.00", margin="540.00", margin_percent="54.00")
    client = TestClient(create_app())

    finance = client.get("/api/reports/finance").json()
    summary = client.get("/api/reports/overview").json()["finance_summary"]

    assert finance["known_tax"] == "60.00"
    assert finance["known_margin"] == "540.00"
    assert finance["known_margin_percent"] == "54.00"
    for field in FINANCE_SNAPSHOT_FIELDS:
        assert field in finance
        assert field in summary
    assert finance["tax_snapshot_record_count"] + finance["missing_tax_snapshot_count"] == finance["produced_order_count"]
    assert finance["margin_snapshot_record_count"] + finance["missing_margin_snapshot_count"] == finance["produced_order_count"]
    # The overview carries the identical DTO, so the two tabs can never disagree.
    assert {k: v for k, v in summary.items() if k != "generated_at"} == {k: v for k, v in finance.items() if k != "generated_at"}


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_changing_the_tax_rate_setting_leaves_the_finance_api_response_unchanged(monkeypatch, tmp_path):
    db = tmp_path / "finance-api-rate.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    initialize_database(DatabaseConfig(path=db))
    seed_snapshot_batch(db, sale_price="1000.00", total_cost="400.00", tax=None, margin=None, margin_percent=None)
    client = TestClient(create_app())
    before = {k: v for k, v in client.get("/api/reports/finance").json().items() if k != "generated_at"}

    assert client.put("/api/settings/tax-rate", json={"tax_rate_percent": "20"}).status_code == 200
    assert {k: v for k, v in client.get("/api/reports/finance").json().items() if k != "generated_at"} == before
    assert client.put("/api/settings/tax-rate", json={"tax_rate_percent": None}).status_code == 200
    assert {k: v for k, v in client.get("/api/reports/finance").json().items() if k != "generated_at"} == before
    assert before["known_tax"] is None
    assert before["known_margin"] is None


def test_reports_routes_are_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert ("/api/reports/overview", ("GET",)) in routes
    assert ("/api/reports/inventory", ("GET",)) in routes
    assert ("/api/reports/orders", ("GET",)) in routes
    assert ("/api/reports/production", ("GET",)) in routes
    assert ("/api/reports/finance", ("GET",)) in routes
