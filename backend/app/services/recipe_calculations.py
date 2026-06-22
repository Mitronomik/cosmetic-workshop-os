from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.decimal_utils import quantize_percentage, quantize_volume, quantize_weight
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import parse_unit, positive_amount
from app.domain.units import UnitCode
from app.models.recipe import (
    RecipeCalculationIssue,
    RecipeCalculationLine,
    RecipeCalculationResult,
    RecipeCalculationTotal,
)
from app.repositories.recipes import RecipeRepository, RecipeVersionNotFoundError

CALCULATION_TARGET_UNITS = {UnitCode.GRAM, UnitCode.MILLILITER}


class RecipeCalculationService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.repository = RecipeRepository(config)

    def calculate_version(
        self,
        version_id: int,
        *,
        target_batch_size_value: Decimal | int | str | None = None,
        target_batch_size_unit: UnitCode | str | None = None,
    ) -> RecipeCalculationResult:
        version_row, line_rows = self.repository.get_version_calculation_source(version_id)
        target_value, target_unit = self._target_from_input_or_version(
            explicit_value=target_batch_size_value,
            explicit_unit=target_batch_size_unit,
            stored_value=version_row["target_batch_size_value"],
            stored_unit=version_row["target_batch_size_unit"],
        )

        issues: list[RecipeCalculationIssue] = []
        percent_total = sum((Decimal(row["amount_value"]) for row in line_rows if row["amount_unit"] == UnitCode.PERCENT.value), Decimal("0"))
        percent_total = quantize_percentage(percent_total, field="percent_total")
        has_percent_lines = any(row["amount_unit"] == UnitCode.PERCENT.value for row in line_rows)

        if has_percent_lines and target_value is None:
            issues.append(_issue("error", "missing_target_batch_size", "target_batch_size_value", "Для строк в процентах нужен размер партии.", "Укажите размер партии в граммах или миллилитрах."))
        if has_percent_lines:
            if percent_total < Decimal("100.00"):
                issues.append(_issue("warning", "percent_total_below_100", "percent_total", f"Сумма процентных строк меньше 100%: {percent_total}%.", "Проверьте рецепт или оставьте как есть, если это намеренно."))
            elif percent_total > Decimal("100.00"):
                issues.append(_issue("error", "percent_total_above_100", "percent_total", f"Сумма процентных строк больше 100%: {percent_total}%.", "Исправьте проценты в версии рецепта."))

        lines: list[RecipeCalculationLine] = []
        totals: dict[UnitCode, Decimal] = {}
        for row in line_rows:
            source_unit = UnitCode(row["amount_unit"])
            source_value = Decimal(row["amount_value"])
            calculated_value: Decimal | None = source_value
            calculated_unit: UnitCode | None = source_unit
            note = "Фиксированное количество оставлено без масштабирования."
            if source_unit == UnitCode.PERCENT:
                if target_value is None or target_unit is None:
                    calculated_value = None
                    calculated_unit = None
                    note = "Нельзя рассчитать процентную строку без размера партии."
                else:
                    calculated_unit = target_unit
                    raw = target_value * source_value / Decimal("100")
                    calculated_value = quantize_weight(raw, field="calculated_amount_value") if target_unit == UnitCode.GRAM else quantize_volume(raw, field="calculated_amount_value")
                    note = f"{source_value}% от партии {target_value} {target_unit.value}."
            if calculated_value is not None and calculated_unit is not None:
                totals[calculated_unit] = totals.get(calculated_unit, Decimal("0")) + calculated_value
            lines.append(RecipeCalculationLine(row["id"], row["position"], row["phase"], row["ingredient_id"], row["ingredient_name"], source_value, source_unit, calculated_value, calculated_unit, note))

        totals_by_unit = [RecipeCalculationTotal(unit, _quantize_total(value, unit)) for unit, value in sorted(totals.items(), key=lambda item: item[0].value)]
        can_calculate = not any(issue.severity == "error" for issue in issues)
        status = "calculated" if can_calculate else "has_errors"
        return RecipeCalculationResult(
            recipe_version_id=version_row["id"],
            recipe_template_id=version_row["recipe_template_id"],
            recipe_name=version_row["recipe_name"],
            version_number=version_row["version_number"],
            status=status,
            target_batch_size_value=target_value,
            target_batch_size_unit=target_unit,
            percent_total=percent_total,
            can_calculate=can_calculate,
            issues=issues,
            lines=lines,
            totals_by_unit=totals_by_unit,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _target_from_input_or_version(self, *, explicit_value, explicit_unit, stored_value, stored_unit):
        if explicit_value is not None or explicit_unit is not None:
            if explicit_value is None or explicit_unit is None:
                raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Размер партии и единица измерения должны быть указаны вместе.", "target_batch_size_value", None, "Укажите размер партии и единицу: g или ml."))
            return _parse_calculation_target(explicit_value, explicit_unit)
        if stored_value is None and stored_unit is None:
            return None, None
        return _parse_calculation_target(stored_value, stored_unit)


def _parse_calculation_target(value, unit_value):
    unit = parse_unit(unit_value, field="target_batch_size_unit", allowed=CALCULATION_TARGET_UNITS)
    return positive_amount(value, unit, field="target_batch_size_value"), unit


def _quantize_total(value: Decimal, unit: UnitCode) -> Decimal:
    if unit == UnitCode.GRAM:
        return quantize_weight(value, field="total_value")
    if unit == UnitCode.MILLILITER:
        return quantize_volume(value, field="total_value")
    if unit == UnitCode.PIECE:
        return value.quantize(Decimal("1"))
    return value


def _issue(severity: str, code: str, field: str | None, message: str, next_action: str | None) -> RecipeCalculationIssue:
    return RecipeCalculationIssue(severity=severity, code=code, field=field, message=message, next_action=next_action)


__all__ = ["RecipeCalculationService", "RecipeVersionNotFoundError"]
