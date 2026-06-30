from dataclasses import dataclass

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import normalize_optional_text, normalize_required_text, require_positive_id
from app.models.client_wishes_feedback import ClientFeedbackSentiment, ClientFeedbackType, ClientWishCategory, ClientWishPriority, ClientWishStatus


def _limited(value: str, *, field: str, label: str, max_length: int) -> str:
    if len(value) > max_length:
        raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, f"{label} слишком длинное. Максимум {max_length} символов.", field, value[:80], "Сократите текст."))
    return value


def _optional_positive_id(value: int | None, *, field: str, label: str) -> int | None:
    if value is None:
        return None
    return require_positive_id(value, field=field, label=label)


def _parse_enum(enum_cls, value, *, field: str, message: str, next_action: str):
    try:
        return value if isinstance(value, enum_cls) else enum_cls(value)
    except ValueError as exc:
        raise DomainValidationError(DomainIssue(DomainIssueCode.INVALID_CATEGORY, message, field, str(value), next_action)) from exc


@dataclass(frozen=True)
class ClientWishDraft:
    client_id: int
    client_recipe_id: int | None
    title: str
    description: str = ""
    category: ClientWishCategory = ClientWishCategory.OTHER
    priority: ClientWishPriority = ClientWishPriority.NORMAL

    @classmethod
    def create(cls, *, client_id: int | None, client_recipe_id: int | None = None, title: str = "", description: str | None = "", category: ClientWishCategory | str = ClientWishCategory.OTHER, priority: ClientWishPriority | str = ClientWishPriority.NORMAL) -> "ClientWishDraft":
        return cls(
            client_id=require_positive_id(client_id, field="client_id", label="Клиент"),
            client_recipe_id=_optional_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт"),
            title=_limited(normalize_required_text(title, field="title", label="Название пожелания"), field="title", label="Название пожелания", max_length=180),
            description=_limited(normalize_optional_text(description), field="description", label="Описание пожелания", max_length=1600),
            category=_parse_enum(ClientWishCategory, category, field="category", message="Категория пожелания недопустима.", next_action="Выберите допустимую категорию пожелания."),
            priority=_parse_enum(ClientWishPriority, priority, field="priority", message="Приоритет пожелания недопустим.", next_action="Выберите low, normal или high."),
        )


@dataclass(frozen=True)
class ClientWishStatusUpdate:
    status: ClientWishStatus

    @classmethod
    def create(cls, *, status: ClientWishStatus | str) -> "ClientWishStatusUpdate":
        return cls(_parse_enum(ClientWishStatus, status, field="status", message="Статус пожелания недопустим.", next_action="Выберите open, planned, resolved или archived."))


@dataclass(frozen=True)
class ClientFeedbackDraft:
    client_id: int
    client_recipe_id: int | None
    feedback_type: ClientFeedbackType
    sentiment: ClientFeedbackSentiment
    rating: int | None
    text: str
    follow_up_needed: bool
    follow_up_note: str
    occurred_at: str | None

    @classmethod
    def create(cls, *, client_id: int | None, client_recipe_id: int | None = None, feedback_type: ClientFeedbackType | str = ClientFeedbackType.NOTE, sentiment: ClientFeedbackSentiment | str = ClientFeedbackSentiment.NEUTRAL, rating: int | None = None, text: str = "", follow_up_needed: bool = False, follow_up_note: str | None = "", occurred_at: str | None = None) -> "ClientFeedbackDraft":
        if rating is not None and (not isinstance(rating, int) or isinstance(rating, bool) or rating < 1 or rating > 5):
            raise DomainValidationError(DomainIssue(DomainIssueCode.REQUIRED_FIELD, "Оценка отзыва должна быть целым числом от 1 до 5.", "rating", str(rating), "Укажите оценку 1–5 или оставьте поле пустым."))
        return cls(
            client_id=require_positive_id(client_id, field="client_id", label="Клиент"),
            client_recipe_id=_optional_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт"),
            feedback_type=_parse_enum(ClientFeedbackType, feedback_type, field="feedback_type", message="Тип отзыва недопустим.", next_action="Выберите допустимый тип отзыва."),
            sentiment=_parse_enum(ClientFeedbackSentiment, sentiment, field="sentiment", message="Тональность отзыва недопустима.", next_action="Выберите positive, neutral, negative или mixed."),
            rating=rating,
            text=_limited(normalize_required_text(text, field="text", label="Текст отзыва"), field="text", label="Текст отзыва", max_length=2000),
            follow_up_needed=bool(follow_up_needed),
            follow_up_note=_limited(normalize_optional_text(follow_up_note), field="follow_up_note", label="Заметка для следующего действия", max_length=1200),
            occurred_at=normalize_optional_text(occurred_at) or None,
        )
