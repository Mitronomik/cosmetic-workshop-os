"""The required-but-nullable tax context of a production confirmation request.

Durable contract: ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

The client echoes back, unchanged, the pair the latest readiness result
returned. Exactly two shapes are accepted:

1. **valid configured context** — a canonical two-decimal percentage string plus
   the canonical ``YYYY-MM-DDTHH:MM:SSZ`` timestamp;
2. **no-valid-rate context** — explicit ``null`` and explicit ``null``, meaning
   readiness observed no valid configured tax rate, from a missing setting row
   **or** from an invalid persisted value alike.

Omission is not the same as explicit ``null/null``: it means an outdated client
contract, and is rejected separately at the request boundary. This module never
repairs, rounds, or reinterprets a value — anything outside the contract is
rejected so the confirmation writes nothing.
"""

from dataclasses import dataclass
from typing import Final

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.tax_rate import canonical_tax_rate_percent, parse_tax_rate_percent
from app.domain.tax_rate_timestamps import is_canonical_api_timestamp

EXPECTED_PERCENT_FIELD: Final = "expected_tax_rate_percent"
EXPECTED_EFFECTIVE_AT_FIELD: Final = "expected_tax_rate_effective_at"

CONTEXT_NEXT_ACTION: Final = "Запустите проверку готовности заново и подтвердите изготовление ещё раз."

MISSING_CONTEXT_MESSAGE: Final = (
    "Подтверждение изготовления пришло без сведений о налоговой ставке. "
    "Изготовление не выполнено."
)
INVALID_CONTEXT_MESSAGE: Final = (
    "Сведения о налоговой ставке в подтверждении изготовления некорректны. "
    "Изготовление не выполнено."
)


@dataclass(frozen=True, slots=True)
class ExpectedTaxRateContext:
    """A validated confirmation context, ready to compare with backend state.

    ``percent`` is either the canonical two-decimal string or ``None``, and
    ``effective_at`` is either the canonical API timestamp or ``None``. The two
    are always both set or both absent.
    """

    percent: str | None
    effective_at: str | None

    def __post_init__(self) -> None:
        if (self.percent is None) != (self.effective_at is None):
            raise ValueError("An expected tax-rate context is either fully configured or fully absent.")

    @classmethod
    def no_valid_rate(cls) -> "ExpectedTaxRateContext":
        return cls(percent=None, effective_at=None)

    @property
    def pair(self) -> tuple[str | None, str | None]:
        """The comparable canonical pair used by the stale-context check."""
        return (self.percent, self.effective_at)


def parse_expected_tax_rate_context(percent: object, effective_at: object) -> ExpectedTaxRateContext:
    """Validate the client-supplied pair, rejecting anything off-contract."""
    if percent is None and effective_at is None:
        return ExpectedTaxRateContext.no_valid_rate()
    if percent is None or effective_at is None:
        raise _invalid(
            EXPECTED_PERCENT_FIELD if percent is None else EXPECTED_EFFECTIVE_AT_FIELD,
            percent if percent is None else effective_at,
        )
    return ExpectedTaxRateContext(
        percent=_canonical_percent(percent),
        effective_at=_canonical_effective_at(effective_at),
    )


def missing_tax_rate_context_error() -> DomainValidationError:
    """The rejection for a request that omits either context key entirely."""
    return DomainValidationError(
        DomainIssue(
            code=DomainIssueCode.TAX_RATE_CONTEXT_REQUIRED,
            message=MISSING_CONTEXT_MESSAGE,
            field=EXPECTED_PERCENT_FIELD,
            next_action=CONTEXT_NEXT_ACTION,
        )
    )


def _canonical_percent(value: object) -> str:
    """Require the exact canonical two-decimal percentage, never rounding it.

    C1 parsing settles the shape, precision, and range; the canonical round-trip
    then rejects a value that is merely equivalent — `6`, `6.0`, and `06.00` all
    parse to the same number but none of them is what readiness returned.
    """
    if not isinstance(value, str):
        raise _invalid(EXPECTED_PERCENT_FIELD, value)
    try:
        parsed = parse_tax_rate_percent(value)
    except DomainValidationError as failure:
        raise _invalid(EXPECTED_PERCENT_FIELD, value) from failure
    if canonical_tax_rate_percent(parsed) != value:
        raise _invalid(EXPECTED_PERCENT_FIELD, value)
    return value


def _canonical_effective_at(value: object) -> str:
    if not is_canonical_api_timestamp(value):
        raise _invalid(EXPECTED_EFFECTIVE_AT_FIELD, value)
    return str(value)


def _invalid(field: str, value: object) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(
            code=DomainIssueCode.INVALID_TAX_RATE_CONTEXT,
            message=INVALID_CONTEXT_MESSAGE,
            field=field,
            value=_safe_value(value),
            next_action=CONTEXT_NEXT_ACTION,
        )
    )


def _safe_value(value: object) -> str:
    """Echo a short client string back, but never a raw object repr."""
    return value[:40] if isinstance(value, str) else type(value).__name__


__all__ = [
    "EXPECTED_EFFECTIVE_AT_FIELD",
    "EXPECTED_PERCENT_FIELD",
    "ExpectedTaxRateContext",
    "missing_tax_rate_context_error",
    "parse_expected_tax_rate_context",
]
