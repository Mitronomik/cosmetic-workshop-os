from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Final

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError

WEIGHT_QUANT: Final = Decimal("0.001")
VOLUME_QUANT: Final = Decimal("0.001")
PERCENT_QUANT: Final = Decimal("0.01")
MONEY_QUANT: Final = Decimal("0.01")
COUNT_QUANT: Final = Decimal("1")
DENSITY_QUANT: Final = Decimal("0.0001")

ROUNDING_MODE: Final = ROUND_HALF_UP


def parse_decimal(value: Decimal | int | str, *, field: str = "value") -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.FLOAT_NOT_ALLOWED,
                message=f"Поле “{field}” должно передаваться как строка, целое число или Decimal, не float.",
                field=field,
                value=repr(value),
                next_action="Передайте число строкой, например “12.5” или “12,5” при пользовательском вводе.",
            )
        )
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if not isinstance(value, str):
        raise _invalid_decimal(value, field)
    normalized = value.strip().replace(",", ".")
    if not normalized:
        raise _invalid_decimal(value, field)
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise _invalid_decimal(value, field) from exc


def _invalid_decimal(value: object, field: str) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(
            code=DomainIssueCode.INVALID_DECIMAL,
            message=f"В поле “{field}” указано “{value}”. Нужно число, например 30 или 30,5.",
            field=field,
            value=str(value),
            next_action="Исправьте значение на обычное десятичное число.",
        )
    )


def quantize_decimal(value: Decimal | int | str, quantum: Decimal, *, field: str = "value") -> Decimal:
    return parse_decimal(value, field=field).quantize(quantum, rounding=ROUNDING_MODE)


def quantize_weight(value: Decimal | int | str, *, field: str = "weight_g") -> Decimal:
    return quantize_decimal(value, WEIGHT_QUANT, field=field)


def quantize_volume(value: Decimal | int | str, *, field: str = "volume_ml") -> Decimal:
    return quantize_decimal(value, VOLUME_QUANT, field=field)


def quantize_percentage(value: Decimal | int | str, *, field: str = "percentage") -> Decimal:
    return quantize_decimal(value, PERCENT_QUANT, field=field)


def quantize_money(value: Decimal | int | str, *, field: str = "money") -> Decimal:
    return quantize_decimal(value, MONEY_QUANT, field=field)


def quantize_count(value: Decimal | int | str, *, field: str = "count") -> Decimal:
    return quantize_decimal(value, COUNT_QUANT, field=field)


def quantize_density(value: Decimal | int | str, *, field: str = "density_g_per_ml") -> Decimal:
    return quantize_decimal(value, DENSITY_QUANT, field=field)
