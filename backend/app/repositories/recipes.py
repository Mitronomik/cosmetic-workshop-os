from contextlib import nullcontext
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.domain.units import UnitCode
from app.models.recipe import RecipeIngredient, RecipeTemplate, RecipeVersion, RecipeVersionDetail, RecipeVersionStatus


class RecipeTemplateNotFoundError(LookupError): pass
class RecipeVersionNotFoundError(LookupError): pass


class RecipeRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create_template(self, draft: RecipeTemplateDraft, *, connection: sqlite3.Connection | None = None) -> RecipeTemplate:
        with _scope(self.config, connection) as c:
            cur = c.execute("INSERT INTO recipe_templates (name, product_type, description, notes) VALUES (?, ?, ?, ?)", (draft.name, draft.product_type, draft.description, draft.notes))
            row = c.execute("SELECT * FROM recipe_templates WHERE id=?", (cur.lastrowid,)).fetchone()
            tag_ids = _template_tag_ids(c, row["id"])
        return _template(row, tag_ids)

    def get_template(self, template_id: int, *, connection: sqlite3.Connection | None = None) -> RecipeTemplate:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM recipe_templates WHERE id=?", (template_id,)).fetchone()
            tag_ids = () if row is None else _template_tag_ids(c, row["id"])
        if row is None: raise RecipeTemplateNotFoundError(f"Recipe template {template_id} was not found.")
        return _template(row, tag_ids)

    def list_templates(self) -> list[RecipeTemplate]:
        with session(self.config) as c:
            rows = c.execute("SELECT * FROM recipe_templates ORDER BY is_active DESC, name, id").fetchall()
            tags_by_template = _template_tag_ids_by_template(c, [r["id"] for r in rows])
        return [_template(r, tags_by_template.get(r["id"], ())) for r in rows]

    def deactivate_template(self, template_id: int, *, connection: sqlite3.Connection | None = None) -> RecipeTemplate:
        with _scope(self.config, connection) as c:
            cur = c.execute("UPDATE recipe_templates SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?", (template_id,))
            if cur.rowcount == 0: raise RecipeTemplateNotFoundError(f"Recipe template {template_id} was not found.")
            row = c.execute("SELECT * FROM recipe_templates WHERE id=?", (template_id,)).fetchone()
            tag_ids = _template_tag_ids(c, row["id"])
        return _template(row, tag_ids)

    def next_version_number(self, template_id: int, *, connection: sqlite3.Connection | None = None) -> int:
        with _scope(self.config, connection) as c:
            value = c.execute("SELECT COALESCE(MAX(version_number), 0) + 1 FROM recipe_versions WHERE recipe_template_id=?", (template_id,)).fetchone()[0]
        return int(value)

    def create_version(self, template_id: int, version_number: int, draft: RecipeVersionDraft, *, connection: sqlite3.Connection | None = None) -> RecipeVersion:
        with _scope(self.config, connection) as c:
            cur = c.execute("""INSERT INTO recipe_versions (recipe_template_id, version_number, status, title, target_batch_size_value, target_batch_size_unit, notes, change_note, created_from_version_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (template_id, version_number, draft.status.value, draft.title, None if draft.target_batch_size_value is None else str(draft.target_batch_size_value), None if draft.target_batch_size_unit is None else draft.target_batch_size_unit.value, draft.notes, draft.change_note, draft.created_from_version_id))
            row = c.execute("SELECT * FROM recipe_versions WHERE id=?", (cur.lastrowid,)).fetchone()
        return _version(row)

    def create_ingredient_line(self, version_id: int, draft: RecipeIngredientDraft, *, connection: sqlite3.Connection | None = None) -> RecipeIngredient:
        with _scope(self.config, connection) as c:
            cur = c.execute("""INSERT INTO recipe_ingredients (recipe_version_id, ingredient_id, position, phase, amount_value, amount_unit, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""", (version_id, draft.ingredient_id, draft.position, draft.phase, str(draft.amount_value), draft.amount_unit.value, draft.notes))
            row = c.execute("SELECT * FROM recipe_ingredients WHERE id=?", (cur.lastrowid,)).fetchone()
        return _ingredient(row)

    def get_version(self, version_id: int, *, connection: sqlite3.Connection | None = None) -> RecipeVersion:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM recipe_versions WHERE id=?", (version_id,)).fetchone()
        if row is None: raise RecipeVersionNotFoundError(f"Recipe version {version_id} was not found.")
        return _version(row)

    def list_versions_for_template(self, template_id: int) -> list[RecipeVersion]:
        with session(self.config) as c:
            rows = c.execute("SELECT * FROM recipe_versions WHERE recipe_template_id=? ORDER BY version_number, id", (template_id,)).fetchall()
        return [_version(r) for r in rows]

    def get_version_detail(self, version_id: int) -> RecipeVersionDetail:
        with session(self.config) as c:
            row = c.execute("SELECT * FROM recipe_versions WHERE id=?", (version_id,)).fetchone()
            if row is None: raise RecipeVersionNotFoundError(f"Recipe version {version_id} was not found.")
            rows = c.execute("SELECT * FROM recipe_ingredients WHERE recipe_version_id=? ORDER BY position, id", (version_id,)).fetchall()
        return RecipeVersionDetail(version=_version(row), ingredients=[_ingredient(r) for r in rows])

    def get_version_calculation_source(self, version_id: int):
        with session(self.config) as c:
            version_row = c.execute(
                """
                SELECT rv.*, rt.name AS recipe_name
                FROM recipe_versions rv
                JOIN recipe_templates rt ON rt.id = rv.recipe_template_id
                WHERE rv.id=?
                """,
                (version_id,),
            ).fetchone()
            if version_row is None:
                raise RecipeVersionNotFoundError(f"Recipe version {version_id} was not found.")
            line_rows = c.execute(
                """
                SELECT ri.*, i.name AS ingredient_name
                FROM recipe_ingredients ri
                JOIN ingredients i ON i.id = ri.ingredient_id
                WHERE ri.recipe_version_id=?
                ORDER BY ri.position, ri.id
                """,
                (version_id,),
            ).fetchall()
        return version_row, line_rows


def _template(r, tag_ids=()):
    return RecipeTemplate(r["id"], r["name"], r["product_type"], r["description"], r["notes"], bool(r["is_active"]), r["created_at"], r["updated_at"], r["catalog_category_id"], tuple(tag_ids))


def _template_tag_ids(c: sqlite3.Connection, template_id: int) -> tuple[int, ...]:
    rows = c.execute(
        "SELECT tag_id FROM recipe_template_catalog_tags WHERE recipe_template_id=? ORDER BY tag_id",
        (template_id,),
    ).fetchall()
    return tuple(int(r["tag_id"]) for r in rows)


def _template_tag_ids_by_template(c: sqlite3.Connection, template_ids: list[int]) -> dict[int, tuple[int, ...]]:
    if not template_ids:
        return {}
    placeholders = ",".join("?" for _ in template_ids)
    rows = c.execute(
        f"SELECT recipe_template_id, tag_id FROM recipe_template_catalog_tags WHERE recipe_template_id IN ({placeholders}) ORDER BY recipe_template_id, tag_id",
        template_ids,
    ).fetchall()
    result: dict[int, list[int]] = {template_id: [] for template_id in template_ids}
    for row in rows:
        result[int(row["recipe_template_id"])].append(int(row["tag_id"]))
    return {template_id: tuple(tag_ids) for template_id, tag_ids in result.items()}

def _version(r):
    return RecipeVersion(r["id"], r["recipe_template_id"], r["version_number"], RecipeVersionStatus(r["status"]), r["title"], None if r["target_batch_size_value"] is None else Decimal(r["target_batch_size_value"]), None if r["target_batch_size_unit"] is None else UnitCode(r["target_batch_size_unit"]), r["notes"], r["change_note"], r["created_from_version_id"], r["created_at"], r["updated_at"])

def _ingredient(r):
    return RecipeIngredient(r["id"], r["recipe_version_id"], r["ingredient_id"], r["position"], r["phase"], Decimal(r["amount_value"]), UnitCode(r["amount_unit"]), r["notes"], r["created_at"])

def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
