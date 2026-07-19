from decimal import Decimal

from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.decimal_utils import quantize_money
from app.domain.packaging_stock_movements import PackagingStockMovementDraft, PackagingStockMovementType
from app.domain.stock_movements import StockMovementDraft, StockMovementType
from app.domain.units import UnitCode
from app.models.order import OrderStatus
from app.models.production_batch import ProductionBatchDetail
from app.repositories.audit import AuditLogRepository
from app.repositories.orders import OrderNotFoundError, OrderRepository
from app.repositories.packaging_stock_movements import PackagingStockMovementRepository
from app.repositories.production_batches import ProductionBatchAlreadyExistsError, ProductionBatchRepository
from app.repositories.stock_movements import StockMovementRepository
from app.services.production_readiness import ProductionReadinessLifecycleError, ProductionReadinessService


class ProductionConfirmationRequiredError(ValueError):
    pass


class ProductionConfirmationLifecycleError(ValueError):
    pass


class ProductionConfirmationReadinessError(ValueError):
    def __init__(self, message: str, *, code: str = "readiness_blocked") -> None:
        super().__init__(message)
        self.code = code



class ProductionConfirmationStaleStateError(ProductionConfirmationLifecycleError):
    pass


class ProductionConfirmationService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.orders = OrderRepository(config)
        self.readiness = ProductionReadinessService(config)
        self.batches = ProductionBatchRepository()
        self.stock_movements = StockMovementRepository(config)
        self.packaging_movements = PackagingStockMovementRepository(config)
        self.audit = AuditLogRepository(config)

    def produce_order(self, order_id: int, confirm: bool, notes: str | None = None) -> ProductionBatchDetail:
        if confirm is not True:
            raise ProductionConfirmationRequiredError("Для изготовления нужно явно передать confirm=true.")
        order = self.orders.get_by_id(order_id)
        self._validate_lifecycle(order)
        readiness_order_snapshot = self._critical_order_snapshot(order)
        readiness = self.readiness.check_order(order_id)
        if not readiness.can_produce or readiness.blocking_issues:
            messages = "; ".join(issue.message for issue in readiness.blocking_issues) or "Заказ пока нельзя изготовить. Сначала устраните блокирующие замечания проверки."
            raise ProductionConfirmationReadinessError(messages, code="readiness_blocked")

        with transaction(self.config) as connection:
            locked_order = self.orders.get_by_id(order_id, connection=connection)
            self._validate_lifecycle(locked_order)
            if self._critical_order_snapshot(locked_order) != readiness_order_snapshot:
                raise ProductionConfirmationStaleStateError("Готовность заказа изменилась перед изготовлением. Запустите проверку готовности ещё раз.")
            if self.batches.exists_for_order(order_id, connection=connection):
                raise ProductionConfirmationLifecycleError("Заказ уже изготовлен: производственная партия уже существует.")
            readiness = self.readiness.check_order(order_id)
            if not readiness.can_produce or readiness.blocking_issues:
                messages = "; ".join(issue.message for issue in readiness.blocking_issues) or "Заказ пока нельзя изготовить. Сначала устраните блокирующие замечания проверки."
                raise ProductionConfirmationReadinessError(messages, code="readiness_changed")
            component_cost = Decimal("0")
            component_cost_known = True
            ingredient_rows=[]
            for line in readiness.ingredients:
                for selected in line.selected_lots:
                    lot = connection.execute("SELECT lot_code, unit_cost, expires_at FROM ingredient_lots WHERE id=?", (selected.lot_id,)).fetchone()
                    unit_cost = None if lot is None or lot["unit_cost"] is None else quantize_money(lot["unit_cost"], field="unit_cost_snapshot")
                    qty = Decimal(selected.selected_quantity)
                    line_cost = None if unit_cost is None else quantize_money(unit_cost * qty, field="ingredient_total_cost_snapshot")
                    if line_cost is None:
                        component_cost_known = False
                    else:
                        component_cost += line_cost
                    ingredient_rows.append((line, selected, lot, unit_cost, line_cost))
            packaging_cost = Decimal("0")
            packaging_cost_known = True
            packaging_rows=[]
            for line in readiness.packaging:
                item = connection.execute("SELECT name, unit, unit_cost FROM packaging_items WHERE id=?", (line.packaging_item_id,)).fetchone()
                unit_cost = None if item is None or item["unit_cost"] is None else quantize_money(item["unit_cost"], field="unit_cost_snapshot")
                qty = Decimal(line.required_quantity)
                line_cost = None if unit_cost is None else quantize_money(unit_cost * qty, field="packaging_total_cost_snapshot")
                if line_cost is None:
                    packaging_cost_known = False
                else:
                    packaging_cost += line_cost
                packaging_rows.append((line, item, unit_cost, line_cost))
            other_cost = Decimal("0.00")
            component_cost_snapshot = quantize_money(component_cost, field="component_cost") if component_cost_known else None
            packaging_cost_snapshot = quantize_money(packaging_cost, field="packaging_cost") if packaging_cost_known else None
            total_cost = quantize_money(component_cost + packaging_cost + other_cost, field="total_cost") if component_cost_known and packaging_cost_known else None
            batch = self.batches.create_batch(connection=connection, order_id=locked_order.id, recipe_version_id=locked_order.recipe_version_id, client_recipe_id=locked_order.client_recipe_id, final_batch_value=locked_order.target_batch_size_value, final_batch_unit=locked_order.target_batch_size_unit, component_cost=component_cost_snapshot, packaging_cost=packaging_cost_snapshot, other_cost=other_cost, total_cost=total_cost, sale_price=locked_order.sale_price, tax=None, margin=None, margin_percent=None, notes=(notes or "").strip())
            for line, selected, lot, unit_cost, line_cost in ingredient_rows:
                qty = Decimal(selected.selected_quantity)
                unit = UnitCode(selected.unit)
                self.batches.create_ingredient(connection=connection, production_batch_id=batch.id, ingredient_id=line.ingredient_id, ingredient_lot_id=selected.lot_id, ingredient_name_snapshot=line.ingredient_name, lot_code_snapshot="" if lot is None else lot["lot_code"], required_quantity=Decimal(line.required_quantity), consumed_quantity=qty, unit=unit, unit_cost_snapshot=unit_cost, total_cost_snapshot=line_cost, expiration_date_snapshot=None if lot is None else lot["expires_at"])
                self.stock_movements.create(StockMovementDraft.create(ingredient_lot_id=selected.lot_id, movement_type=StockMovementType.WRITE_OFF, quantity=qty, unit=unit, reason="production confirmation", note=f"Production batch #{batch.id} for order #{locked_order.id}", reference_type="production_batch", reference_id=str(batch.id), source="production"), connection=connection)
            for line, item, unit_cost, line_cost in packaging_rows:
                qty = Decimal(line.required_quantity)
                unit = UnitCode.PIECE if item is None else UnitCode(item["unit"])
                self.batches.create_packaging(connection=connection, production_batch_id=batch.id, packaging_item_id=line.packaging_item_id, packaging_name_snapshot=line.name if item is None else item["name"], quantity=qty, unit=unit, unit_cost_snapshot=unit_cost, total_cost_snapshot=line_cost)
                self.packaging_movements.create(PackagingStockMovementDraft.create(packaging_item_id=line.packaging_item_id, movement_type=PackagingStockMovementType.WRITE_OFF, quantity=qty, unit=unit, reason="production confirmation", source="production", notes=f"Production batch #{batch.id} for order #{locked_order.id}"), connection=connection)
            self.orders.mark_produced(locked_order.id, connection=connection)
            self.audit.create_log(action="production_confirmed", entity_type="production_batch", entity_id=str(batch.id), summary=f"Order #{locked_order.id} produced as batch #{batch.id}", metadata={"order_id": locked_order.id, "production_batch_id": batch.id, "status": "produced", "ingredient_rows": len(ingredient_rows), "packaging_rows": len(packaging_rows)}, connection=connection)
            return self.batches.get_detail(batch.id, connection=connection)

    def _validate_lifecycle(self, order) -> None:
        if not order.is_active or order.status in {OrderStatus.ARCHIVED, OrderStatus.CANCELLED, OrderStatus.PRODUCED, OrderStatus.DELIVERED}:
            raise ProductionConfirmationLifecycleError("Этот заказ нельзя изготовить в текущем статусе.")

    def _critical_order_snapshot(self, order) -> tuple:
        return (
            order.recipe_version_id,
            order.client_recipe_id,
            order.target_batch_size_value,
            order.target_batch_size_unit,
            order.packaging_item_id,
            order.packaging_quantity,
            order.sale_price,
            order.status,
            order.is_active,
        )


__all__ = ["ProductionConfirmationService", "ProductionConfirmationRequiredError", "ProductionConfirmationLifecycleError", "ProductionConfirmationStaleStateError", "ProductionConfirmationReadinessError", "ProductionReadinessLifecycleError", "OrderNotFoundError", "ProductionBatchAlreadyExistsError"]
