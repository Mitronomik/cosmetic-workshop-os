from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.packaging_stock_movements import PackagingMovementDirection, PackagingStockMovementType
from app.domain.units import UnitCode


class PackagingStockMovementCreateRequest(BaseModel):
    packaging_item_id: int
    movement_type: PackagingStockMovementType
    quantity: Decimal | int | str
    unit: UnitCode
    occurred_at: str | None = None
    reason: str = ""
    source: str = "manual"
    notes: str = ""

    model_config = ConfigDict(use_enum_values=False)

    @field_validator("quantity", mode="before")
    @classmethod
    def reject_float_quantity(cls, value):
        if isinstance(value, float):
            raise ValueError("Quantity must be sent as a string, integer, or Decimal value; float is not allowed.")
        return value


class PackagingStockMovementResponse(BaseModel):
    id: int
    packaging_item_id: int
    movement_type: PackagingStockMovementType
    quantity: str
    unit: UnitCode
    direction: PackagingMovementDirection
    occurred_at: str
    reason: str
    source: str
    notes: str
    created_at: str


class PackagingStockMovementsResponse(BaseModel):
    movements: list[PackagingStockMovementResponse]


class PackagingItemBalanceResponse(BaseModel):
    packaging_item_id: int
    quantity: str
