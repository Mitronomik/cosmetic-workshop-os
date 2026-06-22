from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.ingredients import IngredientCategory
from app.domain.units import UnitCode


class IngredientCreateRequest(BaseModel):
    name: str
    category: IngredientCategory
    default_unit: UnitCode
    density_g_per_ml: Decimal | int | str | None = None
    notes: str = ""
    inci_name: str = ""
    supplier_hint: str = ""
    allergen_note: str = ""
    usage_note: str = ""

    model_config = ConfigDict(use_enum_values=False)

    @field_validator("density_g_per_ml", mode="before")
    @classmethod
    def reject_float_density(cls, value):
        if isinstance(value, float):
            raise ValueError("density_g_per_ml must be sent as a string, integer, Decimal, or null; float is not allowed.")
        return value


class IngredientUpdateRequest(IngredientCreateRequest):
    pass


class IngredientResponse(BaseModel):
    id: int
    name: str
    category: IngredientCategory
    default_unit: UnitCode
    density_g_per_ml: str | None
    is_active: bool
    notes: str
    inci_name: str
    supplier_hint: str
    allergen_note: str
    usage_note: str
    created_at: str
    updated_at: str
    catalog_category_id: int | None = None
    catalog_tag_ids: list[int] = Field(default_factory=list)


class IngredientsResponse(BaseModel):
    ingredients: list[IngredientResponse]
