"""Pure-domain coverage for the `C2-I` readiness financial calculation.

Durable contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.
Nothing here touches a database, a repository, or an HTTP layer.
"""

from decimal import Decimal

import pytest

from app.domain.production_financials import (
    FinancialEstimateStatus,
    FinancialWarningCode,
    ProductionFinancialInputs,
    TaxRateContext,
    estimate_production_financials,
)

EFFECTIVE_AT = "2026-07-27T19:44:53Z"


def configured(percent: str) -> TaxRateContext:
    return TaxRateContext.configured(Decimal(percent), EFFECTIVE_AT)


def estimate(*, sale_price=None, total_cost=None, rate=None):
    return estimate_production_financials(
        ProductionFinancialInputs(
            sale_price=None if sale_price is None else Decimal(sale_price),
            total_cost=None if total_cost is None else Decimal(total_cost),
            tax_rate=rate if rate is not None else configured("6.00"),
        )
    )


def codes(result) -> list[str]:
    return [code.value for code in result.warning_codes]


# --- Calculation -----------------------------------------------------------


def test_configured_six_percent_produces_the_full_estimate():
    result = estimate(sale_price="200.00", total_cost="110.00")

    assert result.sale_price == "200.00"
    assert result.total_cost == "110.00"
    assert result.tax_rate_percent == "6.00"
    assert result.tax_rate_effective_at == EFFECTIVE_AT
    assert result.tax_amount == "12.00"
    assert result.margin == "78.00"
    assert result.margin_percent == "39.00"
    assert result.status is FinancialEstimateStatus.AVAILABLE
    assert codes(result) == []


def test_configured_zero_percent_is_a_real_rate_and_not_a_missing_one():
    result = estimate(sale_price="200.00", total_cost="110.00", rate=configured("0.00"))

    assert result.tax_rate_percent == "0.00"
    assert result.tax_amount == "0.00"
    assert result.margin == "90.00"
    assert result.margin_percent == "45.00"
    assert result.status is FinancialEstimateStatus.AVAILABLE
    assert codes(result) == []


def test_zero_margin_is_reported_as_an_exact_zero():
    result = estimate(sale_price="100.00", total_cost="94.00")

    assert result.tax_amount == "6.00"
    assert result.margin == "0.00"
    assert result.margin_percent == "0.00"
    assert result.status is FinancialEstimateStatus.AVAILABLE


def test_negative_margin_and_negative_margin_percent_are_never_clamped():
    result = estimate(sale_price="100.00", total_cost="200.00")

    assert result.tax_amount == "6.00"
    assert result.margin == "-106.00"
    assert result.margin_percent == "-106.00"
    assert result.status is FinancialEstimateStatus.AVAILABLE


def test_tax_rounds_half_up_on_the_final_amount_only():
    # 33.33 x 6.5% = 2.16645 -> the intermediate product is never pre-rounded.
    result = estimate(sale_price="33.33", total_cost="10.00", rate=configured("6.50"))

    assert result.tax_amount == "2.17"
    assert result.margin == "21.16"


def test_margin_rounds_half_up_on_the_final_amount_only():
    # 10.005 x 50% = 5.0025 tax -> 5.00; margin 10.005 - 1.00 - 5.00 = 4.005 -> 4.01.
    result = estimate(sale_price="10.005", total_cost="1.00", rate=configured("50.00"))

    assert result.tax_amount == "5.00"
    assert result.margin == "4.01"


def test_margin_percent_rounds_half_up_on_the_final_result_only():
    # 1192.35 / 1400 x 100 = 85.1678... -> 85.17.
    result = estimate(sale_price="1400.00", total_cost="123.65")

    assert result.margin == "1192.35"
    assert result.margin_percent == "85.17"


def test_repeating_division_is_rounded_only_once_at_the_end():
    # 100 / 300 x 100 = 33.333... -> 33.33.
    result = estimate(sale_price="300.00", total_cost="182.00", rate=configured("6.00"))

    assert result.tax_amount == "18.00"
    assert result.margin == "100.00"
    assert result.margin_percent == "33.33"


def test_no_binary_float_reaches_the_calculation_or_the_result():
    result = estimate(sale_price="0.10", total_cost="0.20", rate=configured("10.00"))

    assert result.tax_amount == "0.01"
    assert result.margin == "-0.11"
    for value in (result.sale_price, result.total_cost, result.tax_amount, result.margin, result.margin_percent):
        assert isinstance(value, str)
        assert Decimal(value) == Decimal(value)


@pytest.mark.parametrize("sale_price", ["7", "7.0", "7.00"])
def test_every_monetary_and_percentage_output_has_exactly_two_decimals(sale_price):
    result = estimate(sale_price=sale_price, total_cost="1", rate=configured("6"))

    for value in (result.sale_price, result.total_cost, result.tax_rate_percent, result.tax_amount, result.margin, result.margin_percent):
        assert value is not None
        assert len(value.partition(".")[2]) == 2


# --- Availability ----------------------------------------------------------


def test_missing_rate_makes_everything_unavailable_without_fabricating_zero():
    result = estimate(sale_price="200.00", total_cost="110.00", rate=TaxRateContext.missing())

    assert result.tax_rate_percent is None
    assert result.tax_rate_effective_at is None
    assert result.tax_amount is None
    assert result.margin is None
    assert result.margin_percent is None
    assert result.status is FinancialEstimateStatus.UNAVAILABLE
    assert codes(result) == [FinancialWarningCode.TAX_RATE_MISSING]


def test_invalid_persisted_rate_returns_a_null_rate_context():
    result = estimate(sale_price="200.00", total_cost="110.00", rate=TaxRateContext.invalid_value())

    assert result.tax_rate_percent is None
    assert result.tax_rate_effective_at is None
    assert result.tax_amount is None
    assert result.margin is None
    assert result.margin_percent is None
    assert result.status is FinancialEstimateStatus.UNAVAILABLE


def test_missing_sale_price_makes_everything_unavailable():
    result = estimate(total_cost="110.00")

    assert result.sale_price is None
    assert result.tax_amount is None
    assert result.margin is None
    assert result.margin_percent is None
    assert result.status is FinancialEstimateStatus.UNAVAILABLE


def test_missing_total_cost_still_calculates_tax():
    result = estimate(sale_price="200.00")

    assert result.total_cost is None
    assert result.tax_amount == "12.00"
    assert result.margin is None
    assert result.margin_percent is None
    assert result.status is FinancialEstimateStatus.PARTIAL


def test_zero_sale_price_returns_margin_but_no_margin_percent():
    result = estimate(sale_price="0", total_cost="110.00")

    assert result.sale_price == "0.00"
    assert result.tax_amount == "0.00"
    assert result.margin == "-110.00"
    assert result.margin_percent is None
    assert result.status is FinancialEstimateStatus.PARTIAL


def test_zero_sale_price_with_a_zero_rate_still_reports_an_honest_negative_margin():
    result = estimate(sale_price="0", total_cost="25.50", rate=configured("0.00"))

    assert result.tax_amount == "0.00"
    assert result.margin == "-25.50"
    assert result.margin_percent is None


def test_a_valid_rate_with_neither_sale_price_nor_cost_is_unavailable():
    result = estimate()

    assert result.tax_rate_percent == "6.00"
    assert result.tax_amount is None
    assert result.status is FinancialEstimateStatus.UNAVAILABLE


# --- Warning behavior ------------------------------------------------------


def test_the_three_existing_warning_codes_are_preserved():
    result = estimate(rate=TaxRateContext.missing())

    assert codes(result) == [
        FinancialWarningCode.TAX_RATE_MISSING,
        FinancialWarningCode.SALE_PRICE_MISSING,
        FinancialWarningCode.COST_DATA_MISSING,
    ]


def test_only_the_two_accepted_new_warning_codes_exist():
    assert {code.value for code in FinancialWarningCode} == {
        "tax_rate_missing",
        "sale_price_missing",
        "cost_data_missing",
        "margin_percent_unavailable_zero_sale_price",
        "tax_rate_invalid",
    }


def test_no_alias_warning_code_is_introduced():
    values = {code.value for code in FinancialWarningCode}

    assert not values & {"tax_rate_unconfigured", "sale_price_unavailable", "total_cost_unavailable"}


def test_invalid_rate_emits_tax_rate_invalid_and_never_tax_rate_missing():
    result = estimate(sale_price="200.00", total_cost="110.00", rate=TaxRateContext.invalid_value())

    assert codes(result) == [FinancialWarningCode.TAX_RATE_INVALID]
    assert FinancialWarningCode.TAX_RATE_MISSING not in result.warning_codes


def test_zero_sale_price_emits_the_zero_denominator_warning():
    result = estimate(sale_price="0", total_cost="110.00")

    assert codes(result) == [FinancialWarningCode.MARGIN_PERCENT_UNAVAILABLE_ZERO_SALE_PRICE]


def test_zero_sale_price_without_a_margin_does_not_add_the_zero_denominator_warning():
    result = estimate(sale_price="0")

    assert codes(result) == [FinancialWarningCode.COST_DATA_MISSING]


def test_each_semantic_warning_is_emitted_at_most_once():
    result = estimate(sale_price="0", total_cost="110.00", rate=TaxRateContext.invalid_value())

    assert len(codes(result)) == len(set(codes(result)))


def test_different_missing_inputs_produce_different_warnings_together():
    result = estimate(rate=TaxRateContext.invalid_value())

    assert codes(result) == [
        FinancialWarningCode.TAX_RATE_INVALID,
        FinancialWarningCode.SALE_PRICE_MISSING,
        FinancialWarningCode.COST_DATA_MISSING,
    ]


def test_a_complete_available_estimate_emits_no_warning_at_all():
    assert codes(estimate(sale_price="200.00", total_cost="110.00")) == []


# --- Status semantics ------------------------------------------------------


@pytest.mark.parametrize(
    ("sale_price", "total_cost", "rate", "expected"),
    [
        ("200.00", "110.00", configured("6.00"), FinancialEstimateStatus.AVAILABLE),
        ("0", "110.00", configured("6.00"), FinancialEstimateStatus.PARTIAL),
        ("200.00", None, configured("6.00"), FinancialEstimateStatus.PARTIAL),
        ("200.00", "110.00", TaxRateContext.missing(), FinancialEstimateStatus.UNAVAILABLE),
        ("200.00", "110.00", TaxRateContext.invalid_value(), FinancialEstimateStatus.UNAVAILABLE),
        (None, "110.00", configured("6.00"), FinancialEstimateStatus.UNAVAILABLE),
    ],
)
def test_the_accepted_availability_matrix_is_implemented_exactly(sale_price, total_cost, rate, expected):
    result = estimate(sale_price=sale_price, total_cost=total_cost, rate=rate)

    assert result.status is expected
    assert set(FinancialEstimateStatus) == {
        FinancialEstimateStatus.AVAILABLE,
        FinancialEstimateStatus.PARTIAL,
        FinancialEstimateStatus.UNAVAILABLE,
    }


def test_the_result_is_immutable():
    result = estimate(sale_price="200.00", total_cost="110.00")

    with pytest.raises(AttributeError):
        result.margin = "1.00"  # type: ignore[misc]
