from __future__ import annotations

from decimal import Decimal

from app.db.config import DatabaseConfig
from app.db.connection import session
from app.domain.purchase_suggestions import MANAGED_GENERATED_REASONS, PurchaseSuggestionCandidate, PurchaseSuggestionGenerationResult
from app.domain.units import UnitCode
from app.models.order import OrderStatus
from app.repositories.ingredients import IngredientNotFoundError, IngredientRepository
from app.repositories.orders import OrderRepository
from app.repositories.packaging_items import PackagingItemNotFoundError, PackagingItemRepository
from app.repositories.purchase_suggestions import PurchaseSuggestionRepository
from app.services.inventory import InventoryService
from app.services.production_readiness import ProductionReadinessLifecycleError, ProductionReadinessService

ACTIVE_ORDER_EXCLUDED_STATUSES = {OrderStatus.PRODUCED, OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.ARCHIVED}


class PurchaseSuggestionValidationError(ValueError):
    pass


class PurchaseSuggestionGenerationService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.suggestions = PurchaseSuggestionRepository(config)
        self.inventory = InventoryService(config)
        self.orders = OrderRepository(config)
        self.readiness = ProductionReadinessService(config)

    def regenerate_suggestions(self) -> PurchaseSuggestionGenerationResult:
        candidates = self._candidates()
        active_keys = {c.suggestion_key for c in candidates}
        created = updated = 0
        with session(self.config) as connection:
            for candidate in candidates:
                _, was_created, was_updated = self.suggestions.upsert_open_candidate(candidate, connection=connection)
                created += int(was_created)
                updated += int(was_updated)
            archived = self.suggestions.archive_open_suggestions_if_not_in_keys(active_keys, MANAGED_GENERATED_REASONS, connection=connection)
            open_count = self.suggestions.count_open(connection=connection)
        return PurchaseSuggestionGenerationResult(created, updated, archived, open_count)

    def _candidates(self) -> list[PurchaseSuggestionCandidate]:
        return [*self._low_ingredient_stock(), *self._low_packaging_stock(), *self._order_shortages()]

    def _low_ingredient_stock(self) -> list[PurchaseSuggestionCandidate]:
        balances: dict[int, Decimal] = {}
        units: dict[int, str] = {}
        names: dict[int, str] = {}
        for lot in self.inventory.list_ingredient_lot_balances(include_inactive=False):
            balances[lot.ingredient_id] = balances.get(lot.ingredient_id, Decimal("0")) + Decimal(lot.balance_quantity)
            units.setdefault(lot.ingredient_id, lot.unit)
            names.setdefault(lot.ingredient_id, lot.ingredient_name)
        with session(self.config) as c:
            rows = c.execute("SELECT id, name, default_unit, minimum_stock FROM ingredients WHERE is_active=1 AND minimum_stock IS NOT NULL ORDER BY id").fetchall()
        result=[]
        for row in rows:
            available = balances.get(row["id"], Decimal("0"))
            minimum = Decimal(row["minimum_stock"])
            if available < minimum:
                missing = minimum - available
                unit = units.get(row["id"], row["default_unit"])
                name = names.get(row["id"], row["name"])
                result.append(PurchaseSuggestionCandidate(
                    f"below_minimum_stock:ingredient:{row['id']}", "ingredient", row["id"], name, _fmt(missing), unit, "below_minimum_stock", "ingredient", row["id"],
                    f"Купить компонент «{name}»: не хватает {_fmt(missing)} {unit} до минимального остатка.",
                    f"Текущий остаток ниже минимума: доступно {_fmt(available)} {unit}, минимум {_fmt(minimum)} {unit}.",
                ))
        return result

    def _low_packaging_stock(self) -> list[PurchaseSuggestionCandidate]:
        balances = {b.packaging_item_id: Decimal(b.balance_quantity) for b in self.inventory.list_packaging_balances(include_inactive=False)}
        with session(self.config) as c:
            rows = c.execute("SELECT id, name, unit, minimum_stock FROM packaging_items WHERE is_active=1 AND minimum_stock IS NOT NULL ORDER BY id").fetchall()
        result=[]
        for row in rows:
            available = balances.get(row["id"], Decimal("0")); minimum = Decimal(row["minimum_stock"])
            if available < minimum:
                missing = minimum - available
                result.append(PurchaseSuggestionCandidate(
                    f"below_minimum_stock:packaging:{row['id']}", "packaging", row["id"], row["name"], _fmt(missing), row["unit"], "below_minimum_stock", "packaging_item", row["id"],
                    f"Купить тару «{row['name']}»: не хватает {_fmt(missing)} {row['unit']} до минимального остатка.",
                    f"Текущий остаток ниже минимума: доступно {_fmt(available)} {row['unit']}, минимум {_fmt(minimum)} {row['unit']}.",
                ))
        return result

    def _order_shortages(self) -> list[PurchaseSuggestionCandidate]:
        result=[]
        for order in self.orders.list_orders(include_inactive=False):
            if order.status in ACTIVE_ORDER_EXCLUDED_STATUSES:
                continue
            try:
                readiness = self.readiness.check_order(order.id)
            except ProductionReadinessLifecycleError:
                continue
            for line in readiness.ingredients:
                if line.can_fulfill or line.missing_quantity is None:
                    continue
                qty = Decimal(line.missing_quantity)
                if qty <= 0:
                    continue
                result.append(PurchaseSuggestionCandidate(
                    f"insufficient_for_order:ingredient:{line.ingredient_id}:order:{order.id}", "ingredient", line.ingredient_id, line.ingredient_name, _fmt(qty), line.required_unit, "insufficient_for_order", "order", order.id,
                    f"Купить компонент «{line.ingredient_name}» для заказа №{order.id}: не хватает {_fmt(qty)} {line.required_unit}.",
                    f"Недостаточно компонента для заказа «{order.product_name}».",
                ))
            for line in readiness.packaging:
                if line.can_fulfill or line.missing_quantity is None:
                    continue
                qty = Decimal(line.missing_quantity)
                if qty <= 0:
                    continue
                result.append(PurchaseSuggestionCandidate(
                    f"insufficient_for_order:packaging:{line.packaging_item_id}:order:{order.id}", "packaging", line.packaging_item_id, line.name, _fmt(qty), UnitCode.PIECE.value, "insufficient_for_order", "order", order.id,
                    f"Купить тару «{line.name}» для заказа №{order.id}: не хватает {_fmt(qty)} {UnitCode.PIECE.value}.",
                    f"Недостаточно тары для заказа «{order.product_name}».",
                ))
        return result


class PurchaseSuggestionCommandService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.suggestions = PurchaseSuggestionRepository(config)
        self.ingredients = IngredientRepository(config)
        self.packaging = PackagingItemRepository(config)

    def create_manual(self, *, item_type: str, item_id: int, recommended_quantity, unit: str, notes: str = ""):
        qty = _positive_quantity(recommended_quantity)
        unit = _unit(unit)
        if item_type == "ingredient":
            try: item = self.ingredients.get_by_id(item_id)
            except IngredientNotFoundError as exc: raise PurchaseSuggestionValidationError("Компонент не найден.") from exc
        elif item_type == "packaging":
            try: item = self.packaging.get_by_id(item_id)
            except PackagingItemNotFoundError as exc: raise PurchaseSuggestionValidationError("Тара не найдена.") from exc
        else:
            raise PurchaseSuggestionValidationError("Тип позиции должен быть ingredient или packaging.")
        if not item.is_active:
            raise PurchaseSuggestionValidationError("Можно создать закупку только для активной позиции.")
        return self.suggestions.create_manual_suggestion(item_type=item_type, item_id=item_id, item_name_snapshot=item.name, recommended_quantity=_fmt(qty), unit=unit, notes=notes or "")

    def update_open(self, suggestion_id: int, *, recommended_quantity, unit: str, notes: str = ""):
        qty = _positive_quantity(recommended_quantity)
        return self.suggestions.update_open_suggestion(suggestion_id, recommended_quantity=_fmt(qty), unit=_unit(unit), notes=notes or "")


def _positive_quantity(value) -> Decimal:
    if isinstance(value, float):
        raise PurchaseSuggestionValidationError("Количество нужно передавать строкой или целым числом, не float.")
    try:
        qty = Decimal(str(value))
    except Exception as exc:
        raise PurchaseSuggestionValidationError("Количество должно быть числом больше нуля.") from exc
    if qty <= 0:
        raise PurchaseSuggestionValidationError("Количество должно быть больше нуля.")
    return qty


def _unit(value: str) -> str:
    unit = " ".join(value.strip().split()) if isinstance(value, str) else ""
    if not unit:
        raise PurchaseSuggestionValidationError("Единица измерения обязательна.")
    return unit


def _fmt(value: Decimal) -> str:
    return format(value.normalize(), "f")
