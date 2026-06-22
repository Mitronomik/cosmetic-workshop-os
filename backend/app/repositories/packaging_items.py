from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.packaging_items import PackagingItemDraft, PackagingKind
from app.domain.units import UnitCode
from app.models.packaging_item import PackagingItem


class PackagingItemNotFoundError(LookupError):
    pass


class PackagingItemRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(
        self, draft: PackagingItemDraft, *, connection: sqlite3.Connection | None = None
    ) -> PackagingItem:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                INSERT INTO packaging_items (
                    name, kind, unit, capacity_value, capacity_unit, material,
                    supplier_hint, unit_cost, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _draft_values(draft),
            )
            row = connection.execute(
                "SELECT * FROM packaging_items WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return _row_to_packaging_item(row)

    def get_by_id(self, packaging_item_id: int) -> PackagingItem:
        with session(self.config) as connection:
            row = connection.execute(
                "SELECT * FROM packaging_items WHERE id = ?", (packaging_item_id,)
            ).fetchone()
            tag_ids = _packaging_item_tag_ids(connection, [packaging_item_id]).get(packaging_item_id, ())
        if row is None:
            raise PackagingItemNotFoundError(
                f"Packaging item {packaging_item_id} was not found."
            )
        return _row_to_packaging_item(row, tag_ids)

    def get_by_id_for_update(
        self, item_id: int, *, connection: sqlite3.Connection
    ) -> object:
        row = connection.execute(
            "SELECT * FROM packaging_items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise PackagingItemNotFoundError(f"Item {item_id} was not found.")
        return _row_to_packaging_item(row)

    def list_active(self) -> list[PackagingItem]:
        with session(self.config) as connection:
            rows = connection.execute(
                "SELECT * FROM packaging_items WHERE is_active = 1 ORDER BY name, id"
            ).fetchall()
            tag_map = _packaging_item_tag_ids(connection, [row["id"] for row in rows])
        return [_row_to_packaging_item(row, tag_map.get(row["id"], ())) for row in rows]

    def update_basic(
        self,
        packaging_item_id: int,
        draft: PackagingItemDraft,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> PackagingItem:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                UPDATE packaging_items
                SET name = ?, kind = ?, unit = ?, capacity_value = ?, capacity_unit = ?, material = ?,
                    supplier_hint = ?, unit_cost = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*_draft_values(draft), packaging_item_id),
            )
            if cursor.rowcount == 0:
                raise PackagingItemNotFoundError(
                    f"Packaging item {packaging_item_id} was not found."
                )
            row = connection.execute(
                "SELECT * FROM packaging_items WHERE id = ?", (packaging_item_id,)
            ).fetchone()
            tag_ids = _packaging_item_tag_ids(connection, [packaging_item_id]).get(packaging_item_id, ())
        return _row_to_packaging_item(row, tag_ids)

    def deactivate(
        self, packaging_item_id: int, *, connection: sqlite3.Connection | None = None
    ) -> PackagingItem:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                "UPDATE packaging_items SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (packaging_item_id,),
            )
            if cursor.rowcount == 0:
                raise PackagingItemNotFoundError(
                    f"Packaging item {packaging_item_id} was not found."
                )
            row = connection.execute(
                "SELECT * FROM packaging_items WHERE id = ?", (packaging_item_id,)
            ).fetchone()
        return _row_to_packaging_item(row)


def _draft_values(draft: PackagingItemDraft) -> tuple:
    return (
        draft.name,
        draft.kind.value,
        draft.unit.value,
        None if draft.capacity_value is None else str(draft.capacity_value),
        None if draft.capacity_unit is None else draft.capacity_unit.value,
        draft.material,
        draft.supplier_hint,
        None if draft.unit_cost is None else str(draft.unit_cost),
        draft.notes,
    )


def _packaging_item_tag_ids(connection: sqlite3.Connection, packaging_item_ids: list[int]) -> dict[int, tuple[int, ...]]:
    if not packaging_item_ids:
        return {}
    placeholders = ",".join("?" for _ in packaging_item_ids)
    rows = connection.execute(
        f"SELECT packaging_item_id, tag_id FROM packaging_item_catalog_tags WHERE packaging_item_id IN ({placeholders}) ORDER BY packaging_item_id, tag_id",
        packaging_item_ids,
    ).fetchall()
    result: dict[int, list[int]] = {}
    for row in rows:
        result.setdefault(row["packaging_item_id"], []).append(row["tag_id"])
    return {packaging_item_id: tuple(tag_ids) for packaging_item_id, tag_ids in result.items()}


def _row_to_packaging_item(row, catalog_tag_ids: tuple[int, ...] = ()) -> PackagingItem:
    return PackagingItem(
        id=row["id"],
        name=row["name"],
        kind=PackagingKind(row["kind"]),
        unit=UnitCode(row["unit"]),
        capacity_value=(
            None if row["capacity_value"] is None else Decimal(row["capacity_value"])
        ),
        capacity_unit=(
            None if row["capacity_unit"] is None else UnitCode(row["capacity_unit"])
        ),
        material=row["material"],
        supplier_hint=row["supplier_hint"],
        unit_cost=None if row["unit_cost"] is None else Decimal(row["unit_cost"]),
        notes=row["notes"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        catalog_category_id=row["catalog_category_id"],
        catalog_tag_ids=catalog_tag_ids,
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
