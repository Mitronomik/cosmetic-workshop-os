from pydantic import BaseModel

from app.domain.packaging_items import PackagingKind
from app.domain.units import UnitCode


class IngredientLotBalanceRead(BaseModel):
    lot_id: int
    ingredient_id: int
    ingredient_name: str
    lot_code: str
    supplier: str
    unit: UnitCode
    balance_quantity: str
    purchase_date: str | None
    expiration_date: str | None
    is_expired: bool
    expires_soon: bool
    days_until_expiration: int | None
    is_active: bool
    has_positive_balance: bool
    created_at: str
    updated_at: str
    cost_per_unit: str | None
    density_value: str | None
    density_unit: str | None


class IngredientLotBalancesResponse(BaseModel):
    ingredient_lot_balances: list[IngredientLotBalanceRead]


class PackagingBalanceRead(BaseModel):
    packaging_item_id: int
    name: str
    kind: PackagingKind
    kind_label: str
    unit: UnitCode
    balance_quantity: str
    capacity_value: str | None
    capacity_unit: UnitCode | None
    material: str
    supplier_hint: str
    is_active: bool
    has_positive_balance: bool
    created_at: str
    updated_at: str
    unit_cost: str | None
    notes: str


class PackagingBalancesResponse(BaseModel):
    packaging_balances: list[PackagingBalanceRead]


class InventoryOverviewResponse(BaseModel):
    ingredient_lots_total: int
    ingredient_lots_with_positive_balance: int
    ingredient_lots_zero_balance: int
    ingredient_lots_expired: int
    ingredient_lots_expiring_soon: int
    active_ingredient_lots_total: int
    packaging_items_total: int
    packaging_items_with_positive_balance: int
    packaging_items_zero_balance: int
    active_packaging_items_total: int
    generated_at: str
