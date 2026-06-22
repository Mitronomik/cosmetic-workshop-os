from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.units import UnitCode


class RecipeVersionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class RecipeTemplate:
    id: int
    name: str
    product_type: str
    description: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RecipeVersion:
    id: int
    recipe_template_id: int
    version_number: int
    status: RecipeVersionStatus
    title: str
    target_batch_size_value: Decimal | None
    target_batch_size_unit: UnitCode | None
    notes: str
    change_note: str
    created_from_version_id: int | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RecipeIngredient:
    id: int
    recipe_version_id: int
    ingredient_id: int
    position: int
    phase: str
    amount_value: Decimal
    amount_unit: UnitCode
    notes: str
    created_at: str


@dataclass(frozen=True)
class RecipeVersionDetail:
    version: RecipeVersion
    ingredients: list[RecipeIngredient]
