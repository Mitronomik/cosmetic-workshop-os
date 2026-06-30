from dataclasses import dataclass

PURCHASE_SUGGESTION_ITEM_TYPES = {"ingredient", "packaging"}
PURCHASE_SUGGESTION_REASONS = {"below_minimum_stock", "insufficient_for_order", "predicted_shortage", "expiration_replacement", "manual"}
PURCHASE_SUGGESTION_STATUSES = {"open", "purchased", "dismissed", "archived"}
MANAGED_GENERATED_REASONS = {"below_minimum_stock", "insufficient_for_order"}


@dataclass(frozen=True)
class PurchaseSuggestionCandidate:
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
    notes: str = ""


@dataclass(frozen=True)
class PurchaseSuggestionGenerationResult:
    created_count: int
    updated_count: int
    archived_count: int
    open_count: int
