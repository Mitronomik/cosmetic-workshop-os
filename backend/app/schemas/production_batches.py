from pydantic import BaseModel, Field


class ProductionConfirmRequest(BaseModel):
    confirm: bool = Field(default=False)
    notes: str | None = None


class ProductionBatchIngredientResponse(BaseModel):
    id: int
    production_batch_id: int
    ingredient_id: int
    ingredient_lot_id: int
    ingredient_name_snapshot: str
    lot_code_snapshot: str
    required_quantity: str
    consumed_quantity: str
    unit: str
    unit_cost_snapshot: str | None
    total_cost_snapshot: str | None
    expiration_date_snapshot: str | None
    created_at: str


class ProductionBatchPackagingResponse(BaseModel):
    id: int
    production_batch_id: int
    packaging_item_id: int
    packaging_name_snapshot: str
    quantity: str
    unit: str
    unit_cost_snapshot: str | None
    total_cost_snapshot: str | None
    created_at: str


class ProductionBatchListItemResponse(BaseModel):
    id: int
    order_id: int
    product_name: str
    client_id: int
    client_name: str | None
    recipe_version_id: int | None
    client_recipe_id: int | None
    final_batch_value: str
    final_batch_unit: str
    total_cost: str | None
    sale_price: str | None
    tax: str | None
    margin: str | None
    margin_percent: str | None
    produced_at: str
    ingredient_line_count: int
    packaging_line_count: int
    notes: str


class ProductionBatchListResponse(BaseModel):
    production_batches: list[ProductionBatchListItemResponse]
    limit: int
    offset: int


class ProductionBatchDetailResponse(BaseModel):
    id: int
    order_id: int
    product_name: str | None = None
    client_id: int | None = None
    client_name: str | None = None
    recipe_version_id: int | None
    client_recipe_id: int | None
    final_batch_value: str
    final_batch_unit: str
    component_cost: str | None
    packaging_cost: str | None
    other_cost: str
    total_cost: str | None
    sale_price: str | None
    tax: str | None
    margin: str | None
    margin_percent: str | None
    produced_at: str
    notes: str
    created_at: str
    ingredients: list[ProductionBatchIngredientResponse]
    packaging: list[ProductionBatchPackagingResponse]
