from pydantic import BaseModel

from app.domain.production_readiness import ProductionReadinessSeverity, ProductionReadinessStatus


class ProductionReadinessIssue(BaseModel):
    code: str
    severity: ProductionReadinessSeverity
    message: str
    field: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None


class ProductionReadinessLotSelection(BaseModel):
    lot_id: int
    lot_code: str
    selected_quantity: str
    unit: str
    expires_at: str | None
    is_expired: bool
    expires_soon: bool


class ProductionReadinessIngredientLine(BaseModel):
    ingredient_id: int
    ingredient_name: str
    required_quantity: str
    required_unit: str
    available_quantity: str
    missing_quantity: str | None
    can_fulfill: bool
    selected_lots: list[ProductionReadinessLotSelection]
    warnings: list[ProductionReadinessIssue]


class ProductionReadinessPackagingLine(BaseModel):
    packaging_item_id: int
    name: str
    required_quantity: str
    available_quantity: str
    missing_quantity: str | None
    can_fulfill: bool


class ProductionReadinessResponse(BaseModel):
    order_id: int
    can_produce: bool
    status: ProductionReadinessStatus
    blocking_issues: list[ProductionReadinessIssue]
    warnings: list[ProductionReadinessIssue]
    ingredients: list[ProductionReadinessIngredientLine]
    packaging: list[ProductionReadinessPackagingLine]
    estimated_cost: str | None
    estimated_tax: str | None
    estimated_margin: str | None
    generated_at: str
