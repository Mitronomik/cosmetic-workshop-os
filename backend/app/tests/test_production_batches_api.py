import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.main import create_app
from app.repositories.production_batches import ProductionBatchNotFoundError, ProductionBatchRepository
from app.services.database import initialize_database
from app.services.orders import OrderService
from app.services.production_confirmation import ProductionConfirmationService
from app.tests.test_production_confirmation import counts, seed_ready


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "production-batches-read.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def test_repository_list_returns_newest_first_with_counts_and_context(tmp_path):
    c = config(tmp_path)
    *_, old_order = seed_ready(c)
    old = ProductionConfirmationService(c).produce_order(old_order.id, True, notes="old")
    *_, new_order = seed_ready(c)
    new = ProductionConfirmationService(c).produce_order(new_order.id, True, notes="new")

    batches = ProductionBatchRepository(c).list_batches()

    assert [b.id for b in batches] == [new.batch.id, old.batch.id]
    assert batches[0].order_id == new_order.id
    assert batches[0].product_name == "Крем"
    assert batches[0].client_name == "Анна"
    assert batches[0].ingredient_line_count == 1
    assert batches[0].packaging_line_count == 1


def test_repository_detail_returns_snapshots_and_preserves_values_after_source_changes(tmp_path):
    c = config(tmp_path)
    _, ingredient, lot, packaging, order = seed_ready(c)
    created = ProductionConfirmationService(c).produce_order(order.id, True, notes="historical")
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET name='Changed' WHERE id=?", (ingredient.id,))
        con.execute("UPDATE ingredient_lots SET lot_code='ChangedLot', unit_cost='9' WHERE id=?", (lot.id,))
        con.execute("UPDATE packaging_items SET name='ChangedPack', unit_cost='99' WHERE id=?", (packaging.id,))
        con.execute("UPDATE orders SET product_name='Changed order' WHERE id=?", (order.id,))

    detail = ProductionBatchRepository(c).get_detail(created.batch.id)

    assert detail.product_name == "Changed order"
    assert detail.client_name == "Анна"
    assert detail.batch.notes == "historical"
    assert detail.ingredients[0].ingredient_name_snapshot == "Water"
    assert detail.ingredients[0].lot_code_snapshot == "L1"
    assert str(detail.ingredients[0].unit_cost_snapshot) == "2.00"
    assert detail.packaging[0].packaging_name_snapshot == "Банка"
    assert str(detail.packaging[0].unit_cost_snapshot) == "10.00"


def test_repository_get_by_order_and_not_found(tmp_path):
    c = config(tmp_path)
    *_, produced_order = seed_ready(c)
    created = ProductionConfirmationService(c).produce_order(produced_order.id, True)
    *_, plain_order = seed_ready(c)

    assert ProductionBatchRepository(c).get_detail_by_order_id(produced_order.id).batch.id == created.batch.id
    with pytest.raises(ProductionBatchNotFoundError):
        ProductionBatchRepository(c).get_detail_by_order_id(plain_order.id)
    with pytest.raises(ProductionBatchNotFoundError):
        ProductionBatchRepository(c).get_detail(999)


def test_read_repository_methods_do_not_mutate_orders_or_movements(tmp_path):
    c = config(tmp_path)
    *_, order = seed_ready(c)
    created = ProductionConfirmationService(c).produce_order(order.id, True)
    before = counts(c)
    status_before = scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,))

    repo = ProductionBatchRepository(c)
    repo.list_batches()
    repo.get_detail(created.batch.id)
    repo.get_detail_by_order_id(order.id)

    assert counts(c) == before
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == status_before


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_read_endpoints(monkeypatch, tmp_path):
    db = tmp_path / "api-production-batches.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    *_, old_order = seed_ready(c)
    old = ProductionConfirmationService(c).produce_order(old_order.id, True)
    *_, new_order = seed_ready(c)
    new = ProductionConfirmationService(c).produce_order(new_order.id, True)
    *_, plain_order = seed_ready(c)
    before = counts(c)
    api = TestClient(create_app())

    list_response = api.get("/api/production-batches")
    assert list_response.status_code == 200
    body = list_response.json()
    assert [b["id"] for b in body["production_batches"]] == [new.batch.id, old.batch.id]
    assert body["production_batches"][0]["ingredient_line_count"] == 1
    assert body["production_batches"][0]["packaging_line_count"] == 1

    detail_response = api.get(f"/api/production-batches/{new.batch.id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["order_id"] == new_order.id
    assert detail["product_name"] == "Крем"
    assert detail["client_name"] == "Анна"
    assert detail["ingredients"][0]["ingredient_name_snapshot"] == "Water"
    assert detail["packaging"][0]["packaging_name_snapshot"] == "Банка"

    by_order = api.get(f"/api/orders/{new_order.id}/production-batch")
    assert by_order.status_code == 200
    assert by_order.json()["id"] == new.batch.id
    assert api.get(f"/api/orders/{plain_order.id}/production-batch").status_code == 404
    assert api.get("/api/orders/999999/production-batch").status_code == 404
    assert api.get("/api/production-batches/999999").status_code == 404
    assert api.get("/api/production-batches?limit=0").status_code == 422

    assert counts(c) == before
    assert OrderService(c).get_by_id(new_order.id).status.value == "produced"
