import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError as exc:
    TestClient = None
else:
    exc = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.client_recipes import ClientRecipeDraft
from app.domain.clients import ClientDraft
from app.domain.errors import DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.main import create_app
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.services.client_recipes import ClientInactiveError, ClientRecipeService, SourceRecipeVersionEmptyError
from app.services.clients import ClientService
from app.services.database import initialize_database
from app.services.ingredients import IngredientService
from app.services.recipes import RecipeService
from app.tests.table_guards import CURRENT_ALLOWED_TABLES, FORBIDDEN_FUTURE_TABLES, assert_no_forbidden_future_tables, assert_only_current_tables


class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "client-recipes.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def tables(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def seed_source(c, *, with_lines=True):
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ing1 = IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit="g"))
    ing2 = IngredientService(c).create_ingredient(IngredientDraft.create(name="Oil", category="oil", default_unit="g"))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name="Base cream"))
    ingredients = []
    if with_lines:
        ingredients = [
            RecipeIngredientDraft.create(ingredient_id=ing2.id, position=2, amount_value="20", amount_unit="percent", phase="oil", notes="source oil"),
            RecipeIngredientDraft.create(ingredient_id=ing1.id, position=1, amount_value="80", amount_unit="percent", phase="water", notes="source water"),
        ]
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=ingredients))
    return client, version


def draft(client_id=None, version_id=None, source_recipe_version_id=None, **overrides):
    values = {"client_id": client_id, "source_recipe_version_id": version_id if source_recipe_version_id is None else source_recipe_version_id, "title": " Крем для Анны ", "status": "draft", "target_batch_size_value": "50", "target_batch_size_unit": "g", "personalization_notes": " без эфирных масел ", "allergy_notes": " лаванда ", "preference_notes": " легкая текстура ", "contraindication_notes": "", "notes": ""}
    values.update(overrides)
    return ClientRecipeDraft.create(**values)


def test_migration_creates_client_recipe_tables_and_guards(tmp_path):
    c = config(tmp_path)
    names = tables(c)
    assert {"client_recipes", "client_recipe_ingredients"} <= names
    assert "client_recipes" in CURRENT_ALLOWED_TABLES
    assert "client_recipe_ingredients" in CURRENT_ALLOWED_TABLES
    assert "client_recipes" not in FORBIDDEN_FUTURE_TABLES
    assert "client_recipe_ingredients" not in FORBIDDEN_FUTURE_TABLES
    assert_no_forbidden_future_tables(names)
    assert_only_current_tables(names)
    assert {"orders", "production_batches", "import_sources", "import_drafts", "backup_records", "client_wishes", "client_feedback"}.isdisjoint(names)


def test_create_list_get_and_snapshot_lines(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    assert detail.client_recipe.client_id == client.id
    assert detail.client_recipe.source_recipe_version_id == version.version.id
    assert detail.client_recipe.title == "Крем для Анны"
    assert [(i.position, i.ingredient_id, str(i.amount_value), i.amount_unit.value, i.source_recipe_ingredient_id, i.phase, i.notes) for i in detail.ingredients] == [
        (1, version.ingredients[0].ingredient_id, "80.00", "percent", version.ingredients[0].id, "water", "source water"),
        (2, version.ingredients[1].ingredient_id, "20.00", "percent", version.ingredients[1].id, "oil", "source oil"),
    ]
    assert service.get_detail(detail.client_recipe.id).ingredients[0].source_recipe_ingredient_id == version.ingredients[0].id
    assert [r.id for r in service.list_recipes()] == [detail.client_recipe.id]
    assert [r.id for r in service.list_for_client(client.id)] == [detail.client_recipe.id]


def test_snapshot_is_independent_from_later_base_versions_and_source_metadata(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    RecipeService(c).create_version(version.version.recipe_template_id, RecipeVersionDraft.create(title="v2", ingredients=[RecipeIngredientDraft.create(ingredient_id=version.ingredients[0].ingredient_id, position=1, amount_value="5", amount_unit="g")]))
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE recipe_ingredients SET amount_value='1.00', notes='changed' WHERE id=?", (version.ingredients[1].id,))
        con.commit()
    reread = service.get_detail(detail.client_recipe.id)
    assert [(str(i.amount_value), i.notes) for i in reread.ingredients] == [("80.00", "source water"), ("20.00", "source oil")]
    assert scalar(c, "SELECT count(*) FROM client_recipe_ingredients WHERE client_recipe_id=?", (detail.client_recipe.id,)) == 2


@pytest.mark.parametrize("overrides", [
    {"client_id": 999},
    {"source_recipe_version_id": 999},
    {"title": " "},
    {"status": "bad"},
    {"target_batch_size_value": "0"},
    {"target_batch_size_value": "-1"},
    {"target_batch_size_value": 1.2},
    {"target_batch_size_value": "10", "target_batch_size_unit": "percent"},
])
def test_validation_and_missing_references_rejected(tmp_path, overrides):
    c = config(tmp_path)
    client, version = seed_source(c)
    with pytest.raises((DomainValidationError, LookupError)):

        values = {"client_id": client.id, "source_recipe_version_id": version.version.id}
        values.update(overrides)
        ClientRecipeService(c).create_from_recipe_version(draft(**values))
    assert scalar(c, "SELECT count(*) FROM client_recipes") == 0


def test_inactive_client_and_empty_source_version_rejected(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    ClientService(c).deactivate_client(client.id)
    with pytest.raises(ClientInactiveError):
        ClientRecipeService(c).create_from_recipe_version(draft(client.id, version.version.id))
    active_client, empty_version = seed_source(c, with_lines=False)
    with pytest.raises(SourceRecipeVersionEmptyError):
        ClientRecipeService(c).create_from_recipe_version(draft(active_client.id, empty_version.version.id))


def test_deactivate_is_soft_and_list_behavior_explicit(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id)).client_recipe
    deactivated = service.deactivate(created.id)
    assert deactivated.is_active is False
    assert deactivated.status.value == "archived"
    assert service.get_detail(created.id).client_recipe.id == created.id
    assert service.list_recipes(include_inactive=False) == []
    assert [r.id for r in service.list_recipes(include_inactive=True)] == [created.id]


def test_successful_create_writes_audit_and_audit_failures_rollback(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id))
    assert scalar(c, "SELECT count(*) FROM client_recipes") == 1
    assert scalar(c, "SELECT count(*) FROM client_recipe_ingredients") == 2
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action='client_recipe.created'") == 1

    client2, version2 = seed_source(c)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_from_recipe_version(draft(client2.id, version2.version.id, title="Rollback recipe"))
    assert scalar(c, "SELECT count(*) FROM client_recipes WHERE title='Rollback recipe'") == 0

    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.deactivate(created.client_recipe.id)
    assert service.get_detail(created.client_recipe.id).client_recipe.is_active is True


def test_snapshot_line_failure_rolls_back_recipe_and_lines(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    original_repository = service.repository

    class FailingLineRepository:
        def __init__(self):
            self.calls = 0

        def __getattr__(self, name):
            return getattr(original_repository, name)

        def create_ingredient_line(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("simulated snapshot line failure")
            return original_repository.create_ingredient_line(*args, **kwargs)

    service.repository = FailingLineRepository()
    with pytest.raises(RuntimeError):
        service.create_from_recipe_version(draft(client.id, version.version.id))
    assert scalar(c, "SELECT count(*) FROM client_recipes") == 0
    assert scalar(c, "SELECT count(*) FROM client_recipe_ingredients") == 0


def test_validation_failure_creates_no_audit(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    with pytest.raises(DomainValidationError):
        ClientRecipeService(c).create_from_recipe_version(draft(client.id, version.version.id, title=" "))
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action LIKE 'client_recipe.%'") == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_client_recipe_api(monkeypatch, tmp_path):
    db = tmp_path / "api-client-recipes.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    client, version = seed_source(c)
    api = TestClient(create_app())
    payload = {"client_id": client.id, "source_recipe_version_id": version.version.id, "title": "Крем API", "target_batch_size_value": "50", "target_batch_size_unit": "g"}
    response = api.post("/api/client-recipes", json=payload)
    assert response.status_code == 201
    recipe_id = response.json()["client_recipe"]["id"]
    assert len(response.json()["ingredients"]) == 2
    assert api.get("/api/client-recipes").json()["client_recipes"][0]["id"] == recipe_id
    assert api.get(f"/api/clients/{client.id}/recipes").json()["client_recipes"][0]["id"] == recipe_id
    assert api.get(f"/api/client-recipes/{recipe_id}").json()["ingredients"][0]["position"] == 1
    assert api.post(f"/api/client-recipes/{recipe_id}/deactivate").json()["is_active"] is False
    assert api.get("/api/client-recipes/999").status_code == 404
    assert api.post("/api/client-recipes", json={**payload, "source_recipe_version_id": 999}).status_code == 404
