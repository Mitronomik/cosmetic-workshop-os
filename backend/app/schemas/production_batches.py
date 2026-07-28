from pydantic import BaseModel, Field


class ProductionConfirmRequest(BaseModel):
    """The C2-II production confirmation request.

    Both tax-context keys are **required but nullable**, and are declared with
    no default: omitting one is an outdated client contract, while explicit
    `null/null` is the meaningful statement that the client's latest readiness
    result observed no valid configured tax rate. They are typed as `object`
    so an off-contract value reaches the domain parser and is rejected with the
    stable `invalid_tax_rate_context` code, instead of a raw Pydantic error.
    """

    confirm: bool = Field(default=False)
    notes: str | None = None
    expected_tax_rate_percent: object
    expected_tax_rate_effective_at: object


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
    # C2-II exposes the two rate snapshots here and in the confirmation response
    # only. They are deliberately absent from `ProductionBatchListItemResponse`
    # and from every report read model until C2-III.
    tax_rate_percent_snapshot: str | None
    tax_rate_effective_at_snapshot: str | None
    produced_at: str
    notes: str
    created_at: str
    ingredients: list[ProductionBatchIngredientResponse]
    packaging: list[ProductionBatchPackagingResponse]
