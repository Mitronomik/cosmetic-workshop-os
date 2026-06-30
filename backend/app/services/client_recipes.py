from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.client_recipes import ClientRecipeDraft, ClientRecipeIngredientDraft, ClientRecipeIngredientUpdateDraft, validate_client_recipe_update_lines
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import require_positive_id
from app.models.client_recipe import ClientRecipe, ClientRecipeDetail, ClientRecipeStatus
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


class ClientRecipeArchivedError(ValueError):
    pass


class ClientRecipeIngredientLineOwnershipError(ValueError):
    pass


class ClientRecipeRestoreClientInactiveError(ValueError):
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


    def update_composition(self, client_recipe_id: int, lines: list[ClientRecipeIngredientUpdateDraft]) -> ClientRecipeDetail:
        client_recipe_id = require_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт")
        validate_client_recipe_update_lines(lines)
        detail = self.repository.get_detail(client_recipe_id)
        if not detail.client_recipe.is_active or detail.client_recipe.status == ClientRecipeStatus.ARCHIVED:
            raise ClientRecipeArchivedError("Archived client recipe composition cannot be edited.")

        existing_by_id = {line.id: line for line in detail.ingredients}
        replacement_drafts: list[ClientRecipeIngredientDraft] = []
        for line in lines:
            existing_line = None
            if line.id is not None:
                existing_line = existing_by_id.get(line.id)
                if existing_line is None:
                    raise ClientRecipeIngredientLineOwnershipError("Client recipe ingredient line does not belong to this client recipe.")
            ingredient = self.ingredients.get_by_id(line.ingredient_id)
            keeps_existing_ingredient = existing_line is not None and existing_line.ingredient_id == line.ingredient_id
            keeps_existing_line_unchanged = (
                keeps_existing_ingredient
                and existing_line.position == line.position
                and existing_line.phase == line.phase
                and existing_line.amount_value == line.amount_value
                and existing_line.amount_unit == line.amount_unit
                and existing_line.personalization_note == line.personalization_note
                and existing_line.notes == line.notes
            )
            if not ingredient.is_active and not keeps_existing_line_unchanged:
                raise ClientRecipeIngredientInactiveError("Inactive ingredient lines can only remain unchanged or be removed.")
            source_recipe_ingredient_id = existing_line.source_recipe_ingredient_id if keeps_existing_ingredient else None
            replacement_drafts.append(
                ClientRecipeIngredientDraft.create(
                    ingredient_id=line.ingredient_id,
                    source_recipe_ingredient_id=source_recipe_ingredient_id,
                    position=line.position,
                    phase=line.phase,
                    amount_value=line.amount_value,
                    amount_unit=line.amount_unit,
                    personalization_note=line.personalization_note,
                    notes=line.notes,
                )
            )

        old_signature = [(line.ingredient_id, str(line.amount_value), line.amount_unit.value, line.position, line.phase, line.personalization_note, line.notes) for line in detail.ingredients]
        new_signature = [(line.ingredient_id, str(line.amount_value), line.amount_unit.value, line.position, line.phase, line.personalization_note, line.notes) for line in replacement_drafts]
        with transaction(self.config) as connection:
            self.repository.replace_ingredient_lines(client_recipe_id, replacement_drafts, connection=connection)
            self.audit.create_log(
                action="client_recipe.composition_updated",
                entity_type="client_recipe",
                entity_id=str(client_recipe_id),
                summary=f"Client recipe composition updated: {detail.client_recipe.title}",
                metadata={"line_count": len(replacement_drafts), "changed": old_signature != new_signature},
                connection=connection,
            )
        return self.repository.get_detail(client_recipe_id)

    def deactivate(self, client_recipe_id: int) -> ClientRecipe:
        client_recipe_id = require_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт")
        with transaction(self.config) as connection:
            client_recipe = self.repository.deactivate(client_recipe_id, connection=connection)
            self.audit.create_log(action="client_recipe.deactivated", entity_type="client_recipe", entity_id=str(client_recipe.id), summary=f"Client recipe deactivated: {client_recipe.title}", metadata={"client_id": client_recipe.client_id}, connection=connection)
        return client_recipe

    def restore(self, client_recipe_id: int) -> ClientRecipe:
        client_recipe_id = require_positive_id(client_recipe_id, field="client_recipe_id", label="Индивидуальный рецепт")
        with transaction(self.config) as connection:
            current = self.repository.get_detail(client_recipe_id, connection=connection).client_recipe
            client_row = connection.execute("SELECT is_active FROM clients WHERE id=?", (current.client_id,)).fetchone()
            if client_row is None:
                raise ClientNotFoundError(f"Client {current.client_id} was not found.")
            if not bool(client_row["is_active"]):
                raise ClientRecipeRestoreClientInactiveError("Linked client is inactive.")
            if current.is_active and current.status != ClientRecipeStatus.ARCHIVED:
                return current
            client_recipe = self.repository.restore(client_recipe_id, connection=connection)
            self.audit.create_log(
                action="client_recipe.restored",
                entity_type="client_recipe",
                entity_id=str(client_recipe.id),
                summary=f"Client recipe restored: {client_recipe.title}",
                metadata={"client_id": client_recipe.client_id, "restored_status": "draft"},
                connection=connection,
            )
        return client_recipe


__all__ = ["ClientRecipeService", "ClientRecipeNotFoundError", "ClientNotFoundError", "RecipeVersionNotFoundError", "IngredientNotFoundError", "ClientInactiveError", "SourceRecipeVersionEmptyError", "ClientRecipeIngredientInactiveError", "ClientRecipeArchivedError", "ClientRecipeIngredientLineOwnershipError", "ClientRecipeRestoreClientInactiveError"]
