from dataclasses import dataclass
from decimal import Decimal

from app.domain.decimal_utils import quantize_count, quantize_money
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import ALLOWED_BATCH_SIZE_UNITS, normalize_optional_text, normalize_required_text, parse_unit, positive_amount, require_positive_id
from app.domain.units import UnitCode
from app.models.order import OrderStatus


@dataclass(frozen=True)
class OrderDraft:
    client_id: int
    recipe_version_id: int | None
    client_recipe_id: int | None
    product_name: str
    target_batch_size_value: Decimal
    target_batch_size_unit: UnitCode
    packaging_item_id: int | None = None
    packaging_quantity: Decimal | None = None
    status: OrderStatus = OrderStatus.NEW
    sale_price: Decimal | None = None
    ordered_at: str | None = None
    planned_production_at: str | None = None
    produced_at: str | None = None
    delivered_at: str | None = None
    notes: str = ""

    @classmethod
    def create(cls, *, client_id: int | None, recipe_version_id: int | None = None, client_recipe_id: int | None = None, product_name: str, target_batch_size_value: Decimal | int | str, target_batch_size_unit: UnitCode | str, packaging_item_id: int | None = None, packaging_quantity: Decimal | int | str | None = None, status: OrderStatus | str = OrderStatus.NEW, sale_price: Decimal | int | str | None = None, ordered_at: str | None = None, planned_production_at: str | None = None, produced_at: str | None = None, delivered_at: str | None = None, notes: str | None = "") -> "OrderDraft":
        client_id = require_positive_id(client_id, field="client_id", label="Клиент")
        recipe_version_id = None if recipe_version_id is None else require_positive_id(recipe_version_id, field="recipe_version_id", label="Версия рецепта")
        client_recipe_id = None if client_recipe_id is None else require_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт")
        if (recipe_version_id is None) == (client_recipe_id is None):
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "В заказе должен быть выбран ровно один источник рецепта.", "recipe_source", f"recipe_version_id={recipe_version_id}, client_recipe_id={client_recipe_id}", "Выберите либо версию базового рецепта, либо индивидуальный рецепт клиента."))
        unit = parse_unit(target_batch_size_unit, field="target_batch_size_unit", allowed=ALLOWED_BATCH_SIZE_UNITS)
        pkg_id = None if packaging_item_id is None else require_positive_id(packaging_item_id, field="packaging_item_id", label="Тара")
        if packaging_quantity is not None and pkg_id is None:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Для количества тары нужно выбрать конкретную тару.", "packaging_item_id", None, "Выберите тару или оставьте количество тары пустым."))
        pkg_qty = None
        if packaging_quantity is not None:
            pkg_qty = quantize_count(packaging_quantity, field="packaging_quantity")
            if pkg_qty <= 0:
                raise DomainValidationError(DomainIssue(DomainIssueCode.ZERO_QUANTITY, "Количество тары должно быть больше нуля.", "packaging_quantity", str(pkg_qty), "Укажите положительное целое количество тары."))
        parsed_price = None
        if sale_price is not None:
            parsed_price = quantize_money(sale_price, field="sale_price")
            if parsed_price < 0:
                raise DomainValidationError(DomainIssue(DomainIssueCode.NEGATIVE_QUANTITY, "Цена продажи не может быть отрицательной.", "sale_price", str(parsed_price), "Укажите ноль или положительную цену."))
        try:
            parsed_status = status if isinstance(status, OrderStatus) else OrderStatus(status)
        except ValueError as exc:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Статус заказа должен быть допустимым.", "status", str(status), "Выберите допустимый статус заказа.")) from exc
        return cls(client_id, recipe_version_id, client_recipe_id, normalize_required_text(product_name, field="product_name", label="Название продукта"), positive_amount(target_batch_size_value, unit, field="target_batch_size_value"), unit, pkg_id, pkg_qty, parsed_status, parsed_price, _date_text(ordered_at), _date_text(planned_production_at), _date_text(produced_at), _date_text(delivered_at), normalize_optional_text(notes))


def _date_text(value: str | None) -> str | None:
    normalized = normalize_optional_text(value)
    return normalized or None
