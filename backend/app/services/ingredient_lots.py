from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.ingredient_lots import IngredientLotDraft
from app.models.ingredient_lot import IngredientLot
from app.repositories.audit import AuditLogRepository
from app.repositories.ingredient_lots import (
    IngredientLotInactiveIngredientError,
    IngredientLotIngredientMissingError,
    IngredientLotNotFoundError,
    IngredientLotRepository,
)


class IngredientLotService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = IngredientLotRepository(config)
        self.audit = AuditLogRepository(config)

    def create_lot(self, draft: IngredientLotDraft) -> IngredientLot:
        with transaction(self.config) as connection:
            lot = self.repository.create(draft, connection=connection)
            self.audit.create_log(
                action="ingredient_lot.created",
                entity_type="ingredient_lot",
                entity_id=str(lot.id),
                summary=f"Ingredient lot created for ingredient #{lot.ingredient_id}",
                metadata={"ingredient_id": lot.ingredient_id},
                connection=connection,
            )
        return lot

    def get_lot(self, lot_id: int) -> IngredientLot:
        return self.repository.get_by_id(lot_id)

    def list_active_lots(self) -> list[IngredientLot]:
        return self.repository.list_active()

    def list_active_lots_by_ingredient(self, ingredient_id: int) -> list[IngredientLot]:
        return self.repository.list_active_by_ingredient_id(ingredient_id)

    def update_lot(self, lot_id: int, draft: IngredientLotDraft) -> IngredientLot:
        with transaction(self.config) as connection:
            lot = self.repository.update_basic(lot_id, draft, connection=connection)
            self.audit.create_log(
                action="ingredient_lot.updated",
                entity_type="ingredient_lot",
                entity_id=str(lot.id),
                summary=f"Ingredient lot updated for ingredient #{lot.ingredient_id}",
                metadata={"ingredient_id": lot.ingredient_id},
                connection=connection,
            )
        return lot

    def deactivate_lot(self, lot_id: int) -> IngredientLot:
        with transaction(self.config) as connection:
            lot = self.repository.deactivate(lot_id, connection=connection)
            self.audit.create_log(
                action="ingredient_lot.deactivated",
                entity_type="ingredient_lot",
                entity_id=str(lot.id),
                summary=f"Ingredient lot deactivated for ingredient #{lot.ingredient_id}",
                metadata={"ingredient_id": lot.ingredient_id},
                connection=connection,
            )
        return lot


__all__ = [
    "IngredientLotInactiveIngredientError",
    "IngredientLotIngredientMissingError",
    "IngredientLotNotFoundError",
    "IngredientLotService",
]
