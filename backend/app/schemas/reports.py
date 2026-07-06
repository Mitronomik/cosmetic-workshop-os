from pydantic import BaseModel


class ReportWarning(BaseModel):
    code: str
    message: str
    field: str | None = None


class QuantityTotal(BaseModel):
    unit: str
    quantity: str


class InventoryReportResponse(BaseModel):
    generated_at: str
    total_active_ingredients: int
    total_active_ingredient_lots: int
    ingredient_lots_with_positive_balance: int
    expired_ingredient_lots: int
    expiring_soon_ingredient_lots: int
    active_packaging_items: int
    packaging_items_with_positive_balance: int
    open_low_stock_alerts: int
    open_purchase_suggestions: int
    warnings: list[ReportWarning]


class OrdersReportResponse(BaseModel):
    generated_at: str
    total_orders: int
    active_orders: int
    new_orders: int
    waiting_for_materials: int
    ready_to_produce: int
    in_progress: int
    produced: int
    delivered: int
    cancelled: int
    archived: int
    orders_missing_recipe: int
    warnings: list[ReportWarning]


class ProductionReportResponse(BaseModel):
    generated_at: str
    total_production_batches: int
    batches_in_period: int
    last_production_date: str | None
    produced_orders_count: int
    produced_quantity_totals: list[QuantityTotal]
    total_known_cost: str | None
    missing_cost_count: int
    warnings: list[ReportWarning]


class FinanceReportResponse(BaseModel):
    generated_at: str
    produced_order_count: int
    produced_orders_with_sale_price: int
    known_revenue: str | None
    known_production_cost: str | None
    known_margin: str | None
    known_margin_percent: str | None
    missing_sale_price_count: int
    missing_cost_count: int
    warnings: list[ReportWarning]


class AlertsReportSummary(BaseModel):
    open_alerts: int
    critical_or_blocking_alerts: int


class PurchaseReportSummary(BaseModel):
    open_purchase_suggestions: int


class OverviewReportResponse(BaseModel):
    generated_at: str
    inventory_summary: InventoryReportResponse
    orders_summary: OrdersReportResponse
    production_summary: ProductionReportResponse
    alerts_summary: AlertsReportSummary
    purchase_summary: PurchaseReportSummary
    finance_summary: FinanceReportResponse
    warnings: list[ReportWarning]
