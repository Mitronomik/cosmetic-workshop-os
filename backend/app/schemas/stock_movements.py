from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.stock_movements import MovementDirection, StockMovementType
from app.domain.units import UnitCode


class StockMovementCreateRequest(BaseModel):
    ingredient_lot_id: int
    movement_type: StockMovementType
    quantity: Decimal | int | str
    unit: UnitCode
    direction: MovementDirection | None = None
    reason: str = ""
    occurred_at: str | None = None
    note: str = ""
    reference_type: str | None = None
    reference_id: str | None = None
    source: str = "manual"
    correction_of_movement_id: int | None = None

    model_config = ConfigDict(use_enum_values=False)

    @field_validator("quantity", mode="before")
    @classmethod
    def reject_float_quantity(cls, value):
        if isinstance(value, float):
            raise ValueError("Quantity must be sent as a string, integer, or Decimal value; float is not allowed.")
        return value


class StockMovementResponse(BaseModel):
    id: int
    ingredient_lot_id: int
    ingredient_id: int
    movement_type: StockMovementType
    quantity: str
    unit: UnitCode
    direction: MovementDirection
    reason: str
    occurred_at: str
    note: str
    reference_type: str | None
    reference_id: str | None
    source: str
    correction_of_movement_id: int | None
    created_at: str


class StockMovementsResponse(BaseModel):
    movements: list[StockMovementResponse]


class IngredientLotBalanceResponse(BaseModel):
    ingredient_lot_id: int
    quantity: str
