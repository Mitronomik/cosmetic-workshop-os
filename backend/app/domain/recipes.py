from dataclasses import dataclass
from decimal import Decimal

from app.domain.decimal_utils import parse_decimal, quantize_count, quantize_percentage, quantize_volume, quantize_weight
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.units import UnitCode
from app.models.recipe import RecipeVersionStatus

ALLOWED_RECIPE_AMOUNT_UNITS = {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PERCENT, UnitCode.PIECE}
ALLOWED_BATCH_SIZE_UNITS = {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PIECE}


def normalize_required_text(value: str, *, field: str, label: str) -> str:
    normalized = " ".join(value.strip().split()) if isinstance(value, str) else ""
    if not normalized:
        raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, f"{label} обязательно.", field, str(value), f"Заполните поле “{label}”."))
    return normalized


def normalize_optional_text(value: str | None) -> str:
    return " ".join(value.strip().split()) if isinstance(value, str) else ""


def require_positive_id(value: int | None, *, field: str, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, f"{label} должен быть выбран.", field, str(value), f"Выберите существующий {label.lower()}."))
    return value


def parse_unit(value: UnitCode | str, *, field: str, allowed: set[UnitCode]) -> UnitCode:
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except ValueError as exc:
        raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Единица измерения не входит в список допустимых.", field, str(value), "Выберите допустимую единицу измерения.")) from exc
    if unit not in allowed:
        raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Эта единица измерения не разрешена для данного поля.", field, unit.value, "Выберите допустимую единицу измерения."))
    return unit


def positive_amount(value: Decimal | int | str, unit: UnitCode, *, field: str) -> Decimal:
    if unit == UnitCode.GRAM:
        parsed = quantize_weight(value, field=field)
    elif unit == UnitCode.MILLILITER:
        parsed = quantize_volume(value, field=field)
    elif unit == UnitCode.PERCENT:
        parsed = quantize_percentage(value, field=field)
    elif unit == UnitCode.PIECE:
        parsed = quantize_count(value, field=field)
    else:
        parsed = parse_decimal(value, field=field)
    if parsed <= 0:
        raise DomainValidationError(DomainIssue(DomainIssueCode.ZERO_QUANTITY, f"Поле “{field}” должно быть больше нуля.", field, str(parsed), "Укажите положительное количество."))
    return parsed


@dataclass(frozen=True)
class RecipeTemplateDraft:
    name: str
    product_type: str = ""
    description: str = ""
    notes: str = ""

    @classmethod
    def create(cls, *, name: str, product_type: str = "", description: str = "", notes: str = "") -> "RecipeTemplateDraft":
        return cls(normalize_required_text(name, field="name", label="Название рецепта"), normalize_optional_text(product_type), normalize_optional_text(description), normalize_optional_text(notes))


@dataclass(frozen=True)
class RecipeIngredientDraft:
    ingredient_id: int
    position: int
    amount_value: Decimal
    amount_unit: UnitCode
    phase: str = ""
    notes: str = ""

    @classmethod
    def create(cls, *, ingredient_id: int | None, position: int, amount_value: Decimal | int | str, amount_unit: UnitCode | str, phase: str = "", notes: str = "") -> "RecipeIngredientDraft":
        ingredient_id = require_positive_id(ingredient_id, field="ingredient_id", label="Компонент")
        if not isinstance(position, int) or isinstance(position, bool) or position <= 0:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Позиция строки рецепта должна быть положительным целым числом.", "position", str(position), "Укажите порядок строки: 1, 2, 3…"))
        unit = parse_unit(amount_unit, field="amount_unit", allowed=ALLOWED_RECIPE_AMOUNT_UNITS)
        return cls(ingredient_id, position, positive_amount(amount_value, unit, field="amount_value"), unit, normalize_optional_text(phase), normalize_optional_text(notes))


@dataclass(frozen=True)
class RecipeVersionDraft:
    status: RecipeVersionStatus = RecipeVersionStatus.DRAFT
    title: str = ""
    target_batch_size_value: Decimal | None = None
    target_batch_size_unit: UnitCode | None = None
    notes: str = ""
    change_note: str = ""
    created_from_version_id: int | None = None
    ingredients: tuple[RecipeIngredientDraft, ...] = ()

    @classmethod
    def create(cls, *, status: RecipeVersionStatus | str = RecipeVersionStatus.DRAFT, title: str = "", target_batch_size_value: Decimal | int | str | None = None, target_batch_size_unit: UnitCode | str | None = None, notes: str = "", change_note: str = "", created_from_version_id: int | None = None, ingredients=()) -> "RecipeVersionDraft":
        try:
            parsed_status = status if isinstance(status, RecipeVersionStatus) else RecipeVersionStatus(status)
        except ValueError as exc:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Статус версии рецепта должен быть draft, active или archived.", "status", str(status), "Выберите допустимый статус версии.")) from exc
        batch_value = None
        batch_unit = None
        if target_batch_size_value is not None or target_batch_size_unit is not None:
            if target_batch_size_unit is None:
                raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Для размера партии нужна единица измерения.", "target_batch_size_unit", None, "Выберите г, мл или шт."))
            batch_unit = parse_unit(target_batch_size_unit, field="target_batch_size_unit", allowed=ALLOWED_BATCH_SIZE_UNITS)
            if target_batch_size_value is None:
                raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Размер партии должен быть указан числом.", "target_batch_size_value", None, "Укажите положительный размер партии."))
            batch_value = positive_amount(target_batch_size_value, batch_unit, field="target_batch_size_value")
        if created_from_version_id is not None:
            created_from_version_id = require_positive_id(created_from_version_id, field="created_from_version_id", label="Исходная версия")
        return cls(parsed_status, normalize_optional_text(title), batch_value, batch_unit, normalize_optional_text(notes), normalize_optional_text(change_note), created_from_version_id, tuple(ingredients))
