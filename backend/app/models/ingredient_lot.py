from dataclasses import dataclass
from decimal import Decimal

from app.domain.units import UnitCode


@dataclass(frozen=True)
class IngredientLot:
    id: int
    ingredient_id: int
    lot_code: str
    supplier_name: str
    purchased_at: str | None
    expires_at: str | None
    unit: UnitCode
    unit_cost: Decimal | None
    total_cost: Decimal | None
    density_g_per_ml: Decimal | None
    notes: str
    is_active: bool
    created_at: str
    updated_at: str
