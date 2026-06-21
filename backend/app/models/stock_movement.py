from dataclasses import dataclass
from decimal import Decimal

from app.domain.stock_movements import MovementDirection, StockMovementType
from app.domain.units import UnitCode


@dataclass(frozen=True)
class StockMovement:
    id: int
    ingredient_lot_id: int
    ingredient_id: int
    movement_type: StockMovementType
    quantity: Decimal
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
