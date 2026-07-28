"""The persisted tax-rate timestamp boundary (`C2-II` hardening).

Durable contract: ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

`tax_rate_effective_at_snapshot` is an immutable production snapshot, so a
persisted timestamp whose meaning is uncertain must be rejected rather than
coerced. Dropping a `+03:00` offset and calling the result UTC would silently
record an instant three hours away from the one the user actually stored.

These tests pin the exact accepted forms, and prove that an off-contract stored
timestamp degrades to the no-valid-rate context without blocking physical
production and without ever reaching a `ProductionBatch`.
"""

from datetime import date, datetime, timedelta
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.domain.clients import ClientDraft
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.orders import OrderDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.domain.production_financials import FinancialWarningCode
from app.domain.production_tax_context import ExpectedTaxRateContext
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.domain.stock_movements import StockMovementDraft
from app.domain.tax_rate_timestamps import (
    api_timestamp,
    is_readable_storage_timestamp,
    parse_storage_timestamp,
    storage_timestamp,
)
from app.services.clients import ClientService
from app.services.database import initialize_database
from app.services.ingredient_lots import IngredientLotService
from app.services.ingredients import IngredientService
from app.services.orders import OrderService
from app.services.packaging_items import PackagingItemService
from app.services.packaging_stock_movements import PackagingStockMovementService
from app.services.production_confirmation import ProductionConfirmationService
from app.services.production_readiness import ProductionReadinessService
from app.services.recipes import RecipeService
from app.services.stock_movements import StockMovementService
from app.services.tax_rate_context import read_tax_rate_context
from app.services.tax_rate_settings import TaxRateSettingsService

NO_RATE = ExpectedTaxRateContext.no_valid_rate()


# --------------------------------------------------------------------------
# Accepted storage forms
# --------------------------------------------------------------------------


def test_the_documented_storage_form_is_accepted():
    assert parse_storage_timestamp("2026-07-27 19:44:53") == datetime(2026, 7, 27, 19, 44, 53)
    assert is_readable_storage_timestamp("2026-07-27 19:44:53")


@pytest.mark.parametrize("legacy", ["2026-07-27T19:44:53", "2026-07-27T19:44:53Z"])
def test_the_two_supported_exact_legacy_forms_are_accepted(legacy):
    """Existing local rows may carry these; both are unambiguously UTC."""
    assert parse_storage_timestamp(legacy) == datetime(2026, 7, 27, 19, 44, 53)


def test_accepted_forms_all_normalize_to_the_same_canonical_api_value():
    canonical = "2026-07-27T19:44:53Z"
    for stored in ("2026-07-27 19:44:53", "2026-07-27T19:44:53", "2026-07-27T19:44:53Z"):
        assert api_timestamp(stored) == canonical


def test_round_tripping_the_api_form_reproduces_the_storage_form():
    assert storage_timestamp("2026-07-27T19:44:53Z") == "2026-07-27 19:44:53"
    assert api_timestamp(storage_timestamp("2026-07-27T19:44:53Z")) == "2026-07-27T19:44:53Z"


# --------------------------------------------------------------------------
# Rejected storage forms
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stored",
    [
        "2026-07-27T19:44:53+03:00",
        "2026-07-27 19:44:53+03:00",
        "2026-07-27T19:44:53-05:00",
        "2026-07-27T19:44:53.123",
        "2026-07-27 19:44:53.123456",
        "2026-07-27T19:44:53.000Z",
        "2026-02-30 00:00:00",
        "2026-13-01 00:00:00",
        "2026-07-27 25:00:00",
        "2026-07-27 19:60:00",
        "2026-07-27 19:44",
        "2026-07-27",
        "не время",
        "",
        "   ",
        "20260727194453",
        "27.07.2026 19:44:53",
    ],
)
def test_off_contract_stored_timestamps_are_rejected(stored):
    assert parse_storage_timestamp(stored) is None
    assert not is_readable_storage_timestamp(stored)
    assert api_timestamp(stored) is None


def test_an_offset_is_rejected_rather_than_silently_dropped():
    """The failure mode this guards: `+03:00` read back as UTC.

    The naive fallback would have produced `19:44:53` UTC for a value that is
    actually `16:44:53` UTC, and then frozen that into a production snapshot.
    """
    assert parse_storage_timestamp("2026-07-27T19:44:53+03:00") is None
    assert api_timestamp("2026-07-27T19:44:53+03:00") != "2026-07-27T19:44:53Z"


@pytest.mark.parametrize("stored", [None, 12345, 1.5, True, object()])
def test_non_string_stored_values_are_rejected(stored):
    assert parse_storage_timestamp(stored) is None


# --------------------------------------------------------------------------
# Reducer, readiness, and confirmation behavior
# --------------------------------------------------------------------------


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "tax-timestamp-boundary.sqlite")
    initialize_database(c)
    return c


def corrupt_timestamp(c, raw):
    """Store a valid percentage with an off-contract `updated_at`."""
    with sqlite3.connect(c.path) as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value, value_type, description, updated_at)"
            " VALUES ('default_tax_rate', '6.00', 'decimal_string', 'corrupted timestamp', ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (raw,),
        )


def seed_ready(c):
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit="g"))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Cream"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value="100", amount_unit="percent")])).version
    packaging = PackagingItemService(c).create_packaging_item(PackagingItemDraft.create(name="Банка", kind="jar", unit="pcs", unit_cost="10"))
    order = OrderService(c).create(OrderDraft.create(client_id=client.id, recipe_version_id=version.id, product_name="Крем", target_batch_size_value="50", target_batch_size_unit="g", packaging_item_id=packaging.id, packaging_quantity="1", sale_price="200"))
    lot = IngredientLotService(c).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g", lot_code="L1", expires_at=date.today() + timedelta(days=90), unit_cost="2"))
    StockMovementService(c).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="60", unit="g", reason="seed"))
    PackagingStockMovementService(c).create_movement(PackagingStockMovementDraft.create(packaging_item_id=packaging.id, movement_type="receipt", quantity="2", unit="pcs", reason="seed"))
    return order


OFF_CONTRACT = ["2026-07-27T19:44:53+03:00", "2026-07-27 19:44:53.123456", "2026-02-30 00:00:00", "не время"]


@pytest.mark.parametrize("raw", OFF_CONTRACT)
def test_an_off_contract_stored_timestamp_reduces_to_the_no_valid_rate_context(tmp_path, raw):
    c = config(tmp_path)
    corrupt_timestamp(c, raw)

    context = read_tax_rate_context(TaxRateSettingsService(c))

    assert context.percent is None
    assert context.effective_at is None
    assert context.invalid is True
    assert context.comparable_pair == (None, None)


@pytest.mark.parametrize("raw", OFF_CONTRACT)
def test_readiness_reports_the_invalid_rate_warning_and_null_context(tmp_path, raw):
    c = config(tmp_path)
    order = seed_ready(c)
    corrupt_timestamp(c, raw)

    readiness = ProductionReadinessService(c).check_order(order.id)

    codes = [issue.code for issue in readiness.warnings]
    assert FinancialWarningCode.TAX_RATE_INVALID.value in codes
    assert FinancialWarningCode.TAX_RATE_MISSING.value not in codes
    assert readiness.tax_rate_percent is None
    assert readiness.tax_rate_effective_at is None
    assert readiness.estimated_tax is None
    assert readiness.estimated_margin is None
    assert readiness.financial_estimate_status == "unavailable"
    # Physical production stays possible.
    assert readiness.can_produce is True


@pytest.mark.parametrize("raw", OFF_CONTRACT)
def test_confirmation_accepts_null_null_and_persists_no_raw_timestamp(tmp_path, raw):
    c = config(tmp_path)
    order = seed_ready(c)
    corrupt_timestamp(c, raw)

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=NO_RATE)

    assert detail.batch.tax_rate_percent_snapshot is None
    assert detail.batch.tax_rate_effective_at_snapshot is None
    assert detail.batch.tax is None
    assert detail.batch.margin is None
    assert detail.batch.margin_percent is None
    # Physical production completed in full.
    assert str(detail.batch.total_cost) == "110.00"
    assert len(detail.ingredients) == 1 and len(detail.packaging) == 1

    with sqlite3.connect(c.path) as connection:
        connection.row_factory = sqlite3.Row
        batches = [dict(row) for row in connection.execute("SELECT * FROM production_batches")]
        setting = connection.execute("SELECT value, updated_at FROM app_settings WHERE key='default_tax_rate'").fetchone()
        setting_audits = connection.execute("SELECT count(*) FROM audit_logs WHERE action='tax_rate_setting_changed'").fetchone()[0]
    assert raw not in str(batches)
    # The setting is not repaired, cleared, rewritten, or audited.
    assert tuple(setting) == ("6.00", raw)
    assert setting_audits == 0


def test_a_canonical_stored_timestamp_still_produces_a_full_snapshot(tmp_path):
    """The hardening must not reject the normal configured path."""
    c = config(tmp_path)
    order = seed_ready(c)
    state = TaxRateSettingsService(c).update_tax_rate("6")
    expected = ExpectedTaxRateContext(percent=state.tax_rate_percent, effective_at=state.effective_at)

    detail = ProductionConfirmationService(c).produce_order(order.id, True, expected_tax_rate=expected)

    assert detail.batch.tax_rate_percent_snapshot == "6.00"
    assert detail.batch.tax_rate_effective_at_snapshot == state.effective_at
    assert str(detail.batch.tax) == "12.00"
