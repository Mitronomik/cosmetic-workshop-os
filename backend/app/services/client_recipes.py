from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.client_recipes import ClientRecipeDraft, ClientRecipeIngredientDraft
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import require_positive_id
from app.models.client_recipe import ClientRecipe, ClientRecipeDetail
from app.repositories.audit import AuditLogRepository
from app.repositories.client_recipes import ClientRecipeNotFoundError, ClientRecipeRepository
from app.repositories.clients import ClientNotFoundError, ClientRepository
from app.repositories.ingredients import IngredientNotFoundError, IngredientRepository
from app.repositories.recipes import RecipeRepository, RecipeVersionNotFoundError


class ClientInactiveError(ValueError):
    pass


class SourceRecipeVersionEmptyError(ValueError):
    pass


class ClientRecipeIngredientInactiveError(ValueError):
    pass


class ClientRecipeService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = ClientRecipeRepository(config)
        self.clients = ClientRepository(config)
        self.recipes = RecipeRepository(config)
        self.ingredients = IngredientRepository(config)
        self.audit = AuditLogRepository(config)

    def create_from_recipe_version(self, draft: ClientRecipeDraft) -> ClientRecipeDetail:
        with transaction(self.config) as connection:
            client = self.clients.get_by_id(draft.client_id)
            if not client.is_active:
                raise ClientInactiveError("Client is inactive.")
            source_detail = self.recipes.get_version_detail(draft.source_recipe_version_id)
            if not source_detail.ingredients:
                raise SourceRecipeVersionEmptyError("Source recipe version has no ingredient lines.")
            snapshot_drafts: list[ClientRecipeIngredientDraft] = []
            for line in source_detail.ingredients:
                ingredient = self.ingredients.get_by_id(line.ingredient_id)
                if not ingredient.is_active:
                    raise ClientRecipeIngredientInactiveError("Ingredient is inactive.")
                snapshot_drafts.append(ClientRecipeIngredientDraft.create(ingredient_id=line.ingredient_id, source_recipe_ingredient_id=line.id, position=line.position, phase=line.phase, amount_value=line.amount_value, amount_unit=line.amount_unit, notes=line.notes))
            client_recipe = self.repository.create(draft, connection=connection)
            for line_draft in snapshot_drafts:
                self.repository.create_ingredient_line(client_recipe.id, line_draft, connection=connection)
            self.audit.create_log(action="client_recipe.created", entity_type="client_recipe", entity_id=str(client_recipe.id), summary=f"Client recipe created: {client_recipe.title}", metadata={"client_id": client.id, "source_recipe_version_id": draft.source_recipe_version_id}, connection=connection)
        return self.repository.get_detail(client_recipe.id)

    def get_detail(self, client_recipe_id: int) -> ClientRecipeDetail:
        client_recipe_id = require_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт")
        return self.repository.get_detail(client_recipe_id)

    def list_recipes(self, *, include_inactive: bool = True) -> list[ClientRecipe]:
        return self.repository.list_recipes(include_inactive=include_inactive)

    def list_for_client(self, client_id: int, *, include_inactive: bool = True) -> list[ClientRecipe]:
        client_id = require_positive_id(client_id, field="client_id", label="Клиент")
        self.clients.get_by_id(client_id)
        return self.repository.list_for_client(client_id, include_inactive=include_inactive)

    def deactivate(self, client_recipe_id: int) -> ClientRecipe:
        client_recipe_id = require_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт")
        with transaction(self.config) as connection:
            client_recipe = self.repository.deactivate(client_recipe_id, connection=connection)
            self.audit.create_log(action="client_recipe.deactivated", entity_type="client_recipe", entity_id=str(client_recipe.id), summary=f"Client recipe deactivated: {client_recipe.title}", metadata={"client_id": client_recipe.client_id}, connection=connection)
        return client_recipe


__all__ = ["ClientRecipeService", "ClientRecipeNotFoundError", "ClientNotFoundError", "RecipeVersionNotFoundError", "IngredientNotFoundError", "ClientInactiveError", "SourceRecipeVersionEmptyError", "ClientRecipeIngredientInactiveError"]
