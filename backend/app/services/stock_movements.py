from decimal import Decimal

from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.stock_movements import StockMovementDraft
from app.models.stock_movement import StockMovement
from app.repositories.audit import AuditLogRepository
from app.repositories.stock_movements import (
    StockMovementInactiveLotError,
    StockMovementInsufficientBalanceError,
    StockMovementLotMissingError,
    StockMovementLotUnitMismatchError,
    StockMovementNotFoundError,
    StockMovementRepository,
)


class StockMovementService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = StockMovementRepository(config)
        self.audit = AuditLogRepository(config)

    def create_movement(self, draft: StockMovementDraft) -> StockMovement:
        with transaction(self.config) as connection:
            movement = self.repository.create(draft, connection=connection)
            self.audit.create_log(
                action="stock_movement.created",
                entity_type="stock_movement",
                entity_id=str(movement.id),
                summary=f"Stock movement created for lot #{movement.ingredient_lot_id}",
                metadata={"ingredient_lot_id": movement.ingredient_lot_id, "ingredient_id": movement.ingredient_id},
                connection=connection,
            )
        return movement

    def get_movement(self, movement_id: int) -> StockMovement:
        return self.repository.get_by_id(movement_id)

    def list_movements(self) -> list[StockMovement]:
        return self.repository.list_all()

    def list_movements_by_lot(self, lot_id: int) -> list[StockMovement]:
        return self.repository.list_by_lot(lot_id)

    def calculate_lot_quantity(self, lot_id: int) -> Decimal:
        return self.repository.calculate_lot_quantity(lot_id)


__all__ = [
    "StockMovementInactiveLotError",
    "StockMovementInsufficientBalanceError",
    "StockMovementLotMissingError",
    "StockMovementLotUnitMismatchError",
    "StockMovementNotFoundError",
    "StockMovementService",
]
