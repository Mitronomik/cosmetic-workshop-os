from dataclasses import dataclass
from decimal import Decimal

from app.domain.packaging_stock_movements import PackagingStockMovementType, PackagingMovementDirection
from app.domain.units import UnitCode


@dataclass(frozen=True)
class PackagingStockMovement:
    id: int
    packaging_item_id: int
    movement_type: PackagingStockMovementType
    quantity: Decimal
    unit: UnitCode
    direction: PackagingMovementDirection
    occurred_at: str
    reason: str
    source: str
    notes: str
    created_at: str
