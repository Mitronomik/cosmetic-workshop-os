from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.decimal_utils import quantize_money, quantize_volume, quantize_weight
from app.domain.errors import DomainValidationError
from app.domain.production_financials import (
    FinancialWarningCode,
    ProductionFinancialInputs,
    TaxRateContext,
    estimate_production_financials,
)
from app.domain.tax_rate import parse_tax_rate_percent
from app.domain.units import UnitCode
from app.models.order import OrderStatus
from app.repositories.ingredients import IngredientRepository
from app.repositories.orders import OrderNotFoundError, OrderRepository
from app.repositories.packaging_items import PackagingItemNotFoundError, PackagingItemRepository
from app.repositories.settings import SettingsNotInitializedError
from app.schemas.production_readiness import (
    ProductionReadinessIngredientLine,
    ProductionReadinessIssue,
    ProductionReadinessLotSelection,
    ProductionReadinessPackagingLine,
    ProductionReadinessResponse,
)
from app.services.inventory import DEFAULT_EXPIRATION_WINDOW_DAYS, InventoryService
from app.services.recipe_calculations import RecipeCalculationService
from app.services.tax_rate_settings import TaxRateSettingsService
from app.repositories.client_recipes import ClientRecipeRepository
from app.repositories.recipes import RecipeRepository

FINANCIAL_WARNINGS: dict[FinancialWarningCode, tuple[str, str | None]] = {
    FinancialWarningCode.TAX_RATE_MISSING: ("Налоговая ставка пока не настроена, поэтому налог и маржа не рассчитаны.", "tax_rate"),
    FinancialWarningCode.SALE_PRICE_MISSING: ("В заказе нет цены продажи, поэтому налог и маржа не рассчитаны.", "sale_price"),
    FinancialWarningCode.COST_DATA_MISSING: ("Не хватает цен партий или тары для полной оценки себестоимости.", None),
    FinancialWarningCode.MARGIN_PERCENT_UNAVAILABLE_ZERO_SALE_PRICE: ("Цена продажи равна нулю, поэтому маржинальность в процентах не рассчитана.", "sale_price"),
    FinancialWarningCode.TAX_RATE_INVALID: ("Сохранённая налоговая ставка повреждена, поэтому налог и маржа не рассчитаны. Укажите ставку заново в настройках.", "tax_rate"),
}


class ProductionReadinessLifecycleError(ValueError):
    pass


class ProductionReadinessService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.orders = OrderRepository(config)
        self.inventory = InventoryService(config)
        self.calculations = RecipeCalculationService(config)
        self.recipes = RecipeRepository(config)
        self.client_recipes = ClientRecipeRepository(config)
        self.ingredients_repo = IngredientRepository(config)
        self.packaging_repo = PackagingItemRepository(config)
        self.tax_rate_settings = TaxRateSettingsService(config)

    def check_order(self, order_id: int) -> ProductionReadinessResponse:
        order = self.orders.get_by_id(order_id)
        if not order.is_active or order.status == OrderStatus.ARCHIVED:
            raise ProductionReadinessLifecycleError("Архивный заказ нельзя проверять к производству.")
        if order.status == OrderStatus.CANCELLED:
            raise ProductionReadinessLifecycleError("Отмененный заказ нельзя проверять к производству.")

        blocking: list[ProductionReadinessIssue] = []
        warnings: list[ProductionReadinessIssue] = []
        if order.target_batch_size_value <= 0:
            blocking.append(_issue("invalid_order_batch_size", "blocking", "Размер партии заказа должен быть больше нуля.", "target_batch_size_value", "order", order.id))

        recipe_lines = self._recipe_lines(order, blocking, warnings)
        ingredient_lines, ingredient_cost = self._check_ingredients(recipe_lines, blocking, warnings)
        packaging_lines, packaging_cost = self._check_packaging(order, blocking, warnings)
        financials = self._estimate_financials(order, ingredient_cost, packaging_cost, warnings)

        can_produce = not blocking and all(line.can_fulfill for line in ingredient_lines) and all(line.can_fulfill for line in packaging_lines)
        status = "blocked" if blocking else "warning" if warnings else "ready"
        return ProductionReadinessResponse(
            order_id=order.id,
            can_produce=can_produce,
            status=status,
            blocking_issues=blocking,
            warnings=warnings,
            ingredients=ingredient_lines,
            packaging=packaging_lines,
            sale_price=financials.sale_price,
            estimated_cost=financials.total_cost,
            tax_rate_percent=financials.tax_rate_percent,
            tax_rate_effective_at=financials.tax_rate_effective_at,
            estimated_tax=financials.tax_amount,
            estimated_margin=financials.margin,
            estimated_margin_percent=financials.margin_percent,
            financial_estimate_status=financials.status,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def _recipe_lines(self, order, blocking, warnings):
        if order.recipe_version_id is not None:
            result = self.calculations.calculate_version(order.recipe_version_id, target_batch_size_value=order.target_batch_size_value, target_batch_size_unit=order.target_batch_size_unit)
            for issue in result.issues:
                target = blocking if issue.severity == "error" else warnings
                target.append(_issue(issue.code, "blocking" if issue.severity == "error" else "warning", issue.message, issue.field, "recipe_version", order.recipe_version_id))
            if not result.lines:
                blocking.append(_issue("recipe_composition_empty", "blocking", "В выбранной версии рецепта нет строк состава.", "recipe_version_id", "recipe_version", order.recipe_version_id))
            return [(line.ingredient_id, line.ingredient_name, line.calculated_amount_value, line.calculated_amount_unit) for line in result.lines]
        if order.client_recipe_id is not None:
            detail = self.client_recipes.get_detail(order.client_recipe_id)
            if not detail.ingredients:
                blocking.append(_issue("client_recipe_composition_empty", "blocking", "В индивидуальном рецепте нет строк состава.", "client_recipe_id", "client_recipe", order.client_recipe_id))
            percent_total = sum((line.amount_value for line in detail.ingredients if line.amount_unit == UnitCode.PERCENT), Decimal("0"))
            if percent_total < Decimal("100") and percent_total > 0:
                warnings.append(_issue("percent_total_below_100", "warning", f"Сумма процентных строк индивидуального рецепта меньше 100%: {percent_total}%.", "percent_total", "client_recipe", order.client_recipe_id))
            elif percent_total > Decimal("100"):
                blocking.append(_issue("percent_total_above_100", "blocking", f"Сумма процентных строк индивидуального рецепта больше 100%: {percent_total}%.", "percent_total", "client_recipe", order.client_recipe_id))
            ingredients = {i.id: i.name for i in self.ingredients_repo.list_active()}
            rows=[]
            for line in detail.ingredients:
                value, unit = line.amount_value, line.amount_unit
                if unit == UnitCode.PERCENT:
                    value = order.target_batch_size_value * value / Decimal("100")
                    unit = order.target_batch_size_unit
                rows.append((line.ingredient_id, ingredients.get(line.ingredient_id, "Компонент из индивидуальной формулы"), value, unit))
            return rows
        blocking.append(_issue("missing_recipe_source", "blocking", "В заказе не выбран источник рецепта.", "recipe_source", "order", order.id))
        return []

    def _check_ingredients(self, recipe_lines, blocking, warnings):
        lots_by_ingredient = defaultdict(list)
        for lot in self.inventory.list_ingredient_lot_balances(include_inactive=False, only_positive=True, expires_within_days=DEFAULT_EXPIRATION_WINDOW_DAYS):
            lots_by_ingredient[lot.ingredient_id].append(lot)
        ingredients = {i.id: i for i in self.ingredients_repo.list_active()}
        result=[]; total_cost=Decimal("0"); all_cost_known=True
        required_by_ingredient: dict[int, tuple[str, Decimal, UnitCode, list[ProductionReadinessIssue]]] = {}
        for ingredient_id, name, value, unit in recipe_lines:
            if value is None or unit is None:
                issue=_issue("ingredient_amount_not_calculated", "blocking", "Количество компонента не удалось рассчитать.", "recipe_ingredient", "ingredient", ingredient_id)
                blocking.append(issue); continue
            if unit == UnitCode.PERCENT:
                issue=_issue("ingredient_amount_not_calculated", "blocking", "Процентная строка не была рассчитана в фактическое количество.", "recipe_ingredient", "ingredient", ingredient_id)
                blocking.append(issue); continue
            if ingredient_id in required_by_ingredient:
                old_name, old_value, old_unit, old_warnings = required_by_ingredient[ingredient_id]
                if old_unit == unit:
                    required_by_ingredient[ingredient_id] = (old_name, old_value + value, old_unit, old_warnings)
                else:
                    issue=_issue("mixed_required_units", "blocking", "Один компонент рассчитан в разных единицах; пока нельзя надежно проверить склад.", "amount_unit", "ingredient", ingredient_id)
                    blocking.append(issue)
            else:
                required_by_ingredient[ingredient_id]=(name, value, unit, [])

        for ingredient_id, (name, required, unit, line_warnings) in required_by_ingredient.items():
            ingredient = ingredients.get(ingredient_id)
            lot_candidates=[]
            for lot in lots_by_ingredient.get(ingredient_id, []):
                converted, conversion_issue = self._convert_required(required, unit, UnitCode(lot.unit), ingredient, lot)
                if conversion_issue is not None:
                    line_warnings.append(conversion_issue); warnings.append(conversion_issue); continue
                lot_candidates.append((lot, converted))
            selected=[]; remaining=None; available=Decimal("0")
            lot_units = {UnitCode(candidate[0].unit) for candidate in lot_candidates}
            if len(lot_units) > 1:
                blocking.append(_issue("mixed_lot_units_not_supported", "blocking", "Для одного компонента найдены партии в разных единицах. Пока нельзя надежно подобрать партии автоматически.", "unit", "ingredient", ingredient_id))
                result.append(ProductionReadinessIngredientLine(ingredient_id=ingredient_id, ingredient_name=name, required_quantity=str(required), required_unit=unit.value, available_quantity="0", missing_quantity=str(required), can_fulfill=False, selected_lots=[], warnings=line_warnings))
                continue
            if lot_candidates:
                required_in_lot_unit = lot_candidates[0][1]
                remaining = required_in_lot_unit
                for lot, converted_required in sorted(lot_candidates, key=lambda item: (item[0].expiration_date is None, item[0].expiration_date or "9999-12-31", item[0].lot_id)):
                    available += Decimal(lot.balance_quantity)
                    if remaining <= 0: continue
                    take = min(Decimal(lot.balance_quantity), remaining)
                    if take <= 0: continue
                    selected.append(ProductionReadinessLotSelection(lot_id=lot.lot_id, lot_code=lot.lot_code, selected_quantity=str(take), unit=lot.unit.value if hasattr(lot.unit, "value") else str(lot.unit), expires_at=lot.expiration_date, is_expired=lot.is_expired, expires_soon=lot.expires_soon))
                    if lot.is_expired:
                        issue=_issue("lot_expired", "warning", f"Выбранная партия “{lot.lot_code}” уже просрочена.", "expires_at", "ingredient_lot", lot.lot_id); line_warnings.append(issue); warnings.append(issue)
                    elif lot.expires_soon:
                        issue=_issue("lot_expires_soon", "warning", f"Выбранная партия “{lot.lot_code}” скоро истекает.", "expires_at", "ingredient_lot", lot.lot_id); line_warnings.append(issue); warnings.append(issue)
                    if lot.cost_per_unit is None: all_cost_known=False
                    else: total_cost += take * Decimal(lot.cost_per_unit)
                    remaining -= take
            missing = None
            can = bool(lot_candidates) and remaining is not None and remaining <= 0
            if not lot_candidates:
                missing = str(required)
                blocking.append(_issue("ingredient_lot_missing", "blocking", f"Для компонента “{name}” нет доступной партии с положительным остатком.", "ingredient_id", "ingredient", ingredient_id))
            elif not can:
                missing_qty = remaining if remaining is not None else required
                missing = str(missing_qty)
                blocking.append(_issue("ingredient_stock_insufficient", "blocking", f"Компонента “{name}” недостаточно для заказа.", "ingredient_id", "ingredient", ingredient_id))
            result.append(ProductionReadinessIngredientLine(ingredient_id=ingredient_id, ingredient_name=name, required_quantity=str(required), required_unit=unit.value, available_quantity=str(available), missing_quantity=missing, can_fulfill=can, selected_lots=selected, warnings=line_warnings))
        if not all_cost_known:
            total_cost = None
        return result, total_cost

    def _convert_required(self, value, from_unit, to_unit, ingredient, lot):
        if from_unit == to_unit:
            return value, None
        density = None
        if lot.density_value is not None:
            density = Decimal(lot.density_value)
        elif ingredient is not None and ingredient.density_g_per_ml is not None:
            density = ingredient.density_g_per_ml
        if from_unit == UnitCode.MILLILITER and to_unit == UnitCode.GRAM:
            if density is None:
                return None, _issue("density_missing", "warning", "Для перевода мл в граммы не указана плотность компонента или партии.", "density_g_per_ml", "ingredient", None if ingredient is None else ingredient.id)
            return quantize_weight(value * density, field="required_quantity"), None
        if from_unit == UnitCode.GRAM and to_unit == UnitCode.MILLILITER:
            if density is None:
                return None, _issue("density_missing", "warning", "Для перевода граммов в мл не указана плотность компонента или партии.", "density_g_per_ml", "ingredient", None if ingredient is None else ingredient.id)
            return quantize_volume(value / density, field="required_quantity"), None
        return None, _issue("unit_mismatch", "warning", f"Нельзя сопоставить рецепт в {from_unit.value} со складской партией в {to_unit.value}.", "unit", "ingredient", None if ingredient is None else ingredient.id)

    def _check_packaging(self, order, blocking, warnings):
        if order.packaging_item_id is None:
            warnings.append(_issue("packaging_not_selected", "info", "Тара для заказа не выбрана; проверка тары пропущена.", "packaging_item_id", "order", order.id))
            return [], Decimal("0")
        try:
            item = self.packaging_repo.get_by_id(order.packaging_item_id)
        except PackagingItemNotFoundError:
            blocking.append(_issue("packaging_missing", "blocking", "Выбранная тара не найдена.", "packaging_item_id", "packaging_item", order.packaging_item_id))
            return [], None
        if not item.is_active:
            blocking.append(_issue("packaging_inactive", "blocking", f"Тара “{item.name}” неактивна.", "packaging_item_id", "packaging_item", item.id))
        if order.packaging_quantity is None:
            blocking.append(_issue("packaging_quantity_missing", "blocking", "Для выбранной тары нужно указать количество.", "packaging_quantity", "order", order.id))
            return [ProductionReadinessPackagingLine(packaging_item_id=item.id, name=item.name, required_quantity="0", available_quantity="0", missing_quantity=None, can_fulfill=False)], None
        balances = {b.packaging_item_id: b for b in self.inventory.list_packaging_balances(include_inactive=True)}
        balance = balances.get(item.id)
        available = Decimal("0") if balance is None else Decimal(balance.balance_quantity)
        missing = order.packaging_quantity - available
        can = missing <= 0 and item.is_active
        if not can:
            blocking.append(_issue("packaging_stock_insufficient", "blocking", f"Тары “{item.name}” недостаточно для заказа.", "packaging_item_id", "packaging_item", item.id))
        cost = None if item.unit_cost is None else item.unit_cost * order.packaging_quantity
        return [ProductionReadinessPackagingLine(packaging_item_id=item.id, name=item.name, required_quantity=str(order.packaging_quantity), available_quantity=str(available), missing_quantity=str(missing) if missing > 0 else None, can_fulfill=can)], cost

    def _estimate_financials(self, order, ingredient_cost, packaging_cost, warnings):
        """Run the pure financial calculation and map its warnings.

        The service supplies backend-owned values and owns no formula; the
        arithmetic lives in `app.domain.production_financials`.
        """
        total_cost = None if ingredient_cost is None or packaging_cost is None else quantize_money(ingredient_cost + packaging_cost, field="estimated_cost")
        estimate = estimate_production_financials(
            ProductionFinancialInputs(sale_price=order.sale_price, total_cost=total_cost, tax_rate=self._tax_rate_context())
        )
        warnings.extend(_financial_issue(code, order.id) for code in estimate.warning_codes)
        return estimate

    def _tax_rate_context(self) -> TaxRateContext:
        """Read the current rate through the C1 service and re-validate it.

        The C1 Settings repair surface deliberately still returns the stored
        text for an externally corrupted row so the user can replace it, so
        `is_configured` alone is not proof that the value is financially
        authoritative. Anything that does not re-parse as the canonical C1
        percentage — or that carries no effective timestamp — becomes the C2
        no-valid-rate context instead of a calculated or fabricated value.
        """
        try:
            state = self.tax_rate_settings.get_tax_rate()
        except SettingsNotInitializedError:
            return TaxRateContext.missing()
        if state.tax_rate_percent is None:
            return TaxRateContext.missing()
        try:
            percent = parse_tax_rate_percent(state.tax_rate_percent)
        except DomainValidationError:
            return TaxRateContext.invalid_value()
        if state.effective_at is None:
            return TaxRateContext.invalid_value()
        return TaxRateContext.configured(percent, state.effective_at)


def _issue(code, severity, message, field=None, entity_type=None, entity_id=None):
    return ProductionReadinessIssue(code=code, severity=severity, message=message, field=field, entity_type=entity_type, entity_id=entity_id)


def _financial_issue(code: FinancialWarningCode, order_id: int) -> ProductionReadinessIssue:
    """Carry a financial warning through the existing non-blocking structure."""
    message, field = FINANCIAL_WARNINGS[code]
    return _issue(code.value, "warning", message, field, "order", order_id)


__all__ = ["ProductionReadinessService", "ProductionReadinessLifecycleError", "OrderNotFoundError"]
