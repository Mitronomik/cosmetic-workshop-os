from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.decimal_utils import quantize_count
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.packaging_items import normalize_optional_text, parse_packaging_unit
from app.domain.units import UnitCode


class PackagingMovementDirection(StrEnum):
    IN = "in"
    OUT = "out"


class PackagingStockMovementType(StrEnum):
    RECEIPT = "receipt"
    MANUAL_ADJUSTMENT_IN = "manual_adjustment_in"
    MANUAL_ADJUSTMENT_OUT = "manual_adjustment_out"
    WRITE_OFF = "write_off"
    RETURN_TO_SUPPLIER = "return_to_supplier"


PACKAGING_MOVEMENT_TYPE_DIRECTIONS = {
    PackagingStockMovementType.RECEIPT: PackagingMovementDirection.IN,
    PackagingStockMovementType.MANUAL_ADJUSTMENT_IN: PackagingMovementDirection.IN,
    PackagingStockMovementType.MANUAL_ADJUSTMENT_OUT: PackagingMovementDirection.OUT,
    PackagingStockMovementType.WRITE_OFF: PackagingMovementDirection.OUT,
    PackagingStockMovementType.RETURN_TO_SUPPLIER: PackagingMovementDirection.OUT,
}


def parse_positive_packaging_item_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Нужно выбрать существующую тару или упаковку.",
                field="packaging_item_id",
                value=str(value),
                next_action="Выберите активную тару или упаковку из справочника тары.",
            )
        )
    return value


def parse_packaging_movement_type(value: PackagingStockMovementType | str) -> PackagingStockMovementType:
    try:
        return value if isinstance(value, PackagingStockMovementType) else PackagingStockMovementType(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Тип движения тары должен быть одним из допустимых типов MVP.", "movement_type", str(value), "Выберите поступление, ручную корректировку, списание или возврат поставщику.")
        ) from exc


def parse_packaging_stock_quantity(value: Decimal | int | str, *, unit: UnitCode) -> Decimal:
    if unit != UnitCode.PIECE:
        raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Движения тары учитываются только в штуках.", "unit", str(unit), "Используйте единицу “шт”; проценты, мл и граммы не подходят для тары."))
    quantity = quantize_count(value, field="quantity")
    if quantity == 0:
        raise DomainValidationError(DomainIssue(DomainIssueCode.ZERO_QUANTITY, "Количество движения тары должно быть больше нуля.", "quantity", str(quantity), "Укажите положительное целое количество."))
    if quantity < 0:
        raise DomainValidationError(DomainIssue(DomainIssueCode.NEGATIVE_QUANTITY, "Количество движения тары не может быть отрицательным.", "quantity", str(quantity), "Укажите положительное целое количество."))
    return quantity


@dataclass(frozen=True)
class PackagingStockMovementDraft:
    packaging_item_id: int
    movement_type: PackagingStockMovementType
    quantity: Decimal
    unit: UnitCode
    direction: PackagingMovementDirection
    occurred_at: str | None = None
    reason: str = ""
    source: str = "manual"
    notes: str = ""

    @classmethod
    def create(cls, *, packaging_item_id: int, movement_type: PackagingStockMovementType | str, quantity: Decimal | int | str, unit: UnitCode | str, occurred_at: str | None = None, reason: str | None = "", source: str | None = "manual", notes: str | None = "") -> "PackagingStockMovementDraft":
        item_id = parse_positive_packaging_item_id(packaging_item_id)
        parsed_type = parse_packaging_movement_type(movement_type)
        normalized_reason = normalize_optional_text(reason or "")
        if parsed_type in {PackagingStockMovementType.MANUAL_ADJUSTMENT_IN, PackagingStockMovementType.MANUAL_ADJUSTMENT_OUT} and not normalized_reason:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Укажите причину ручной корректировки склада.", "reason", None, "Коротко опишите, почему вы меняете остаток тары вручную."))
        parsed_unit = parse_packaging_unit(unit)
        return cls(
            packaging_item_id=item_id,
            movement_type=parsed_type,
            quantity=parse_packaging_stock_quantity(quantity, unit=parsed_unit),
            unit=parsed_unit,
            direction=PACKAGING_MOVEMENT_TYPE_DIRECTIONS[parsed_type],
            occurred_at=occurred_at,
            reason=normalized_reason,
            source=normalize_optional_text(source or "") or "manual",
            notes=(notes or "").strip(),
        )

    @property
    def signed_delta(self) -> Decimal:
        return self.quantity if self.direction == PackagingMovementDirection.IN else -self.quantity
