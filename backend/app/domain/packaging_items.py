from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.decimal_utils import quantize_money, quantize_volume, quantize_weight
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.units import UnitCode


class PackagingKind(StrEnum):
    JAR = "jar"
    BOTTLE = "bottle"
    TUBE = "tube"
    PUMP = "pump"
    CAP = "cap"
    DROPPER = "dropper"
    LABEL = "label"
    BOX = "box"
    BAG = "bag"
    OTHER = "other"


PACKAGING_KIND_RUSSIAN_LABELS: dict[PackagingKind, str] = {
    PackagingKind.JAR: "Баночка",
    PackagingKind.BOTTLE: "Флакон",
    PackagingKind.TUBE: "Туба",
    PackagingKind.PUMP: "Помпа",
    PackagingKind.CAP: "Крышка",
    PackagingKind.DROPPER: "Пипетка",
    PackagingKind.LABEL: "Этикетка",
    PackagingKind.BOX: "Коробка",
    PackagingKind.BAG: "Пакет",
    PackagingKind.OTHER: "Другое",
}

ALLOWED_CAPACITY_UNITS = {UnitCode.MILLILITER, UnitCode.GRAM}


def normalize_packaging_name(name: str) -> str:
    normalized = " ".join(name.strip().split()) if isinstance(name, str) else ""
    if not normalized:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Название тары обязательно.",
                field="name",
                value=str(name),
                next_action="Введите понятное название тары, например “Баночка 30 мл”.",
            )
        )
    return normalized


def normalize_optional_text(value: str) -> str:
    return " ".join(value.strip().split()) if isinstance(value, str) else ""


def parse_packaging_kind(value: PackagingKind | str) -> PackagingKind:
    try:
        return value if isinstance(value, PackagingKind) else PackagingKind(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_CATEGORY,
                message="Вид тары должен быть выбран из списка MVP.",
                field="kind",
                value=str(value),
                next_action="Выберите баночку, флакон, тубу, помпу, крышку, пипетку, этикетку, коробку, пакет или другое.",
            )
        ) from exc


def parse_packaging_unit(value: UnitCode | str) -> UnitCode:
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Единица тары должна быть штуками.",
                field="unit",
                value=str(value),
                next_action="Используйте единицу “шт”.",
            )
        ) from exc
    if unit != UnitCode.PIECE:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Тара учитывается только в штуках.",
                field="unit",
                value=str(unit),
                next_action="Используйте единицу “шт”, проценты и произвольные единицы не подходят для тары.",
            )
        )
    return unit


def parse_capacity_unit(value: UnitCode | str | None) -> UnitCode | None:
    if value is None:
        return None
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except ValueError as exc:
        raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Единица объема/веса тары должна быть мл или г.", "capacity_unit", str(value), "Выберите мл или г.")) from exc
    if unit not in ALLOWED_CAPACITY_UNITS:
        raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Единица вместимости тары должна быть мл или г.", "capacity_unit", str(unit), "Выберите мл или г; проценты не подходят."))
    return unit


def parse_capacity(value: Decimal | int | str | None, unit: UnitCode | str | None) -> tuple[Decimal | None, UnitCode | None]:
    capacity_unit = parse_capacity_unit(unit)
    if value is None:
        if capacity_unit is not None:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Для единицы вместимости укажите значение.", "capacity_value", None, "Укажите положительное число или оставьте вместимость пустой."))
        return None, None
    if capacity_unit is None:
        raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Для вместимости тары нужна единица измерения.", "capacity_unit", None, "Выберите мл или г."))
    capacity = quantize_volume(value, field="capacity_value") if capacity_unit == UnitCode.MILLILITER else quantize_weight(value, field="capacity_value")
    if capacity <= 0:
        raise DomainValidationError(DomainIssue(DomainIssueCode.ZERO_QUANTITY, "Вместимость тары должна быть положительной.", "capacity_value", str(capacity), "Укажите число больше нуля."))
    return capacity, capacity_unit


def parse_unit_cost(value: Decimal | int | str | None) -> Decimal | None:
    if value is None:
        return None
    cost = quantize_money(value, field="unit_cost")
    if cost < 0:
        raise DomainValidationError(DomainIssue(DomainIssueCode.NEGATIVE_QUANTITY, "Стоимость единицы тары не может быть отрицательной.", "unit_cost", str(cost), "Укажите ноль или положительную стоимость."))
    return cost


@dataclass(frozen=True)
class PackagingItemDraft:
    name: str
    kind: PackagingKind
    unit: UnitCode = UnitCode.PIECE
    capacity_value: Decimal | None = None
    capacity_unit: UnitCode | None = None
    material: str = ""
    supplier_hint: str = ""
    unit_cost: Decimal | None = None
    notes: str = ""

    @classmethod
    def create(cls, *, name: str, kind: PackagingKind | str, unit: UnitCode | str = UnitCode.PIECE, capacity_value: Decimal | int | str | None = None, capacity_unit: UnitCode | str | None = None, material: str = "", supplier_hint: str = "", unit_cost: Decimal | int | str | None = None, notes: str = "") -> "PackagingItemDraft":
        parsed_capacity, parsed_capacity_unit = parse_capacity(capacity_value, capacity_unit)
        return cls(
            name=normalize_packaging_name(name),
            kind=parse_packaging_kind(kind),
            unit=parse_packaging_unit(unit),
            capacity_value=parsed_capacity,
            capacity_unit=parsed_capacity_unit,
            material=normalize_optional_text(material),
            supplier_hint=normalize_optional_text(supplier_hint),
            unit_cost=parse_unit_cost(unit_cost),
            notes=notes.strip() if isinstance(notes, str) else "",
        )
