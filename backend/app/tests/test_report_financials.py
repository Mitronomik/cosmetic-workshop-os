"""Focused tests for the pure `C2-III-B` finance aggregation.

Contract: ``docs/reports.md`` § *Accepted `C2-III-B` snapshot aggregation
contract*. These tests touch no database, no service and no HTTP layer — they
pin the arithmetic and the row-set semantics on their own, so a regression here
cannot hide behind a fixture.
"""

from decimal import Decimal

import pytest

from app.domain.report_financials import (
    ReportFinancialRow,
    ReportFinancialWarningCode,
    aggregate_report_financials,
)


def row(sale_price=None, total_cost=None, tax=None, margin=None) -> ReportFinancialRow:
    """One persisted batch. Every field defaults to "no snapshot saved"."""
    return ReportFinancialRow(
        sale_price=None if sale_price is None else Decimal(sale_price),
        total_cost=None if total_cost is None else Decimal(total_cost),
        tax=None if tax is None else Decimal(tax),
        margin=None if margin is None else Decimal(margin),
    )


def complete(sale_price, total_cost, tax, margin) -> ReportFinancialRow:
    """A post-`C2-II` batch that saved its full financial snapshot."""
    return row(sale_price=sale_price, total_cost=total_cost, tax=tax, margin=margin)


def legacy(sale_price, total_cost) -> ReportFinancialRow:
    """A pre-`C2-II` batch: price and cost known, no tax or margin snapshot."""
    return row(sale_price=sale_price, total_cost=total_cost)


def codes(result) -> set[str]:
    return {code.value for code in result.warning_codes}


# --- independent totals ------------------------------------------------------


def test_no_rows_produce_no_totals_and_no_warnings():
    result = aggregate_report_financials([])
    assert result.produced_order_count == 0
    assert result.known_revenue is None
    assert result.known_production_cost is None
    assert result.known_tax is None
    assert result.known_margin is None
    assert result.known_margin_percent is None
    assert result.warning_codes == ()


def test_one_complete_snapshot_row_reports_each_persisted_value():
    result = aggregate_report_financials([complete("1000.00", "400.00", "60.00", "540.00")])
    assert result.produced_order_count == 1
    assert result.produced_orders_with_sale_price == 1
    assert result.known_revenue == "1000.00"
    assert result.known_production_cost == "400.00"
    assert result.known_tax == "60.00"
    assert result.known_margin == "540.00"
    assert result.known_margin_percent == "54.00"
    assert result.warning_codes == ()


def test_multiple_complete_rows_sum_each_total_independently():
    result = aggregate_report_financials([
        complete("1000.00", "400.00", "60.00", "540.00"),
        complete("500.00", "150.00", "30.00", "320.00"),
    ])
    assert result.known_revenue == "1500.00"
    assert result.known_production_cost == "550.00"
    assert result.known_tax == "90.00"
    assert result.known_margin == "860.00"


def test_each_total_covers_every_non_null_value_even_when_the_others_are_missing():
    result = aggregate_report_financials([
        row(sale_price="100.00"),
        row(total_cost="40.00"),
        row(tax="6.00"),
        row(margin="54.00"),
    ])
    assert result.known_revenue == "100.00"
    assert result.known_production_cost == "40.00"
    assert result.known_tax == "6.00"
    assert result.known_margin == "54.00"


# --- snapshot ownership ------------------------------------------------------


def test_margin_is_the_persisted_snapshot_and_is_never_reconstructed():
    """A deliberately inconsistent row proves the numbers are read, not derived.

    ``sale_price - total_cost`` would be ``600.00`` and
    ``sale_price - total_cost - tax`` would be ``540.00``. The persisted margin
    is neither, and the report must report the persisted value.
    """
    result = aggregate_report_financials([complete("1000.00", "400.00", "60.00", "111.11")])
    assert result.known_margin == "111.11"
    assert result.known_tax == "60.00"


def test_paired_price_and_cost_alone_never_produce_a_margin():
    result = aggregate_report_financials([legacy("1000.00", "400.00")])
    assert result.known_margin is None
    assert result.known_margin_percent is None
    assert result.known_tax is None
    assert result.complete_finance_record_count == 1
    assert codes(result) == {"tax_unavailable", "margin_unavailable"}


# --- null and zero -----------------------------------------------------------


def test_absent_tax_snapshots_leave_known_tax_unavailable():
    result = aggregate_report_financials([legacy("100.00", "40.00"), legacy("200.00", "80.00")])
    assert result.known_tax is None


def test_tax_snapshots_summing_to_zero_are_a_real_configured_zero():
    result = aggregate_report_financials([
        complete("100.00", "40.00", "0.00", "60.00"),
        complete("200.00", "80.00", "0.00", "120.00"),
    ])
    assert result.known_tax == "0.00"
    assert result.tax_snapshot_record_count == 2


def test_a_single_configured_zero_tax_row_stays_known_next_to_a_missing_one():
    result = aggregate_report_financials([complete("100.00", "40.00", "0.00", "60.00"), legacy("50.00", "20.00")])
    assert result.known_tax == "0.00"
    assert result.tax_snapshot_record_count == 1
    assert result.missing_tax_snapshot_count == 1
    assert "partial_tax_basis" in codes(result)


def test_absent_margin_snapshots_leave_known_margin_unavailable():
    result = aggregate_report_financials([legacy("100.00", "40.00")])
    assert result.known_margin is None


def test_margin_snapshots_summing_to_zero_are_a_real_zero():
    result = aggregate_report_financials([
        complete("100.00", "40.00", "6.00", "40.00"),
        complete("100.00", "40.00", "6.00", "-40.00"),
    ])
    assert result.known_margin == "0.00"
    assert result.known_margin_percent == "0.00"


def test_a_negative_persisted_margin_keeps_its_sign():
    result = aggregate_report_financials([complete("100.00", "160.00", "6.00", "-66.00")])
    assert result.known_margin == "-66.00"
    assert result.known_margin_percent == "-66.00"


# --- row sets ----------------------------------------------------------------


def test_a_row_in_p_only_contributes_to_revenue_and_cost():
    result = aggregate_report_financials([legacy("1000.00", "400.00")])
    assert result.known_revenue == "1000.00"
    assert result.known_production_cost == "400.00"
    assert result.complete_finance_record_count == 1
    assert result.incomplete_margin_count == 0
    assert result.tax_snapshot_record_count == 0
    assert result.margin_snapshot_record_count == 0


def test_a_row_in_t_but_not_m_contributes_tax_without_margin():
    """Tax was saved but the cost was never known, so no margin exists."""
    result = aggregate_report_financials([row(sale_price="1000.00", tax="60.00")])
    assert result.known_tax == "60.00"
    assert result.known_margin is None
    assert result.tax_snapshot_record_count == 1
    assert result.margin_snapshot_record_count == 0
    assert result.complete_finance_record_count == 0
    assert codes(result) == {"missing_production_cost", "margin_unavailable"}


def test_a_row_outside_p_still_contributes_its_one_known_side():
    result = aggregate_report_financials([row(sale_price="1000.00"), row(total_cost="400.00")])
    assert result.known_revenue == "1000.00"
    assert result.known_production_cost == "400.00"
    assert result.complete_finance_record_count == 0
    assert result.incomplete_margin_count == 2


def test_legacy_and_snapshot_counters_describe_different_row_sets():
    result = aggregate_report_financials([
        complete("1000.00", "400.00", "60.00", "540.00"),
        legacy("500.00", "200.00"),
        row(sale_price="300.00"),
    ])
    assert result.complete_finance_record_count == 2
    assert result.incomplete_margin_count == 1
    assert result.margin_snapshot_record_count == 1
    assert result.missing_margin_snapshot_count == 2
    assert result.tax_snapshot_record_count == 1
    assert result.missing_tax_snapshot_count == 2


# --- percentage --------------------------------------------------------------


def test_margin_percent_divides_by_sale_prices_of_exactly_the_margin_rows():
    """`M` earns 300 on 1000; a further 9000 of revenue has no margin snapshot.

    The same-basis answer is ``30.00``. The global-revenue denominator would be
    ``3.00``, so this fixture fails loudly if that mistake is ever reintroduced.
    """
    result = aggregate_report_financials([
        complete("1000.00", "640.00", "60.00", "300.00"),
        legacy("9000.00", "5000.00"),
    ])
    assert result.known_revenue == "10000.00"
    assert result.known_margin == "300.00"
    assert result.known_margin_percent == "30.00"


def test_margin_percent_is_not_any_average_or_sum_of_row_percentages():
    """Two rows at 50% and 10% of very different sizes.

    Aggregate: ``550 / 1100 = 50.00%`` — not the arithmetic mean of the row
    percentages (30.00), not their sum (60.00), and not a weighted average built
    from persisted row percentages.
    """
    result = aggregate_report_financials([
        complete("1000.00", "440.00", "60.00", "500.00"),
        complete("100.00", "84.00", "6.00", "50.00"),
    ])
    assert result.known_margin == "550.00"
    assert result.known_margin_percent == "50.00"


def test_margin_percent_reports_a_negative_aggregate_margin():
    result = aggregate_report_financials([
        complete("100.00", "60.00", "6.00", "34.00"),
        complete("100.00", "200.00", "6.00", "-106.00"),
    ])
    assert result.known_margin == "-72.00"
    assert result.known_margin_percent == "-36.00"


def test_a_zero_sale_row_joins_the_numerator_but_not_the_denominator():
    result = aggregate_report_financials([
        complete("1000.00", "700.00", "60.00", "240.00"),
        complete("0.00", "40.00", "0.00", "-40.00"),
    ])
    assert result.known_margin == "200.00"
    assert result.margin_snapshot_record_count == 2
    # 200 ÷ 1000, because the zero-sale row adds nothing to the basis.
    assert result.known_margin_percent == "20.00"
    assert "margin_percent_unavailable_zero_basis" not in codes(result)


def test_an_all_zero_sale_basis_keeps_the_margin_but_drops_the_percentage():
    result = aggregate_report_financials([
        complete("0.00", "40.00", "0.00", "-40.00"),
        complete("0.00", "10.00", "0.00", "-10.00"),
    ])
    assert result.known_margin == "-50.00"
    assert result.known_margin_percent is None
    assert "margin_percent_unavailable_zero_basis" in codes(result)


def test_an_empty_margin_row_set_has_no_percentage_and_no_zero_basis_warning():
    result = aggregate_report_financials([legacy("1000.00", "400.00")])
    assert result.known_margin_percent is None
    assert "margin_percent_unavailable_zero_basis" not in codes(result)


def test_the_percentage_is_rounded_once_at_the_end():
    """``100 ÷ 300 × 100`` is a repeating decimal; only the result is rounded."""
    result = aggregate_report_financials([complete("300.00", "194.00", "6.00", "100.00")])
    assert result.known_margin_percent == "33.33"


# --- counters ----------------------------------------------------------------


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [legacy("100.00", "40.00")],
        [complete("100.00", "40.00", "6.00", "54.00")],
        [complete("100.00", "40.00", "6.00", "54.00"), legacy("50.00", "20.00"), row(), row(tax="1.00")],
        [row(sale_price="0.00", margin="0.00"), row(total_cost="10.00")],
    ],
)
def test_each_snapshot_counter_pair_sums_to_the_produced_order_count(rows):
    result = aggregate_report_financials(rows)
    assert result.tax_snapshot_record_count + result.missing_tax_snapshot_count == result.produced_order_count
    assert result.margin_snapshot_record_count + result.missing_margin_snapshot_count == result.produced_order_count


def test_legacy_paired_counters_keep_their_pre_c2_iii_b_meanings():
    result = aggregate_report_financials([
        legacy("100.00", "40.00"),
        row(sale_price="100.00"),
        row(total_cost="40.00"),
        row(),
    ])
    assert result.complete_finance_record_count == 1
    assert result.incomplete_margin_count == 3
    assert result.missing_sale_price_count == 2
    assert result.missing_cost_count == 2
    assert result.produced_orders_with_sale_price == 2


# --- warnings ----------------------------------------------------------------


def test_missing_input_warnings_track_each_side_independently():
    result = aggregate_report_financials([row(sale_price="100.00"), row(total_cost="40.00")])
    assert "missing_sale_price" in codes(result)
    assert "missing_production_cost" in codes(result)


def test_complete_snapshots_raise_no_warning_at_all():
    result = aggregate_report_financials([complete("100.00", "40.00", "6.00", "54.00")])
    assert result.warning_codes == ()


def test_tax_unavailable_and_partial_tax_basis_are_mutually_exclusive():
    none_saved = aggregate_report_financials([legacy("100.00", "40.00"), legacy("50.00", "20.00")])
    assert "tax_unavailable" in codes(none_saved)
    assert "partial_tax_basis" not in codes(none_saved)

    some_saved = aggregate_report_financials([complete("100.00", "40.00", "6.00", "54.00"), legacy("50.00", "20.00")])
    assert "partial_tax_basis" in codes(some_saved)
    assert "tax_unavailable" not in codes(some_saved)


def test_margin_unavailable_and_partial_margin_basis_are_mutually_exclusive():
    none_saved = aggregate_report_financials([legacy("100.00", "40.00")])
    assert "margin_unavailable" in codes(none_saved)
    assert "partial_margin_basis" not in codes(none_saved)

    some_saved = aggregate_report_financials([complete("100.00", "40.00", "6.00", "54.00"), legacy("50.00", "20.00")])
    assert "partial_margin_basis" in codes(some_saved)
    assert "margin_unavailable" not in codes(some_saved)


def test_full_snapshot_coverage_emits_no_partial_warning():
    result = aggregate_report_financials([
        complete("100.00", "40.00", "6.00", "54.00"),
        complete("200.00", "80.00", "12.00", "108.00"),
    ])
    assert "partial_tax_basis" not in codes(result)
    assert "partial_margin_basis" not in codes(result)


def test_a_configured_zero_is_never_warned_as_missing():
    result = aggregate_report_financials([complete("100.00", "40.00", "0.00", "60.00")])
    assert "tax_unavailable" not in codes(result)
    assert "partial_tax_basis" not in codes(result)
    assert result.known_tax == "0.00"


def test_every_warning_code_appears_at_most_once():
    result = aggregate_report_financials([
        row(),
        row(),
        row(sale_price="0.00", margin="0.00"),
        legacy("10.00", "5.00"),
    ])
    assert len(result.warning_codes) == len(set(result.warning_codes))


def test_warning_codes_are_the_seven_accepted_stable_codes():
    assert {code.value for code in ReportFinancialWarningCode} == {
        "missing_sale_price",
        "missing_production_cost",
        "tax_unavailable",
        "partial_tax_basis",
        "margin_unavailable",
        "partial_margin_basis",
        "margin_percent_unavailable_zero_basis",
    }


def test_no_rows_means_no_unavailable_warning_because_nothing_is_missing():
    """An empty workshop is an empty state, not incomplete financial data."""
    result = aggregate_report_financials([])
    assert "tax_unavailable" not in codes(result)
    assert "margin_unavailable" not in codes(result)
