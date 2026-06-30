from dataclasses import dataclass


@dataclass(frozen=True)
class PurchaseSuggestion:
    id: int
    suggestion_key: str
    item_type: str
    item_id: int
    item_name_snapshot: str
    recommended_quantity: str
    unit: str
    reason: str
    source_entity_type: str
    source_entity_id: int | None
    message: str
    status: str
    notes: str
    created_at: str
    updated_at: str
    resolved_at: str | None
