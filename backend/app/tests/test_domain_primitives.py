from decimal import Decimal
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.repositories.database import ALLOWED_PR6_TABLES
from app.services.database import initialize_database
from app.domain.conversions import milliliters_to_grams
from app.domain.decimal_utils import (
    parse_decimal,
    quantize_count,
    quantize_money,
    quantize_percentage,
    quantize_volume,
    quantize_weight,
)
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.measurements import Density, Money, Percentage, Quantity, Volume, Weight
from app.domain.units import MVP_UNITS, UnitCode


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    return {row[0] for row in rows}


def test_parse_decimal_accepts_strings_commas_ints_and_decimal():
    assert parse_decimal("12.50") == Decimal("12.50")
    assert parse_decimal("12,50") == Decimal("12.50")
    assert parse_decimal(12) == Decimal("12")
    assert parse_decimal(Decimal("0.125")) == Decimal("0.125")


@pytest.mark.parametrize("bad_value", ["", "много", object()])
def test_parse_decimal_rejects_invalid_values(bad_value):
    with pytest.raises(DomainValidationError) as exc_info:
        parse_decimal(bad_value, field="Остаток")

    assert exc_info.value.issue.code == DomainIssueCode.INVALID_DECIMAL
    assert exc_info.value.issue.field == "Остаток"


@pytest.mark.parametrize("bad_float", [1.2, True])
def test_parse_decimal_rejects_float_and_bool_inputs(bad_float):
    with pytest.raises(DomainValidationError) as exc_info:
        parse_decimal(bad_float, field="critical_amount")

    assert exc_info.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED


def test_quantization_rules_are_explicit_and_half_up():
    assert quantize_weight("1.2345") == Decimal("1.235")
    assert quantize_volume("2.3455") == Decimal("2.346")
    assert quantize_percentage("3.455") == Decimal("3.46")
    assert quantize_money("10.005") == Decimal("10.01")
    assert quantize_count("2.0") == Decimal("2")


def test_mvp_unit_definitions_have_canonical_codes_and_russian_labels():
    assert set(MVP_UNITS) == {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PERCENT, UnitCode.PIECE}
    assert MVP_UNITS[UnitCode.GRAM].russian_label == "г"
    assert MVP_UNITS[UnitCode.MILLILITER].russian_label == "мл"
    assert MVP_UNITS[UnitCode.PERCENT].russian_label == "%"
    assert MVP_UNITS[UnitCode.PIECE].russian_label == "шт"


def test_measurement_value_objects_quantize_and_attach_units():
    assert Weight.from_value("10.1234").grams == Decimal("10.123")
    assert Weight.from_value("10.1234").unit == UnitCode.GRAM
    assert Volume.from_value("5.5555").milliliters == Decimal("5.556")
    assert Percentage.from_value("12.345").value == Decimal("12.35")
    assert Money.from_value("99.995").amount == Decimal("100.00")
    assert Quantity.from_value("4.0").count == Decimal("4")
    assert Density.from_value("0.98765").grams_per_milliliter == Decimal("0.9877")


def test_fractional_counts_are_rejected_instead_of_rounded():
    with pytest.raises(DomainValidationError) as quantize_exc:
        quantize_count("2.5")
    assert quantize_exc.value.issue.code == DomainIssueCode.NON_INTEGER_QUANTITY

    with pytest.raises(DomainValidationError) as quantity_exc:
        Quantity.from_value("4.4")
    assert quantity_exc.value.issue.code == DomainIssueCode.NON_INTEGER_QUANTITY


def test_whole_number_counts_are_accepted_and_normalized():
    assert quantize_count("2") == Decimal("2")
    assert quantize_count(2) == Decimal("2")
    assert quantize_count(Decimal("2")) == Decimal("2")
    assert quantize_count("2.0") == Decimal("2")
    assert Quantity.from_value("3.0").count == Decimal("3")


def test_negative_measurements_are_rejected():
    with pytest.raises(DomainValidationError) as exc_info:
        Weight.from_value("-0.001")

    assert exc_info.value.issue.code == DomainIssueCode.NEGATIVE_QUANTITY


def test_percentage_bounds_reject_values_over_100():
    with pytest.raises(DomainValidationError) as exc_info:
        Percentage.from_value("100.01")

    assert exc_info.value.issue.code == DomainIssueCode.PERCENTAGE_OUT_OF_RANGE


def test_density_must_be_positive():
    with pytest.raises(DomainValidationError) as exc_info:
        Density.from_value("0")

    assert exc_info.value.issue.code == DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY


def test_milliliters_to_grams_uses_density_without_silent_water_assumption():
    result = milliliters_to_grams(Volume.from_value("10"), Density.from_value("0.95"))

    assert result.is_exact is True
    assert result.weight == Weight.from_value("9.5")
    assert result.warnings == ()


def test_milliliters_to_grams_returns_warning_when_density_is_missing():
    result = milliliters_to_grams(Volume.from_value("10"), None)

    assert result.is_exact is False
    assert result.weight is None
    assert len(result.warnings) == 1
    assert result.warnings[0].code == DomainIssueCode.MISSING_DENSITY


def test_domain_primitives_do_not_add_unrelated_business_tables(tmp_path):
    config = DatabaseConfig(path=tmp_path / "domain-primitives.sqlite")
    initialize_database(config)

    tables = table_names(config.path)

    assert tables <= ALLOWED_PR6_TABLES
    assert not {
        "recipes",
        "recipe_versions",
        "recipe_ingredients",
        "client_recipes",
        "client_recipe_ingredients",
            "packaging_items",
        "stock_movements",
        "clients",
        "client_wishes",
        "client_feedback",
        "orders",
        "production_batches",
        "import_sources",
        "import_drafts",
        "backup_records",
    } & tables
