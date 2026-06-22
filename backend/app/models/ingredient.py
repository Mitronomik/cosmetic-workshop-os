from dataclasses import dataclass
from decimal import Decimal

from app.domain.ingredients import IngredientCategory
from app.domain.units import UnitCode


@dataclass(frozen=True)
class Ingredient:
    id: int
    name: str
    category: IngredientCategory
    default_unit: UnitCode
    density_g_per_ml: Decimal | None
    is_active: bool
    notes: str
    inci_name: str
    supplier_hint: str
    allergen_note: str
    usage_note: str
    created_at: str
    updated_at: str
    catalog_category_id: int | None = None
    catalog_tag_ids: tuple[int, ...] = ()
