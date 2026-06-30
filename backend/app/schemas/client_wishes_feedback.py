from pydantic import BaseModel, ConfigDict

from app.models.client_wishes_feedback import ClientFeedbackSentiment, ClientFeedbackType, ClientWishCategory, ClientWishPriority, ClientWishStatus


class ClientWishCreateRequest(BaseModel):
    client_recipe_id: int | None = None
    title: str
    description: str = ""
    category: ClientWishCategory = ClientWishCategory.OTHER
    priority: ClientWishPriority = ClientWishPriority.NORMAL
    model_config = ConfigDict(use_enum_values=False, extra="forbid")


class ClientWishStatusUpdateRequest(BaseModel):
    status: ClientWishStatus
    model_config = ConfigDict(use_enum_values=False, extra="forbid")


class ClientWishResponse(BaseModel):
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


class ClientWishesResponse(BaseModel):
    wishes: list[ClientWishResponse]


class ClientFeedbackCreateRequest(BaseModel):
    client_recipe_id: int | None = None
    feedback_type: ClientFeedbackType = ClientFeedbackType.NOTE
    sentiment: ClientFeedbackSentiment = ClientFeedbackSentiment.NEUTRAL
    rating: int | None = None
    text: str
    follow_up_needed: bool = False
    follow_up_note: str = ""
    occurred_at: str | None = None
    model_config = ConfigDict(use_enum_values=False, extra="forbid")


class ClientFeedbackResponse(BaseModel):
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


class ClientFeedbackListResponse(BaseModel):
    feedback: list[ClientFeedbackResponse]
