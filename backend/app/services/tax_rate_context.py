"""One backend-owned reduction of the tax-rate setting to the C2 context.

Durable contract: ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

Production readiness and production confirmation must agree exactly on what the
current tax-rate state is, so both call this reducer instead of parsing the
setting themselves. It reads through the single C1 ``TaxRateSettingsService``,
re-validates with the C1 parser, and returns one of the two contexts the
contract allows — a valid configured context, or the no-valid-rate context that
a missing row and an invalid persisted value both reduce to.

The raw uninterpreted setting text never leaves this module.
"""

import sqlite3

from app.domain.errors import DomainValidationError
from app.domain.production_financials import TaxRateContext
from app.domain.tax_rate import parse_tax_rate_percent
from app.repositories.settings import SettingsNotInitializedError
from app.schemas.tax_rate_settings import TaxRateSettingResponse
from app.services.tax_rate_settings import TaxRateSettingsService


def read_tax_rate_context(
    settings: TaxRateSettingsService,
    connection: sqlite3.Connection | None = None,
) -> TaxRateContext:
    """Read the current setting and reduce it to the authoritative C2 context.

    When ``connection`` is supplied the read happens on that exact connection,
    so production confirmation observes the setting inside its own transaction
    without opening a second one. The read writes nothing and audits nothing.
    """
    try:
        return reduce_tax_rate_context(settings.get_tax_rate(connection))
    except SettingsNotInitializedError:
        return TaxRateContext.missing()


def reduce_tax_rate_context(state: TaxRateSettingResponse) -> TaxRateContext:
    """Reduce one C1 setting response to the authoritative C2 context.

    The C1 Settings repair surface deliberately still returns the stored text
    for an externally corrupted row so the user can replace it, so
    ``is_configured`` alone is not proof that the value is financially
    authoritative. Anything that does not re-parse as the canonical C1
    percentage — or that carries no effective timestamp — becomes the
    no-valid-rate context instead of a calculated or fabricated value.

    Missing and invalid stay distinguishable here, because readiness warning
    generation needs the difference; every other caller compares only
    ``TaxRateContext.comparable_pair``, where both reduce to ``null/null``.
    """
    if state.tax_rate_percent is None:
        return TaxRateContext.missing()
    try:
        percent = parse_tax_rate_percent(state.tax_rate_percent)
    except DomainValidationError:
        return TaxRateContext.invalid_value()
    if state.effective_at is None:
        return TaxRateContext.invalid_value()
    return TaxRateContext.configured(percent, state.effective_at)


__all__ = ["read_tax_rate_context", "reduce_tax_rate_context"]
