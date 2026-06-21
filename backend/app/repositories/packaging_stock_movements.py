from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.packaging_stock_movements import PackagingMovementDirection, PackagingStockMovementDraft, PackagingStockMovementType
from app.domain.units import UnitCode
from app.models.packaging_stock_movement import PackagingStockMovement


class PackagingStockMovementNotFoundError(LookupError):
    pass


class PackagingStockMovementItemMissingError(LookupError):
    pass


class PackagingStockMovementInactiveItemError(ValueError):
    pass


class PackagingStockMovementInsufficientBalanceError(ValueError):
    pass


class PackagingStockMovementRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: PackagingStockMovementDraft, *, connection: sqlite3.Connection | None = None) -> PackagingStockMovement:
        with _connection_scope(self.config, connection) as connection:
            _get_active_packaging_item(connection, draft.packaging_item_id)
            if draft.direction == PackagingMovementDirection.OUT:
                current = _calculate_packaging_item_quantity(connection, draft.packaging_item_id)
                if current - draft.quantity < 0:
                    raise PackagingStockMovementInsufficientBalanceError("Outgoing packaging movement would make item balance negative.")
            cursor = connection.execute(
                """
                INSERT INTO packaging_stock_movements (
                    packaging_item_id, movement_type, quantity, unit, direction, occurred_at,
                    reason, source, notes
                ) VALUES (?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?)
                """,
                (draft.packaging_item_id, draft.movement_type.value, str(draft.quantity), draft.unit.value, draft.direction.value, draft.occurred_at, draft.reason, draft.source, draft.notes),
            )
            row = connection.execute("SELECT * FROM packaging_stock_movements WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_packaging_stock_movement(row)

    def get_by_id(self, movement_id: int) -> PackagingStockMovement:
        with session(self.config) as connection:
            row = connection.execute("SELECT * FROM packaging_stock_movements WHERE id = ?", (movement_id,)).fetchone()
        if row is None:
            raise PackagingStockMovementNotFoundError(f"Packaging stock movement {movement_id} was not found.")
        return _row_to_packaging_stock_movement(row)

    def list_all(self) -> list[PackagingStockMovement]:
        with session(self.config) as connection:
            rows = connection.execute("SELECT * FROM packaging_stock_movements ORDER BY created_at, id").fetchall()
        return [_row_to_packaging_stock_movement(row) for row in rows]

    def list_by_packaging_item(self, packaging_item_id: int) -> list[PackagingStockMovement]:
        with session(self.config) as connection:
            _get_existing_packaging_item(connection, packaging_item_id)
            rows = connection.execute("SELECT * FROM packaging_stock_movements WHERE packaging_item_id = ? ORDER BY created_at, id", (packaging_item_id,)).fetchall()
        return [_row_to_packaging_stock_movement(row) for row in rows]

    def calculate_packaging_item_quantity(self, packaging_item_id: int) -> Decimal:
        with session(self.config) as connection:
            _get_existing_packaging_item(connection, packaging_item_id)
            return _calculate_packaging_item_quantity(connection, packaging_item_id)


def _get_existing_packaging_item(connection, packaging_item_id: int):
    row = connection.execute("SELECT id, is_active FROM packaging_items WHERE id = ?", (packaging_item_id,)).fetchone()
    if row is None:
        raise PackagingStockMovementItemMissingError(f"Packaging item {packaging_item_id} was not found.")
    return row


def _get_active_packaging_item(connection, packaging_item_id: int):
    row = _get_existing_packaging_item(connection, packaging_item_id)
    if not bool(row["is_active"]):
        raise PackagingStockMovementInactiveItemError(f"Packaging item {packaging_item_id} is inactive.")
    return row


def _calculate_packaging_item_quantity(connection, packaging_item_id: int) -> Decimal:
    rows = connection.execute("SELECT quantity, direction FROM packaging_stock_movements WHERE packaging_item_id = ? ORDER BY created_at, id", (packaging_item_id,)).fetchall()
    total = Decimal("0")
    for row in rows:
        quantity = Decimal(row["quantity"])
        total += quantity if row["direction"] == PackagingMovementDirection.IN.value else -quantity
    return total


def _row_to_packaging_stock_movement(row) -> PackagingStockMovement:
    return PackagingStockMovement(
        id=row["id"],
        packaging_item_id=row["packaging_item_id"],
        movement_type=PackagingStockMovementType(row["movement_type"]),
        quantity=Decimal(row["quantity"]),
        unit=UnitCode(row["unit"]),
        direction=PackagingMovementDirection(row["direction"]),
        occurred_at=row["occurred_at"],
        reason=row["reason"],
        source=row["source"],
        notes=row["notes"],
        created_at=row["created_at"],
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
