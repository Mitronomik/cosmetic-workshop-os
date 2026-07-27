"""Validation and canonical formatting for the workshop tax-rate percentage.

The setting is a percentage, not a coefficient: ``6.00`` means ``6%``. Input is a
decimal string with at most two fractional digits; excess precision is rejected
and never rounded, so ``quantize_percentage`` must not be used here.
"""

import re
from decimal import Decimal
from typing import Final

from app.domain.decimal_utils import parse_decimal
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError

TAX_RATE_FIELD: Final = "tax_rate_percent"
TAX_RATE_MIN: Final = Decimal("0")
TAX_RATE_MAX: Final = Decimal("100")
TAX_RATE_CANONICAL_QUANT: Final = Decimal("0.01")
TAX_RATE_MAX_FRACTIONAL_DIGITS: Final = 2

_TAX_RATE_SHAPE: Final = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")


def parse_tax_rate_percent(value: object) -> Decimal:
    """Return the validated percentage, rejecting anything outside the contract."""
    if not isinstance(value, str):
        raise _issue(
            DomainIssueCode.INVALID_TAX_RATE_TYPE,
            "Налоговую ставку нужно передавать текстом, например “6” или “6.50”.",
            value,
            "Передайте ставку строкой с точкой в качестве десятичного разделителя.",
        )
    text = value.strip()
    if not _TAX_RATE_SHAPE.match(text):
        raise _issue(
            DomainIssueCode.INVALID_TAX_RATE_FORMAT,
            f"Налоговая ставка “{value}” указана неверно. Нужно число, например 6 или 6.50.",
            value,
            "Введите ставку в процентах обычным числом, например 6 или 6,5.",
        )
    fractional_digits = len(text.partition(".")[2])
    if fractional_digits > TAX_RATE_MAX_FRACTIONAL_DIGITS:
        raise _issue(
            DomainIssueCode.TAX_RATE_PRECISION_EXCEEDED,
            f"Налоговая ставка “{value}” слишком точная. Допустимо не больше двух знаков после запятой.",
            value,
            "Укажите ставку не точнее двух знаков, например 6.50 вместо 6.005.",
        )
    parsed = parse_decimal(text, field=TAX_RATE_FIELD)
    if parsed < TAX_RATE_MIN or parsed > TAX_RATE_MAX:
        raise _issue(
            DomainIssueCode.TAX_RATE_OUT_OF_RANGE,
            f"Налоговая ставка “{value}” вне допустимого диапазона. Допустимо от 0 до 100 процентов.",
            value,
            "Укажите ставку в процентах от 0 до 100, например 6.",
        )
    return parsed


def canonical_tax_rate_percent(value: Decimal) -> str:
    """Return the canonical exactly-two-fractional-digit representation."""
    return str(value.quantize(TAX_RATE_CANONICAL_QUANT))


def _issue(code: DomainIssueCode, message: str, value: object, next_action: str) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(code=code, message=message, field=TAX_RATE_FIELD, value=_safe_value(value), next_action=next_action)
    )


def _safe_value(value: object) -> str:
    if isinstance(value, str):
        return value[:40]
    return type(value).__name__
