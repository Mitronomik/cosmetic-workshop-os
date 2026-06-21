from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.units import UnitCode


class IngredientLotCreateRequest(BaseModel):
    ingredient_id: int
    lot_code: str = ""
    supplier_name: str = ""
    purchased_at: date | None = None
    expires_at: date | None = None
    unit: UnitCode
    unit_cost: Decimal | int | str | None = None
    total_cost: Decimal | int | str | None = None
    density_g_per_ml: Decimal | int | str | None = None
    notes: str = ""

    model_config = ConfigDict(use_enum_values=False)

    @field_validator("density_g_per_ml", "unit_cost", "total_cost", mode="before")
    @classmethod
    def reject_float_decimal_fields(cls, value):
        if isinstance(value, float):
            raise ValueError("Decimal fields must be sent as strings, integers, Decimal values, or null; float is not allowed.")
        return value


class IngredientLotUpdateRequest(IngredientLotCreateRequest):
    pass


class IngredientLotResponse(BaseModel):
    id: int
    ingredient_id: int
    lot_code: str
    supplier_name: str
    purchased_at: str | None
    expires_at: str | None
    unit: UnitCode
    unit_cost: str | None
    total_cost: str | None
    density_g_per_ml: str | None
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


class IngredientLotsResponse(BaseModel):
    lots: list[IngredientLotResponse]
