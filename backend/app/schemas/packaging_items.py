from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.packaging_items import PackagingKind
from app.domain.units import UnitCode


class PackagingItemCreateRequest(BaseModel):
    name: str
    kind: PackagingKind
    unit: UnitCode = UnitCode.PIECE
    capacity_value: Decimal | int | str | None = None
    capacity_unit: UnitCode | None = None
    material: str = ""
    supplier_hint: str = ""
    unit_cost: Decimal | int | str | None = None
    notes: str = ""

    model_config = ConfigDict(use_enum_values=False)

    @field_validator("capacity_value", "unit_cost", mode="before")
    @classmethod
    def reject_float_numbers(cls, value):
        if isinstance(value, float):
            raise ValueError("Decimal numeric fields must be sent as strings, integers, Decimal, or null; float is not allowed.")
        return value


class PackagingItemUpdateRequest(PackagingItemCreateRequest):
    pass


class PackagingItemResponse(BaseModel):
    id: int
    name: str
    kind: PackagingKind
    unit: UnitCode
    capacity_value: str | None
    capacity_unit: UnitCode | None
    material: str
    supplier_hint: str
    unit_cost: str | None
    notes: str
    is_active: bool
    created_at: str
    updated_at: str
    catalog_category_id: int | None = None
    catalog_tag_ids: list[int] = Field(default_factory=list)


class PackagingItemsResponse(BaseModel):
    packaging_items: list[PackagingItemResponse]
