from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.stock_movements import MovementDirection, StockMovementDraft, StockMovementType
from app.domain.units import UnitCode
from app.models.stock_movement import StockMovement


class StockMovementNotFoundError(LookupError):
    pass


class StockMovementLotMissingError(LookupError):
    pass


class StockMovementInactiveLotError(ValueError):
    pass


class StockMovementLotUnitMismatchError(ValueError):
    pass


class StockMovementInsufficientBalanceError(ValueError):
    pass


class StockMovementRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: StockMovementDraft, *, connection: sqlite3.Connection | None = None) -> StockMovement:
        with _connection_scope(self.config, connection) as connection:
            lot = _get_active_lot(connection, draft.ingredient_lot_id)
            if lot["unit"] != draft.unit.value:
                raise StockMovementLotUnitMismatchError("Movement unit must match ingredient lot unit.")
            if draft.direction == MovementDirection.OUT:
                current = _calculate_lot_quantity(connection, draft.ingredient_lot_id)
                if current - draft.quantity < 0:
                    raise StockMovementInsufficientBalanceError("Outgoing movement would make lot balance negative.")
            cursor = connection.execute(
                """
                INSERT INTO stock_movements (
                    ingredient_lot_id, ingredient_id, movement_type, quantity, unit, direction,
                    reason, occurred_at, note, reference_type, reference_id, source, correction_of_movement_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?)
                """,
                (
                    draft.ingredient_lot_id,
                    lot["ingredient_id"],
                    draft.movement_type.value,
                    str(draft.quantity),
                    draft.unit.value,
                    draft.direction.value,
                    draft.reason,
                    draft.occurred_at,
                    draft.note,
                    draft.reference_type,
                    draft.reference_id,
                    draft.source,
                    draft.correction_of_movement_id,
                ),
            )
            row = connection.execute("SELECT * FROM stock_movements WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_movement(row)

    def get_by_id(self, movement_id: int) -> StockMovement:
        with session(self.config) as connection:
            row = connection.execute("SELECT * FROM stock_movements WHERE id = ?", (movement_id,)).fetchone()
        if row is None:
            raise StockMovementNotFoundError(f"Stock movement {movement_id} was not found.")
        return _row_to_movement(row)

    def list_all(self) -> list[StockMovement]:
        with session(self.config) as connection:
            rows = connection.execute("SELECT * FROM stock_movements ORDER BY created_at, id").fetchall()
        return [_row_to_movement(row) for row in rows]

    def list_by_lot(self, lot_id: int) -> list[StockMovement]:
        with session(self.config) as connection:
            rows = connection.execute(
                "SELECT * FROM stock_movements WHERE ingredient_lot_id = ? ORDER BY created_at, id", (lot_id,)
            ).fetchall()
        return [_row_to_movement(row) for row in rows]

    def calculate_lot_quantity(self, lot_id: int) -> Decimal:
        with session(self.config) as connection:
            _get_existing_lot(connection, lot_id)
            return _calculate_lot_quantity(connection, lot_id)


def _get_existing_lot(connection, lot_id: int):
    row = connection.execute("SELECT id, ingredient_id, unit, is_active FROM ingredient_lots WHERE id = ?", (lot_id,)).fetchone()
    if row is None:
        raise StockMovementLotMissingError(f"Ingredient lot {lot_id} was not found.")
    return row


def _get_active_lot(connection, lot_id: int):
    row = _get_existing_lot(connection, lot_id)
    if not bool(row["is_active"]):
        raise StockMovementInactiveLotError(f"Ingredient lot {lot_id} is inactive.")
    return row


def _calculate_lot_quantity(connection, lot_id: int) -> Decimal:
    rows = connection.execute(
        "SELECT quantity, direction FROM stock_movements WHERE ingredient_lot_id = ? ORDER BY created_at, id", (lot_id,)
    ).fetchall()
    total = Decimal("0")
    for row in rows:
        quantity = Decimal(row["quantity"])
        total += quantity if row["direction"] == MovementDirection.IN.value else -quantity
    return total


def _row_to_movement(row) -> StockMovement:
    return StockMovement(
        id=row["id"],
        ingredient_lot_id=row["ingredient_lot_id"],
        ingredient_id=row["ingredient_id"],
        movement_type=StockMovementType(row["movement_type"]),
        quantity=Decimal(row["quantity"]),
        unit=UnitCode(row["unit"]),
        direction=MovementDirection(row["direction"]),
        reason=row["reason"],
        occurred_at=row["occurred_at"],
        note=row["note"],
        reference_type=row["reference_type"],
        reference_id=row["reference_id"],
        source=row["source"],
        correction_of_movement_id=row["correction_of_movement_id"],
        created_at=row["created_at"],
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
