from dataclasses import dataclass


@dataclass(frozen=True)
class AuditLog:
    id: int | None
    created_at: str | None
    actor_type: str
    action: str
    entity_type: str | None
    entity_id: str | None
    summary: str
    metadata_json: str
