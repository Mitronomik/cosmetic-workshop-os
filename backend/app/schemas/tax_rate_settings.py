from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaxRateSettingUpdateRequest(BaseModel):
    """Configure/change (`"6.00"`) or explicitly clear (`null`) the tax rate.

    The field is intentionally untyped here so that wrong payload shapes — JSON
    numbers, `bool`, `NaN`, objects — reach the domain validator and receive the
    project structured Russian error instead of a generic framework message.
    """

    model_config = ConfigDict(extra="forbid")

    tax_rate_percent: Any = Field(...)


class TaxRateSettingResponse(BaseModel):
    tax_rate_percent: str | None
    is_configured: bool
    effective_at: str | None
    message: str
