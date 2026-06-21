from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.measurements import Density
from app.domain.units import UnitCode


class IngredientCategory(StrEnum):
    OIL = "oil"
    BUTTER = "butter"
    WAX = "wax"
    EMULSIFIER = "emulsifier"
    HUMECTANT = "humectant"
    ACTIVE = "active"
    PRESERVATIVE = "preservative"
    FRAGRANCE = "fragrance"
    ESSENTIAL_OIL = "essential_oil"
    COLORANT = "colorant"
    WATER_PHASE = "water_phase"
    ADDITIVE = "additive"
    OTHER = "other"


INGREDIENT_CATEGORY_RUSSIAN_LABELS: dict[IngredientCategory, str] = {
    IngredientCategory.OIL: "Масло",
    IngredientCategory.BUTTER: "Баттер",
    IngredientCategory.WAX: "Воск",
    IngredientCategory.EMULSIFIER: "Эмульгатор",
    IngredientCategory.HUMECTANT: "Увлажнитель",
    IngredientCategory.ACTIVE: "Актив",
    IngredientCategory.PRESERVATIVE: "Консервант",
    IngredientCategory.FRAGRANCE: "Отдушка",
    IngredientCategory.ESSENTIAL_OIL: "Эфирное масло",
    IngredientCategory.COLORANT: "Краситель",
    IngredientCategory.WATER_PHASE: "Водная фаза",
    IngredientCategory.ADDITIVE: "Добавка",
    IngredientCategory.OTHER: "Другое",
}

ALLOWED_INGREDIENT_UNITS = {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PERCENT, UnitCode.PIECE}


def normalize_ingredient_name(name: str) -> str:
    normalized = " ".join(name.strip().split()) if isinstance(name, str) else ""
    if not normalized:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Название компонента обязательно.",
                field="name",
                value=str(name),
                next_action="Введите понятное название компонента, например “Масло ши”.",
            )
        )
    return normalized


def parse_ingredient_category(value: IngredientCategory | str) -> IngredientCategory:
    try:
        return value if isinstance(value, IngredientCategory) else IngredientCategory(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_CATEGORY,
                message="Категория компонента должна быть выбрана из списка MVP.",
                field="category",
                value=str(value),
                next_action="Выберите одну из допустимых категорий компонента.",
            )
        ) from exc


def parse_ingredient_unit(value: UnitCode | str) -> UnitCode:
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Единица компонента должна быть одной из допустимых MVP единиц.",
                field="default_unit",
                value=str(value),
                next_action="Выберите граммы, миллилитры, проценты или штуки.",
            )
        ) from exc
    if unit not in ALLOWED_INGREDIENT_UNITS:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_UNIT,
                message="Единица компонента не разрешена для справочника компонентов.",
                field="default_unit",
                value=str(unit),
                next_action="Выберите граммы или миллилитры, если это обычный компонент.",
            )
        )
    return unit


@dataclass(frozen=True)
class IngredientDraft:
    name: str
    category: IngredientCategory
    default_unit: UnitCode
    density: Density | None = None
    notes: str = ""
    inci_name: str = ""
    supplier_hint: str = ""
    allergen_note: str = ""
    usage_note: str = ""

    @classmethod
    def create(
        cls,
        *,
        name: str,
        category: IngredientCategory | str,
        default_unit: UnitCode | str,
        density_g_per_ml: Density | str | int | None = None,
        notes: str = "",
        inci_name: str = "",
        supplier_hint: str = "",
        allergen_note: str = "",
        usage_note: str = "",
    ) -> "IngredientDraft":
        density = density_g_per_ml if isinstance(density_g_per_ml, Density) else None
        if density_g_per_ml is not None and density is None:
            density = Density.from_value(density_g_per_ml)
        return cls(
            name=normalize_ingredient_name(name),
            category=parse_ingredient_category(category),
            default_unit=parse_ingredient_unit(default_unit),
            density=density,
            notes=notes.strip(),
            inci_name=inci_name.strip(),
            supplier_hint=supplier_hint.strip(),
            allergen_note=allergen_note.strip(),
            usage_note=usage_note.strip(),
        )
