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
    catalog_category_id: int | None = None
    catalog_tag_ids: tuple[int, ...] = ()


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


@dataclass(frozen=True)
class RecipeCalculationIssue:
    severity: str
    code: str
    field: str | None
    message: str
    next_action: str | None = None


@dataclass(frozen=True)
class RecipeCalculationLine:
    recipe_ingredient_id: int
    position: int
    phase: str
    ingredient_id: int
    ingredient_name: str
    source_amount_value: Decimal
    source_amount_unit: UnitCode
    calculated_amount_value: Decimal | None
    calculated_amount_unit: UnitCode | None
    calculation_note: str


@dataclass(frozen=True)
class RecipeCalculationTotal:
    unit: UnitCode
    total_value: Decimal


@dataclass(frozen=True)
class RecipeCalculationResult:
    recipe_version_id: int
    recipe_template_id: int
    recipe_name: str
    version_number: int
    status: str
    target_batch_size_value: Decimal | None
    target_batch_size_unit: UnitCode | None
    percent_total: Decimal
    can_calculate: bool
    issues: list[RecipeCalculationIssue]
    lines: list[RecipeCalculationLine]
    totals_by_unit: list[RecipeCalculationTotal]
    generated_at: str
