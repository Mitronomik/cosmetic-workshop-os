from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.db.connection import session
from app.domain.alerts import ALERT_TYPES, AlertCandidate, AlertGenerationResult
from app.models.order import OrderStatus
from app.repositories.alerts import AlertRepository
from app.repositories.orders import OrderRepository
from app.services.inventory import DEFAULT_EXPIRATION_WINDOW_DAYS, InventoryService
from app.services.production_readiness import ProductionReadinessLifecycleError, ProductionReadinessService

ACTIVE_ORDER_EXCLUDED_STATUSES = {OrderStatus.PRODUCED, OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.ARCHIVED}


class AlertGenerationService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.alerts = AlertRepository(config)
        self.inventory = InventoryService(config)
        self.orders = OrderRepository(config)
        self.readiness = ProductionReadinessService(config)

    def regenerate_alerts(self) -> AlertGenerationResult:
        candidates = self._candidates()
        active_keys = {candidate.alert_key for candidate in candidates}
        created = updated = 0
        with session(self.config) as connection:
            for candidate in candidates:
                _, was_created, was_updated = self.alerts.upsert_open_candidate(candidate, connection=connection)
                created += int(was_created)
                updated += int(was_updated)
            resolved = self.alerts.mark_open_alerts_resolved_if_not_in_keys(active_keys, ALERT_TYPES, connection=connection)
            open_count = self.alerts.count_open(connection=connection)
        return AlertGenerationResult(created, updated, resolved, open_count)

    def _candidates(self) -> list[AlertCandidate]:
        return [*self._low_ingredient_stock(), *self._low_packaging_stock(), *self._ingredient_expiration(), *self._order_readiness()]

    def _low_ingredient_stock(self) -> list[AlertCandidate]:
        balances: dict[int, Decimal] = {}
        units: dict[int, str] = {}
        names: dict[int, str] = {}
        for lot in self.inventory.list_ingredient_lot_balances(include_inactive=False):
            balances[lot.ingredient_id] = balances.get(lot.ingredient_id, Decimal("0")) + Decimal(lot.balance_quantity)
            units.setdefault(lot.ingredient_id, lot.unit)
            names.setdefault(lot.ingredient_id, lot.ingredient_name)
        rows = self._threshold_rows("ingredients", "id, name, default_unit, minimum_stock", "is_active=1 AND minimum_stock IS NOT NULL")
        result=[]
        for row in rows:
            available = balances.get(row["id"], Decimal("0"))
            minimum = Decimal(row["minimum_stock"])
            unit = units.get(row["id"], row["default_unit"])
            if available < minimum:
                name = names.get(row["id"], row["name"])
                result.append(AlertCandidate(f"low_ingredient_stock:ingredient:{row['id']}", "low_ingredient_stock", "warning", f"Компонент «{name}» ниже минимального остатка: доступно {available} {unit}, минимум {minimum} {unit}.", "ingredient", row["id"], "Добавьте компонент в закупку или внесите новую партию после покупки."))
        return result

    def _low_packaging_stock(self) -> list[AlertCandidate]:
        balances = {b.packaging_item_id: Decimal(b.balance_quantity) for b in self.inventory.list_packaging_balances(include_inactive=False)}
        rows = self._threshold_rows("packaging_items", "id, name, unit, minimum_stock", "is_active=1 AND minimum_stock IS NOT NULL")
        result=[]
        for row in rows:
            available = balances.get(row["id"], Decimal("0")); minimum = Decimal(row["minimum_stock"])
            if available < minimum:
                result.append(AlertCandidate(f"low_packaging_stock:packaging:{row['id']}", "low_packaging_stock", "warning", f"Тара «{row['name']}» ниже минимального остатка: доступно {available} {row['unit']}, минимум {minimum} {row['unit']}.", "packaging_item", row["id"], "Добавьте тару в закупку или внесите приход после покупки."))
        return result

    def _ingredient_expiration(self) -> list[AlertCandidate]:
        result=[]
        today = date.today()
        windows = self._expiration_windows()
        for lot in self.inventory.list_ingredient_lot_balances(include_inactive=False, only_positive=True, expires_within_days=36500):
            if lot.expiration_date is None:
                continue
            expiration = date.fromisoformat(lot.expiration_date)
            label = lot.lot_code or f"#{lot.lot_id}"
            if expiration < today:
                result.append(AlertCandidate(f"ingredient_expired:ingredient_lot:{lot.lot_id}", "ingredient_expired", "critical", f"Партия компонента «{lot.ingredient_name}» просрочена: партия {label}, срок был до {lot.expiration_date}.", "ingredient_lot", lot.lot_id, "Не используйте эту партию в производстве. Проверьте склад и оформите списание, если партия больше не пригодна."))
            else:
                window = windows.get(lot.ingredient_id, DEFAULT_EXPIRATION_WINDOW_DAYS)
                if expiration <= today + timedelta(days=window):
                    result.append(AlertCandidate(f"ingredient_expiration_soon:ingredient_lot:{lot.lot_id}", "ingredient_expiration_soon", "warning", f"Партия компонента «{lot.ingredient_name}» скоро истечёт: партия {label}, срок до {lot.expiration_date}.", "ingredient_lot", lot.lot_id, "Используйте партию раньше других или проверьте, нужна ли замена."))
        return result

    def _order_readiness(self) -> list[AlertCandidate]:
        result=[]
        for order in self.orders.list_orders(include_inactive=False):
            if order.status in ACTIVE_ORDER_EXCLUDED_STATUSES:
                continue
            try:
                readiness = self.readiness.check_order(order.id)
            except ProductionReadinessLifecycleError:
                continue
            if any((not line.can_fulfill) or any(issue.entity_type == "ingredient" for issue in readiness.blocking_issues) for line in readiness.ingredients):
                result.append(AlertCandidate(f"insufficient_materials_for_order:order:{order.id}", "insufficient_materials_for_order", "blocking", f"Заказ «{order.product_name}» нельзя изготовить: не хватает компонентов.", "order", order.id, "Откройте заказ, проверьте готовность производства и добавьте недостающие компоненты."))
            if any((not line.can_fulfill) for line in readiness.packaging) or any(issue.entity_type == "packaging_item" for issue in readiness.blocking_issues):
                result.append(AlertCandidate(f"insufficient_packaging_for_order:order:{order.id}", "insufficient_packaging_for_order", "blocking", f"Заказ «{order.product_name}» нельзя изготовить: не хватает тары.", "order", order.id, "Откройте заказ, проверьте готовность производства и добавьте недостающую тару."))
        return result

    def _threshold_rows(self, table: str, columns: str, where: str):
        with session(self.config) as c:
            return c.execute(f"SELECT {columns} FROM {table} WHERE {where} ORDER BY id").fetchall()

    def _expiration_windows(self) -> dict[int, int]:
        with session(self.config) as c:
            return {r["id"]: (r["expiration_alert_days"] if r["expiration_alert_days"] is not None else DEFAULT_EXPIRATION_WINDOW_DAYS) for r in c.execute("SELECT id, expiration_alert_days FROM ingredients").fetchall()}
