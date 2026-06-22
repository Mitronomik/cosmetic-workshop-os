from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.units import UnitCode


class ClientRecipeStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class ClientRecipe:
    id: int
    client_id: int
    source_recipe_version_id: int
    title: str
    status: ClientRecipeStatus
    target_batch_size_value: Decimal | None
    target_batch_size_unit: UnitCode | None
    personalization_notes: str
    allergy_notes: str
    preference_notes: str
    contraindication_notes: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ClientRecipeIngredient:
    id: int
    client_recipe_id: int
    ingredient_id: int
    source_recipe_ingredient_id: int | None
    position: int
    phase: str
    amount_value: Decimal
    amount_unit: UnitCode
    personalization_note: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class ClientRecipeDetail:
    client_recipe: ClientRecipe
    ingredients: list[ClientRecipeIngredient]
