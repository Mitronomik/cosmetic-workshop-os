from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.units import UnitCode


class OrderStatus(StrEnum):
    NEW = "new"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    READY_TO_PRODUCE = "ready_to_produce"
    IN_PROGRESS = "in_progress"
    PRODUCED = "produced"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Order:
    id: int
    client_id: int
    recipe_version_id: int | None
    client_recipe_id: int | None
    product_name: str
    target_batch_size_value: Decimal
    target_batch_size_unit: UnitCode
    packaging_item_id: int | None
    packaging_quantity: Decimal | None
    status: OrderStatus
    sale_price: Decimal | None
    ordered_at: str | None
    planned_production_at: str | None
    produced_at: str | None
    delivered_at: str | None
    notes: str
    is_active: bool
    created_at: str
    updated_at: str
