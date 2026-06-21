from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.ingredients import IngredientDraft
from app.models.ingredient import Ingredient
from app.repositories.audit import AuditLogRepository
from app.repositories.ingredients import IngredientNotFoundError, IngredientRepository


class IngredientService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = IngredientRepository(config)
        self.audit = AuditLogRepository(config)

    def create_ingredient(self, draft: IngredientDraft) -> Ingredient:
        with transaction(self.config) as connection:
            ingredient = self.repository.create(draft, connection=connection)
            self.audit.create_log(
                action="ingredient.created",
                entity_type="ingredient",
                entity_id=str(ingredient.id),
                summary=f"Ingredient created: {ingredient.name}",
                metadata={"category": ingredient.category.value},
                connection=connection,
            )
        return ingredient

    def get_ingredient(self, ingredient_id: int) -> Ingredient:
        return self.repository.get_by_id(ingredient_id)

    def list_active_ingredients(self) -> list[Ingredient]:
        return self.repository.list_active()

    def update_ingredient(self, ingredient_id: int, draft: IngredientDraft) -> Ingredient:
        with transaction(self.config) as connection:
            ingredient = self.repository.update_basic(ingredient_id, draft, connection=connection)
            self.audit.create_log(
                action="ingredient.updated",
                entity_type="ingredient",
                entity_id=str(ingredient.id),
                summary=f"Ingredient updated: {ingredient.name}",
                metadata={"category": ingredient.category.value},
                connection=connection,
            )
        return ingredient

    def deactivate_ingredient(self, ingredient_id: int) -> Ingredient:
        with transaction(self.config) as connection:
            ingredient = self.repository.deactivate(ingredient_id, connection=connection)
            self.audit.create_log(
                action="ingredient.deactivated",
                entity_type="ingredient",
                entity_id=str(ingredient.id),
                summary=f"Ingredient deactivated: {ingredient.name}",
                connection=connection,
            )
        return ingredient


__all__ = ["IngredientNotFoundError", "IngredientService"]
