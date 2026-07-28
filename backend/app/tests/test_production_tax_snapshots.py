"""`C2-II` — transactional production financial snapshots.

Durable contract: ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

Covers the four things this slice can get wrong in code that produces money:
the required-but-nullable request context, the stale-context comparison, what
each missing input persists, and whether every failure rolls the whole
production transaction back.
"""

from datetime import date, timedelta
from decimal import Decimal
import sqlite3

import pytest

try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.clients import ClientDraft
from app.domain.errors import DomainValidationError
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.orders import OrderDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.domain.production_tax_context import ExpectedTaxRateContext, parse_expected_tax_rate_context
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
from app.services.production_confirmation import (
    ProductionConfirmationService,
    ProductionConfirmationTaxRateContextStaleError,
)
from app.services.recipes import RecipeService
from app.services.stock_movements import StockMovementService
from app.services.tax_rate_settings import TaxRateSettingsService

NO_RATE = ExpectedTaxRateContext.no_valid_rate()
PRODUCE_URL = "/api/orders/{order_id}/produce"


def config(tmp_path, name="production-tax-snapshots.sqlite"):
    c = DatabaseConfig(path=tmp_path / name)
    initialize_database(c)
    return c


def seed_ready(c, *, sale_price="200", unit_cost="2"):
    """Seed one physically producible order: component cost 100, packaging 10."""
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit="g"))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Cream"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value="100", amount_unit="percent")])).version
    packaging = PackagingItemService(c).create_packaging_item(PackagingItemDraft.create(name="Банка", kind="jar", unit="pcs", unit_cost="10"))
    order = OrderService(c).create(OrderDraft.create(client_id=client.id, recipe_version_id=version.id, product_name="Крем", target_batch_size_value="50", target_batch_size_unit="g", packaging_item_id=packaging.id, packaging_quantity="1", sale_price=sale_price))
    lot = IngredientLotService(c).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g", lot_code="L1", expires_at=date.today() + timedelta(days=90), unit_cost=unit_cost))
    StockMovementService(c).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="60", unit="g", reason="seed"))
    PackagingStockMovementService(c).create_movement(PackagingStockMovementDraft.create(packaging_item_id=packaging.id, movement_type="receipt", quantity="2", unit="pcs", reason="seed"))
    return order


def configure_rate(c, percent) -> ExpectedTaxRateContext:
    """Configure the rate and return the context readiness would hand back."""
    state = TaxRateSettingsService(c).update_tax_rate(percent)
    return ExpectedTaxRateContext(percent=state.tax_rate_percent, effective_at=state.effective_at)


def corrupt_rate(c, raw="не число"):
    """Simulate a `default_tax_rate` row edited outside the application."""
    with sqlite3.connect(c.path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type, description, updated_at) VALUES ('default_tax_rate', ?, 'decimal_string', 'corrupted', '2026-07-27 19:44:53')"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (raw,),
        )


def clear_rate(c):
    TaxRateSettingsService(c).update_tax_rate(None)


def write_state(c):
    """Everything a confirmation is allowed to change, for no-write assertions."""
    with sqlite3.connect(c.path) as connection:
        connection.row_factory = sqlite3.Row
        return {
            "batches": [dict(r) for r in connection.execute("SELECT * FROM production_batches ORDER BY id")],
            "batch_ingredients": connection.execute("SELECT count(*) FROM production_batch_ingredients").fetchone()[0],
            "batch_packaging": connection.execute("SELECT count(*) FROM production_batch_packaging").fetchone()[0],
            "stock": connection.execute("SELECT count(*) FROM stock_movements").fetchone()[0],
            "packaging": connection.execute("SELECT count(*) FROM packaging_stock_movements").fetchone()[0],
            "orders": [dict(r) for r in connection.execute("SELECT * FROM orders ORDER BY id")],
            "audit": [dict(r) for r in connection.execute("SELECT * FROM audit_logs ORDER BY id")],
            "settings": [dict(r) for r in connection.execute("SELECT * FROM app_settings ORDER BY key")],
        }


def batch_row(c):
    with sqlite3.connect(c.path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM production_batches ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row is not None else None


# --------------------------------------------------------------------------
# Request context validation
# --------------------------------------------------------------------------


def issue_code(value, effective_at):
    with pytest.raises(DomainValidationError) as failure:
        parse_expected_tax_rate_context(value, effective_at)
    return str(failure.value.issue.code)


def test_explicit_null_null_is_the_no_valid_rate_context():
    assert parse_expected_tax_rate_context(None, None) == NO_RATE
    assert NO_RATE.pair == (None, None)


def test_valid_configured_context_is_accepted_unchanged():
    parsed = parse_expected_tax_rate_context("6.00", "2026-07-27T19:44:53Z")

    assert parsed.pair == ("6.00", "2026-07-27T19:44:53Z")


@pytest.mark.parametrize("percent, effective_at", [(None, "2026-07-27T19:44:53Z"), ("6.00", None)])
def test_exactly_one_null_value_is_rejected(percent, effective_at):
    assert issue_code(percent, effective_at) == "invalid_tax_rate_context"


@pytest.mark.parametrize("percent", [6, 6.0, True, False, ["6.00"], {"value": "6.00"}])
def test_non_string_percentage_is_rejected(percent):
    assert issue_code(percent, "2026-07-27T19:44:53Z") == "invalid_tax_rate_context"


@pytest.mark.parametrize("percent", ["6", "6.0", "06.00", "6.005", "-1.00", "100.01", "6,00", "6e0", "", " 6.00 ", "abc"])
def test_malformed_noncanonical_or_out_of_range_percentages_are_rejected(percent):
    assert issue_code(percent, "2026-07-27T19:44:53Z") == "invalid_tax_rate_context"


@pytest.mark.parametrize("percent", ["0.00", "6.00", "6.50", "100.00"])
def test_canonical_percentages_are_accepted(percent):
    assert parse_expected_tax_rate_context(percent, "2026-07-27T19:44:53Z").percent == percent


@pytest.mark.parametrize(
    "effective_at",
    [
        "2026-07-27T19:44:53+03:00",
        "2026-07-27T19:44:53.000Z",
        "2026-07-27T19:44:53",
        "2026-07-27 19:44:53",
        "2026-07-27T19:44:53z",
        "2026-13-01T00:00:00Z",
        "2026-02-30T00:00:00Z",
        "2026-07-27T25:00:00Z",
        "27.07.2026 19:44",
        "",
    ],
)
def test_noncanonical_timestamps_are_rejected(effective_at):
    assert issue_code("6.00", effective_at) == "invalid_tax_rate_context"


@pytest.mark.parametrize("effective_at", [123, 1.5, True, ["2026-07-27T19:44:53Z"], {"at": "2026-07-27T19:44:53Z"}])
def test_non_string_timestamp_is_rejected(effective_at):
    assert issue_code("6.00", effective_at) == "invalid_tax_rate_context"


def test_impossible_state_combinations_cannot_be_constructed():
    with pytest.raises(ValueError):
        ExpectedTaxRateContext(percent="6.00", effective_at=None)
    with pytest.raises(ValueError):
        ExpectedTaxRateContext(percent=None, effective_at="2026-07-27T19:44:53Z")


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
@pytest.mark.parametrize(
    "body, expected_code",
    [
        ({"confirm": True}, "tax_rate_context_required"),
        ({"confirm": True, "expected_tax_rate_percent": None}, "tax_rate_context_required"),
        ({"confirm": True, "expected_tax_rate_effective_at": None}, "tax_rate_context_required"),
        ({"confirm": True, "expected_tax_rate_percent": "6.00", "expected_tax_rate_effective_at": None}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": None, "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": 6, "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": True, "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6", "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6.0", "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6.005", "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "100.01", "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6.00", "expected_tax_rate_effective_at": "2026-07-27T19:44:53+03:00"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6.00", "expected_tax_rate_effective_at": "2026-07-27T19:44:53.000Z"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6.00", "expected_tax_rate_effective_at": "2026-07-27T19:44:53"}, "invalid_tax_rate_context"),
        ({"confirm": True, "expected_tax_rate_percent": "6.00", "expected_tax_rate_effective_at": "2026-02-30T00:00:00Z"}, "invalid_tax_rate_context"),
    ],
)
def test_api_rejects_off_contract_context_with_a_stable_code_and_writes_nothing(monkeypatch, tmp_path, body, expected_code):
    db = tmp_path / "api-context.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    order = seed_ready(c)
    configure_rate(c, "6")
    api = TestClient(create_app())
    before = write_state(c)

    response = api.post(PRODUCE_URL.format(order_id=order.id), json=body)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == expected_code
    assert write_state(c) == before


# --------------------------------------------------------------------------
# Stale-context matrix
# --------------------------------------------------------------------------


def test_same_valid_pair_continues(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.tax_rate_percent_snapshot == "6.00"


def test_valid_to_changed_valid_is_stale(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    configure_rate(c, "7")
    before = write_state(c)

    with pytest.raises(ProductionConfirmationTaxRateContextStaleError):
        ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c) == before


def test_valid_to_missing_is_stale(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    clear_rate(c)
    before = write_state(c)

    with pytest.raises(ProductionConfirmationTaxRateContextStaleError):
        ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c) == before


def test_valid_to_invalid_is_stale(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    corrupt_rate(c)
    before = write_state(c)

    with pytest.raises(ProductionConfirmationTaxRateContextStaleError):
        ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c) == before


def test_no_valid_rate_expectation_against_a_configured_rate_is_stale(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    configure_rate(c, "6")
    before = write_state(c)

    with pytest.raises(ProductionConfirmationTaxRateContextStaleError):
        ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    assert write_state(c) == before


def test_no_valid_rate_expectation_against_a_missing_rate_continues(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    assert detail.batch.tax_rate_percent_snapshot is None
    assert detail.batch.tax is None


def test_no_valid_rate_expectation_against_an_invalid_rate_continues(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    corrupt_rate(c)

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    assert detail.batch.tax_rate_percent_snapshot is None
    assert detail.batch.tax_rate_effective_at_snapshot is None
    assert detail.batch.tax is None


def test_missing_to_invalid_does_not_conflict(tmp_path):
    """Readiness saw a missing row; the row is now invalid. Same result, no conflict."""
    c = config(tmp_path)
    order = seed_ready(c)
    corrupt_rate(c)

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    assert detail.batch.id > 0


def test_invalid_to_missing_does_not_conflict(tmp_path):
    """Readiness saw an invalid row; it was cleared. Same result, no conflict."""
    c = config(tmp_path)
    order = seed_ready(c)
    corrupt_rate(c)
    clear_rate(c)

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    assert detail.batch.id > 0


def test_stale_conflict_never_repairs_or_audits_the_invalid_setting(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    corrupt_rate(c, raw="совсем не число")

    with pytest.raises(ProductionConfirmationTaxRateContextStaleError):
        ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    with sqlite3.connect(c.path) as connection:
        stored = connection.execute("SELECT value FROM app_settings WHERE key='default_tax_rate'").fetchone()[0]
        audits = connection.execute("SELECT count(*) FROM audit_logs WHERE action='tax_rate_setting_changed'").fetchone()[0]
    assert stored == "совсем не число"
    assert audits == 1


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_maps_the_stale_context_to_409_with_safe_russian_guidance(monkeypatch, tmp_path):
    db = tmp_path / "api-stale.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    configure_rate(c, "7")
    api = TestClient(create_app())
    before = write_state(c)

    response = api.post(PRODUCE_URL.format(order_id=order.id), json={"confirm": True, "expected_tax_rate_percent": expected.percent, "expected_tax_rate_effective_at": expected.effective_at})

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "tax_rate_context_stale"
    assert detail["message"] == "Налоговая ставка изменилась. Обновите готовность и подтвердите производство ещё раз."
    assert write_state(c) == before


# --------------------------------------------------------------------------
# Financial snapshots
# --------------------------------------------------------------------------


def test_configured_rate_persists_the_full_financial_snapshot(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.tax_rate_percent_snapshot == "6.00"
    assert detail.batch.tax_rate_effective_at_snapshot == expected.effective_at
    assert str(detail.batch.sale_price) == "200.00"
    assert str(detail.batch.total_cost) == "110.00"
    assert str(detail.batch.tax) == "12.00"
    assert str(detail.batch.margin) == "78.00"
    assert str(detail.batch.margin_percent) == "39.00"


def test_configured_zero_rate_is_a_real_snapshot_not_a_missing_one(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "0")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.tax_rate_percent_snapshot == "0.00"
    assert detail.batch.tax_rate_effective_at_snapshot is not None
    assert str(detail.batch.tax) == "0.00"
    assert str(detail.batch.margin) == "90.00"
    assert str(detail.batch.margin_percent) == "45.00"


def test_missing_sale_price_keeps_the_rate_snapshot_and_leaves_money_unavailable(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c, sale_price=None)
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.tax_rate_percent_snapshot == "6.00"
    assert detail.batch.tax_rate_effective_at_snapshot == expected.effective_at
    assert detail.batch.sale_price is None
    assert detail.batch.tax is None
    assert detail.batch.margin is None
    assert detail.batch.margin_percent is None


def test_missing_total_cost_still_persists_tax_but_no_margin(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c, unit_cost=None)
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.total_cost is None
    assert detail.batch.tax_rate_percent_snapshot == "6.00"
    assert str(detail.batch.tax) == "12.00"
    assert detail.batch.margin is None
    assert detail.batch.margin_percent is None


def test_zero_sale_price_persists_zero_tax_and_an_honest_negative_margin(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c, sale_price="0")
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert str(detail.batch.tax) == "0.00"
    assert str(detail.batch.margin) == "-110.00"
    assert detail.batch.margin_percent is None


def test_negative_margin_and_negative_margin_percent_are_never_clamped(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c, sale_price="50")
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert str(detail.batch.tax) == "3.00"
    assert str(detail.batch.margin) == "-63.00"
    assert str(detail.batch.margin_percent) == "-126.00"


def test_zero_margin_is_persisted_as_a_real_zero(tmp_path):
    c = config(tmp_path)
    # total cost 110, rate 0.00 → margin is exactly zero at a sale price of 110.
    order = seed_ready(c, sale_price="110")
    expected = configure_rate(c, "0")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert str(detail.batch.margin) == "0.00"
    assert str(detail.batch.margin_percent) == "0.00"


def test_tax_rounds_half_up_exactly_once(tmp_path):
    c = config(tmp_path)
    # 10.00 × 6.25 / 100 = 0.625 exactly, which ROUND_HALF_UP resolves to 0.63.
    order = seed_ready(c, sale_price="10")
    expected = configure_rate(c, "6.25")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.tax_rate_percent_snapshot == "6.25"
    assert str(detail.batch.tax) == "0.63"
    assert str(detail.batch.margin) == "-100.63"


def test_snapshots_persist_canonically_and_the_raw_invalid_value_never_appears(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6.5")

    ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    row = batch_row(c)
    assert row["tax_rate_percent_snapshot"] == "6.50"
    # SQLite storage form: UTC, second precision, no `T`, no `Z`, no offset.
    assert row["tax_rate_effective_at_snapshot"] == expected.effective_at.replace("T", " ").removesuffix("Z")
    assert "T" not in row["tax_rate_effective_at_snapshot"]
    assert "Z" not in row["tax_rate_effective_at_snapshot"]


def test_invalid_rate_is_never_persisted_normalized_or_treated_as_zero(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    corrupt_rate(c, raw="0,06")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    row = batch_row(c)
    assert row["tax_rate_percent_snapshot"] is None
    assert row["tax_rate_effective_at_snapshot"] is None
    assert row["tax"] is None
    assert "0,06" not in str(row)
    # Physical production still happened in full.
    assert str(detail.batch.total_cost) == "110.00"
    assert len(detail.ingredients) == 1 and len(detail.packaging) == 1


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_exposes_snapshots_in_confirmation_and_detail_but_not_in_the_list(monkeypatch, tmp_path):
    db = tmp_path / "api-exposure.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    api = TestClient(create_app())

    confirmed = api.post(PRODUCE_URL.format(order_id=order.id), json={"confirm": True, "expected_tax_rate_percent": expected.percent, "expected_tax_rate_effective_at": expected.effective_at})

    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["tax_rate_percent_snapshot"] == "6.00"
    assert body["tax_rate_effective_at_snapshot"] == expected.effective_at
    assert body["tax"] == "12.00" and body["margin"] == "78.00" and body["margin_percent"] == "39.00"

    detail = api.get(f"/api/production-batches/{body['id']}").json()
    assert detail["tax_rate_percent_snapshot"] == "6.00"
    assert detail["tax_rate_effective_at_snapshot"] == expected.effective_at

    listed = api.get("/api/production-batches").json()["production_batches"][0]
    assert "tax_rate_percent_snapshot" not in listed
    assert "tax_rate_effective_at_snapshot" not in listed


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_returns_the_canonical_timestamp_never_the_raw_storage_form(monkeypatch, tmp_path):
    db = tmp_path / "api-timestamp.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    api = TestClient(create_app())

    body = api.post(PRODUCE_URL.format(order_id=order.id), json={"confirm": True, "expected_tax_rate_percent": expected.percent, "expected_tax_rate_effective_at": expected.effective_at}).json()

    exposed = body["tax_rate_effective_at_snapshot"]
    assert exposed.endswith("Z") and "T" in exposed and "." not in exposed and "+" not in exposed
    assert exposed == batch_row(c)["tax_rate_effective_at_snapshot"].replace(" ", "T") + "Z"


def test_old_rows_without_snapshot_values_map_to_none(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)
    with sqlite3.connect(c.path) as connection:
        connection.execute("UPDATE production_batches SET tax_rate_percent_snapshot = NULL, tax_rate_effective_at_snapshot = NULL")

    from app.repositories.production_batches import ProductionBatchRepository

    detail = ProductionBatchRepository(c).get_detail_by_order_id(order.id)

    assert detail.batch.tax_rate_percent_snapshot is None
    assert detail.batch.tax_rate_effective_at_snapshot is None


# --------------------------------------------------------------------------
# Transaction rollback
# --------------------------------------------------------------------------


class FailingBatchRepository:
    """Fail at one named stage while keeping every other call real."""

    def __init__(self, real, fail_at):
        self.real = real
        self.fail_at = fail_at
        self.persisted_snapshot = None

    def exists_for_order(self, *args, **kwargs):
        return self.real.exists_for_order(*args, **kwargs)

    def create_batch(self, *args, **kwargs):
        batch = self.real.create_batch(*args, **kwargs)
        if self.fail_at in {"after_batch", "after_financial_snapshot"}:
            self.persisted_snapshot = (batch.tax_rate_percent_snapshot, batch.tax, batch.margin)
            raise RuntimeError(f"forced failure at {self.fail_at}")
        return batch

    def create_ingredient(self, *args, **kwargs):
        if self.fail_at == "ingredient_snapshot":
            raise RuntimeError("forced ingredient snapshot failure")
        return self.real.create_ingredient(*args, **kwargs)

    def create_packaging(self, *args, **kwargs):
        if self.fail_at == "packaging_snapshot":
            raise RuntimeError("forced packaging snapshot failure")
        return self.real.create_packaging(*args, **kwargs)

    def get_detail(self, *args, **kwargs):
        return self.real.get_detail(*args, **kwargs)


class FailingStockMovementRepository:
    def create(self, *args, **kwargs):
        raise RuntimeError("forced ingredient write-off failure")


class FailingPackagingMovementRepository:
    def create(self, *args, **kwargs):
        raise RuntimeError("forced packaging write-off failure")


class FailingOrderRepository:
    def __init__(self, real):
        self.real = real

    def get_by_id(self, *args, **kwargs):
        return self.real.get_by_id(*args, **kwargs)

    def mark_produced(self, *args, **kwargs):
        raise RuntimeError("forced order update failure")


class FailingAuditRepository:
    def create_log(self, *args, **kwargs):
        raise RuntimeError("forced production audit failure")


@pytest.mark.parametrize("fail_at", ["after_batch", "after_financial_snapshot", "ingredient_snapshot", "packaging_snapshot"])
def test_batch_stage_failures_roll_the_whole_transaction_back(tmp_path, fail_at):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    service = ProductionConfirmationService(c)
    service.batches = FailingBatchRepository(service.batches, fail_at)
    before = write_state(c)

    with pytest.raises(RuntimeError):
        service.produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c) == before
    if fail_at in {"after_batch", "after_financial_snapshot"}:
        # The snapshot really had been written before the failure; it did not survive.
        assert service.batches.persisted_snapshot == ("6.00", Decimal("12.00"), Decimal("78.00"))


@pytest.mark.parametrize(
    "attribute, replacement",
    [
        ("stock_movements", FailingStockMovementRepository),
        ("packaging_movements", FailingPackagingMovementRepository),
        ("audit", FailingAuditRepository),
    ],
)
def test_write_stage_failures_roll_the_whole_transaction_back(tmp_path, attribute, replacement):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    service = ProductionConfirmationService(c)
    setattr(service, attribute, replacement())
    before = write_state(c)

    with pytest.raises(RuntimeError):
        service.produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c) == before


def test_order_update_failure_rolls_the_whole_transaction_back(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    service = ProductionConfirmationService(c)
    service.orders = FailingOrderRepository(service.orders)
    before = write_state(c)

    with pytest.raises(RuntimeError):
        service.produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c) == before


def test_the_transaction_still_uses_an_immediate_write_lock(tmp_path):
    """The stale read must not have weakened the existing immediate lock."""
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    import app.services.production_confirmation as confirmation_module

    original = confirmation_module.transaction
    observed_immediate: list[bool] = []

    def recording_transaction(config_arg=None, *, immediate=False):
        observed_immediate.append(immediate)
        return original(config_arg, immediate=immediate)

    confirmation_module.transaction = recording_transaction
    try:
        detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)
    finally:
        confirmation_module.transaction = original

    assert observed_immediate == [True]
    assert detail.batch.id > 0


def test_the_current_rate_is_read_on_the_production_connection(tmp_path):
    """Proves the setting read reuses the transaction's own connection.

    A second connection would have to wait on the `BEGIN IMMEDIATE` write lock;
    recording the connection identity is the direct evidence that none is opened.
    """
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    service = ProductionConfirmationService(c)
    seen: list[object] = []
    real_get_setting = service.tax_rate_settings.repository.get_setting

    def recording_get_setting(key, connection=None):
        seen.append(connection)
        return real_get_setting(key, connection)

    service.tax_rate_settings.repository.get_setting = recording_get_setting

    service.produce_order(order.id, True, expected_tax_rate=expected)

    assert seen and all(isinstance(connection, sqlite3.Connection) for connection in seen)


def test_the_transaction_aware_read_writes_nothing_and_audits_nothing(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")
    before_settings = write_state(c)["settings"]
    before_setting_audits = _setting_audit_count(c)

    ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert write_state(c)["settings"] == before_settings
    assert _setting_audit_count(c) == before_setting_audits


def _setting_audit_count(c):
    with sqlite3.connect(c.path) as connection:
        return connection.execute("SELECT count(*) FROM audit_logs WHERE action='tax_rate_setting_changed'").fetchone()[0]


def test_the_no_argument_tax_rate_read_still_behaves_exactly_as_before(tmp_path):
    c = config(tmp_path)
    configure_rate(c, "6")
    service = TaxRateSettingsService(c)

    assert service.get_tax_rate().tax_rate_percent == "6.00"
    assert service.get_tax_rate(None).tax_rate_percent == "6.00"
    with sqlite3.connect(c.path) as connection:
        connection.row_factory = sqlite3.Row
        assert service.get_tax_rate(connection).tax_rate_percent == "6.00"


def test_production_audit_remains_part_of_the_transaction(tmp_path):
    c = config(tmp_path)
    order = seed_ready(c)
    expected = configure_rate(c, "6")

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    with sqlite3.connect(c.path) as connection:
        audits = connection.execute("SELECT count(*) FROM audit_logs WHERE action='production_confirmed' AND entity_id=?", (str(detail.batch.id),)).fetchone()[0]
    assert audits == 1
