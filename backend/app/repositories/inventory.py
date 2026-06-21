import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.packaging_items import PACKAGING_KIND_RUSSIAN_LABELS, PackagingKind


class InventoryRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def list_ingredient_lots(self) -> list[sqlite3.Row]:
        with session(self.config) as connection:
            return connection.execute(
                """
                SELECT
                    lots.id AS lot_id,
                    lots.ingredient_id,
                    ingredients.name AS ingredient_name,
                    lots.lot_code,
                    lots.supplier_name AS supplier,
                    lots.unit,
                    lots.purchased_at AS purchase_date,
                    lots.expires_at AS expiration_date,
                    lots.is_active,
                    lots.created_at,
                    lots.updated_at,
                    lots.unit_cost AS cost_per_unit,
                    lots.density_g_per_ml AS density_value
                FROM ingredient_lots AS lots
                JOIN ingredients ON ingredients.id = lots.ingredient_id
                ORDER BY ingredients.name ASC, lots.expires_at IS NULL ASC, lots.expires_at ASC, lots.id ASC
                """
            ).fetchall()

    def list_stock_movement_quantities(self) -> list[sqlite3.Row]:
        with session(self.config) as connection:
            return connection.execute("SELECT ingredient_lot_id, quantity, direction FROM stock_movements ORDER BY created_at, id").fetchall()

    def list_packaging_items(self) -> list[sqlite3.Row]:
        with session(self.config) as connection:
            return connection.execute(
                """
                SELECT
                    id AS packaging_item_id,
                    name,
                    kind,
                    unit,
                    capacity_value,
                    capacity_unit,
                    material,
                    supplier_hint,
                    unit_cost,
                    notes,
                    is_active,
                    created_at,
                    updated_at
                FROM packaging_items
                ORDER BY name ASC, id ASC
                """
            ).fetchall()

    def list_packaging_movement_quantities(self) -> list[sqlite3.Row]:
        with session(self.config) as connection:
            return connection.execute("SELECT packaging_item_id, quantity, direction FROM packaging_stock_movements ORDER BY created_at, id").fetchall()


def packaging_kind_label(kind_value: str) -> str:
    kind = PackagingKind(kind_value)
    return PACKAGING_KIND_RUSSIAN_LABELS[kind]
