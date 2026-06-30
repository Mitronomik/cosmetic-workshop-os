from dataclasses import dataclass
from enum import StrEnum


class ClientWishCategory(StrEnum):
    TEXTURE = "texture"
    SCENT = "scent"
    PACKAGING = "packaging"
    INGREDIENT = "ingredient"
    ALLERGY = "allergy"
    CONTRAINDICATION = "contraindication"
    EFFECT = "effect"
    PRICE = "price"
    OTHER = "other"


class ClientWishPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class ClientWishStatus(StrEnum):
    OPEN = "open"
    PLANNED = "planned"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class ClientFeedbackType(StrEnum):
    NOTE = "note"
    REACTION = "reaction"
    TEXTURE = "texture"
    SCENT = "scent"
    EFFECT = "effect"
    PACKAGING = "packaging"
    REQUEST = "request"
    OTHER = "other"


class ClientFeedbackSentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


@dataclass(frozen=True)
class ClientWish:
    id: int
    client_id: int
    client_recipe_id: int | None
    title: str
    description: str
    category: ClientWishCategory
    priority: ClientWishPriority
    status: ClientWishStatus
    is_active: bool
    created_at: str
    updated_at: str
    resolved_at: str | None


@dataclass(frozen=True)
class ClientFeedback:
    id: int
    client_id: int
    client_recipe_id: int | None
    feedback_type: ClientFeedbackType
    sentiment: ClientFeedbackSentiment
    rating: int | None
    text: str
    follow_up_needed: bool
    follow_up_note: str
    occurred_at: str | None
    created_at: str
