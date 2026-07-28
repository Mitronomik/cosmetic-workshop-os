"""Pure financial estimate for production readiness (`C2-I`).

Durable contract: ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

This module owns the calculation only. It opens no connection, reads no
repository, knows nothing about FastAPI, Pydantic, or
``ProductionReadinessIssue``, and writes nothing. The service layer supplies
backend-owned values, maps the returned warning codes onto the existing
readiness warning structure, and never re-implements a formula here.

`Decimal` only, never binary float, and only the final amount of each formula is
rounded. A missing input stays missing: it is never turned into a fabricated
zero, and a negative margin is never clamped.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Final

from app.domain.decimal_utils import quantize_money, quantize_percentage

PERCENT_DIVISOR: Final = Decimal("100")


class FinancialEstimateStatus(StrEnum):
    """How complete the readiness financial estimate is."""

    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class FinancialWarningCode(StrEnum):
    """Stable non-blocking readiness warning codes owned by the C2 contract.

    The first three are existing readiness codes, preserved unchanged in name
    and meaning; the last two are the only codes `C2-I` adds.
    """

    TAX_RATE_MISSING = "tax_rate_missing"
    SALE_PRICE_MISSING = "sale_price_missing"
    COST_DATA_MISSING = "cost_data_missing"
    MARGIN_PERCENT_UNAVAILABLE_ZERO_SALE_PRICE = "margin_percent_unavailable_zero_sale_price"
    TAX_RATE_INVALID = "tax_rate_invalid"


@dataclass(frozen=True, slots=True)
class TaxRateContext:
    """The authoritative C2 tax-rate context.

    Exactly two shapes exist. A **valid context** carries a percentage and its
    effective timestamp. A **no-valid-rate context** carries neither, and
    records through ``invalid`` whether it came from an absent setting row or
    from a persisted value that could not be interpreted. The raw uninterpreted
    text never enters this structure.
    """

    percent: Decimal | None = None
    effective_at: str | None = None
    invalid: bool = False

    @classmethod
    def configured(cls, percent: Decimal, effective_at: str) -> "TaxRateContext":
        return cls(percent=percent, effective_at=effective_at)

    @classmethod
    def missing(cls) -> "TaxRateContext":
        return cls()

    @classmethod
    def invalid_value(cls) -> "TaxRateContext":
        return cls(invalid=True)

    @property
    def is_configured(self) -> bool:
        return self.percent is not None


@dataclass(frozen=True, slots=True)
class ProductionFinancialInputs:
    """Backend-owned inputs. ``None`` means genuinely unavailable, never zero."""

    sale_price: Decimal | None
    total_cost: Decimal | None
    tax_rate: TaxRateContext


@dataclass(frozen=True, slots=True)
class ProductionFinancialEstimate:
    """Canonical two-decimal strings, or ``None`` when a value is unavailable."""

    sale_price: str | None
    total_cost: str | None
    tax_rate_percent: str | None
    tax_rate_effective_at: str | None
    tax_amount: str | None
    margin: str | None
    margin_percent: str | None
    status: FinancialEstimateStatus
    warning_codes: tuple[FinancialWarningCode, ...]


def estimate_production_financials(inputs: ProductionFinancialInputs) -> ProductionFinancialEstimate:
    """Return the readiness financial estimate for one order."""
    sale_price, total_cost, rate = inputs.sale_price, inputs.total_cost, inputs.tax_rate
    tax_amount = _tax_amount(sale_price, rate.percent)
    margin = _margin(sale_price, total_cost, tax_amount)
    margin_percent = _margin_percent(margin, sale_price)
    return ProductionFinancialEstimate(
        sale_price=_money(sale_price),
        total_cost=_money(total_cost),
        tax_rate_percent=_percent(rate.percent),
        tax_rate_effective_at=rate.effective_at,
        tax_amount=_money(tax_amount),
        margin=_money(margin),
        margin_percent=_percent(margin_percent),
        status=_status(tax_amount, margin, margin_percent),
        warning_codes=_warning_codes(inputs, margin),
    )


def _tax_amount(sale_price: Decimal | None, percent: Decimal | None) -> Decimal | None:
    """`ROUND_MONEY(sale_price × tax_rate_percent / 100)`, rounded once."""
    if sale_price is None or percent is None:
        return None
    return quantize_money(sale_price * percent / PERCENT_DIVISOR, field="estimated_tax")


def _margin(sale_price: Decimal | None, total_cost: Decimal | None, tax_amount: Decimal | None) -> Decimal | None:
    """`ROUND_MONEY(sale_price - total_cost - tax_amount)`, never clamped."""
    if sale_price is None or total_cost is None or tax_amount is None:
        return None
    return quantize_money(sale_price - total_cost - tax_amount, field="estimated_margin")


def _margin_percent(margin: Decimal | None, sale_price: Decimal | None) -> Decimal | None:
    """`ROUND_PERCENT(margin / sale_price × 100)` only when the base is positive."""
    if margin is None or sale_price is None or sale_price <= 0:
        return None
    return quantize_percentage(margin / sale_price * PERCENT_DIVISOR, field="estimated_margin_percent")


def _status(
    tax_amount: Decimal | None,
    margin: Decimal | None,
    margin_percent: Decimal | None,
) -> FinancialEstimateStatus:
    if tax_amount is None:
        return FinancialEstimateStatus.UNAVAILABLE
    if margin is None or margin_percent is None:
        return FinancialEstimateStatus.PARTIAL
    return FinancialEstimateStatus.AVAILABLE


def _warning_codes(
    inputs: ProductionFinancialInputs,
    margin: Decimal | None,
) -> tuple[FinancialWarningCode, ...]:
    """One warning per applicable semantic condition, never two for one.

    An invalid persisted rate emits ``tax_rate_invalid`` instead of — never in
    addition to — ``tax_rate_missing``. The zero-denominator warning explains
    only the case where a margin exists but its percentage cannot be expressed;
    when the margin itself is unavailable, the missing-input warning already
    explains that.
    """
    codes: list[FinancialWarningCode] = []
    if inputs.tax_rate.invalid:
        codes.append(FinancialWarningCode.TAX_RATE_INVALID)
    elif not inputs.tax_rate.is_configured:
        codes.append(FinancialWarningCode.TAX_RATE_MISSING)
    if inputs.sale_price is None:
        codes.append(FinancialWarningCode.SALE_PRICE_MISSING)
    if inputs.total_cost is None:
        codes.append(FinancialWarningCode.COST_DATA_MISSING)
    if margin is not None and inputs.sale_price == 0:
        codes.append(FinancialWarningCode.MARGIN_PERCENT_UNAVAILABLE_ZERO_SALE_PRICE)
    return tuple(codes)


def _money(value: Decimal | None) -> str | None:
    return None if value is None else str(quantize_money(value, field="money"))


def _percent(value: Decimal | None) -> str | None:
    return None if value is None else str(quantize_percentage(value, field="percentage"))


__all__ = [
    "FinancialEstimateStatus",
    "FinancialWarningCode",
    "ProductionFinancialEstimate",
    "ProductionFinancialInputs",
    "TaxRateContext",
    "estimate_production_financials",
]
