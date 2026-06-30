from datetime import date, timedelta
import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.clients import ClientDraft
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.orders import OrderDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.domain.stock_movements import StockMovementDraft
from app.main import create_app
from app.services.clients import ClientService
from app.services.database import initialize_database
from app.services.ingredient_lots import IngredientLotService
from app.services.ingredients import IngredientService
from app.services.orders import OrderService
from app.services.packaging_items import PackagingItemService
from app.services.packaging_stock_movements import PackagingStockMovementService
from app.services.production_confirmation import ProductionConfirmationLifecycleError, ProductionConfirmationReadinessError, ProductionConfirmationRequiredError, ProductionConfirmationService
from app.services.recipes import RecipeService
from app.services.stock_movements import StockMovementService


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "production-confirmation.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def seed_ready(c, *, lot_qty="60", packaging_qty="2"):
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit="g"))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Cream"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value="100", amount_unit="percent")])).version
    packaging = PackagingItemService(c).create_packaging_item(PackagingItemDraft.create(name="Банка", kind="jar", unit="pcs", unit_cost="10"))
    order = OrderService(c).create(OrderDraft.create(client_id=client.id, recipe_version_id=version.id, product_name="Крем", target_batch_size_value="50", target_batch_size_unit="g", packaging_item_id=packaging.id, packaging_quantity="1", sale_price="200"))
    lot = IngredientLotService(c).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g", lot_code="L1", expires_at=date.today() + timedelta(days=90), unit_cost="2"))
    StockMovementService(c).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity=lot_qty, unit="g", reason="seed"))
    if packaging_qty:
        PackagingStockMovementService(c).create_movement(PackagingStockMovementDraft.create(packaging_item_id=packaging.id, movement_type="receipt", quantity=packaging_qty, unit="pcs", reason="seed"))
    return client, ingredient, lot, packaging, order


def counts(c):
    return {
        "batches": scalar(c, "SELECT count(*) FROM production_batches"),
        "batch_ingredients": scalar(c, "SELECT count(*) FROM production_batch_ingredients"),
        "batch_packaging": scalar(c, "SELECT count(*) FROM production_batch_packaging"),
        "stock": scalar(c, "SELECT count(*) FROM stock_movements WHERE movement_type='write_off'"),
        "packaging": scalar(c, "SELECT count(*) FROM packaging_stock_movements WHERE movement_type='write_off'"),
    }


def test_producing_ready_order_creates_batch_snapshots_movements_and_status(tmp_path):
    c = config(tmp_path)
    _, _, lot, packaging, order = seed_ready(c)
    detail = ProductionConfirmationService(c).produce_order(order.id, confirm=True, notes="done")
    assert detail.batch.order_id == order.id
    assert detail.batch.component_cost == 100
    assert detail.batch.packaging_cost == 10
    assert detail.batch.total_cost == 110
    assert detail.batch.sale_price == 200
    assert detail.batch.tax is None and detail.batch.margin is None and detail.batch.margin_percent is None
    assert detail.ingredients[0].ingredient_name_snapshot == "Water"
    assert detail.ingredients[0].lot_code_snapshot == "L1"
    assert detail.ingredients[0].unit_cost_snapshot == 2
    assert detail.packaging[0].packaging_name_snapshot == "Банка"
    assert detail.packaging[0].unit_cost_snapshot == 10
    assert counts(c) == {"batches": 1, "batch_ingredients": 1, "batch_packaging": 1, "stock": 1, "packaging": 1}
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == "produced"
    assert scalar(c, "SELECT produced_at IS NOT NULL FROM orders WHERE id=?", (order.id,)) == 1
    assert StockMovementService(c).calculate_lot_quantity(lot.id) == 10
    assert PackagingStockMovementService(c).calculate_packaging_item_quantity(packaging.id) == 1


def test_cannot_produce_without_explicit_confirmation(tmp_path):
    c = config(tmp_path)
    *_, order = seed_ready(c)
    service = ProductionConfirmationService(c)
    for value in (False, None):
        with pytest.raises(ProductionConfirmationRequiredError):
            service.produce_order(order.id, confirm=value)
    assert counts(c)["batches"] == 0
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == "new"


def test_cancelled_archived_and_inactive_orders_are_rejected(tmp_path):
    c = config(tmp_path)
    *_, cancelled = seed_ready(c)
    *_, archived = seed_ready(c)
    OrderService(c).cancel(cancelled.id)
    OrderService(c).archive(archived.id)
    for order in (cancelled, archived):
        with pytest.raises(ProductionConfirmationLifecycleError):
            ProductionConfirmationService(c).produce_order(order.id, True)
    assert counts(c)["batches"] == 0


def test_cannot_produce_order_twice(tmp_path):
    c = config(tmp_path)
    *_, order = seed_ready(c)
    service = ProductionConfirmationService(c)
    service.produce_order(order.id, True)
    with pytest.raises(ProductionConfirmationLifecycleError):
        service.produce_order(order.id, True)
    assert counts(c)["batches"] == 1
    assert counts(c)["stock"] == 1


def test_insufficient_ingredient_prevents_production(tmp_path):
    c = config(tmp_path)
    *_, order = seed_ready(c, lot_qty="10")
    with pytest.raises(ProductionConfirmationReadinessError):
        ProductionConfirmationService(c).produce_order(order.id, True)
    assert counts(c)["batches"] == 0
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == "new"


def test_missing_packaging_prevents_production(tmp_path):
    c = config(tmp_path)
    *_, order = seed_ready(c, packaging_qty=None)
    with pytest.raises(ProductionConfirmationReadinessError):
        ProductionConfirmationService(c).produce_order(order.id, True)
    assert counts(c)["batches"] == 0


class FailingPackagingMovementRepository:
    def create(self, *args, **kwargs):
        raise RuntimeError("forced packaging write failure")


def test_transaction_rolls_back_partial_writes_on_failure(tmp_path):
    c = config(tmp_path)
    *_, order = seed_ready(c)
    service = ProductionConfirmationService(c)
    service.packaging_movements = FailingPackagingMovementRepository()
    with pytest.raises(RuntimeError):
        service.produce_order(order.id, True)
    assert counts(c) == {"batches": 0, "batch_ingredients": 0, "batch_packaging": 0, "stock": 0, "packaging": 0}
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == "new"


def test_production_snapshots_are_immutable_after_source_changes(tmp_path):
    c = config(tmp_path)
    _, ingredient, lot, packaging, order = seed_ready(c)
    detail = ProductionConfirmationService(c).produce_order(order.id, True)
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET name='Changed' WHERE id=?", (ingredient.id,))
        con.execute("UPDATE ingredient_lots SET lot_code='ChangedLot', unit_cost='9' WHERE id=?", (lot.id,))
        con.execute("UPDATE packaging_items SET name='ChangedPack', unit_cost='99' WHERE id=?", (packaging.id,))
    with sqlite3.connect(c.path) as con:
        bi = con.execute("SELECT ingredient_name_snapshot, lot_code_snapshot, unit_cost_snapshot FROM production_batch_ingredients WHERE production_batch_id=?", (detail.batch.id,)).fetchone()
        bp = con.execute("SELECT packaging_name_snapshot, unit_cost_snapshot FROM production_batch_packaging WHERE production_batch_id=?", (detail.batch.id,)).fetchone()
    assert tuple(bi) == ("Water", "L1", "2.00")
    assert tuple(bp) == ("Банка", "10.00")


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_produce_endpoint(monkeypatch, tmp_path):
    db = tmp_path / "api-production.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    *_, order = seed_ready(c)
    api = TestClient(create_app())
    assert api.post(f"/api/orders/{order.id}/produce", json={}).status_code == 422
    response = api.post(f"/api/orders/{order.id}/produce", json={"confirm": True, "notes": "ok"})
    assert response.status_code == 200
    assert response.json()["order_id"] == order.id
    assert response.json()["ingredients"]
    assert api.post("/api/orders/999/produce", json={"confirm": True}).status_code == 404
    assert api.post(f"/api/orders/{order.id}/produce", json={"confirm": True}).status_code == 409
