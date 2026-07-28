from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.report_financials import ReportFinancialRow, ReportFinancialWarningCode, aggregate_report_financials
from app.schemas.reports import AlertsReportSummary, FinanceReportResponse, InventoryReportResponse, OrdersReportResponse, OverviewReportResponse, ProductionReportResponse, PurchaseReportSummary, QuantityTotal, ReportWarning

EXPIRING_SOON_DAYS = 30
ORDER_STATUSES = ("new", "waiting_for_materials", "ready_to_produce", "in_progress", "produced", "delivered", "cancelled", "archived")


class ReportsService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def get_overview(self) -> OverviewReportResponse:
        generated_at = _now()
        inventory = self.get_inventory_report(generated_at=generated_at)
        orders = self.get_orders_report(generated_at=generated_at)
        production = self.get_production_report(generated_at=generated_at)
        finance = self.get_finance_report(generated_at=generated_at)
        alerts = self._alerts_summary()
        purchases = self._purchase_summary()
        warnings = [*inventory.warnings, *orders.warnings, *production.warnings, *finance.warnings]
        return OverviewReportResponse(
            generated_at=generated_at,
            inventory_summary=inventory,
            orders_summary=orders,
            production_summary=production,
            alerts_summary=alerts,
            purchase_summary=purchases,
            finance_summary=finance,
            warnings=warnings,
        )

    def get_inventory_report(self, *, generated_at: str | None = None) -> InventoryReportResponse:
        today = date.today()
        with session(self.config) as connection:
            total_active_ingredients = _count(connection, "SELECT COUNT(*) FROM ingredients WHERE is_active=1")
            total_active_lots = _count(connection, "SELECT COUNT(*) FROM ingredient_lots WHERE is_active=1")
            active_packaging = _count(connection, "SELECT COUNT(*) FROM packaging_items WHERE is_active=1")
            low_stock_alerts = _count(connection, "SELECT COUNT(*) FROM alerts WHERE status='open' AND type IN ('low_ingredient_stock', 'low_packaging_stock')")
            open_suggestions = _count(connection, "SELECT COUNT(*) FROM purchase_suggestions WHERE status='open'")
            ingredient_lot_balances = _ingredient_lot_balances(connection)
            packaging_balances = _packaging_balances(connection)
            lot_rows = connection.execute("SELECT id, expires_at FROM ingredient_lots WHERE is_active=1").fetchall()
        expired = 0
        expiring = 0
        for row in lot_rows:
            if not row["expires_at"]:
                continue
            days = (date.fromisoformat(row["expires_at"]) - today).days
            if days < 0:
                expired += 1
            elif days <= EXPIRING_SOON_DAYS:
                expiring += 1
        return InventoryReportResponse(
            generated_at=generated_at or _now(),
            total_active_ingredients=total_active_ingredients,
            total_active_ingredient_lots=total_active_lots,
            ingredient_lots_with_positive_balance=sum(1 for value in ingredient_lot_balances.values() if value > 0),
            expired_ingredient_lots=expired,
            expiring_soon_ingredient_lots=expiring,
            active_packaging_items=active_packaging,
            packaging_items_with_positive_balance=sum(1 for value in packaging_balances.values() if value > 0),
            open_low_stock_alerts=low_stock_alerts,
            open_purchase_suggestions=open_suggestions,
            warnings=[],
        )

    def get_orders_report(self, *, generated_at: str | None = None) -> OrdersReportResponse:
        with session(self.config) as connection:
            total = _count(connection, "SELECT COUNT(*) FROM orders")
            active = _count(connection, "SELECT COUNT(*) FROM orders WHERE is_active=1")
            counts = {status: 0 for status in ORDER_STATUSES}
            for row in connection.execute("SELECT status, COUNT(*) AS count FROM orders GROUP BY status").fetchall():
                counts[row["status"]] = int(row["count"])
            missing_recipe = _count(connection, "SELECT COUNT(*) FROM orders WHERE recipe_version_id IS NULL AND client_recipe_id IS NULL")
        warnings = []
        if missing_recipe:
            warnings.append(_warning("orders_missing_recipe", "Есть заказы без выбранной базовой или индивидуальной рецептуры.", "orders_missing_recipe"))
        return OrdersReportResponse(generated_at=generated_at or _now(), total_orders=total, active_orders=active, new_orders=counts["new"], waiting_for_materials=counts["waiting_for_materials"], ready_to_produce=counts["ready_to_produce"], in_progress=counts["in_progress"], produced=counts["produced"], delivered=counts["delivered"], cancelled=counts["cancelled"], archived=counts["archived"], orders_missing_recipe=missing_recipe, warnings=warnings)

    def get_production_report(self, *, generated_at: str | None = None) -> ProductionReportResponse:
        with session(self.config) as connection:
            rows = connection.execute("SELECT final_batch_value, final_batch_unit, total_cost, produced_at FROM production_batches ORDER BY produced_at DESC, id DESC").fetchall()
            produced_orders = _count(connection, "SELECT COUNT(DISTINCT order_id) FROM production_batches")
        warnings = []
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        total_cost = Decimal("0")
        missing_cost = 0
        for row in rows:
            totals[row["final_batch_unit"]] += Decimal(row["final_batch_value"])
            if row["total_cost"] is None:
                missing_cost += 1
            else:
                total_cost += Decimal(row["total_cost"])
        if not rows:
            warnings.append(_warning("no_production_data", "Производственных партий пока нет."))
        if len(totals) > 1:
            warnings.append(_warning("mixed_units", "Общий объём производства показан отдельно по единицам, потому что партии указаны в разных единицах.", "produced_quantity_totals"))
        if missing_cost:
            warnings.append(_warning("missing_production_cost", "Не для всех производственных партий известна себестоимость.", "total_known_cost"))
        return ProductionReportResponse(generated_at=generated_at or _now(), total_production_batches=len(rows), batches_in_period=len(rows), last_production_date=rows[0]["produced_at"] if rows else None, produced_orders_count=produced_orders, produced_quantity_totals=[QuantityTotal(unit=unit, quantity=str(quantity)) for unit, quantity in sorted(totals.items())], total_known_cost=str(total_cost) if rows and missing_cost < len(rows) else None, missing_cost_count=missing_cost, warnings=warnings)

    def get_finance_report(self, *, generated_at: str | None = None) -> FinanceReportResponse:
        """The snapshot-backed finance report (`C2-III-B`).

        The persisted `ProductionBatch` financial snapshots are read and handed
        to the pure aggregation domain; this method calculates no tax and no
        margin of its own, and deliberately reads no tax-rate setting. The
        persisted row ``margin_percent`` is not selected at all, because it is a
        historical per-row value and is never aggregated.
        """
        with session(self.config) as connection:
            rows = connection.execute("SELECT sale_price, total_cost, tax, margin FROM production_batches").fetchall()

        aggregate = aggregate_report_financials(
            ReportFinancialRow(
                sale_price=_decimal(row["sale_price"]),
                total_cost=_decimal(row["total_cost"]),
                tax=_decimal(row["tax"]),
                margin=_decimal(row["margin"]),
            )
            for row in rows
        )

        return FinanceReportResponse(
            generated_at=generated_at or _now(),
            produced_order_count=aggregate.produced_order_count,
            produced_orders_with_sale_price=aggregate.produced_orders_with_sale_price,
            known_revenue=aggregate.known_revenue,
            known_production_cost=aggregate.known_production_cost,
            known_tax=aggregate.known_tax,
            known_margin=aggregate.known_margin,
            known_margin_percent=aggregate.known_margin_percent,
            complete_finance_record_count=aggregate.complete_finance_record_count,
            incomplete_margin_count=aggregate.incomplete_margin_count,
            missing_sale_price_count=aggregate.missing_sale_price_count,
            missing_cost_count=aggregate.missing_cost_count,
            tax_snapshot_record_count=aggregate.tax_snapshot_record_count,
            missing_tax_snapshot_count=aggregate.missing_tax_snapshot_count,
            margin_snapshot_record_count=aggregate.margin_snapshot_record_count,
            missing_margin_snapshot_count=aggregate.missing_margin_snapshot_count,
            warnings=[_finance_warning(code) for code in aggregate.warning_codes],
        )

    def _alerts_summary(self) -> AlertsReportSummary:
        with session(self.config) as connection:
            return AlertsReportSummary(open_alerts=_count(connection, "SELECT COUNT(*) FROM alerts WHERE status='open'"), critical_or_blocking_alerts=_count(connection, "SELECT COUNT(*) FROM alerts WHERE status='open' AND severity IN ('critical', 'blocking')"))

    def _purchase_summary(self) -> PurchaseReportSummary:
        with session(self.config) as connection:
            return PurchaseReportSummary(open_purchase_suggestions=_count(connection, "SELECT COUNT(*) FROM purchase_suggestions WHERE status='open'"))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _warning(code: str, message: str, field: str | None = None) -> ReportWarning:
    return ReportWarning(code=code, message=message, field=field)


def _decimal(value: str | None) -> Decimal | None:
    """A persisted money snapshot, or ``None`` when the row has none.

    A missing snapshot stays missing here rather than becoming a zero, which is
    what keeps an old batch out of the tax and margin totals instead of dragging
    them down with a value the workshop never recorded.
    """
    return None if value is None else Decimal(value)


# The user-facing meaning of every finance warning, with the report field it is
# about. The wording says what was *saved when the batch was produced*: reports
# read historical snapshots and never recalculate them from the current tax
# setting, so no message may suggest a calculation happened here.
_FINANCE_WARNING_TEXT: dict[ReportFinancialWarningCode, tuple[str, str]] = {
    ReportFinancialWarningCode.MISSING_SALE_PRICE: ("Не у всех произведённых заказов указана цена продажи.", "known_revenue"),
    ReportFinancialWarningCode.MISSING_PRODUCTION_COST: ("Не для всех производственных партий известна себестоимость.", "known_production_cost"),
    ReportFinancialWarningCode.TAX_UNAVAILABLE: ("Для произведённых партий нет сохранённых данных о налоге.", "known_tax"),
    ReportFinancialWarningCode.PARTIAL_TAX_BASIS: ("Налог показан только по партиям, где он был зафиксирован при изготовлении.", "known_tax"),
    ReportFinancialWarningCode.MARGIN_UNAVAILABLE: ("Для произведённых партий нет сохранённых данных о марже.", "known_margin"),
    ReportFinancialWarningCode.PARTIAL_MARGIN_BASIS: ("Маржа показана только по партиям, где она была зафиксирована при изготовлении.", "known_margin"),
    ReportFinancialWarningCode.MARGIN_PERCENT_UNAVAILABLE_ZERO_BASIS: ("Процент маржи недоступен: у учтённых партий нулевая сумма цен продажи.", "known_margin_percent"),
}


def _finance_warning(code: ReportFinancialWarningCode) -> ReportWarning:
    message, field = _FINANCE_WARNING_TEXT[code]
    return _warning(code.value, message, field)


def _count(connection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def _ingredient_lot_balances(connection) -> dict[int, Decimal]:
    balances = {int(row["id"]): Decimal("0") for row in connection.execute("SELECT id FROM ingredient_lots WHERE is_active=1")}
    rows = connection.execute("""
        SELECT sm.ingredient_lot_id, sm.direction, sm.quantity
        FROM stock_movements sm
        JOIN ingredient_lots il ON il.id = sm.ingredient_lot_id
        WHERE il.is_active=1
    """).fetchall()
    for row in rows:
        quantity = Decimal(row["quantity"])
        balances[int(row["ingredient_lot_id"])] += quantity if row["direction"] == "in" else -quantity
    return balances


def _packaging_balances(connection) -> dict[int, Decimal]:
    balances = {int(row["id"]): Decimal("0") for row in connection.execute("SELECT id FROM packaging_items WHERE is_active=1")}
    rows = connection.execute("""
        SELECT psm.packaging_item_id, psm.direction, psm.quantity
        FROM packaging_stock_movements psm
        JOIN packaging_items pi ON pi.id = psm.packaging_item_id
        WHERE pi.is_active=1
    """).fetchall()
    for row in rows:
        quantity = Decimal(row["quantity"])
        balances[int(row["packaging_item_id"])] += quantity if row["direction"] == "in" else -quantity
    return balances
