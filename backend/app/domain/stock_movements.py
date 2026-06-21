from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.decimal_utils import quantize_count, quantize_volume, quantize_weight
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.ingredient_lots import (
    ALLOWED_INGREDIENT_LOT_UNITS,
    normalize_optional_text,
    parse_ingredient_lot_unit,
    parse_positive_ingredient_id,
)
from app.domain.units import UnitCode


class MovementDirection(StrEnum):
    IN = "in"
    OUT = "out"


class StockMovementType(StrEnum):
    RECEIPT = "receipt"
    MANUAL_ADJUSTMENT_IN = "manual_adjustment_in"
    MANUAL_ADJUSTMENT_OUT = "manual_adjustment_out"
    WRITE_OFF = "write_off"
    RETURN_TO_SUPPLIER = "return_to_supplier"


MOVEMENT_TYPE_DIRECTIONS = {
    StockMovementType.RECEIPT: MovementDirection.IN,
    StockMovementType.MANUAL_ADJUSTMENT_IN: MovementDirection.IN,
    StockMovementType.MANUAL_ADJUSTMENT_OUT: MovementDirection.OUT,
    StockMovementType.WRITE_OFF: MovementDirection.OUT,
    StockMovementType.RETURN_TO_SUPPLIER: MovementDirection.OUT,
}


def parse_movement_type(value: StockMovementType | str) -> StockMovementType:
    try:
        return value if isinstance(value, StockMovementType) else StockMovementType(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Тип движения склада должен быть одним из допустимых типов MVP.",
                field="movement_type",
                value=str(value),
                next_action="Выберите поступление, ручную корректировку, списание или возврат поставщику.",
            )
        ) from exc


def parse_direction(value: MovementDirection | str) -> MovementDirection:
    try:
        return value if isinstance(value, MovementDirection) else MovementDirection(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Направление движения должно быть “in” или “out”.",
                field="direction",
                value=str(value),
                next_action="Используйте направление, соответствующее типу движения.",
            )
        ) from exc


def parse_stock_quantity(value: Decimal | int | str, *, unit: UnitCode) -> Decimal:
    if unit == UnitCode.GRAM:
        quantity = quantize_weight(value, field="quantity")
    elif unit == UnitCode.MILLILITER:
        quantity = quantize_volume(value, field="quantity")
    elif unit == UnitCode.PIECE:
        quantity = quantize_count(value, field="quantity")
    else:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Единица складского движения должна быть граммы, миллилитры или штуки.",
                field="unit",
                value=str(unit),
                next_action="Выберите фактическую складскую единицу, не проценты.",
            )
        )
    if quantity == 0:
        raise DomainValidationError(
            DomainIssue(
                DomainIssueCode.ZERO_QUANTITY,
                "Количество движения должно быть больше нуля.",
                "quantity",
                str(quantity),
                "Укажите положительное количество.",
            )
        )
    if quantity < 0:
        raise DomainValidationError(
            DomainIssue(
                DomainIssueCode.NEGATIVE_QUANTITY,
                "Количество движения не может быть отрицательным.",
                "quantity",
                str(quantity),
                "Укажите положительное количество.",
            )
        )
    return quantity


@dataclass(frozen=True)
class StockMovementDraft:
    ingredient_lot_id: int
    movement_type: StockMovementType
    quantity: Decimal
    unit: UnitCode
    direction: MovementDirection
    reason: str = ""
    occurred_at: str | None = None
    note: str = ""
    reference_type: str | None = None
    reference_id: str | None = None
    source: str = "manual"
    correction_of_movement_id: int | None = None

    @classmethod
    def create(
        cls,
        *,
        ingredient_lot_id: int,
        movement_type: StockMovementType | str,
        quantity: Decimal | int | str,
        unit: UnitCode | str,
        direction: MovementDirection | str | None = None,
        reason: str | None = "",
        occurred_at: str | None = None,
        note: str | None = "",
        reference_type: str | None = None,
        reference_id: str | None = None,
        source: str | None = "manual",
        correction_of_movement_id: int | None = None,
    ) -> "StockMovementDraft":
        lot_id = parse_positive_ingredient_id(ingredient_lot_id)
        parsed_type = parse_movement_type(movement_type)
        parsed_direction = MOVEMENT_TYPE_DIRECTIONS[parsed_type] if direction is None else parse_direction(direction)
        expected_direction = MOVEMENT_TYPE_DIRECTIONS[parsed_type]
        if parsed_direction != expected_direction:
            raise DomainValidationError(
                DomainIssue(
                    DomainIssueCode.REQUIRED_FIELD,
                    "Направление движения не соответствует типу движения.",
                    "direction",
                    str(parsed_direction),
                    f"Для типа {parsed_type.value} используйте направление {expected_direction.value}.",
                )
            )
        parsed_unit = parse_ingredient_lot_unit(unit)
        if parsed_unit not in ALLOWED_INGREDIENT_LOT_UNITS:
            raise DomainValidationError(
                DomainIssue(
                    DomainIssueCode.INVALID_UNIT,
                    "Единица складского движения недопустима.",
                    "unit",
                    str(parsed_unit),
                    "Выберите граммы, миллилитры или штуки.",
                )
            )
        return cls(
            ingredient_lot_id=lot_id,
            movement_type=parsed_type,
            quantity=parse_stock_quantity(quantity, unit=parsed_unit),
            unit=parsed_unit,
            direction=parsed_direction,
            reason=normalize_optional_text(reason),
            occurred_at=occurred_at,
            note=(note or "").strip(),
            reference_type=normalize_optional_text(reference_type) or None,
            reference_id=normalize_optional_text(reference_id) or None,
            source=normalize_optional_text(source) or "manual",
            correction_of_movement_id=correction_of_movement_id,
        )

    @property
    def signed_delta(self) -> Decimal:
        return self.quantity if self.direction == MovementDirection.IN else -self.quantity
