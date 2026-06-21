from dataclasses import dataclass
from enum import StrEnum


class UnitCode(StrEnum):
    GRAM = "g"
    MILLILITER = "ml"
    PERCENT = "percent"
    PIECE = "pcs"


@dataclass(frozen=True)
class UnitDefinition:
    code: UnitCode
    english_label: str
    russian_label: str
    quantity_kind: str


GRAM = UnitDefinition(UnitCode.GRAM, "gram", "г", "weight")
MILLILITER = UnitDefinition(UnitCode.MILLILITER, "milliliter", "мл", "volume")
PERCENT = UnitDefinition(UnitCode.PERCENT, "percent", "%", "percentage")
PIECE = UnitDefinition(UnitCode.PIECE, "piece", "шт", "count")

MVP_UNITS = {
    UnitCode.GRAM: GRAM,
    UnitCode.MILLILITER: MILLILITER,
    UnitCode.PERCENT: PERCENT,
    UnitCode.PIECE: PIECE,
}
