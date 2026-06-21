from dataclasses import dataclass
from decimal import Decimal

from app.domain.decimal_utils import (
    parse_decimal,
    quantize_count,
    quantize_density,
    quantize_money,
    quantize_percentage,
    quantize_volume,
    quantize_weight,
)
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.units import UnitCode


def _require_non_negative(value: Decimal, *, field: str) -> None:
    if value < 0:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.NEGATIVE_QUANTITY,
                message=f"Поле “{field}” не может быть отрицательным.",
                field=field,
                value=str(value),
                next_action="Укажите ноль или положительное значение.",
            )
        )


def _require_positive(value: Decimal, *, field: str) -> None:
    if value <= 0:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY,
                message=f"Поле “{field}” должно быть больше нуля.",
                field=field,
                value=str(value),
                next_action="Укажите известную плотность в г/мл.",
            )
        )


@dataclass(frozen=True)
class Weight:
    grams: Decimal
    unit: UnitCode = UnitCode.GRAM

    @classmethod
    def from_value(cls, value: Decimal | int | str) -> "Weight":
        grams = quantize_weight(value)
        _require_non_negative(grams, field="weight_g")
        return cls(grams=grams)


@dataclass(frozen=True)
class Volume:
    milliliters: Decimal
    unit: UnitCode = UnitCode.MILLILITER

    @classmethod
    def from_value(cls, value: Decimal | int | str) -> "Volume":
        milliliters = quantize_volume(value)
        _require_non_negative(milliliters, field="volume_ml")
        return cls(milliliters=milliliters)


@dataclass(frozen=True)
class Percentage:
    value: Decimal
    unit: UnitCode = UnitCode.PERCENT

    @classmethod
    def from_value(cls, value: Decimal | int | str) -> "Percentage":
        percentage = quantize_percentage(value)
        _require_non_negative(percentage, field="percentage")
        if percentage > Decimal("100"):
            raise DomainValidationError(
                DomainIssue(
                    code=DomainIssueCode.PERCENTAGE_OUT_OF_RANGE,
                    message="Процент должен быть в диапазоне от 0 до 100.",
                    field="percentage",
                    value=str(percentage),
                    next_action="Проверьте процент в строке расчета.",
                )
            )
        return cls(value=percentage)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "RUB"

    @classmethod
    def from_value(cls, value: Decimal | int | str, *, currency: str = "RUB") -> "Money":
        amount = quantize_money(value)
        _require_non_negative(amount, field="money")
        return cls(amount=amount, currency=currency)


@dataclass(frozen=True)
class Quantity:
    count: Decimal
    unit: UnitCode = UnitCode.PIECE

    @classmethod
    def from_value(cls, value: Decimal | int | str) -> "Quantity":
        count = quantize_count(value)
        _require_non_negative(count, field="count")
        return cls(count=count)


@dataclass(frozen=True)
class Density:
    grams_per_milliliter: Decimal

    @classmethod
    def from_value(cls, value: Decimal | int | str) -> "Density":
        density = quantize_density(value)
        _require_positive(density, field="density_g_per_ml")
        return cls(grams_per_milliliter=density)
