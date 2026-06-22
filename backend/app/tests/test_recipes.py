import sqlite3
import pytest

from app.db.config import DatabaseConfig
from app.domain.errors import DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.services.database import initialize_database
from app.services.ingredients import IngredientService
from app.services.recipes import RecipeIngredientInactiveError, RecipeService, RecipeTemplateInactiveError
from app.tests.table_guards import CURRENT_ALLOWED_TABLES, FORBIDDEN_FUTURE_TABLES, assert_no_forbidden_future_tables, assert_only_current_tables

class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")

def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "recipes.sqlite")
    initialize_database(c)
    return c

def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]

def tables(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def ingredient(c, name="Oil"):
    return IngredientService(c).create_ingredient(IngredientDraft.create(name=name, category="oil", default_unit="g"))

def template(c):
    return RecipeService(c).create_template(RecipeTemplateDraft.create(name="  Base cream  ", description="  good   cream  "))

def line(ingredient_id, position=1, amount="10", unit="percent", phase=" water  phase ", notes=" note  text "):
    return RecipeIngredientDraft.create(ingredient_id=ingredient_id, position=position, amount_value=amount, amount_unit=unit, phase=phase, notes=notes)

def test_migration_table_scope_and_guards(tmp_path):
    c = config(tmp_path)
    names = tables(c)
    assert {"recipe_templates", "recipe_versions", "recipe_ingredients"} <= names
    assert "recipe_templates" in CURRENT_ALLOWED_TABLES
    assert "recipe_versions" in CURRENT_ALLOWED_TABLES
    assert "recipe_ingredients" in CURRENT_ALLOWED_TABLES
    assert_no_forbidden_future_tables(names)
    assert_only_current_tables(names)
    assert {"client_recipes", "orders", "production_batches", "import_sources", "import_drafts"}.isdisjoint(names)
    assert "client_recipes" in FORBIDDEN_FUTURE_TABLES

def test_template_create_get_list_deactivate_and_empty_name(tmp_path):
    c = config(tmp_path)
    service = RecipeService(c)
    t = service.create_template(RecipeTemplateDraft.create(name="  Cream  ", notes=" note  here "))
    assert t.name == "Cream"
    assert t.notes == "note here"
    assert service.get_template(t.id).id == t.id
    assert [x.id for x in service.list_templates()] == [t.id]
    deactivated = service.deactivate_template(t.id)
    assert deactivated.is_active is False
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action='recipe_template.deactivated'") == 1
    with pytest.raises(DomainValidationError):
        RecipeTemplateDraft.create(name=" ")

def test_version_numbers_list_detail_and_batch_validation(tmp_path):
    c = config(tmp_path)
    ing = ingredient(c)
    t = template(c)
    service = RecipeService(c)
    v1 = service.create_version(t.id, RecipeVersionDraft.create(title=" first ", target_batch_size_value="100.5", target_batch_size_unit="g", ingredients=[line(ing.id)]) )
    v2 = service.create_version(t.id, RecipeVersionDraft.create(target_batch_size_value=2, target_batch_size_unit="pcs", ingredients=[line(ing.id, position=1, amount="5", unit="g")]))
    assert v1.version.version_number == 1
    assert v1.version.title == "first"
    assert v1.version.target_batch_size_value is not None
    assert v2.version.version_number == 2
    assert [v.version_number for v in service.list_versions_for_template(t.id)] == [1, 2]
    detail = service.get_version_detail(v1.version.id)
    assert [(x.position, x.phase, x.notes) for x in detail.ingredients] == [(1, "water phase", "note text")]
    with pytest.raises(DomainValidationError):
        RecipeVersionDraft.create(target_batch_size_value=1.2, target_batch_size_unit="g")
    with pytest.raises(DomainValidationError):
        RecipeVersionDraft.create(target_batch_size_value="10", target_batch_size_unit="percent")

def test_invalid_template_and_inactive_template_rejected(tmp_path):
    c = config(tmp_path)
    ing = ingredient(c)
    service = RecipeService(c)
    with pytest.raises(LookupError):
        service.create_version(999, RecipeVersionDraft.create(ingredients=[line(ing.id)]))
    t = template(c)
    service.deactivate_template(t.id)
    with pytest.raises(RecipeTemplateInactiveError):
        service.create_version(t.id, RecipeVersionDraft.create(ingredients=[line(ing.id)]))

def test_created_from_version_same_template_succeeds(tmp_path):
    c = config(tmp_path)
    ing = ingredient(c)
    t = template(c)
    service = RecipeService(c)
    v1 = service.create_version(t.id, RecipeVersionDraft.create(ingredients=[line(ing.id)]))
    v2 = service.create_version(
        t.id,
        RecipeVersionDraft.create(created_from_version_id=v1.version.id, ingredients=[line(ing.id)]),
    )
    assert v2.version.version_number == 2
    assert v2.version.created_from_version_id == v1.version.id
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action='recipe_version.created'") == 2


def test_created_from_version_non_existing_rejected_without_version_or_audit(tmp_path):
    c = config(tmp_path)
    ing = ingredient(c)
    t = template(c)
    before_audit = scalar(c, "SELECT count(*) FROM audit_logs")
    with pytest.raises(LookupError):
        RecipeService(c).create_version(
            t.id,
            RecipeVersionDraft.create(created_from_version_id=999, ingredients=[line(ing.id)]),
        )
    assert scalar(c, "SELECT count(*) FROM recipe_versions") == 0
    assert scalar(c, "SELECT count(*) FROM recipe_ingredients") == 0
    assert scalar(c, "SELECT count(*) FROM audit_logs") == before_audit


def test_created_from_version_cross_template_rejected_without_version_or_audit(tmp_path):
    c = config(tmp_path)
    ing = ingredient(c)
    t1 = template(c)
    t2 = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Second recipe"))
    service = RecipeService(c)
    source = service.create_version(t1.id, RecipeVersionDraft.create(ingredients=[line(ing.id)]))
    before_versions = scalar(c, "SELECT count(*) FROM recipe_versions")
    before_lines = scalar(c, "SELECT count(*) FROM recipe_ingredients")
    before_audit = scalar(c, "SELECT count(*) FROM audit_logs")
    with pytest.raises(DomainValidationError) as exc:
        service.create_version(
            t2.id,
            RecipeVersionDraft.create(created_from_version_id=source.version.id, ingredients=[line(ing.id)]),
        )
    assert exc.value.issue.field == "created_from_version_id"
    assert exc.value.issue.message == "Исходная версия должна относиться к этому же рецепту."
    assert scalar(c, "SELECT count(*) FROM recipe_versions") == before_versions
    assert scalar(c, "SELECT count(*) FROM recipe_ingredients") == before_lines
    assert scalar(c, "SELECT count(*) FROM audit_logs") == before_audit

def test_ingredient_line_validation_and_active_ingredient_requirement(tmp_path):
    c = config(tmp_path)
    ing1 = ingredient(c, "Oil A")
    ing2 = ingredient(c, "Oil B")
    t = template(c)
    detail = RecipeService(c).create_version(t.id, RecipeVersionDraft.create(ingredients=[line(ing2.id, 2, "2", "ml"), line(ing1.id, 1, "1", "g")]))
    assert [x.position for x in detail.ingredients] == [1, 2]
    with pytest.raises(DomainValidationError): line(None)
    with pytest.raises(DomainValidationError): line(ing1.id, amount="0")
    with pytest.raises(DomainValidationError): line(ing1.id, amount=1.1)
    with pytest.raises(DomainValidationError): line(ing1.id, unit="bad")
    IngredientService(c).deactivate_ingredient(ing1.id)
    with pytest.raises(RecipeIngredientInactiveError):
        RecipeService(c).create_version(t.id, RecipeVersionDraft.create(ingredients=[line(ing1.id)]))
    with pytest.raises(LookupError):
        RecipeService(c).create_version(t.id, RecipeVersionDraft.create(ingredients=[line(999)]))

def test_version_create_rolls_back_on_invalid_line_and_audit_failure(tmp_path):
    c = config(tmp_path)
    ing = ingredient(c)
    t = template(c)
    with pytest.raises(DomainValidationError):
        RecipeVersionDraft.create(ingredients=[line(ing.id), line(ing.id, position=2, amount="0")])
    assert scalar(c, "SELECT count(*) FROM recipe_versions") == 0
    assert scalar(c, "SELECT count(*) FROM recipe_ingredients") == 0
    service = RecipeService(c)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_version(t.id, RecipeVersionDraft.create(ingredients=[line(ing.id)]))
    assert scalar(c, "SELECT count(*) FROM recipe_versions") == 0
    assert scalar(c, "SELECT count(*) FROM recipe_ingredients") == 0

def test_audit_failure_rolls_back_template_create_and_validation_writes_no_audit(tmp_path):
    c = config(tmp_path)
    service = RecipeService(c)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_template(RecipeTemplateDraft.create(name="Rollback Recipe"))
    assert scalar(c, "SELECT count(*) FROM recipe_templates WHERE name='Rollback Recipe'") == 0
    before = scalar(c, "SELECT count(*) FROM audit_logs")
    with pytest.raises(DomainValidationError):
        RecipeTemplateDraft.create(name="")
    assert scalar(c, "SELECT count(*) FROM audit_logs") == before

def test_recipe_api_endpoint_functions(monkeypatch, tmp_path):
    from app.db.config import DATABASE_PATH_ENV
    from app.api.recipes import create_template as api_create_template, list_templates as api_list_templates, get_template as api_get_template, deactivate_template as api_deactivate_template, create_version as api_create_version, list_versions as api_list_versions, get_version_detail as api_get_version_detail
    from app.schemas.recipes import RecipeIngredientCreateRequest, RecipeTemplateCreateRequest, RecipeVersionCreateRequest
    database_path = tmp_path / "api-recipes.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    ing = IngredientService().create_ingredient(IngredientDraft.create(name="Oil", category="oil", default_unit="g"))
    created = api_create_template(RecipeTemplateCreateRequest(name="Cream", product_type="cream"))
    tid = created.id
    assert api_list_templates().recipe_templates[0].id == tid
    assert api_get_template(tid).name == "Cream"
    version = api_create_version(tid, RecipeVersionCreateRequest(ingredients=[RecipeIngredientCreateRequest(ingredient_id=ing.id, position=1, amount_value="10", amount_unit="percent")]))
    vid = version.version.id
    assert api_list_versions(tid).recipe_versions[0].version_number == 1
    assert api_get_version_detail(vid).ingredients[0].ingredient_id == ing.id
    with pytest.raises(Exception):
        api_create_version(tid, RecipeVersionCreateRequest(ingredients=[RecipeIngredientCreateRequest(position=1, amount_value="10", amount_unit="percent")]))
    assert api_deactivate_template(tid).is_active is False
