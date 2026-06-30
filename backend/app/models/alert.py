from dataclasses import dataclass


@dataclass(frozen=True)
class Alert:
    id: int
    alert_key: str
    type: str
    severity: str
    message: str
    related_entity_type: str
    related_entity_id: int
    recommended_action: str
    status: str
    created_at: str
    updated_at: str
    resolved_at: str | None
    dismissed_at: str | None
