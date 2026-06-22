from contextlib import nullcontext
import sqlite3
from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.catalog import CatalogCategoryDraft, CatalogTagDraft
from app.models.catalog import CatalogCategory, CatalogScope, CatalogTag


class CatalogCategoryNotFoundError(LookupError):
    pass


class CatalogTagNotFoundError(LookupError):
    pass


class CatalogDuplicateSlugError(ValueError):
    pass


class CatalogRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create_category(self, draft: CatalogCategoryDraft, *, connection=None):
        with _scope(self.config, connection) as c:
            try:
                cur = c.execute(
                    "INSERT INTO catalog_categories (scope,parent_id,name,slug,sort_order) VALUES (?,?,?,?,?)",
                    (
                        draft.scope.value,
                        draft.parent_id,
                        draft.name,
                        draft.slug,
                        draft.sort_order,
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise CatalogDuplicateSlugError("Duplicate category slug.") from e
            row = c.execute(
                "SELECT * FROM catalog_categories WHERE id=?", (cur.lastrowid,)
            ).fetchone()
        return _cat(row)

    def update_category(self, id: int, draft: CatalogCategoryDraft, *, connection=None):
        with _scope(self.config, connection) as c:
            old = c.execute(
                "SELECT * FROM catalog_categories WHERE id=?", (id,)
            ).fetchone()
            if old is None:
                raise CatalogCategoryNotFoundError()
            if old["is_system"]:
                raise ValueError("System category cannot be edited.")
            try:
                cur = c.execute(
                    "UPDATE catalog_categories SET scope=?, parent_id=?, name=?, slug=?, sort_order=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (
                        draft.scope.value,
                        draft.parent_id,
                        draft.name,
                        draft.slug,
                        draft.sort_order,
                        id,
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise CatalogDuplicateSlugError("Duplicate category slug.") from e
            row = c.execute(
                "SELECT * FROM catalog_categories WHERE id=?", (id,)
            ).fetchone()
        return _cat(row)

    def get_category(self, id: int, *, connection=None):
        with _scope(self.config, connection) as c:
            row = c.execute(
                "SELECT * FROM catalog_categories WHERE id=?", (id,)
            ).fetchone()
        if row is None:
            raise CatalogCategoryNotFoundError()
        return _cat(row)

    def list_categories(self, scope: CatalogScope, include_inactive=False):
        sql = (
            "SELECT * FROM catalog_categories WHERE scope=?"
            + ("" if include_inactive else " AND is_active=1")
            + " ORDER BY sort_order,name,id"
        )
        with session(self.config) as c:
            rows = c.execute(sql, (scope.value,)).fetchall()
        return [_cat(r) for r in rows]

    def archive_category(self, id: int, *, connection=None):
        with _scope(self.config, connection) as c:
            row = c.execute(
                "SELECT * FROM catalog_categories WHERE id=?", (id,)
            ).fetchone()
            if row is None:
                raise CatalogCategoryNotFoundError()
            if row["is_system"]:
                raise ValueError("System category cannot be archived.")
            c.execute(
                "UPDATE catalog_categories SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (id,),
            )
            row = c.execute(
                "SELECT * FROM catalog_categories WHERE id=?", (id,)
            ).fetchone()
        return _cat(row)

    def create_tag(self, draft: CatalogTagDraft, *, connection=None):
        with _scope(self.config, connection) as c:
            try:
                cur = c.execute(
                    "INSERT INTO catalog_tags (scope,name,slug,color) VALUES (?,?,?,?)",
                    (draft.scope.value, draft.name, draft.slug, draft.color),
                )
            except sqlite3.IntegrityError as e:
                raise CatalogDuplicateSlugError("Duplicate tag slug.") from e
            row = c.execute(
                "SELECT * FROM catalog_tags WHERE id=?", (cur.lastrowid,)
            ).fetchone()
        return _tag(row)

    def update_tag(self, id: int, draft: CatalogTagDraft, *, connection=None):
        with _scope(self.config, connection) as c:
            if (
                c.execute("SELECT 1 FROM catalog_tags WHERE id=?", (id,)).fetchone()
                is None
            ):
                raise CatalogTagNotFoundError()
            try:
                c.execute(
                    "UPDATE catalog_tags SET scope=?, name=?, slug=?, color=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (draft.scope.value, draft.name, draft.slug, draft.color, id),
                )
            except sqlite3.IntegrityError as e:
                raise CatalogDuplicateSlugError("Duplicate tag slug.") from e
            row = c.execute("SELECT * FROM catalog_tags WHERE id=?", (id,)).fetchone()
        return _tag(row)

    def get_tag(self, id: int, *, connection=None):
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM catalog_tags WHERE id=?", (id,)).fetchone()
        if row is None:
            raise CatalogTagNotFoundError()
        return _tag(row)

    def list_tags(self, scope: CatalogScope, include_inactive=False):
        sql = (
            "SELECT * FROM catalog_tags WHERE scope=?"
            + ("" if include_inactive else " AND is_active=1")
            + " ORDER BY name,id"
        )
        with session(self.config) as c:
            rows = c.execute(sql, (scope.value,)).fetchall()
        return [_tag(r) for r in rows]

    def archive_tag(self, id: int, *, connection=None):
        with _scope(self.config, connection) as c:
            if (
                c.execute("SELECT 1 FROM catalog_tags WHERE id=?", (id,)).fetchone()
                is None
            ):
                raise CatalogTagNotFoundError()
            c.execute(
                "UPDATE catalog_tags SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (id,),
            )
            row = c.execute("SELECT * FROM catalog_tags WHERE id=?", (id,)).fetchone()
        return _tag(row)

    def assign_category(
        self,
        table: str,
        id_col: str,
        item_id: int,
        category_id: int | None,
        *,
        connection=None,
    ):
        with _scope(self.config, connection) as c:
            cur = c.execute(
                f"UPDATE {table} SET catalog_category_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (category_id, item_id),
            )
            if cur.rowcount == 0:
                raise LookupError("Item not found")

    def replace_tags(
        self,
        table: str,
        id_col: str,
        item_id: int,
        tag_ids: list[int],
        *,
        connection=None,
    ):
        with _scope(self.config, connection) as c:
            c.execute(f"DELETE FROM {table} WHERE {id_col}=?", (item_id,))
            c.executemany(
                f"INSERT INTO {table} ({id_col}, tag_id) VALUES (?,?)",
                [(item_id, t) for t in sorted(set(tag_ids))],
            )


def _cat(r):
    return CatalogCategory(
        r["id"],
        CatalogScope(r["scope"]),
        r["parent_id"],
        r["name"],
        r["slug"],
        r["sort_order"],
        bool(r["is_system"]),
        bool(r["is_active"]),
        r["created_at"],
        r["updated_at"],
    )


def _tag(r):
    return CatalogTag(
        r["id"],
        CatalogScope(r["scope"]),
        r["name"],
        r["slug"],
        r["color"],
        bool(r["is_active"]),
        r["created_at"],
        r["updated_at"],
    )


def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
