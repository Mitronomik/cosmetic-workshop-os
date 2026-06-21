from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.measurements import Density
from app.domain.units import UnitCode
from app.models.ingredient_lot import IngredientLot


class IngredientLotNotFoundError(LookupError):
    pass


class IngredientLotIngredientMissingError(LookupError):
    pass


class IngredientLotInactiveIngredientError(ValueError):
    pass


class IngredientLotRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: IngredientLotDraft, *, connection: sqlite3.Connection | None = None) -> IngredientLot:
        with _connection_scope(self.config, connection) as connection:
            _ensure_active_ingredient(connection, draft.ingredient_id)
            cursor = connection.execute(
                """
                INSERT INTO ingredient_lots (
                    ingredient_id, lot_code, supplier_name, purchased_at, expires_at,
                    unit, unit_cost, total_cost, density_g_per_ml, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft.ingredient_id,
                    draft.lot_code,
                    draft.supplier_name,
                    _date_to_storage(draft.purchased_at),
                    _date_to_storage(draft.expires_at),
                    draft.unit.value,
                    _decimal_to_storage(draft.unit_cost),
                    _decimal_to_storage(draft.total_cost),
                    _density_to_storage(draft.density),
                    draft.notes,
                ),
            )
            row = connection.execute("SELECT * FROM ingredient_lots WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_lot(row)

    def get_by_id(self, lot_id: int) -> IngredientLot:
        with session(self.config) as connection:
            row = connection.execute("SELECT * FROM ingredient_lots WHERE id = ?", (lot_id,)).fetchone()
        if row is None:
            raise IngredientLotNotFoundError(f"Ingredient lot {lot_id} was not found.")
        return _row_to_lot(row)

    def list_active(self) -> list[IngredientLot]:
        with session(self.config) as connection:
            rows = connection.execute(
                "SELECT * FROM ingredient_lots WHERE is_active = 1 ORDER BY id"
            ).fetchall()
        return [_row_to_lot(row) for row in rows]

    def list_active_by_ingredient_id(self, ingredient_id: int) -> list[IngredientLot]:
        with session(self.config) as connection:
            rows = connection.execute(
                """
                SELECT * FROM ingredient_lots
                WHERE ingredient_id = ? AND is_active = 1
                ORDER BY expires_at IS NULL, expires_at, id
                """,
                (ingredient_id,),
            ).fetchall()
        return [_row_to_lot(row) for row in rows]

    def update_basic(self, lot_id: int, draft: IngredientLotDraft, *, connection: sqlite3.Connection | None = None) -> IngredientLot:
        with _connection_scope(self.config, connection) as connection:
            _ensure_active_ingredient(connection, draft.ingredient_id)
            cursor = connection.execute(
                """
                UPDATE ingredient_lots
                SET ingredient_id = ?, lot_code = ?, supplier_name = ?, purchased_at = ?, expires_at = ?,
                    unit = ?, unit_cost = ?, total_cost = ?, density_g_per_ml = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    draft.ingredient_id,
                    draft.lot_code,
                    draft.supplier_name,
                    _date_to_storage(draft.purchased_at),
                    _date_to_storage(draft.expires_at),
                    draft.unit.value,
                    _decimal_to_storage(draft.unit_cost),
                    _decimal_to_storage(draft.total_cost),
                    _density_to_storage(draft.density),
                    draft.notes,
                    lot_id,
                ),
            )
            if cursor.rowcount == 0:
                raise IngredientLotNotFoundError(f"Ingredient lot {lot_id} was not found.")
            row = connection.execute("SELECT * FROM ingredient_lots WHERE id = ?", (lot_id,)).fetchone()
        return _row_to_lot(row)

    def deactivate(self, lot_id: int, *, connection: sqlite3.Connection | None = None) -> IngredientLot:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                "UPDATE ingredient_lots SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (lot_id,),
            )
            if cursor.rowcount == 0:
                raise IngredientLotNotFoundError(f"Ingredient lot {lot_id} was not found.")
            row = connection.execute("SELECT * FROM ingredient_lots WHERE id = ?", (lot_id,)).fetchone()
        return _row_to_lot(row)


def _ensure_active_ingredient(connection, ingredient_id: int) -> None:
    row = connection.execute("SELECT is_active FROM ingredients WHERE id = ?", (ingredient_id,)).fetchone()
    if row is None:
        raise IngredientLotIngredientMissingError(f"Ingredient {ingredient_id} was not found.")
    if not bool(row["is_active"]):
        raise IngredientLotInactiveIngredientError(f"Ingredient {ingredient_id} is inactive.")


def _date_to_storage(value) -> str | None:
    return None if value is None else value.isoformat()


def _decimal_to_storage(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _density_to_storage(density: Density | None) -> str | None:
    return None if density is None else str(density.grams_per_milliliter)


def _row_to_lot(row) -> IngredientLot:
    return IngredientLot(
        id=row["id"],
        ingredient_id=row["ingredient_id"],
        lot_code=row["lot_code"],
        supplier_name=row["supplier_name"],
        purchased_at=row["purchased_at"],
        expires_at=row["expires_at"],
        unit=UnitCode(row["unit"]),
        unit_cost=None if row["unit_cost"] is None else Decimal(row["unit_cost"]),
        total_cost=None if row["total_cost"] is None else Decimal(row["total_cost"]),
        density_g_per_ml=None if row["density_g_per_ml"] is None else Decimal(row["density_g_per_ml"]),
        notes=row["notes"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
