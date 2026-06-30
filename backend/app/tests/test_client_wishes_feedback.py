import sqlite3
import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.client_recipes import ClientRecipeDraft
from app.domain.client_wishes_feedback import ClientFeedbackDraft, ClientWishDraft, ClientWishStatusUpdate
from app.domain.clients import ClientDraft
from app.domain.errors import DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.main import create_app
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.services.client_recipes import ClientRecipeService
from app.services.client_wishes_feedback import ClientFeedbackService, ClientRecipeClientMismatchError, ClientWishFeedbackClientInactiveError, ClientWishService
from app.services.clients import ClientService
from app.services.database import initialize_database
from app.services.ingredients import IngredientService
from app.services.recipes import RecipeService
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables


class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "wishes-feedback.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def tables(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def seed_client_recipe(c, *, client_name="Анна"):
    client = ClientService(c).create_client(ClientDraft.create(full_name=client_name))
    ingredient = IngredientService(c).create_ingredient(IngredientDraft.create(name=f"Water {client.id}", category="water_phase", default_unit="g"))
    template = RecipeService(c).create_template(RecipeTemplateDraft.create(name=f"Cream {client.id}"))
    version = RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value="100", amount_unit="percent")]))
    recipe = ClientRecipeService(c).create_from_recipe_version(ClientRecipeDraft.create(client_id=client.id, source_recipe_version_id=version.version.id, title="Client cream"))
    return client, recipe.client_recipe


def wish_draft(client_id, **overrides):
    values = {"client_id": client_id, "title": "Сделать легче", "description": "Крем показался жирным", "category": "texture", "priority": "normal"}
    values.update(overrides)
    return ClientWishDraft.create(**values)


def feedback_draft(client_id, **overrides):
    values = {"client_id": client_id, "feedback_type": "texture", "sentiment": "negative", "rating": 3, "text": "Слишком плотный", "follow_up_needed": True, "follow_up_note": "Уменьшить масла", "occurred_at": "2026-06-30"}
    values.update(overrides)
    return ClientFeedbackDraft.create(**values)


def test_migration_creates_tables_and_guards(tmp_path):
    c = config(tmp_path)
    names = tables(c)
    assert {"client_wishes", "client_feedback"} <= names
    assert_only_current_tables(names)
    assert_no_forbidden_future_tables(names)


def test_wish_create_list_get_validation_and_inactive_client(tmp_path):
    c = config(tmp_path)
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    service = ClientWishService(c)
    wish = service.create(wish_draft(client.id))
    assert wish.title == "Сделать легче"
    assert [w.id for w in service.list_for_client(client.id)] == [wish.id]
    assert service.get(wish.id).id == wish.id
    for bad in ({"title": " "}, {"category": "bad"}, {"priority": "bad"}):
        with pytest.raises(DomainValidationError):
            wish_draft(client.id, **bad)
    with pytest.raises(Exception):
        service.create(wish_draft(999))
    ClientService(c).deactivate_client(client.id)
    with pytest.raises(ClientWishFeedbackClientInactiveError):
        service.create(wish_draft(client.id, title="after archive"))


def test_wish_client_recipe_link_rules_allow_archived_same_client(tmp_path):
    c = config(tmp_path)
    client, recipe = seed_client_recipe(c)
    other, other_recipe = seed_client_recipe(c, client_name="Мария")
    service = ClientWishService(c)
    assert service.create(wish_draft(client.id, client_recipe_id=recipe.id)).client_recipe_id == recipe.id
    ClientRecipeService(c).deactivate(recipe.id)
    assert service.create(wish_draft(client.id, client_recipe_id=recipe.id, title="История")).client_recipe_id == recipe.id
    with pytest.raises(ClientRecipeClientMismatchError):
        service.create(wish_draft(client.id, client_recipe_id=other_recipe.id))
    with pytest.raises(ClientRecipeNotFoundError):
        service.create(wish_draft(client.id, client_recipe_id=999))


def test_wish_status_archive_filters_and_audit_rollbacks(tmp_path):
    c = config(tmp_path)
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    service = ClientWishService(c)
    wish = service.create(wish_draft(client.id))
    assert service.update_status(wish.id, ClientWishStatusUpdate.create(status="planned")).status.value == "planned"
    resolved = service.update_status(wish.id, ClientWishStatusUpdate.create(status="resolved"))
    assert resolved.resolved_at is not None
    archived = service.archive(wish.id)
    assert archived.status.value == "archived" and archived.is_active is False
    assert service.list_for_client(client.id, include_inactive=False) == []
    assert [w.id for w in service.list_for_client(client.id, include_inactive=True)] == [wish.id]
    with pytest.raises(DomainValidationError):
        ClientWishStatusUpdate.create(status="bad")

    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create(wish_draft(client.id, title="Rollback create"))
    assert scalar(c, "SELECT count(*) FROM client_wishes WHERE title='Rollback create'") == 0
    with pytest.raises(RuntimeError):
        service.update_status(wish.id, ClientWishStatusUpdate.create(status="open"))
    assert service.get(wish.id).status.value == "archived"
    with pytest.raises(RuntimeError):
        service.archive(wish.id)


def test_feedback_create_list_get_validation_and_inactive_client(tmp_path):
    c = config(tmp_path)
    client = ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    service = ClientFeedbackService(c)
    feedback = service.create(feedback_draft(client.id))
    assert feedback.text == "Слишком плотный"
    assert [f.id for f in service.list_for_client(client.id)] == [feedback.id]
    assert service.get(feedback.id).id == feedback.id
    for bad in ({"text": " "}, {"feedback_type": "bad"}, {"sentiment": "bad"}, {"rating": 0}, {"rating": 6}):
        with pytest.raises(DomainValidationError):
            feedback_draft(client.id, **bad)
    assert feedback_draft(client.id, rating=None).rating is None
    with pytest.raises(Exception):
        service.create(feedback_draft(999))
    ClientService(c).deactivate_client(client.id)
    with pytest.raises(ClientWishFeedbackClientInactiveError):
        service.create(feedback_draft(client.id, text="after archive"))


def test_feedback_client_recipe_link_rules_allow_archived_same_client_and_audit_rollback(tmp_path):
    c = config(tmp_path)
    client, recipe = seed_client_recipe(c)
    _, other_recipe = seed_client_recipe(c, client_name="Мария")
    service = ClientFeedbackService(c)
    assert service.create(feedback_draft(client.id, client_recipe_id=recipe.id)).client_recipe_id == recipe.id
    ClientRecipeService(c).deactivate(recipe.id)
    assert service.create(feedback_draft(client.id, client_recipe_id=recipe.id, text="Исторический отзыв")).client_recipe_id == recipe.id
    with pytest.raises(ClientRecipeClientMismatchError):
        service.create(feedback_draft(client.id, client_recipe_id=other_recipe.id))
    with pytest.raises(ClientRecipeNotFoundError):
        service.create(feedback_draft(client.id, client_recipe_id=999))
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create(feedback_draft(client.id, text="Rollback feedback"))
    assert scalar(c, "SELECT count(*) FROM client_feedback WHERE text='Rollback feedback'") == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_endpoints_and_feedback_append_only(monkeypatch, tmp_path):
    db = tmp_path / "api-wishes-feedback.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    client, recipe = seed_client_recipe(c)
    api = TestClient(create_app())
    wish_payload = {"client_recipe_id": recipe.id, "title": "Сделать легче", "category": "texture", "priority": "normal"}
    created_wish = api.post(f"/api/clients/{client.id}/wishes", json=wish_payload)
    assert created_wish.status_code == 201
    wish_id = created_wish.json()["id"]
    assert api.get(f"/api/clients/{client.id}/wishes").json()["wishes"][0]["id"] == wish_id
    assert api.get(f"/api/client-wishes/{wish_id}").status_code == 200
    assert api.put(f"/api/client-wishes/{wish_id}/status", json={"status": "resolved"}).json()["resolved_at"] is not None
    assert api.post(f"/api/client-wishes/{wish_id}/archive").json()["is_active"] is False
    assert api.post(f"/api/clients/{client.id}/wishes", json={**wish_payload, "client_recipe_id": 999}).status_code == 404
    assert api.post("/api/clients/999/wishes", json=wish_payload).status_code == 404
    assert api.post(f"/api/clients/{client.id}/wishes", json={**wish_payload, "category": "bad"}).status_code == 422

    feedback_payload = {"client_recipe_id": recipe.id, "feedback_type": "texture", "sentiment": "negative", "rating": 3, "text": "Слишком плотный", "follow_up_needed": True}
    created_feedback = api.post(f"/api/clients/{client.id}/feedback", json=feedback_payload)
    assert created_feedback.status_code == 201
    feedback_id = created_feedback.json()["id"]
    assert api.get(f"/api/clients/{client.id}/feedback").json()["feedback"][0]["id"] == feedback_id
    assert api.get(f"/api/client-feedback/{feedback_id}").status_code == 200
    assert api.put(f"/api/client-feedback/{feedback_id}", json={"text": "edit"}).status_code == 405
    assert api.delete(f"/api/client-feedback/{feedback_id}").status_code == 405
    ClientService(c).deactivate_client(client.id)
    assert api.post(f"/api/clients/{client.id}/feedback", json=feedback_payload).status_code == 409
