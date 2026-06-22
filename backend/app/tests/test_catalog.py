import sqlite3
import pytest

from app.db.config import DatabaseConfig
from app.domain.catalog import CatalogCategoryDraft, CatalogTagDraft
from app.domain.errors import DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.recipes import RecipeTemplateDraft
from app.services.catalog import CatalogService
from app.services.database import initialize_database
from app.services.ingredients import IngredientService
from app.services.packaging_items import PackagingItemService
from app.services.recipes import RecipeService
from app.tests.table_guards import assert_no_forbidden_future_tables


class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")


def cfg(tmp_path):
    c = DatabaseConfig(path=tmp_path / "catalog.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def tables(c):
    with sqlite3.connect(c.path) as con:
        return {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }


def cols(c, t):
    with sqlite3.connect(c.path) as con:
        return {r[1] for r in con.execute(f"PRAGMA table_info({t})")}


def ingredient(c):
    return IngredientService(c).create_ingredient(
        IngredientDraft.create(name="Масло", category="oil", default_unit="g")
    )


def packaging(c):
    return PackagingItemService(c).create_packaging_item(
        PackagingItemDraft.create(name="Банка", kind="jar")
    )


def recipe(c):
    return RecipeService(c).create_template(
        RecipeTemplateDraft.create(name="Крем", product_type="cream")
    )


def test_migration_creates_catalog_tables_and_nullable_columns(tmp_path):
    c = cfg(tmp_path)
    ts = tables(c)
    assert {
        "catalog_categories",
        "catalog_tags",
        "ingredient_catalog_tags",
        "packaging_item_catalog_tags",
        "recipe_template_catalog_tags",
    } <= ts
    assert "catalog_category_id" in cols(c, "ingredients")
    assert "catalog_category_id" in cols(c, "packaging_items")
    assert "catalog_category_id" in cols(c, "recipe_templates")
    assert_no_forbidden_future_tables(ts)


def test_category_create_list_get_update_archive_and_cyrillic_slug(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    cat = s.create_category(
        CatalogCategoryDraft.create(scope="ingredient", name="Активные масла")
    )
    assert cat.slug.startswith("category-") and cat.is_active
    assert s.get_category(cat.id).name == "Активные масла"
    assert [x.id for x in s.list_categories("ingredient")] == [cat.id]
    updated = s.update_category(
        cat.id,
        CatalogCategoryDraft.create(scope="ingredient", name="Oils", slug="oils"),
    )
    assert updated.slug == "oils"
    archived = s.archive_category(cat.id)
    assert not archived.is_active
    assert s.list_categories("ingredient") == []


def test_tag_create_list_get_update_archive(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    tag = s.create_tag(
        CatalogTagDraft.create(
            scope="ingredient", name="Cold", slug="cold", color="#fff"
        )
    )
    assert s.get_tag(tag.id).color == "#fff"
    assert [x.id for x in s.list_tags("ingredient")] == [tag.id]
    assert (
        s.update_tag(
            tag.id,
            CatalogTagDraft.create(scope="ingredient", name="Fresh", slug="fresh"),
        ).slug
        == "fresh"
    )
    assert not s.archive_tag(tag.id).is_active


def test_reject_blank_names_invalid_scopes_and_parent_cross_scope(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    with pytest.raises(DomainValidationError):
        CatalogCategoryDraft.create(scope="ingredient", name=" ")
    with pytest.raises(DomainValidationError):
        CatalogTagDraft.create(scope="bad", name="X")
    parent = s.create_category(
        CatalogCategoryDraft.create(scope="packaging", name="Tare", slug="tare")
    )
    with pytest.raises(DomainValidationError):
        s.create_category(
            CatalogCategoryDraft.create(
                scope="ingredient", name="Oil", slug="oil", parent_id=parent.id
            )
        )


def test_duplicate_slug_rejected_within_scope_allowed_across_scopes(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    s.create_category(
        CatalogCategoryDraft.create(scope="ingredient", name="A", slug="same")
    )
    with pytest.raises(Exception):
        s.create_category(
            CatalogCategoryDraft.create(scope="ingredient", name="B", slug="same")
        )
    s.create_category(
        CatalogCategoryDraft.create(scope="packaging", name="B", slug="same")
    )


def test_ingredient_category_and_tag_assignment_validation_idempotent(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    item = ingredient(c)
    ic = s.create_category(
        CatalogCategoryDraft.create(scope="ingredient", name="Oils", slug="oils")
    )
    pc = s.create_category(
        CatalogCategoryDraft.create(scope="packaging", name="Jars", slug="jars")
    )
    s.assign_category("ingredient", item.id, ic.id)
    assert (
        scalar(c, "SELECT catalog_category_id FROM ingredients WHERE id=?", (item.id,))
        == ic.id
    )
    with pytest.raises(DomainValidationError):
        s.assign_category("ingredient", item.id, pc.id)
    t1 = s.create_tag(CatalogTagDraft.create(scope="ingredient", name="A", slug="a"))
    t2 = s.create_tag(CatalogTagDraft.create(scope="ingredient", name="B", slug="b"))
    s.replace_tags("ingredient", item.id, [t2.id, t1.id, t1.id])
    s.replace_tags("ingredient", item.id, [t1.id, t2.id])
    with sqlite3.connect(c.path) as con:
        rows = con.execute(
            "SELECT tag_id FROM ingredient_catalog_tags WHERE ingredient_id=? ORDER BY tag_id",
            (item.id,),
        ).fetchall()
    assert [r[0] for r in rows] == [t1.id, t2.id]
    s.archive_tag(t1.id)
    with pytest.raises(DomainValidationError):
        s.replace_tags("ingredient", item.id, [t1.id])


def test_packaging_and_recipe_template_assignments(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    p = packaging(c)
    r = recipe(c)
    pc = s.create_category(
        CatalogCategoryDraft.create(scope="packaging", name="Jars", slug="jars")
    )
    rc = s.create_category(
        CatalogCategoryDraft.create(scope="recipe", name="Creams", slug="creams")
    )
    pt = s.create_tag(
        CatalogTagDraft.create(scope="packaging", name="Glass", slug="glass")
    )
    rt = s.create_tag(CatalogTagDraft.create(scope="recipe", name="Face", slug="face"))
    s.assign_category("packaging", p.id, pc.id)
    s.replace_tags("packaging", p.id, [pt.id])
    s.assign_category("recipe", r.id, rc.id)
    s.replace_tags("recipe", r.id, [rt.id])
    assert (
        scalar(c, "SELECT catalog_category_id FROM packaging_items WHERE id=?", (p.id,))
        == pc.id
    )
    assert (
        scalar(
            c, "SELECT catalog_category_id FROM recipe_templates WHERE id=?", (r.id,)
        )
        == rc.id
    )


def test_audit_failure_rolls_back_category_tag_and_assignment(tmp_path):
    c = cfg(tmp_path)
    s = CatalogService(c)
    s.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        s.create_category(
            CatalogCategoryDraft.create(
                scope="ingredient", name="Rollback", slug="rollback"
            )
        )
    assert (
        scalar(c, "SELECT count(*) FROM catalog_categories WHERE slug='rollback'") == 0
    )
    with pytest.raises(RuntimeError):
        s.create_tag(
            CatalogTagDraft.create(scope="ingredient", name="Rollback", slug="rollback")
        )
    assert scalar(c, "SELECT count(*) FROM catalog_tags WHERE slug='rollback'") == 0
    ok = CatalogService(c)
    item = ingredient(c)
    cat = ok.create_category(
        CatalogCategoryDraft.create(scope="ingredient", name="Ok", slug="ok")
    )
    s.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        s.assign_category("ingredient", item.id, cat.id)
    assert (
        scalar(c, "SELECT catalog_category_id FROM ingredients WHERE id=?", (item.id,))
        is None
    )
