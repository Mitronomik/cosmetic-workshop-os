from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator


class PurchaseSuggestionResponse(BaseModel):
    id: int
    suggestion_key: str
    item_type: str
    item_id: int
    item_name_snapshot: str
    recommended_quantity: str
    unit: str
    reason: str
    source_entity_type: str
    source_entity_id: int | None
    message: str
    status: str
    notes: str
    created_at: str
    updated_at: str
    resolved_at: str | None


class PurchaseSuggestionListResponse(BaseModel):
    purchase_suggestions: list[PurchaseSuggestionResponse]
    limit: int
    offset: int


class PurchaseSuggestionGenerationResponse(BaseModel):
    created_count: int
    updated_count: int
    archived_count: int
    open_count: int


class ManualPurchaseSuggestionRequest(BaseModel):
    item_type: Literal["ingredient", "packaging"]
    item_id: int
    recommended_quantity: Decimal | int | str
    unit: str
    notes: str = ""

    @field_validator("recommended_quantity", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float):
            raise ValueError("recommended_quantity must not be sent as float.")
        return value


class PurchaseSuggestionUpdateRequest(BaseModel):
    recommended_quantity: Decimal | int | str
    unit: str
    notes: str = ""

    @field_validator("recommended_quantity", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float):
            raise ValueError("recommended_quantity must not be sent as float.")
        return value
