from dataclasses import dataclass, field

from app.domain.errors import DomainIssue, DomainIssueCode
from app.domain.measurements import Density, Volume, Weight


@dataclass(frozen=True)
class ConversionResult:
    weight: Weight | None
    warnings: tuple[DomainIssue, ...] = field(default_factory=tuple)

    @property
    def is_exact(self) -> bool:
        return self.weight is not None and not self.warnings


MISSING_DENSITY_WARNING = DomainIssue(
    code=DomainIssueCode.MISSING_DENSITY,
    message="Плотность не указана: нельзя точно перевести миллилитры в граммы.",
    field="density_g_per_ml",
    next_action="Укажите плотность ингредиента в г/мл или подтвердите явное приближение в будущей производственной операции.",
)


def milliliters_to_grams(volume: Volume, density: Density | None) -> ConversionResult:
    if density is None:
        return ConversionResult(weight=None, warnings=(MISSING_DENSITY_WARNING,))
    grams = volume.milliliters * density.grams_per_milliliter
    return ConversionResult(weight=Weight.from_value(grams), warnings=())
