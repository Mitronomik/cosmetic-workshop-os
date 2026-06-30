from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.units import UnitCode
from app.models.production_batch import ProductionBatch, ProductionBatchDetail, ProductionBatchIngredient, ProductionBatchListItem, ProductionBatchPackaging


class ProductionBatchAlreadyExistsError(ValueError):
    pass


class ProductionBatchNotFoundError(LookupError):
    pass


class ProductionBatchRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create_batch(self, *, connection: sqlite3.Connection, order_id: int, recipe_version_id: int | None, client_recipe_id: int | None, final_batch_value: Decimal, final_batch_unit: UnitCode, component_cost: Decimal | None, packaging_cost: Decimal | None, other_cost: Decimal, total_cost: Decimal | None, sale_price: Decimal | None, tax: Decimal | None, margin: Decimal | None, margin_percent: Decimal | None, notes: str) -> ProductionBatch:
        try:
            cur = connection.execute(
                """
                INSERT INTO production_batches (order_id, recipe_version_id, client_recipe_id, final_batch_value, final_batch_unit, component_cost, packaging_cost, other_cost, total_cost, sale_price, tax, margin, margin_percent, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, recipe_version_id, client_recipe_id, str(final_batch_value), final_batch_unit.value, _d(component_cost), _d(packaging_cost), _d(other_cost), _d(total_cost), _d(sale_price), _d(tax), _d(margin), _d(margin_percent), notes or ""),
            )
        except sqlite3.IntegrityError as exc:
            raise ProductionBatchAlreadyExistsError("Для этого заказа уже есть производственная партия.") from exc
        return _batch(connection.execute("SELECT * FROM production_batches WHERE id=?", (cur.lastrowid,)).fetchone())

    def create_ingredient(self, *, connection: sqlite3.Connection, production_batch_id: int, ingredient_id: int, ingredient_lot_id: int, ingredient_name_snapshot: str, lot_code_snapshot: str, required_quantity: Decimal, consumed_quantity: Decimal, unit: UnitCode, unit_cost_snapshot: Decimal | None, total_cost_snapshot: Decimal | None, expiration_date_snapshot: str | None) -> ProductionBatchIngredient:
        cur = connection.execute(
            """
            INSERT INTO production_batch_ingredients (production_batch_id, ingredient_id, ingredient_lot_id, ingredient_name_snapshot, lot_code_snapshot, required_quantity, consumed_quantity, unit, unit_cost_snapshot, total_cost_snapshot, expiration_date_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (production_batch_id, ingredient_id, ingredient_lot_id, ingredient_name_snapshot, lot_code_snapshot or "", str(required_quantity), str(consumed_quantity), unit.value, _d(unit_cost_snapshot), _d(total_cost_snapshot), expiration_date_snapshot),
        )
        return _ingredient(connection.execute("SELECT * FROM production_batch_ingredients WHERE id=?", (cur.lastrowid,)).fetchone())

    def create_packaging(self, *, connection: sqlite3.Connection, production_batch_id: int, packaging_item_id: int, packaging_name_snapshot: str, quantity: Decimal, unit: UnitCode, unit_cost_snapshot: Decimal | None, total_cost_snapshot: Decimal | None) -> ProductionBatchPackaging:
        cur = connection.execute(
            """
            INSERT INTO production_batch_packaging (production_batch_id, packaging_item_id, packaging_name_snapshot, quantity, unit, unit_cost_snapshot, total_cost_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (production_batch_id, packaging_item_id, packaging_name_snapshot, str(quantity), unit.value, _d(unit_cost_snapshot), _d(total_cost_snapshot)),
        )
        return _packaging(connection.execute("SELECT * FROM production_batch_packaging WHERE id=?", (cur.lastrowid,)).fetchone())

    def exists_for_order(self, order_id: int, *, connection: sqlite3.Connection) -> bool:
        return connection.execute("SELECT 1 FROM production_batches WHERE order_id=?", (order_id,)).fetchone() is not None

    def list_batches(self, *, limit: int = 50, offset: int = 0) -> list[ProductionBatchListItem]:
        with session(self.config) as connection:
            rows = connection.execute(
                """
                SELECT pb.*, o.product_name, o.client_id, c.full_name AS client_name,
                       (SELECT COUNT(*) FROM production_batch_ingredients pbi WHERE pbi.production_batch_id = pb.id) AS ingredient_line_count,
                       (SELECT COUNT(*) FROM production_batch_packaging pbp WHERE pbp.production_batch_id = pb.id) AS packaging_line_count
                FROM production_batches pb
                JOIN orders o ON o.id = pb.order_id
                LEFT JOIN clients c ON c.id = o.client_id
                ORDER BY pb.produced_at DESC, pb.id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [_list_item(r) for r in rows]

    def get_detail(self, batch_id: int, *, connection: sqlite3.Connection | None = None) -> ProductionBatchDetail:
        if connection is None:
            with session(self.config) as c:
                return self.get_detail(batch_id, connection=c)
        row = connection.execute(
            """
            SELECT pb.*, o.product_name, o.client_id, c.full_name AS client_name
            FROM production_batches pb
            JOIN orders o ON o.id = pb.order_id
            LEFT JOIN clients c ON c.id = o.client_id
            WHERE pb.id=?
            """,
            (batch_id,),
        ).fetchone()
        if row is None:
            raise ProductionBatchNotFoundError(f"Production batch {batch_id} was not found.")
        batch = _batch(row)
        ingredients = [_ingredient(r) for r in connection.execute("SELECT * FROM production_batch_ingredients WHERE production_batch_id=? ORDER BY id", (batch_id,)).fetchall()]
        packaging = [_packaging(r) for r in connection.execute("SELECT * FROM production_batch_packaging WHERE production_batch_id=? ORDER BY id", (batch_id,)).fetchall()]
        return ProductionBatchDetail(batch=batch, ingredients=ingredients, packaging=packaging, product_name=row["product_name"], client_id=row["client_id"], client_name=row["client_name"])

    def get_detail_by_order_id(self, order_id: int, *, connection: sqlite3.Connection | None = None) -> ProductionBatchDetail:
        if connection is None:
            with session(self.config) as c:
                return self.get_detail_by_order_id(order_id, connection=c)
        row = connection.execute("SELECT id FROM production_batches WHERE order_id=?", (order_id,)).fetchone()
        if row is None:
            raise ProductionBatchNotFoundError(f"Production batch for order {order_id} was not found.")
        return self.get_detail(row["id"], connection=connection)


def _d(v): return None if v is None else str(v)
def _dec(v): return None if v is None else Decimal(v)

def _batch(r):
    return ProductionBatch(r["id"], r["order_id"], r["recipe_version_id"], r["client_recipe_id"], Decimal(r["final_batch_value"]), UnitCode(r["final_batch_unit"]), _dec(r["component_cost"]), _dec(r["packaging_cost"]), Decimal(r["other_cost"]), _dec(r["total_cost"]), _dec(r["sale_price"]), _dec(r["tax"]), _dec(r["margin"]), _dec(r["margin_percent"]), r["produced_at"], r["notes"], r["created_at"])

def _ingredient(r):
    return ProductionBatchIngredient(r["id"], r["production_batch_id"], r["ingredient_id"], r["ingredient_lot_id"], r["ingredient_name_snapshot"], r["lot_code_snapshot"], Decimal(r["required_quantity"]), Decimal(r["consumed_quantity"]), UnitCode(r["unit"]), _dec(r["unit_cost_snapshot"]), _dec(r["total_cost_snapshot"]), r["expiration_date_snapshot"], r["created_at"])

def _packaging(r):
    return ProductionBatchPackaging(r["id"], r["production_batch_id"], r["packaging_item_id"], r["packaging_name_snapshot"], Decimal(r["quantity"]), UnitCode(r["unit"]), _dec(r["unit_cost_snapshot"]), _dec(r["total_cost_snapshot"]), r["created_at"])


def _list_item(r):
    return ProductionBatchListItem(r["id"], r["order_id"], r["product_name"], r["client_id"], r["client_name"], r["recipe_version_id"], r["client_recipe_id"], Decimal(r["final_batch_value"]), UnitCode(r["final_batch_unit"]), _dec(r["total_cost"]), _dec(r["sale_price"]), _dec(r["tax"]), _dec(r["margin"]), _dec(r["margin_percent"]), r["produced_at"], int(r["ingredient_line_count"]), int(r["packaging_line_count"]), r["notes"])
