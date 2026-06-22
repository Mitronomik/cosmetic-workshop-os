from dataclasses import dataclass
from decimal import Decimal

from app.domain.packaging_items import PackagingKind
from app.domain.units import UnitCode


@dataclass(frozen=True)
class PackagingItem:
    id: int
    name: str
    kind: PackagingKind
    unit: UnitCode
    capacity_value: Decimal | None
    capacity_unit: UnitCode | None
    material: str
    supplier_hint: str
    unit_cost: Decimal | None
    notes: str
    is_active: bool
    created_at: str
    updated_at: str
    catalog_category_id: int | None = None
    catalog_tag_ids: tuple[int, ...] = ()
