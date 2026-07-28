"""Pure snapshot-backed finance-report aggregation (`C2-III-B`).

Durable contract: ``docs/reports.md`` § *Accepted `C2-III-B` snapshot aggregation
contract*, decided in ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

This module owns the aggregation only. It opens no connection, imports neither
FastAPI nor Pydantic, reads no repository and no setting, writes nothing, and
renders no document. The service layer supplies the persisted row values and
maps the returned warning codes onto the existing report warning structure.

The single rule everything here follows: **report tax and report margin come
from the persisted `ProductionBatch` snapshots and are never reconstructed.**
Nothing in this module computes ``sale_price - total_cost``, computes
``sale_price - total_cost - tax``, reads a current tax rate, or repairs a row
whose snapshot is missing. A row produced before the snapshots existed simply
stays outside the tax and margin totals.

Four row sets are kept apart, because under snapshot-backed aggregation they are
genuinely different sets:

``R``
    every production batch row;
``P``
    rows where ``sale_price`` and ``total_cost`` are both known — the *legacy*
    paired-input coverage the pre-existing counters describe;
``T``
    rows where the persisted ``tax`` snapshot is known;
``M``
    rows where the persisted ``margin`` snapshot is known.

`Decimal` only, never binary float. Each total is summed at full precision and
rounded exactly once at the end, so no intermediate rounding accumulates. A
missing value stays missing: ``None`` is never turned into a fabricated zero,
an explicit ``"0.00"`` stays a real known zero, and a negative margin keeps its
sign rather than being clamped.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Final

from app.domain.decimal_utils import quantize_money, quantize_percentage

PERCENT_MULTIPLIER: Final = Decimal("100")
ZERO: Final = Decimal("0")


class ReportFinancialWarningCode(StrEnum):
    """Stable finance-report warning codes.

    The first four are pre-existing codes, preserved unchanged in name. Their
    margin conditions are restated against persisted margin snapshots; the last
    three are the only codes `C2-III-B` adds.
    """

    MISSING_SALE_PRICE = "missing_sale_price"
    MISSING_PRODUCTION_COST = "missing_production_cost"
    TAX_UNAVAILABLE = "tax_unavailable"
    PARTIAL_TAX_BASIS = "partial_tax_basis"
    MARGIN_UNAVAILABLE = "margin_unavailable"
    PARTIAL_MARGIN_BASIS = "partial_margin_basis"
    MARGIN_PERCENT_UNAVAILABLE_ZERO_BASIS = "margin_percent_unavailable_zero_basis"


@dataclass(frozen=True, slots=True)
class ReportFinancialRow:
    """One persisted production batch, as the finance report reads it.

    ``None`` means the row genuinely has no persisted value, never zero. The
    persisted row ``margin_percent`` is deliberately absent: it is a historical
    per-row value and is never aggregated.
    """

    sale_price: Decimal | None
    total_cost: Decimal | None
    tax: Decimal | None
    margin: Decimal | None


@dataclass(frozen=True, slots=True)
class ReportFinancialAggregate:
    """Canonical two-decimal strings, or ``None`` when a total is unavailable.

    ``complete_finance_record_count`` and ``incomplete_margin_count`` describe
    the legacy paired sale-price/cost coverage of ``P``. The four snapshot
    counters describe ``T`` and ``M``. The two kinds are not interchangeable,
    and each snapshot pair sums to ``produced_order_count``.
    """

    produced_order_count: int
    produced_orders_with_sale_price: int
    known_revenue: str | None
    known_production_cost: str | None
    known_tax: str | None
    known_margin: str | None
    known_margin_percent: str | None
    complete_finance_record_count: int
    incomplete_margin_count: int
    missing_sale_price_count: int
    missing_cost_count: int
    tax_snapshot_record_count: int
    missing_tax_snapshot_count: int
    margin_snapshot_record_count: int
    missing_margin_snapshot_count: int
    warning_codes: tuple[ReportFinancialWarningCode, ...]


def aggregate_report_financials(rows: Iterable[ReportFinancialRow]) -> ReportFinancialAggregate:
    """Return the one deterministic finance aggregation for these rows."""
    batches = tuple(rows)
    counts = _counts(batches)
    margin_total = _sum(row.margin for row in batches)
    # The denominator uses sale prices from exactly the rows in `M` — the rows
    # whose persisted margin is in the numerator above — never the global
    # known-revenue total, and never an average of persisted row percentages.
    margin_basis_revenue = _sum(row.sale_price for row in batches if row.margin is not None)
    has_margin = counts.margin_snapshot_record_count > 0
    return ReportFinancialAggregate(
        produced_order_count=len(batches),
        produced_orders_with_sale_price=counts.with_sale_price,
        known_revenue=_money(_sum(row.sale_price for row in batches)) if counts.with_sale_price else None,
        known_production_cost=_money(_sum(row.total_cost for row in batches)) if counts.with_cost else None,
        known_tax=_money(_sum(row.tax for row in batches)) if counts.tax_snapshot_record_count else None,
        known_margin=_money(margin_total) if has_margin else None,
        known_margin_percent=_margin_percent(margin_total, margin_basis_revenue) if has_margin else None,
        complete_finance_record_count=counts.complete_finance_record_count,
        incomplete_margin_count=counts.incomplete_margin_count,
        missing_sale_price_count=counts.missing_sale_price_count,
        missing_cost_count=counts.missing_cost_count,
        tax_snapshot_record_count=counts.tax_snapshot_record_count,
        missing_tax_snapshot_count=counts.missing_tax_snapshot_count,
        margin_snapshot_record_count=counts.margin_snapshot_record_count,
        missing_margin_snapshot_count=counts.missing_margin_snapshot_count,
        warning_codes=_warning_codes(counts, has_margin=has_margin, margin_basis_revenue=margin_basis_revenue),
    )


@dataclass(frozen=True, slots=True)
class _Counts:
    """Row-set sizes. Each snapshot pair sums to the total row count."""

    total: int
    with_sale_price: int
    with_cost: int
    missing_sale_price_count: int
    missing_cost_count: int
    complete_finance_record_count: int
    incomplete_margin_count: int
    tax_snapshot_record_count: int
    missing_tax_snapshot_count: int
    margin_snapshot_record_count: int
    missing_margin_snapshot_count: int


def _counts(batches: Sequence[ReportFinancialRow]) -> _Counts:
    """Size every row set in one pass, from persisted values only."""
    with_sale_price = _count(row.sale_price is not None for row in batches)
    with_cost = _count(row.total_cost is not None for row in batches)
    paired = _count(row.sale_price is not None and row.total_cost is not None for row in batches)
    with_tax = _count(row.tax is not None for row in batches)
    with_margin = _count(row.margin is not None for row in batches)
    total = len(batches)
    return _Counts(
        total=total,
        with_sale_price=with_sale_price,
        with_cost=with_cost,
        missing_sale_price_count=total - with_sale_price,
        missing_cost_count=total - with_cost,
        complete_finance_record_count=paired,
        incomplete_margin_count=total - paired,
        tax_snapshot_record_count=with_tax,
        missing_tax_snapshot_count=total - with_tax,
        margin_snapshot_record_count=with_margin,
        missing_margin_snapshot_count=total - with_margin,
    )


def _warning_codes(
    counts: _Counts,
    *,
    has_margin: bool,
    margin_basis_revenue: Decimal,
) -> tuple[ReportFinancialWarningCode, ...]:
    """One warning per applicable condition, never two for the same condition.

    The unavailable and partial forms of each snapshot warning are mutually
    exclusive by construction: "no snapshots at all" and "some snapshots" cannot
    both be true. The zero-basis warning explains only the case where the margin
    total exists but its percentage cannot be expressed; when the margin itself
    is unavailable, ``margin_unavailable`` already explains that.
    """
    codes: list[ReportFinancialWarningCode] = []
    if counts.missing_sale_price_count:
        codes.append(ReportFinancialWarningCode.MISSING_SALE_PRICE)
    if counts.missing_cost_count:
        codes.append(ReportFinancialWarningCode.MISSING_PRODUCTION_COST)
    if counts.total and not counts.tax_snapshot_record_count:
        codes.append(ReportFinancialWarningCode.TAX_UNAVAILABLE)
    elif counts.tax_snapshot_record_count and counts.missing_tax_snapshot_count:
        codes.append(ReportFinancialWarningCode.PARTIAL_TAX_BASIS)
    if counts.total and not counts.margin_snapshot_record_count:
        codes.append(ReportFinancialWarningCode.MARGIN_UNAVAILABLE)
    elif counts.margin_snapshot_record_count and counts.missing_margin_snapshot_count:
        codes.append(ReportFinancialWarningCode.PARTIAL_MARGIN_BASIS)
    if has_margin and margin_basis_revenue == ZERO:
        codes.append(ReportFinancialWarningCode.MARGIN_PERCENT_UNAVAILABLE_ZERO_BASIS)
    return tuple(codes)


def _margin_percent(margin_total: Decimal, margin_basis_revenue: Decimal) -> str | None:
    """``ROUND_PERCENT(Σ margin over M ÷ Σ sale_price over M × 100)``.

    Rounded once, at the end. ``None`` when the same-basis denominator is zero —
    which is a real zero sale-price basis, not a missing margin.
    """
    if margin_basis_revenue == ZERO:
        return None
    return str(quantize_percentage(margin_total / margin_basis_revenue * PERCENT_MULTIPLIER, field="known_margin_percent"))


def _sum(values: Iterable[Decimal | None]) -> Decimal:
    """Total the known values. A ``None`` contributes nothing, never a zero."""
    return sum((value for value in values if value is not None), ZERO)


def _count(flags: Iterable[bool]) -> int:
    return sum(1 for flag in flags if flag)


def _money(value: Decimal) -> str:
    """The canonical two-decimal form, so a zero total reads as ``"0.00"``."""
    return str(quantize_money(value, field="money"))


__all__ = [
    "ReportFinancialAggregate",
    "ReportFinancialRow",
    "ReportFinancialWarningCode",
    "aggregate_report_financials",
]
