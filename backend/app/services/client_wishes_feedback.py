from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.client_wishes_feedback import ClientFeedbackDraft, ClientWishDraft, ClientWishStatusUpdate
from app.domain.recipes import require_positive_id
from app.models.client_wishes_feedback import ClientFeedback, ClientWish, ClientWishStatus
from app.repositories.audit import AuditLogRepository
from app.repositories.client_recipes import ClientRecipeNotFoundError, ClientRecipeRepository
from app.repositories.client_wishes_feedback import ClientFeedbackNotFoundError, ClientFeedbackRepository, ClientWishNotFoundError, ClientWishRepository
from app.repositories.clients import ClientNotFoundError, ClientRepository


class ClientWishFeedbackClientInactiveError(ValueError):
    pass


class ClientRecipeClientMismatchError(ValueError):
    pass


class ClientWishService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = ClientWishRepository(config)
        self.clients = ClientRepository(config)
        self.client_recipes = ClientRecipeRepository(config)
        self.audit = AuditLogRepository(config)

    def create(self, draft: ClientWishDraft) -> ClientWish:
        with transaction(self.config) as connection:
            self._validate_create_context(draft.client_id, draft.client_recipe_id, connection=connection)
            wish = self.repository.create(draft, connection=connection)
            self.audit.create_log(action="client_wish.created", entity_type="client_wish", entity_id=str(wish.id), summary=f"Client wish created: {wish.title}", metadata={"client_id": wish.client_id, "client_recipe_id": wish.client_recipe_id, "category": wish.category.value, "priority": wish.priority.value}, connection=connection)
        return wish

    def list_for_client(self, client_id: int, *, include_inactive: bool = False) -> list[ClientWish]:
        client_id = require_positive_id(client_id, field="client_id", label="Клиент")
        self.clients.get_by_id(client_id)
        return self.repository.list_for_client(client_id, include_inactive=include_inactive)

    def get(self, wish_id: int) -> ClientWish:
        wish_id = require_positive_id(wish_id, field="wish_id", label="Пожелание")
        return self.repository.get(wish_id)

    def update_status(self, wish_id: int, update: ClientWishStatusUpdate) -> ClientWish:
        wish_id = require_positive_id(wish_id, field="wish_id", label="Пожелание")
        with transaction(self.config) as connection:
            before = self.repository.get(wish_id, connection=connection)
            wish = self.repository.update_status(wish_id, update.status, connection=connection)
            self.audit.create_log(action="client_wish.status_changed", entity_type="client_wish", entity_id=str(wish.id), summary=f"Client wish status changed: {wish.title}", metadata={"client_id": wish.client_id, "client_recipe_id": wish.client_recipe_id, "old_status": before.status.value, "new_status": wish.status.value}, connection=connection)
        return wish

    def archive(self, wish_id: int) -> ClientWish:
        wish_id = require_positive_id(wish_id, field="wish_id", label="Пожелание")
        with transaction(self.config) as connection:
            wish = self.repository.archive(wish_id, connection=connection)
            self.audit.create_log(action="client_wish.archived", entity_type="client_wish", entity_id=str(wish.id), summary=f"Client wish archived: {wish.title}", metadata={"client_id": wish.client_id, "client_recipe_id": wish.client_recipe_id, "new_status": ClientWishStatus.ARCHIVED.value}, connection=connection)
        return wish

    def _validate_create_context(self, client_id: int, client_recipe_id: int | None, *, connection) -> None:
        client = self.clients.get_by_id(client_id)
        if not client.is_active:
            raise ClientWishFeedbackClientInactiveError("Client is inactive.")
        if client_recipe_id is not None:
            recipe = self.client_recipes.get_detail(client_recipe_id, connection=connection).client_recipe
            if recipe.client_id != client_id:
                raise ClientRecipeClientMismatchError("Client recipe belongs to another client.")


class ClientFeedbackService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = ClientFeedbackRepository(config)
        self.clients = ClientRepository(config)
        self.client_recipes = ClientRecipeRepository(config)
        self.audit = AuditLogRepository(config)

    def create(self, draft: ClientFeedbackDraft) -> ClientFeedback:
        with transaction(self.config) as connection:
            self._validate_create_context(draft.client_id, draft.client_recipe_id, connection=connection)
            feedback = self.repository.create(draft, connection=connection)
            self.audit.create_log(action="client_feedback.created", entity_type="client_feedback", entity_id=str(feedback.id), summary="Client feedback created", metadata={"client_id": feedback.client_id, "client_recipe_id": feedback.client_recipe_id, "feedback_type": feedback.feedback_type.value, "sentiment": feedback.sentiment.value, "follow_up_needed": feedback.follow_up_needed}, connection=connection)
        return feedback

    def list_for_client(self, client_id: int) -> list[ClientFeedback]:
        client_id = require_positive_id(client_id, field="client_id", label="Клиент")
        self.clients.get_by_id(client_id)
        return self.repository.list_for_client(client_id)

    def get(self, feedback_id: int) -> ClientFeedback:
        feedback_id = require_positive_id(feedback_id, field="feedback_id", label="Отзыв")
        return self.repository.get(feedback_id)

    def _validate_create_context(self, client_id: int, client_recipe_id: int | None, *, connection) -> None:
        client = self.clients.get_by_id(client_id)
        if not client.is_active:
            raise ClientWishFeedbackClientInactiveError("Client is inactive.")
        if client_recipe_id is not None:
            recipe = self.client_recipes.get_detail(client_recipe_id, connection=connection).client_recipe
            if recipe.client_id != client_id:
                raise ClientRecipeClientMismatchError("Client recipe belongs to another client.")


__all__ = ["ClientWishService", "ClientFeedbackService", "ClientWishNotFoundError", "ClientFeedbackNotFoundError", "ClientNotFoundError", "ClientRecipeNotFoundError", "ClientWishFeedbackClientInactiveError", "ClientRecipeClientMismatchError"]
