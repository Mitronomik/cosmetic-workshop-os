from dataclasses import dataclass
from enum import StrEnum


class DomainIssueCode(StrEnum):
    INVALID_DECIMAL = "invalid_decimal"
    FLOAT_NOT_ALLOWED = "float_not_allowed"
    NEGATIVE_QUANTITY = "negative_quantity"
    ZERO_QUANTITY = "zero_quantity"
    MISSING_DENSITY = "missing_density"
    ZERO_OR_NEGATIVE_DENSITY = "zero_or_negative_density"
    PERCENTAGE_OUT_OF_RANGE = "percentage_out_of_range"
    RECIPE_PERCENTAGE_SUM_NOT_100 = "recipe_percentage_sum_not_100"


@dataclass(frozen=True)
class DomainIssue:
    code: DomainIssueCode
    message: str
    field: str | None = None
    value: str | None = None
    next_action: str | None = None


class DomainValidationError(ValueError):
    def __init__(self, issue: DomainIssue) -> None:
        super().__init__(issue.message)
        self.issue = issue
