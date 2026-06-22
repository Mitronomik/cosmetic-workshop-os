from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.client_recipes import ClientRecipeDraft, ClientRecipeIngredientDraft
from app.domain.units import UnitCode
from app.models.client_recipe import ClientRecipe, ClientRecipeDetail, ClientRecipeIngredient, ClientRecipeStatus


class ClientRecipeNotFoundError(LookupError):
    pass


class ClientRecipeRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: ClientRecipeDraft, *, connection: sqlite3.Connection | None = None) -> ClientRecipe:
        with _scope(self.config, connection) as c:
            cur = c.execute(
                """
                INSERT INTO client_recipes (client_id, source_recipe_version_id, title, status, target_batch_size_value, target_batch_size_unit, personalization_notes, allergy_notes, preference_notes, contraindication_notes, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (draft.client_id, draft.source_recipe_version_id, draft.title, draft.status.value, None if draft.target_batch_size_value is None else str(draft.target_batch_size_value), None if draft.target_batch_size_unit is None else draft.target_batch_size_unit.value, draft.personalization_notes, draft.allergy_notes, draft.preference_notes, draft.contraindication_notes, draft.notes),
            )
            row = c.execute("SELECT * FROM client_recipes WHERE id=?", (cur.lastrowid,)).fetchone()
        return _recipe(row)

    def create_ingredient_line(self, client_recipe_id: int, draft: ClientRecipeIngredientDraft, *, connection: sqlite3.Connection | None = None) -> ClientRecipeIngredient:
        with _scope(self.config, connection) as c:
            cur = c.execute(
                """
                INSERT INTO client_recipe_ingredients (client_recipe_id, ingredient_id, source_recipe_ingredient_id, position, phase, amount_value, amount_unit, personalization_note, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (client_recipe_id, draft.ingredient_id, draft.source_recipe_ingredient_id, draft.position, draft.phase, str(draft.amount_value), draft.amount_unit.value, draft.personalization_note, draft.notes),
            )
            row = c.execute("SELECT * FROM client_recipe_ingredients WHERE id=?", (cur.lastrowid,)).fetchone()
        return _ingredient(row)

    def get_detail(self, client_recipe_id: int, *, connection: sqlite3.Connection | None = None) -> ClientRecipeDetail:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM client_recipes WHERE id=?", (client_recipe_id,)).fetchone()
            if row is None:
                raise ClientRecipeNotFoundError(f"Client recipe {client_recipe_id} was not found.")
            rows = c.execute("SELECT * FROM client_recipe_ingredients WHERE client_recipe_id=? ORDER BY position, id", (client_recipe_id,)).fetchall()
        return ClientRecipeDetail(client_recipe=_recipe(row), ingredients=[_ingredient(r) for r in rows])

    def list_recipes(self, *, include_inactive: bool = True) -> list[ClientRecipe]:
        with session(self.config) as c:
            if include_inactive:
                rows = c.execute("SELECT * FROM client_recipes ORDER BY is_active DESC, updated_at DESC, id DESC").fetchall()
            else:
                rows = c.execute("SELECT * FROM client_recipes WHERE is_active=1 ORDER BY updated_at DESC, id DESC").fetchall()
        return [_recipe(r) for r in rows]

    def list_for_client(self, client_id: int, *, include_inactive: bool = True) -> list[ClientRecipe]:
        with session(self.config) as c:
            if include_inactive:
                rows = c.execute("SELECT * FROM client_recipes WHERE client_id=? ORDER BY is_active DESC, updated_at DESC, id DESC", (client_id,)).fetchall()
            else:
                rows = c.execute("SELECT * FROM client_recipes WHERE client_id=? AND is_active=1 ORDER BY updated_at DESC, id DESC", (client_id,)).fetchall()
        return [_recipe(r) for r in rows]

    def deactivate(self, client_recipe_id: int, *, connection: sqlite3.Connection | None = None) -> ClientRecipe:
        with _scope(self.config, connection) as c:
            cur = c.execute("UPDATE client_recipes SET is_active=0, status='archived', updated_at=CURRENT_TIMESTAMP WHERE id=?", (client_recipe_id,))
            if cur.rowcount == 0:
                raise ClientRecipeNotFoundError(f"Client recipe {client_recipe_id} was not found.")
            row = c.execute("SELECT * FROM client_recipes WHERE id=?", (client_recipe_id,)).fetchone()
        return _recipe(row)


def _recipe(r) -> ClientRecipe:
    return ClientRecipe(r["id"], r["client_id"], r["source_recipe_version_id"], r["title"], ClientRecipeStatus(r["status"]), None if r["target_batch_size_value"] is None else Decimal(r["target_batch_size_value"]), None if r["target_batch_size_unit"] is None else UnitCode(r["target_batch_size_unit"]), r["personalization_notes"], r["allergy_notes"], r["preference_notes"], r["contraindication_notes"], r["notes"], bool(r["is_active"]), r["created_at"], r["updated_at"])


def _ingredient(r) -> ClientRecipeIngredient:
    return ClientRecipeIngredient(r["id"], r["client_recipe_id"], r["ingredient_id"], r["source_recipe_ingredient_id"], r["position"], r["phase"], Decimal(r["amount_value"]), UnitCode(r["amount_unit"]), r["personalization_note"], r["notes"], r["created_at"])


def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
