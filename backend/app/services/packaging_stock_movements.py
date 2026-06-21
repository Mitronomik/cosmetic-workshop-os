from decimal import Decimal

from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.models.packaging_stock_movement import PackagingStockMovement
from app.repositories.audit import AuditLogRepository
from app.repositories.packaging_stock_movements import (
    PackagingStockMovementInactiveItemError,
    PackagingStockMovementInsufficientBalanceError,
    PackagingStockMovementItemMissingError,
    PackagingStockMovementNotFoundError,
    PackagingStockMovementRepository,
)


class PackagingStockMovementService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = PackagingStockMovementRepository(config)
        self.audit = AuditLogRepository(config)

    def create_movement(self, draft: PackagingStockMovementDraft) -> PackagingStockMovement:
        with transaction(self.config) as connection:
            movement = self.repository.create(draft, connection=connection)
            self.audit.create_log(
                action="packaging_stock_movement.created",
                entity_type="packaging_stock_movement",
                entity_id=str(movement.id),
                summary=f"Packaging stock movement created for packaging item #{movement.packaging_item_id}",
                metadata={"packaging_item_id": movement.packaging_item_id},
                connection=connection,
            )
        return movement

    def get_movement(self, movement_id: int) -> PackagingStockMovement:
        return self.repository.get_by_id(movement_id)

    def list_movements(self) -> list[PackagingStockMovement]:
        return self.repository.list_all()

    def list_movements_by_packaging_item(self, packaging_item_id: int) -> list[PackagingStockMovement]:
        return self.repository.list_by_packaging_item(packaging_item_id)

    def calculate_packaging_item_quantity(self, packaging_item_id: int) -> Decimal:
        return self.repository.calculate_packaging_item_quantity(packaging_item_id)


__all__ = [
    "PackagingStockMovementInactiveItemError",
    "PackagingStockMovementInsufficientBalanceError",
    "PackagingStockMovementItemMissingError",
    "PackagingStockMovementNotFoundError",
    "PackagingStockMovementService",
]
