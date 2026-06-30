from pydantic import BaseModel


class AlertResponse(BaseModel):
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


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    limit: int
    offset: int


class AlertGenerationResponse(BaseModel):
    created_count: int
    updated_count: int
    resolved_count: int
    open_count: int
