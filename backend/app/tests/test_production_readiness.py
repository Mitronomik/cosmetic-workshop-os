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
from app.services.production_readiness import ProductionReadinessLifecycleError, ProductionReadinessService
from app.services.recipes import RecipeService
from app.services.stock_movements import StockMovementService
from app.tests.table_guards import assert_no_forbidden_future_tables


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "readiness.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def table_names(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def seed_base(c, *, percent="100", ingredient_unit="g", ingredient_density=None, packaging_qty="1"):
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit=ingredient_unit, density_g_per_ml=ingredient_density))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Cream"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value=percent, amount_unit="percent")])).version
    packaging = PackagingItemService(c).create_packaging_item(PackagingItemDraft.create(name="Банка", kind="jar", unit="pcs", unit_cost="10"))
    order = OrderService(c).create(OrderDraft.create(client_id=client.id, recipe_version_id=version.id, product_name="Крем", target_batch_size_value="50", target_batch_size_unit="g", packaging_item_id=packaging.id, packaging_quantity=packaging_qty, sale_price="200"))
    return client, ingredient, version, packaging, order


def add_lot(c, ingredient_id, qty, *, code="L", expires=None, unit="g", unit_cost="2", density=None):
    lot = IngredientLotService(c).create_lot(IngredientLotDraft.create(ingredient_id=ingredient_id, unit=unit, lot_code=code, expires_at=expires, unit_cost=unit_cost, density_g_per_ml=density))
    StockMovementService(c).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity=qty, unit=unit, reason="seed"))
    return lot


def add_packaging(c, packaging_id, qty):
    return PackagingStockMovementService(c).create_movement(PackagingStockMovementDraft.create(packaging_item_id=packaging_id, movement_type="receipt", quantity=qty, unit="pcs", reason="seed"))


def snapshot(c, order_id):
    return {
        "stock": scalar(c, "SELECT count(*) FROM stock_movements"),
        "packaging": scalar(c, "SELECT count(*) FROM packaging_stock_movements"),
        "status": scalar(c, "SELECT status FROM orders WHERE id=?", (order_id,)),
        "produced_at": scalar(c, "SELECT produced_at FROM orders WHERE id=?", (order_id,)),
        "delivered_at": scalar(c, "SELECT delivered_at FROM orders WHERE id=?", (order_id,)),
        "tables": table_names(c),
    }


def test_enough_stock_fefo_costs_and_read_only_guarantee(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_base(c)
    later = date.today() + timedelta(days=90)
    earlier = date.today() + timedelta(days=60)
    add_lot(c, ingredient.id, "20", code="later", expires=later)
    add_lot(c, ingredient.id, "40", code="earlier", expires=earlier)
    add_packaging(c, packaging.id, "2")
    before = snapshot(c, order.id)

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.can_produce is True
    assert result.status == "warning"
    assert [lot.lot_code for lot in result.ingredients[0].selected_lots] == ["earlier", "later"]
    assert result.estimated_cost == "110.00"
    assert result.estimated_tax is None and result.estimated_margin is None
    assert any(issue.code == "tax_rate_missing" for issue in result.warnings)
    assert snapshot(c, order.id) == before
    assert "production_batches" not in table_names(c)
    assert_no_forbidden_future_tables(table_names(c))


def test_missing_ingredient_blocks_readiness(tmp_path):
    c = config(tmp_path)
    _, _, _, packaging, order = seed_base(c)
    add_packaging(c, packaging.id, "1")
    result = ProductionReadinessService(c).check_order(order.id)
    assert result.can_produce is False
    assert any(issue.code == "ingredient_lot_missing" for issue in result.blocking_issues)
    assert result.ingredients[0].missing_quantity == "50.000"


def test_insufficient_ingredient_returns_missing_quantity(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_base(c)
    add_lot(c, ingredient.id, "10", code="small")
    add_packaging(c, packaging.id, "1")
    result = ProductionReadinessService(c).check_order(order.id)
    assert result.can_produce is False
    assert any(issue.code == "ingredient_stock_insufficient" for issue in result.blocking_issues)
    assert result.ingredients[0].missing_quantity == "40.000"


def test_mixed_lot_units_block_automatic_selection_without_mutation(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_base(c, ingredient_density="0.8")
    add_lot(c, ingredient.id, "30", code="grams", unit="g")
    add_lot(c, ingredient.id, "30", code="milliliters", unit="ml", density="0.8")
    add_packaging(c, packaging.id, "1")
    before = snapshot(c, order.id)

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.can_produce is False
    assert any(issue.code == "mixed_lot_units_not_supported" for issue in result.blocking_issues)
    assert result.ingredients[0].selected_lots == []
    assert snapshot(c, order.id) == before


def test_expired_and_expiring_lot_warnings(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_base(c)
    add_lot(c, ingredient.id, "30", code="expired", expires=date.today() - timedelta(days=1))
    add_lot(c, ingredient.id, "30", code="soon", expires=date.today() + timedelta(days=5))
    add_packaging(c, packaging.id, "1")
    result = ProductionReadinessService(c).check_order(order.id)
    assert result.can_produce is True
    codes = [issue.code for issue in result.warnings]
    assert "lot_expired" in codes and "lot_expires_soon" in codes


def test_missing_density_warning_blocks_lot_match_when_conversion_required(tmp_path):
    c = config(tmp_path)
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Hydrolat", category="water_phase", default_unit="ml"))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Tonic"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value="100", amount_unit="percent")])).version
    order = OrderService(c).create(OrderDraft.create(client_id=client.id, recipe_version_id=version.id, product_name="Тоник", target_batch_size_value="50", target_batch_size_unit="ml"))
    add_lot(c, ingredient.id, "100", unit="g")
    result = ProductionReadinessService(c).check_order(order.id)
    assert result.can_produce is False
    assert any(issue.code == "density_missing" for issue in result.warnings)


def test_missing_packaging_blocks_readiness(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, _, order = seed_base(c)
    add_lot(c, ingredient.id, "50")
    result = ProductionReadinessService(c).check_order(order.id)
    assert result.can_produce is False
    assert any(issue.code == "packaging_stock_insufficient" for issue in result.blocking_issues)
    assert result.packaging[0].missing_quantity == "1"


def test_cancelled_and_archived_orders_are_rejected(tmp_path):
    c = config(tmp_path)
    _, _, _, _, cancelled = seed_base(c)
    _, _, _, _, archived = seed_base(c)
    service = OrderService(c)
    service.cancel(cancelled.id)
    service.archive(archived.id)
    with pytest.raises(ProductionReadinessLifecycleError):
        ProductionReadinessService(c).check_order(cancelled.id)
    with pytest.raises(ProductionReadinessLifecycleError):
        ProductionReadinessService(c).check_order(archived.id)


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_endpoint(monkeypatch, tmp_path):
    db = tmp_path / "api-readiness.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    _, ingredient, _, packaging, order = seed_base(c)
    add_lot(c, ingredient.id, "50")
    add_packaging(c, packaging.id, "1")
    api = TestClient(create_app())
    response = api.post(f"/api/orders/{order.id}/check-production-readiness")
    assert response.status_code == 200
    assert response.json()["can_produce"] is True
    assert api.post("/api/orders/999/check-production-readiness").status_code == 404
    OrderService(c).cancel(order.id)
    assert api.post(f"/api/orders/{order.id}/check-production-readiness").status_code == 409
