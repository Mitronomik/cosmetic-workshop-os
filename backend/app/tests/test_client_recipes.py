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
    assert {"orders", "production_batches", "import_sources", "import_drafts", "backup_records"}.isdisjoint(names)


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
    current_lines = api.get(f"/api/client-recipes/{recipe_id}").json()["ingredients"]
    assert current_lines[0]["position"] == 1
    update_response = api.put(
        f"/api/client-recipes/{recipe_id}/ingredients",
        json={
            "ingredients": [
                {"id": current_lines[0]["id"], "ingredient_id": current_lines[0]["ingredient_id"], "position": 1, "phase": current_lines[0]["phase"], "amount_value": "70", "amount_unit": current_lines[0]["amount_unit"], "personalization_note": "API adjusted", "notes": current_lines[0]["notes"]},
                {"id": current_lines[1]["id"], "ingredient_id": current_lines[1]["ingredient_id"], "position": 2, "phase": current_lines[1]["phase"], "amount_value": "30", "amount_unit": current_lines[1]["amount_unit"], "personalization_note": "", "notes": current_lines[1]["notes"]},
            ]
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["ingredients"][0]["amount_value"] == "70.00"
    invalid_response = api.put(f"/api/client-recipes/{recipe_id}/ingredients", json={"ingredients": []})
    assert invalid_response.status_code == 422
    assert api.post(f"/api/client-recipes/{recipe_id}/deactivate").json()["is_active"] is False
    assert api.get("/api/client-recipes/999").status_code == 404
    assert api.post("/api/client-recipes", json={**payload, "source_recipe_version_id": 999}).status_code == 404


def update_line(line, **overrides):
    values = {
        "id": line.id,
        "ingredient_id": line.ingredient_id,
        "position": line.position,
        "phase": line.phase,
        "amount_value": str(line.amount_value),
        "amount_unit": line.amount_unit,
        "personalization_note": line.personalization_note,
        "notes": line.notes,
    }
    values.update(overrides)
    from app.domain.client_recipes import ClientRecipeIngredientUpdateDraft
    return ClientRecipeIngredientUpdateDraft.create(**values)


def test_update_composition_changes_only_target_client_recipe_and_preserves_source(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    first = service.create_from_recipe_version(draft(client.id, version.version.id, title="First"))
    second = service.create_from_recipe_version(draft(client.id, version.version.id, title="Second"))

    updated = service.update_composition(first.client_recipe.id, [
        update_line(first.ingredients[0], amount_value="75", personalization_note="Adjusted for client", notes="updated water"),
        update_line(first.ingredients[1], amount_value="25", position=2),
    ])

    assert [(i.position, str(i.amount_value), i.personalization_note, i.notes) for i in updated.ingredients] == [
        (1, "75.00", "Adjusted for client", "updated water"),
        (2, "25.00", "", "source oil"),
    ]
    source = RecipeService(c).get_version_detail(version.version.id)
    assert [(str(i.amount_value), i.notes) for i in source.ingredients] == [("80.00", "source water"), ("20.00", "source oil")]
    reread_second = service.get_detail(second.client_recipe.id)
    assert [(str(i.amount_value), i.notes) for i in reread_second.ingredients] == [("80.00", "source water"), ("20.00", "source oil")]
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action='client_recipe.composition_updated'") == 1


@pytest.mark.parametrize("bad_lines", [
    lambda lines: [update_line(lines[0], position=1), update_line(lines[1], position=1)],
    lambda lines: [update_line(lines[0], amount_value="0")],
    lambda lines: [update_line(lines[0], amount_value="-1")],
    lambda lines: [],
])
def test_update_composition_validation_failures_keep_existing_lines(tmp_path, bad_lines):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    before = [(i.id, str(i.amount_value), i.position) for i in service.get_detail(detail.client_recipe.id).ingredients]
    with pytest.raises(DomainValidationError):
        service.update_composition(detail.client_recipe.id, bad_lines(detail.ingredients))
    after = [(i.id, str(i.amount_value), i.position) for i in service.get_detail(detail.client_recipe.id).ingredients]
    assert after == before


def test_update_composition_missing_and_inactive_ingredient_rules(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    before = [(i.ingredient_id, str(i.amount_value)) for i in detail.ingredients]

    with pytest.raises(Exception) as missing:
        service.update_composition(detail.client_recipe.id, [update_line(detail.ingredients[0], ingredient_id=999)])
    assert "not found" in str(missing.value).lower()
    assert [(i.ingredient_id, str(i.amount_value)) for i in service.get_detail(detail.client_recipe.id).ingredients] == before

    archived = IngredientService(c).deactivate_ingredient(detail.ingredients[0].ingredient_id)
    assert archived.is_active is False
    unchanged_existing = service.update_composition(detail.client_recipe.id, [update_line(detail.ingredients[0]), update_line(detail.ingredients[1], amount_value="21")])
    assert unchanged_existing.ingredients[0].source_recipe_ingredient_id == detail.ingredients[0].source_recipe_ingredient_id

    with pytest.raises(Exception) as changed_inactive:
        service.update_composition(detail.client_recipe.id, [update_line(unchanged_existing.ingredients[0], amount_value="79"), update_line(unchanged_existing.ingredients[1])])
    assert "inactive" in str(changed_inactive.value).lower()

    removed_inactive = service.update_composition(detail.client_recipe.id, [update_line(unchanged_existing.ingredients[1])])
    assert [line.ingredient_id for line in removed_inactive.ingredients] == [unchanged_existing.ingredients[1].ingredient_id]

    new_ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name="Archived additive", category="active", default_unit="g"))
    IngredientService(c).deactivate_ingredient(new_ingredient.id)
    with pytest.raises(Exception) as inactive:
        service.update_composition(removed_inactive.client_recipe.id, [update_line(removed_inactive.ingredients[0], ingredient_id=new_ingredient.id)])
    assert "inactive" in str(inactive.value).lower()


@pytest.mark.parametrize("mutation", [
    {"phase": "changed phase"},
    {"amount_unit": "g"},
    {"position": 3},
    {"notes": "changed notes"},
    {"personalization_note": "changed personalization"},
])
def test_update_composition_rejects_inactive_existing_line_metadata_changes(tmp_path, mutation):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    IngredientService(c).deactivate_ingredient(detail.ingredients[0].ingredient_id)
    before = [(i.ingredient_id, str(i.amount_value), i.amount_unit.value, i.position, i.phase, i.personalization_note, i.notes) for i in detail.ingredients]

    with pytest.raises(Exception) as inactive:
        service.update_composition(detail.client_recipe.id, [update_line(detail.ingredients[0], **mutation), update_line(detail.ingredients[1])])

    assert "inactive" in str(inactive.value).lower()
    reread = service.get_detail(detail.client_recipe.id)
    assert [(i.ingredient_id, str(i.amount_value), i.amount_unit.value, i.position, i.phase, i.personalization_note, i.notes) for i in reread.ingredients] == before


def test_update_composition_rejects_duplicate_existing_line_ids(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    before = [(i.id, str(i.amount_value), i.position) for i in detail.ingredients]

    with pytest.raises(DomainValidationError):
        service.update_composition(detail.client_recipe.id, [update_line(detail.ingredients[0]), update_line(detail.ingredients[0], position=2, amount_value="20")])

    after = [(i.id, str(i.amount_value), i.position) for i in service.get_detail(detail.client_recipe.id).ingredients]
    assert after == before


def test_update_composition_rejects_archived_recipe_and_foreign_line_id(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    first = service.create_from_recipe_version(draft(client.id, version.version.id, title="First"))
    second = service.create_from_recipe_version(draft(client.id, version.version.id, title="Second"))

    with pytest.raises(Exception) as foreign:
        service.update_composition(first.client_recipe.id, [update_line(second.ingredients[0])])
    assert "does not belong" in str(foreign.value)

    service.deactivate(first.client_recipe.id)
    with pytest.raises(Exception) as archived:
        service.update_composition(first.client_recipe.id, [update_line(first.ingredients[0])])
    assert "archived" in str(archived.value).lower()


def test_update_composition_audit_failure_rolls_back(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    detail = service.create_from_recipe_version(draft(client.id, version.version.id))
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.update_composition(detail.client_recipe.id, [update_line(detail.ingredients[0], amount_value="70")])
    reread = service.get_detail(detail.client_recipe.id)
    assert [(str(i.amount_value), i.notes) for i in reread.ingredients] == [("80.00", "source water"), ("20.00", "source oil")]

def client_recipe_line_signature(detail):
    return [(line.ingredient_id, line.source_recipe_ingredient_id, line.position, line.phase, str(line.amount_value), line.amount_unit.value, line.personalization_note, line.notes) for line in detail.ingredients]


def test_restore_archived_client_recipe_returns_draft_and_keeps_detail_lines(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id))
    service.deactivate(created.client_recipe.id)

    restored = service.restore(created.client_recipe.id)
    detail = service.get_detail(created.client_recipe.id)

    assert restored.is_active is True
    assert restored.status.value == "draft"
    assert detail.client_recipe.is_active is True
    assert client_recipe_line_signature(detail) == client_recipe_line_signature(created)


def test_restore_does_not_mutate_copied_composition(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id))
    before = client_recipe_line_signature(created)

    service.deactivate(created.client_recipe.id)
    service.restore(created.client_recipe.id)

    assert client_recipe_line_signature(service.get_detail(created.client_recipe.id)) == before


def test_restore_does_not_mutate_source_recipe_version(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id))
    source_before = [(line.id, line.ingredient_id, line.position, line.phase, str(line.amount_value), line.amount_unit.value, line.notes) for line in RecipeService(c).get_version_detail(version.version.id).ingredients]

    service.deactivate(created.client_recipe.id)
    service.restore(created.client_recipe.id)

    source_after = [(line.id, line.ingredient_id, line.position, line.phase, str(line.amount_value), line.amount_unit.value, line.notes) for line in RecipeService(c).get_version_detail(version.version.id).ingredients]
    assert source_after == source_before


def test_restore_does_not_mutate_another_client_recipe(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    first = service.create_from_recipe_version(draft(client.id, version.version.id, title="First"))
    second = service.create_from_recipe_version(draft(client.id, version.version.id, title="Second"))
    second_before = client_recipe_line_signature(second)

    service.deactivate(first.client_recipe.id)
    service.restore(first.client_recipe.id)

    assert client_recipe_line_signature(service.get_detail(second.client_recipe.id)) == second_before
    assert service.get_detail(second.client_recipe.id).client_recipe.is_active is True


def test_restore_rejected_when_linked_client_is_inactive_and_recipe_stays_archived(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id))
    ClientService(c).deactivate_client(client.id)
    service.deactivate(created.client_recipe.id)

    from app.services.client_recipes import ClientRecipeRestoreClientInactiveError
    with pytest.raises(ClientRecipeRestoreClientInactiveError):
        service.restore(created.client_recipe.id)

    reread = service.get_detail(created.client_recipe.id).client_recipe
    assert reread.is_active is False
    assert reread.status.value == "archived"


def test_restore_writes_audit_and_audit_failure_rolls_back(tmp_path):
    c = config(tmp_path)
    client, version = seed_source(c)
    service = ClientRecipeService(c)
    created = service.create_from_recipe_version(draft(client.id, version.version.id))
    service.deactivate(created.client_recipe.id)
    service.restore(created.client_recipe.id)
    assert scalar(c, "SELECT count(*) FROM audit_logs WHERE action='client_recipe.restored'") == 1

    service.deactivate(created.client_recipe.id)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.restore(created.client_recipe.id)
    reread = service.get_detail(created.client_recipe.id).client_recipe
    assert reread.is_active is False
    assert reread.status.value == "archived"


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_client_recipe_restore_api(monkeypatch, tmp_path):
    db = tmp_path / "api-client-recipe-restore.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    client, version = seed_source(c)
    api = TestClient(create_app())
    created = ClientRecipeService(c).create_from_recipe_version(draft(client.id, version.version.id)).client_recipe
    ClientRecipeService(c).deactivate(created.id)

    response = api.post(f"/api/client-recipes/{created.id}/restore")
    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert response.json()["status"] == "draft"
    assert api.post("/api/client-recipes/999/restore").status_code == 404

    inactive_client, inactive_version = seed_source(c)
    inactive_recipe = ClientRecipeService(c).create_from_recipe_version(draft(inactive_client.id, inactive_version.version.id)).client_recipe
    ClientService(c).deactivate_client(inactive_client.id)
    ClientRecipeService(c).deactivate(inactive_recipe.id)
    assert api.post(f"/api/client-recipes/{inactive_recipe.id}/restore").status_code == 409
