from dataclasses import dataclass

ALERT_TYPES = {
    "low_ingredient_stock", "low_packaging_stock", "ingredient_expiration_soon", "ingredient_expired",
    "insufficient_materials_for_order", "insufficient_packaging_for_order",
}
ALERT_SEVERITIES = {"info", "warning", "critical", "blocking"}
ALERT_STATUSES = {"open", "resolved", "dismissed"}


@dataclass(frozen=True)
class AlertCandidate:
    alert_key: str
    type: str
    severity: str
    message: str
    related_entity_type: str
    related_entity_id: int
    recommended_action: str


@dataclass(frozen=True)
class AlertGenerationResult:
    created_count: int
    updated_count: int
    resolved_count: int
    open_count: int
