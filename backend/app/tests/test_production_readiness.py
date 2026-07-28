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
from app.repositories.settings import SettingsRepository
from app.services.production_readiness import ProductionReadinessLifecycleError, ProductionReadinessService
from app.services.recipes import RecipeService
from app.services.stock_movements import StockMovementService
from app.services.tax_rate_settings import DEFAULT_TAX_RATE_KEY, TaxRateSettingsService
from app.tests.table_guards import assert_no_forbidden_future_tables


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "readiness.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def rows_of(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return [tuple(row) for row in con.execute(sql, params).fetchall()]


def table_names(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def seed_base(c, *, percent="100", ingredient_unit="g", ingredient_density=None, packaging_qty="1", sale_price="200"):
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit=ingredient_unit, density_g_per_ml=ingredient_density))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Cream"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value=percent, amount_unit="percent")])).version
    packaging = PackagingItemService(c).create_packaging_item(PackagingItemDraft.create(name="Банка", kind="jar", unit="pcs", unit_cost="10"))
    order = OrderService(c).create(OrderDraft.create(client_id=client.id, recipe_version_id=version.id, product_name="Крем", target_batch_size_value="50", target_batch_size_unit="g", packaging_item_id=packaging.id, packaging_quantity=packaging_qty, sale_price=sale_price))
    return client, ingredient, version, packaging, order


def set_tax_rate(c, percent):
    """Configure the rate through the authoritative C1 service."""
    return TaxRateSettingsService(c).update_tax_rate(percent)


def corrupt_tax_rate(c, raw):
    """Write an invalid `default_tax_rate` the way external editing would.

    The C1 API validates every value it writes, so this defensive case can only
    be produced by bypassing the service, exactly as ADR 0012 describes.
    """
    SettingsRepository(c).upsert_setting(DEFAULT_TAX_RATE_KEY, raw, "decimal_string", "externally corrupted value")


def ready_order(c, *, sale_price="200", unit_cost="2"):
    """Seed one physically producible order with complete cost inputs."""
    _, ingredient, _, packaging, order = seed_base(c, sale_price=sale_price)
    add_lot(c, ingredient.id, "50", unit_cost=unit_cost)
    add_packaging(c, packaging.id, "1")
    return order


def warning_codes(result):
    return [issue.code for issue in result.warnings]


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
        "production_batches": scalar(c, "SELECT count(*) FROM production_batches"),
        "production_batch_ingredients": scalar(c, "SELECT count(*) FROM production_batch_ingredients"),
        "production_batch_packaging": scalar(c, "SELECT count(*) FROM production_batch_packaging"),
        "audit_logs": scalar(c, "SELECT count(*) FROM audit_logs"),
        "settings": rows_of(c, "SELECT key, value, value_type, updated_at FROM app_settings ORDER BY key"),
        "orders": rows_of(c, "SELECT * FROM orders ORDER BY id"),
        "stock_rows": rows_of(c, "SELECT * FROM stock_movements ORDER BY id"),
        "packaging_rows": rows_of(c, "SELECT * FROM packaging_stock_movements ORDER BY id"),
        "status": scalar(c, "SELECT status FROM orders WHERE id=?", (order_id,)),
        "produced_at": scalar(c, "SELECT produced_at FROM orders WHERE id=?", (order_id,)),
        "delivered_at": scalar(c, "SELECT delivered_at FROM orders WHERE id=?", (order_id,)),
        "updated_at": scalar(c, "SELECT updated_at FROM orders WHERE id=?", (order_id,)),
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
    assert_no_forbidden_future_tables(table_names(c))


def test_missing_ingredient_blocks_readiness(tmp_path):
    c = config(tmp_path)
    _, _, _, packaging, order = seed_base(c)
    add_packaging(c, packaging.id, "1")
    before = snapshot(c, order.id)
    result = ProductionReadinessService(c).check_order(order.id)
    assert result.can_produce is False
    assert any(issue.code == "ingredient_lot_missing" for issue in result.blocking_issues)
    assert result.ingredients[0].missing_quantity == "50.000"
    assert snapshot(c, order.id) == before


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


# --- C2-I financial readiness estimate -------------------------------------


def test_configured_six_percent_produces_the_full_financial_estimate(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    set_tax_rate(c, "6")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.sale_price == "200.00"
    assert result.estimated_cost == "110.00"
    assert result.tax_rate_percent == "6.00"
    assert result.tax_rate_effective_at is not None and result.tax_rate_effective_at.endswith("Z")
    assert result.estimated_tax == "12.00"
    assert result.estimated_margin == "78.00"
    assert result.estimated_margin_percent == "39.00"
    assert result.financial_estimate_status == "available"
    assert warning_codes(result) == []
    assert result.can_produce is True


def test_configured_zero_percent_is_a_real_rate_and_not_a_missing_one(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    set_tax_rate(c, "0")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.tax_rate_percent == "0.00"
    assert result.estimated_tax == "0.00"
    assert result.estimated_margin == "90.00"
    assert result.estimated_margin_percent == "45.00"
    assert result.financial_estimate_status == "available"
    assert "tax_rate_missing" not in warning_codes(result)


def test_missing_rate_leaves_the_estimate_unavailable_without_a_fabricated_zero(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.tax_rate_percent is None
    assert result.tax_rate_effective_at is None
    assert result.estimated_tax is None
    assert result.estimated_margin is None
    assert result.estimated_margin_percent is None
    assert result.financial_estimate_status == "unavailable"
    assert warning_codes(result) == ["tax_rate_missing"]
    assert result.can_produce is True


@pytest.mark.parametrize("raw", ["", "   ", "abc", "6,5", "-1", "101", "6.005", "6%", "NaN", "Infinity"])
def test_invalid_persisted_rate_becomes_the_no_valid_rate_context(tmp_path, raw):
    c = config(tmp_path)
    order = ready_order(c)
    corrupt_tax_rate(c, raw)

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.tax_rate_percent is None
    assert result.tax_rate_effective_at is None
    assert result.estimated_tax is None
    assert result.estimated_margin is None
    assert result.estimated_margin_percent is None
    assert result.financial_estimate_status == "unavailable"
    assert result.can_produce is True


def test_invalid_persisted_rate_never_returns_the_raw_value_anywhere(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    corrupt_tax_rate(c, "категорически не число")

    result = ProductionReadinessService(c).check_order(order.id)

    assert "категорически" not in result.model_dump_json()


def test_invalid_rate_emits_tax_rate_invalid_and_never_tax_rate_missing(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    corrupt_tax_rate(c, "abc")

    result = ProductionReadinessService(c).check_order(order.id)

    assert warning_codes(result) == ["tax_rate_invalid"]
    assert "tax_rate_missing" not in warning_codes(result)


def test_missing_sale_price_makes_the_estimate_unavailable(tmp_path):
    c = config(tmp_path)
    order = ready_order(c, sale_price=None)
    set_tax_rate(c, "6")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.sale_price is None
    assert result.estimated_cost == "110.00"
    assert result.tax_rate_percent == "6.00"
    assert result.estimated_tax is None
    assert result.estimated_margin is None
    assert result.financial_estimate_status == "unavailable"
    assert warning_codes(result) == ["sale_price_missing"]


def test_missing_total_cost_still_calculates_tax(tmp_path):
    c = config(tmp_path)
    order = ready_order(c, unit_cost=None)
    set_tax_rate(c, "6")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.estimated_cost is None
    assert result.estimated_tax == "12.00"
    assert result.estimated_margin is None
    assert result.estimated_margin_percent is None
    assert result.financial_estimate_status == "partial"
    assert warning_codes(result) == ["cost_data_missing"]


def test_zero_sale_price_returns_margin_but_no_margin_percent(tmp_path):
    c = config(tmp_path)
    order = ready_order(c, sale_price="0")
    set_tax_rate(c, "6")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.sale_price == "0.00"
    assert result.estimated_tax == "0.00"
    assert result.estimated_margin == "-110.00"
    assert result.estimated_margin_percent is None
    assert result.financial_estimate_status == "partial"
    assert warning_codes(result) == ["margin_percent_unavailable_zero_sale_price"]


def test_negative_margin_and_margin_percent_are_returned_unclamped(tmp_path):
    c = config(tmp_path)
    order = ready_order(c, sale_price="50")
    set_tax_rate(c, "6")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.estimated_tax == "3.00"
    assert result.estimated_margin == "-63.00"
    assert result.estimated_margin_percent == "-126.00"
    assert result.financial_estimate_status == "available"


def test_missing_rate_missing_price_and_missing_cost_warn_together_once_each(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_base(c, sale_price=None)
    add_lot(c, ingredient.id, "50", unit_cost=None)
    add_packaging(c, packaging.id, "1")

    result = ProductionReadinessService(c).check_order(order.id)

    assert warning_codes(result) == ["tax_rate_missing", "sale_price_missing", "cost_data_missing"]
    assert len(warning_codes(result)) == len(set(warning_codes(result)))


def test_financial_warnings_are_non_blocking_and_never_change_can_produce(tmp_path):
    c = config(tmp_path)
    order = ready_order(c, sale_price=None, unit_cost=None)
    corrupt_tax_rate(c, "abc")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.can_produce is True
    assert result.blocking_issues == []
    assert result.status == "warning"
    assert all(issue.severity == "warning" for issue in result.warnings)
    assert set(warning_codes(result)) == {"tax_rate_invalid", "sale_price_missing", "cost_data_missing"}


def test_financial_absence_does_not_change_physical_blockers(tmp_path):
    c = config(tmp_path)
    _, _, _, packaging, order = seed_base(c)
    add_packaging(c, packaging.id, "1")

    without_rate = ProductionReadinessService(c).check_order(order.id)
    set_tax_rate(c, "6")
    with_rate = ProductionReadinessService(c).check_order(order.id)

    assert without_rate.can_produce is with_rate.can_produce is False
    assert [issue.code for issue in without_rate.blocking_issues] == [issue.code for issue in with_rate.blocking_issues]
    assert with_rate.estimated_tax == "12.00"


@pytest.mark.parametrize("scenario", ["ready", "blocked", "warning"])
def test_financial_readiness_writes_nothing_for_every_result_shape(tmp_path, scenario):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_base(c)
    if scenario != "blocked":
        add_lot(c, ingredient.id, "50", expires=None if scenario == "ready" else date.today() + timedelta(days=5))
        add_packaging(c, packaging.id, "1")
    set_tax_rate(c, "6")
    before = snapshot(c, order.id)

    first = ProductionReadinessService(c).check_order(order.id)
    second = ProductionReadinessService(c).check_order(order.id)

    assert first.financial_estimate_status == second.financial_estimate_status
    assert snapshot(c, order.id) == before
    assert_no_forbidden_future_tables(table_names(c))


def test_repeated_readiness_calls_never_write_or_audit_the_tax_setting(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    set_tax_rate(c, "6")
    before = snapshot(c, order.id)

    for _ in range(5):
        ProductionReadinessService(c).check_order(order.id)

    assert snapshot(c, order.id) == before
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action='tax_rate_setting_changed'") == 1


def test_readiness_never_repairs_or_clears_an_invalid_persisted_rate(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    corrupt_tax_rate(c, "abc")
    before = snapshot(c, order.id)

    ProductionReadinessService(c).check_order(order.id)

    assert snapshot(c, order.id) == before
    assert scalar(c, "SELECT value FROM app_settings WHERE key=?", (DEFAULT_TAX_RATE_KEY,)) == "abc"


def test_readiness_reads_default_tax_rate_and_ignores_the_legacy_placeholder(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    SettingsRepository(c).upsert_setting("tax.default_rate", "99", "decimal_string", "legacy placeholder")

    result = ProductionReadinessService(c).check_order(order.id)

    assert result.tax_rate_percent is None
    assert result.financial_estimate_status == "unavailable"
    assert scalar(c, "SELECT value FROM app_settings WHERE key='tax.default_rate'") == "99"


def test_response_keeps_every_existing_field_and_adds_only_the_accepted_five(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)
    set_tax_rate(c, "6")

    payload = ProductionReadinessService(c).check_order(order.id).model_dump()

    assert {
        "order_id", "can_produce", "status", "blocking_issues", "warnings",
        "ingredients", "packaging", "estimated_cost", "estimated_tax",
        "estimated_margin", "generated_at",
    } <= set(payload)
    assert set(payload) - {
        "order_id", "can_produce", "status", "blocking_issues", "warnings",
        "ingredients", "packaging", "estimated_cost", "estimated_tax",
        "estimated_margin", "generated_at",
    } == {"sale_price", "tax_rate_percent", "tax_rate_effective_at", "estimated_margin_percent", "financial_estimate_status"}


def test_estimated_total_cost_is_absent_and_no_field_is_duplicated(tmp_path):
    c = config(tmp_path)
    order = ready_order(c)

    payload = ProductionReadinessService(c).check_order(order.id).model_dump()

    assert "estimated_total_cost" not in payload
    assert not {"total_cost", "tax_amount", "margin", "margin_percent"} & set(payload)


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_returns_the_financial_estimate_and_survives_an_invalid_persisted_rate(monkeypatch, tmp_path):
    db = tmp_path / "api-financials.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    order = ready_order(c)
    set_tax_rate(c, "6")
    api = TestClient(create_app())

    body = api.post(f"/api/orders/{order.id}/check-production-readiness").json()
    assert body["tax_rate_percent"] == "6.00"
    assert body["estimated_tax"] == "12.00"
    assert body["estimated_margin_percent"] == "39.00"
    assert body["financial_estimate_status"] == "available"
    assert "estimated_total_cost" not in body

    corrupt_tax_rate(c, "abc")
    response = api.post(f"/api/orders/{order.id}/check-production-readiness")

    assert response.status_code == 200
    assert response.json()["financial_estimate_status"] == "unavailable"
    assert response.json()["tax_rate_percent"] is None
    assert [issue["code"] for issue in response.json()["warnings"]] == ["tax_rate_invalid"]


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
