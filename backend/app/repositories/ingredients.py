from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.ingredients import IngredientCategory, IngredientDraft
from app.domain.measurements import Density
from app.domain.units import UnitCode
from app.models.ingredient import Ingredient


class IngredientNotFoundError(LookupError):
    pass


class IngredientRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(
        self, draft: IngredientDraft, *, connection: sqlite3.Connection | None = None
    ) -> Ingredient:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                INSERT INTO ingredients (
                    name, category, default_unit, density_g_per_ml, notes,
                    inci_name, supplier_hint, allergen_note, usage_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft.name,
                    draft.category.value,
                    draft.default_unit.value,
                    _density_to_storage(draft.density),
                    draft.notes,
                    draft.inci_name,
                    draft.supplier_hint,
                    draft.allergen_note,
                    draft.usage_note,
                ),
            )
            row = connection.execute(
                "SELECT * FROM ingredients WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return _row_to_ingredient(row)

    def get_by_id(self, ingredient_id: int) -> Ingredient:
        with session(self.config) as connection:
            row = connection.execute(
                "SELECT * FROM ingredients WHERE id = ?", (ingredient_id,)
            ).fetchone()
            if row is None:
                raise IngredientNotFoundError(f"Ingredient {ingredient_id} was not found.")
            tag_ids = _ingredient_tag_ids(connection, [ingredient_id]).get(ingredient_id, ())
        return _row_to_ingredient(row, tag_ids)

    def get_by_id_for_update(
        self, item_id: int, *, connection: sqlite3.Connection
    ) -> object:
        row = connection.execute(
            "SELECT * FROM ingredients WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise IngredientNotFoundError(f"Item {item_id} was not found.")
        return _row_to_ingredient(row)

    def list_active(self) -> list[Ingredient]:
        with session(self.config) as connection:
            rows = connection.execute(
                "SELECT * FROM ingredients WHERE is_active = 1 ORDER BY name, id"
            ).fetchall()
            tag_map = _ingredient_tag_ids(connection, [row["id"] for row in rows])
        return [_row_to_ingredient(row, tag_map.get(row["id"], ())) for row in rows]

    def update_basic(
        self,
        ingredient_id: int,
        draft: IngredientDraft,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> Ingredient:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                UPDATE ingredients
                SET name = ?, category = ?, default_unit = ?, density_g_per_ml = ?, notes = ?,
                    inci_name = ?, supplier_hint = ?, allergen_note = ?, usage_note = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    draft.name,
                    draft.category.value,
                    draft.default_unit.value,
                    _density_to_storage(draft.density),
                    draft.notes,
                    draft.inci_name,
                    draft.supplier_hint,
                    draft.allergen_note,
                    draft.usage_note,
                    ingredient_id,
                ),
            )
            if cursor.rowcount == 0:
                raise IngredientNotFoundError(
                    f"Ingredient {ingredient_id} was not found."
                )
            row = connection.execute(
                "SELECT * FROM ingredients WHERE id = ?", (ingredient_id,)
            ).fetchone()
        return _row_to_ingredient(row)

    def deactivate(
        self, ingredient_id: int, *, connection: sqlite3.Connection | None = None
    ) -> Ingredient:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                "UPDATE ingredients SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (ingredient_id,),
            )
            if cursor.rowcount == 0:
                raise IngredientNotFoundError(
                    f"Ingredient {ingredient_id} was not found."
                )
            row = connection.execute(
                "SELECT * FROM ingredients WHERE id = ?", (ingredient_id,)
            ).fetchone()
        return _row_to_ingredient(row)


def _density_to_storage(density: Density | None) -> str | None:
    return None if density is None else str(density.grams_per_milliliter)


def _ingredient_tag_ids(connection: sqlite3.Connection, ingredient_ids: list[int]) -> dict[int, tuple[int, ...]]:
    if not ingredient_ids:
        return {}
    placeholders = ",".join("?" for _ in ingredient_ids)
    rows = connection.execute(
        f"SELECT ingredient_id, tag_id FROM ingredient_catalog_tags WHERE ingredient_id IN ({placeholders}) ORDER BY ingredient_id, tag_id",
        ingredient_ids,
    ).fetchall()
    result: dict[int, list[int]] = {}
    for row in rows:
        result.setdefault(row["ingredient_id"], []).append(row["tag_id"])
    return {ingredient_id: tuple(tag_ids) for ingredient_id, tag_ids in result.items()}


def _row_to_ingredient(row, catalog_tag_ids: tuple[int, ...] = ()) -> Ingredient:
    return Ingredient(
        id=row["id"],
        name=row["name"],
        category=IngredientCategory(row["category"]),
        default_unit=UnitCode(row["default_unit"]),
        density_g_per_ml=(
            None
            if row["density_g_per_ml"] is None
            else Decimal(row["density_g_per_ml"])
        ),
        is_active=bool(row["is_active"]),
        notes=row["notes"],
        inci_name=row["inci_name"],
        supplier_hint=row["supplier_hint"],
        allergen_note=row["allergen_note"],
        usage_note=row["usage_note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        catalog_category_id=row["catalog_category_id"],
        catalog_tag_ids=catalog_tag_ids,
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
