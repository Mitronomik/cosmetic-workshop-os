from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.orders import OrderDraft
from app.domain.units import UnitCode
from app.models.order import Order, OrderStatus


class OrderNotFoundError(LookupError):
    pass


class OrderRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: OrderDraft, *, connection: sqlite3.Connection | None = None) -> Order:
        with _scope(self.config, connection) as c:
            cur = c.execute(
                """
                INSERT INTO orders (client_id, recipe_version_id, client_recipe_id, product_name, target_batch_size_value, target_batch_size_unit, packaging_item_id, packaging_quantity, status, sale_price, ordered_at, planned_production_at, produced_at, delivered_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _values(draft),
            )
            row = c.execute("SELECT * FROM orders WHERE id=?", (cur.lastrowid,)).fetchone()
        return _order(row)

    def get_by_id(self, order_id: int, *, connection: sqlite3.Connection | None = None) -> Order:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise OrderNotFoundError(f"Order {order_id} was not found.")
        return _order(row)

    def list_orders(self, *, include_inactive: bool = True, status: OrderStatus | str | None = None, client_id: int | None = None) -> list[Order]:
        clauses=[]; params=[]
        if not include_inactive: clauses.append("is_active=1")
        if status is not None: clauses.append("status=?"); params.append(status.value if isinstance(status, OrderStatus) else str(status))
        if client_id is not None: clauses.append("client_id=?"); params.append(client_id)
        sql="SELECT * FROM orders" + (" WHERE "+" AND ".join(clauses) if clauses else "") + " ORDER BY is_active DESC, updated_at DESC, id DESC"
        with session(self.config) as c:
            rows=c.execute(sql, tuple(params)).fetchall()
        return [_order(r) for r in rows]

    def update(self, order_id: int, draft: OrderDraft, *, connection: sqlite3.Connection | None = None) -> Order:
        with _scope(self.config, connection) as c:
            cur=c.execute("""
                UPDATE orders SET client_id=?, recipe_version_id=?, client_recipe_id=?, product_name=?, target_batch_size_value=?, target_batch_size_unit=?, packaging_item_id=?, packaging_quantity=?, status=?, sale_price=?, ordered_at=?, planned_production_at=?, produced_at=?, delivered_at=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            """, (*_values(draft), order_id))
            if cur.rowcount == 0: raise OrderNotFoundError(f"Order {order_id} was not found.")
            row=c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return _order(row)

    def cancel(self, order_id:int, *, connection: sqlite3.Connection | None=None) -> Order:
        with _scope(self.config, connection) as c:
            cur=c.execute("UPDATE orders SET status='cancelled', updated_at=CURRENT_TIMESTAMP WHERE id=?", (order_id,))
            if cur.rowcount == 0: raise OrderNotFoundError(f"Order {order_id} was not found.")
            row=c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return _order(row)

    def archive(self, order_id:int, *, connection: sqlite3.Connection | None=None) -> Order:
        with _scope(self.config, connection) as c:
            cur=c.execute("UPDATE orders SET is_active=0, status='archived', updated_at=CURRENT_TIMESTAMP WHERE id=?", (order_id,))
            if cur.rowcount == 0: raise OrderNotFoundError(f"Order {order_id} was not found.")
            row=c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return _order(row)


def _values(d: OrderDraft):
    return (d.client_id, d.recipe_version_id, d.client_recipe_id, d.product_name, str(d.target_batch_size_value), d.target_batch_size_unit.value, d.packaging_item_id, None if d.packaging_quantity is None else str(d.packaging_quantity), d.status.value, None if d.sale_price is None else str(d.sale_price), d.ordered_at, d.planned_production_at, d.produced_at, d.delivered_at, d.notes)


def _order(r) -> Order:
    return Order(r["id"], r["client_id"], r["recipe_version_id"], r["client_recipe_id"], r["product_name"], Decimal(r["target_batch_size_value"]), UnitCode(r["target_batch_size_unit"]), r["packaging_item_id"], None if r["packaging_quantity"] is None else Decimal(r["packaging_quantity"]), OrderStatus(r["status"]), None if r["sale_price"] is None else Decimal(r["sale_price"]), r["ordered_at"], r["planned_production_at"], r["produced_at"], r["delivered_at"], r["notes"], bool(r["is_active"]), r["created_at"], r["updated_at"])


def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
