from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.units import UnitCode
from app.models.recipe import RecipeVersionStatus


class RecipeTemplateCreateRequest(BaseModel):
    name: str
    product_type: str = ""
    description: str = ""
    notes: str = ""


class RecipeTemplateResponse(BaseModel):
    id: int
    name: str
    product_type: str
    description: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


class RecipeTemplatesResponse(BaseModel):
    recipe_templates: list[RecipeTemplateResponse]


class RecipeIngredientCreateRequest(BaseModel):
    ingredient_id: int | None = None
    position: int
    phase: str = ""
    amount_value: Decimal | int | str
    amount_unit: UnitCode
    notes: str = ""
    model_config = ConfigDict(use_enum_values=False)

    @field_validator("amount_value", mode="before")
    @classmethod
    def reject_float_amount(cls, value):
        if isinstance(value, float):
            raise ValueError("amount_value must be sent as a string, integer, or Decimal; float is not allowed.")
        return value


class RecipeVersionCreateRequest(BaseModel):
    status: RecipeVersionStatus = RecipeVersionStatus.DRAFT
    title: str = ""
    target_batch_size_value: Decimal | int | str | None = None
    target_batch_size_unit: UnitCode | None = None
    notes: str = ""
    change_note: str = ""
    created_from_version_id: int | None = None
    ingredients: list[RecipeIngredientCreateRequest] = []
    model_config = ConfigDict(use_enum_values=False)

    @field_validator("target_batch_size_value", mode="before")
    @classmethod
    def reject_float_batch(cls, value):
        if isinstance(value, float):
            raise ValueError("target_batch_size_value must be sent as a string, integer, Decimal, or null; float is not allowed.")
        return value


class RecipeIngredientResponse(BaseModel):
    id: int
    recipe_version_id: int
    ingredient_id: int
    position: int
    phase: str
    amount_value: str
    amount_unit: UnitCode
    notes: str
    created_at: str


class RecipeVersionResponse(BaseModel):
    id: int
    recipe_template_id: int
    version_number: int
    status: RecipeVersionStatus
    title: str
    target_batch_size_value: str | None
    target_batch_size_unit: UnitCode | None
    notes: str
    change_note: str
    created_from_version_id: int | None
    created_at: str
    updated_at: str


class RecipeVersionsResponse(BaseModel):
    recipe_versions: list[RecipeVersionResponse]


class RecipeVersionDetailResponse(BaseModel):
    version: RecipeVersionResponse
    ingredients: list[RecipeIngredientResponse]
