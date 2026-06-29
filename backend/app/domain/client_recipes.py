from dataclasses import dataclass
from decimal import Decimal

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import ALLOWED_BATCH_SIZE_UNITS, ALLOWED_RECIPE_AMOUNT_UNITS, normalize_optional_text, normalize_required_text, parse_unit, positive_amount, require_positive_id
from app.domain.units import UnitCode
from app.models.client_recipe import ClientRecipeStatus


@dataclass(frozen=True)
class ClientRecipeDraft:
    client_id: int
    source_recipe_version_id: int
    title: str
    status: ClientRecipeStatus = ClientRecipeStatus.DRAFT
    target_batch_size_value: Decimal | None = None
    target_batch_size_unit: UnitCode | None = None
    personalization_notes: str = ""
    allergy_notes: str = ""
    preference_notes: str = ""
    contraindication_notes: str = ""
    notes: str = ""

    @classmethod
    def create(cls, *, client_id: int | None, source_recipe_version_id: int | None, title: str, status: ClientRecipeStatus | str = ClientRecipeStatus.DRAFT, target_batch_size_value: Decimal | int | str | None = None, target_batch_size_unit: UnitCode | str | None = None, personalization_notes: str | None = "", allergy_notes: str | None = "", preference_notes: str | None = "", contraindication_notes: str | None = "", notes: str | None = "") -> "ClientRecipeDraft":
        try:
            parsed_status = status if isinstance(status, ClientRecipeStatus) else ClientRecipeStatus(status)
        except ValueError as exc:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Статус индивидуального рецепта должен быть draft, active или archived.", "status", str(status), "Выберите допустимый статус.")) from exc
        batch_value = None
        batch_unit = None
        if target_batch_size_value is not None or target_batch_size_unit is not None:
            if target_batch_size_unit is None:
                raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_UNIT, "Для размера партии нужна единица измерения.", "target_batch_size_unit", None, "Выберите г, мл или шт."))
            batch_unit = parse_unit(target_batch_size_unit, field="target_batch_size_unit", allowed=ALLOWED_BATCH_SIZE_UNITS)
            if target_batch_size_value is None:
                raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Размер партии должен быть указан числом.", "target_batch_size_value", None, "Укажите положительный размер партии."))
            batch_value = positive_amount(target_batch_size_value, batch_unit, field="target_batch_size_value")
        return cls(
            client_id=require_positive_id(client_id, field="client_id", label="Клиент"),
            source_recipe_version_id=require_positive_id(source_recipe_version_id, field="source_recipe_version_id", label="Версия рецепта"),
            title=normalize_required_text(title, field="title", label="Название индивидуального рецепта"),
            status=parsed_status,
            target_batch_size_value=batch_value,
            target_batch_size_unit=batch_unit,
            personalization_notes=normalize_optional_text(personalization_notes),
            allergy_notes=normalize_optional_text(allergy_notes),
            preference_notes=normalize_optional_text(preference_notes),
            contraindication_notes=normalize_optional_text(contraindication_notes),
            notes=normalize_optional_text(notes),
        )


@dataclass(frozen=True)
class ClientRecipeIngredientDraft:
    ingredient_id: int
    source_recipe_ingredient_id: int | None
    position: int
    phase: str
    amount_value: Decimal
    amount_unit: UnitCode
    personalization_note: str = ""
    notes: str = ""

    @classmethod
    def create(cls, *, ingredient_id: int | None, source_recipe_ingredient_id: int | None = None, position: int, phase: str = "", amount_value: Decimal | int | str = "", amount_unit: UnitCode | str = UnitCode.GRAM, personalization_note: str | None = "", notes: str | None = "") -> "ClientRecipeIngredientDraft":
        if source_recipe_ingredient_id is not None:
            source_recipe_ingredient_id = require_positive_id(source_recipe_ingredient_id, field="source_recipe_ingredient_id", label="Исходная строка рецепта")
        if not isinstance(position, int) or isinstance(position, bool) or position <= 0:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Позиция строки индивидуального рецепта должна быть положительным целым числом.", "position", str(position), "Укажите порядок строки: 1, 2, 3…"))
        unit = parse_unit(amount_unit, field="amount_unit", allowed=ALLOWED_RECIPE_AMOUNT_UNITS)
        return cls(require_positive_id(ingredient_id, field="ingredient_id", label="Компонент"), source_recipe_ingredient_id, position, normalize_optional_text(phase), positive_amount(amount_value, unit, field="amount_value"), unit, normalize_optional_text(personalization_note), normalize_optional_text(notes))


@dataclass(frozen=True)
class ClientRecipeIngredientUpdateDraft:
    id: int | None
    ingredient_id: int
    position: int
    phase: str
    amount_value: Decimal
    amount_unit: UnitCode
    personalization_note: str = ""
    notes: str = ""

    @classmethod
    def create(cls, *, id: int | None = None, ingredient_id: int | None, position: int, phase: str = "", amount_value: Decimal | int | str = "", amount_unit: UnitCode | str = UnitCode.GRAM, personalization_note: str | None = "", notes: str | None = "") -> "ClientRecipeIngredientUpdateDraft":
        if id is not None:
            id = require_positive_id(id, field="id", label="Строка индивидуального рецепта")
        if not isinstance(position, int) or isinstance(position, bool) or position <= 0:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Позиция строки индивидуального рецепта должна быть положительным целым числом.", "position", str(position), "Укажите порядок строки: 1, 2, 3…"))
        unit = parse_unit(amount_unit, field="amount_unit", allowed=ALLOWED_RECIPE_AMOUNT_UNITS)
        return cls(id, require_positive_id(ingredient_id, field="ingredient_id", label="Компонент"), position, normalize_optional_text(phase), positive_amount(amount_value, unit, field="amount_value"), unit, normalize_optional_text(personalization_note), normalize_optional_text(notes))


def validate_client_recipe_update_lines(lines: list[ClientRecipeIngredientUpdateDraft]) -> None:
    if not lines:
        raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "В индивидуальном рецепте должна быть хотя бы одна строка состава.", "ingredients", "[]", "Добавьте минимум один компонент."))
    seen_positions: set[int] = set()
    seen_ids: set[int] = set()
    for line in lines:
        if line.id is not None:
            if line.id in seen_ids:
                raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Одна и та же строка индивидуального рецепта не должна повторяться в составе.", "id", str(line.id), "Оставьте каждую существующую строку в списке только один раз."))
            seen_ids.add(line.id)
        if line.position in seen_positions:
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Позиции строк индивидуального рецепта не должны повторяться.", "position", str(line.position), "Назначьте каждой строке уникальный порядок."))
        seen_positions.add(line.position)
