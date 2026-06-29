from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.units import UnitCode
from app.models.client_recipe import ClientRecipeStatus


class ClientRecipeCreateRequest(BaseModel):
    client_id: int | None = None
    source_recipe_version_id: int | None = None
    title: str
    status: ClientRecipeStatus = ClientRecipeStatus.DRAFT
    target_batch_size_value: Decimal | int | str | None = None
    target_batch_size_unit: UnitCode | None = None
    personalization_notes: str = ""
    allergy_notes: str = ""
    preference_notes: str = ""
    contraindication_notes: str = ""
    notes: str = ""
    model_config = ConfigDict(use_enum_values=False)

    @field_validator("target_batch_size_value", mode="before")
    @classmethod
    def reject_float_batch(cls, value):
        if isinstance(value, float):
            raise ValueError("target_batch_size_value must be sent as a string, integer, Decimal, or null; float is not allowed.")
        return value


class ClientRecipeIngredientUpdateRequest(BaseModel):
    id: int | None = None
    ingredient_id: int | None = None
    position: int
    phase: str = ""
    amount_value: Decimal | int | str
    amount_unit: UnitCode
    personalization_note: str = ""
    notes: str = ""
    model_config = ConfigDict(use_enum_values=False, extra="forbid")

    @field_validator("amount_value", mode="before")
    @classmethod
    def reject_float_amount(cls, value):
        if isinstance(value, float):
            raise ValueError("amount_value must be sent as a string, integer, or Decimal; float is not allowed.")
        return value


class ClientRecipeIngredientsUpdateRequest(BaseModel):
    ingredients: list[ClientRecipeIngredientUpdateRequest]
    model_config = ConfigDict(extra="forbid")


class ClientRecipeResponse(BaseModel):
    id: int
    client_id: int
    source_recipe_version_id: int
    title: str
    status: ClientRecipeStatus
    target_batch_size_value: str | None
    target_batch_size_unit: UnitCode | None
    personalization_notes: str
    allergy_notes: str
    preference_notes: str
    contraindication_notes: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


class ClientRecipesResponse(BaseModel):
    client_recipes: list[ClientRecipeResponse]


class ClientRecipeIngredientResponse(BaseModel):
    id: int
    client_recipe_id: int
    ingredient_id: int
    source_recipe_ingredient_id: int | None
    position: int
    phase: str
    amount_value: str
    amount_unit: UnitCode
    personalization_note: str
    notes: str
    created_at: str


class ClientRecipeDetailResponse(BaseModel):
    client_recipe: ClientRecipeResponse
    ingredients: list[ClientRecipeIngredientResponse]
