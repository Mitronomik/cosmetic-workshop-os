from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.units import UnitCode
from app.models.order import OrderStatus


class OrderRequest(BaseModel):
    client_id: int | None = None
    recipe_version_id: int | None = None
    client_recipe_id: int | None = None
    product_name: str
    target_batch_size_value: Decimal | int | str
    target_batch_size_unit: UnitCode
    packaging_item_id: int | None = None
    packaging_quantity: Decimal | int | str | None = None
    status: OrderStatus = OrderStatus.NEW
    sale_price: Decimal | int | str | None = None
    ordered_at: str | None = None
    planned_production_at: str | None = None
    produced_at: str | None = None
    delivered_at: str | None = None
    notes: str = ""
    model_config = ConfigDict(use_enum_values=False, extra="forbid")

    @field_validator("target_batch_size_value", "packaging_quantity", "sale_price", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float): raise ValueError("Decimal values must be strings, integers, Decimal, or null; float is not allowed.")
        return value


class OrderResponse(BaseModel):
    id:int; client_id:int; recipe_version_id:int|None; client_recipe_id:int|None; product_name:str; target_batch_size_value:str; target_batch_size_unit:UnitCode; packaging_item_id:int|None; packaging_quantity:str|None; status:OrderStatus; sale_price:str|None; ordered_at:str|None; planned_production_at:str|None; produced_at:str|None; delivered_at:str|None; notes:str; is_active:bool; created_at:str; updated_at:str


class OrdersResponse(BaseModel):
    orders: list[OrderResponse]
