from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.decimal_utils import quantize_money
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.measurements import Density
from app.domain.units import UnitCode

ALLOWED_INGREDIENT_LOT_UNITS = {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PIECE}


def normalize_optional_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().split())


def parse_ingredient_lot_unit(value: UnitCode | str) -> UnitCode:
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Единица партии компонента должна быть одной из допустимых единиц MVP.",
                field="unit",
                value=str(value),
                next_action="Выберите граммы, миллилитры или штуки.",
            )
        ) from exc
    if unit not in ALLOWED_INGREDIENT_LOT_UNITS:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Проценты нельзя использовать как единицу хранения партии компонента.",
                field="unit",
                value=str(unit),
                next_action="Для партии выберите фактическую единицу: граммы, миллилитры или штуки.",
            )
        )
    return unit


def parse_positive_ingredient_id(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Для партии нужно выбрать существующий компонент.",
                field="ingredient_id",
                value=str(value),
                next_action="Выберите активный компонент из справочника.",
            )
        )
    return value


def parse_optional_money(value: Decimal | int | str | None, *, field: str) -> Decimal | None:
    if value is None:
        return None
    try:
        amount = quantize_money(value, field=field)
        if amount < 0:
            raise DomainValidationError(
                DomainIssue(
                    code=DomainIssueCode.NEGATIVE_QUANTITY,
                    message=f"Поле “{field}” не может быть отрицательным.",
                    field=field,
                    value=str(amount),
                    next_action="Укажите ноль или положительную стоимость.",
                )
            )
        return amount
    except DomainValidationError as exc:
        if exc.issue.code == DomainIssueCode.NEGATIVE_QUANTITY:
            raise DomainValidationError(
                DomainIssue(
                    code=DomainIssueCode.NEGATIVE_QUANTITY,
                    message=f"Поле “{field}” не может быть отрицательным.",
                    field=field,
                    value=exc.issue.value,
                    next_action="Укажите ноль или положительную стоимость.",
                )
            ) from exc
        raise


def validate_lot_dates(purchased_at: date | None, expires_at: date | None) -> None:
    if purchased_at is not None and expires_at is not None and expires_at < purchased_at:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Дата годности партии не может быть раньше даты покупки.",
                field="expires_at",
                value=expires_at.isoformat(),
                next_action="Проверьте даты покупки и срока годности партии.",
            )
        )


@dataclass(frozen=True)
class IngredientLotDraft:
    ingredient_id: int
    unit: UnitCode
    lot_code: str = ""
    supplier_name: str = ""
    purchased_at: date | None = None
    expires_at: date | None = None
    unit_cost: Decimal | None = None
    total_cost: Decimal | None = None
    density: Density | None = None
    notes: str = ""

    @classmethod
    def create(
        cls,
        *,
        ingredient_id: int,
        unit: UnitCode | str,
        lot_code: str | None = "",
        supplier_name: str | None = "",
        purchased_at: date | None = None,
        expires_at: date | None = None,
        unit_cost: Decimal | int | str | None = None,
        total_cost: Decimal | int | str | None = None,
        density_g_per_ml: Density | Decimal | int | str | None = None,
        notes: str | None = "",
    ) -> "IngredientLotDraft":
        density = density_g_per_ml if isinstance(density_g_per_ml, Density) else None
        if density_g_per_ml is not None and density is None:
            density = Density.from_value(density_g_per_ml)
        validate_lot_dates(purchased_at, expires_at)
        return cls(
            ingredient_id=parse_positive_ingredient_id(ingredient_id),
            unit=parse_ingredient_lot_unit(unit),
            lot_code=normalize_optional_text(lot_code),
            supplier_name=normalize_optional_text(supplier_name),
            purchased_at=purchased_at,
            expires_at=expires_at,
            unit_cost=parse_optional_money(unit_cost, field="unit_cost"),
            total_cost=parse_optional_money(total_cost, field="total_cost"),
            density=density,
            notes=(notes or "").strip(),
        )
