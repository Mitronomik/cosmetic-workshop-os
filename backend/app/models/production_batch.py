from dataclasses import dataclass
from decimal import Decimal

from app.domain.units import UnitCode


@dataclass(frozen=True)
class ProductionBatchIngredient:
    id: int
    production_batch_id: int
    ingredient_id: int
    ingredient_lot_id: int
    ingredient_name_snapshot: str
    lot_code_snapshot: str
    required_quantity: Decimal
    consumed_quantity: Decimal
    unit: UnitCode
    unit_cost_snapshot: Decimal | None
    total_cost_snapshot: Decimal | None
    expiration_date_snapshot: str | None
    created_at: str


@dataclass(frozen=True)
class ProductionBatchPackaging:
    id: int
    production_batch_id: int
    packaging_item_id: int
    packaging_name_snapshot: str
    quantity: Decimal
    unit: UnitCode
    unit_cost_snapshot: Decimal | None
    total_cost_snapshot: Decimal | None
    created_at: str


@dataclass(frozen=True)
class ProductionBatch:
    id: int
    order_id: int
    recipe_version_id: int | None
    client_recipe_id: int | None
    final_batch_value: Decimal
    final_batch_unit: UnitCode
    component_cost: Decimal | None
    packaging_cost: Decimal | None
    other_cost: Decimal
    total_cost: Decimal | None
    sale_price: Decimal | None
    tax: Decimal | None
    margin: Decimal | None
    margin_percent: Decimal | None
    produced_at: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class ProductionBatchDetail:
    batch: ProductionBatch
    ingredients: list[ProductionBatchIngredient]
    packaging: list[ProductionBatchPackaging]
