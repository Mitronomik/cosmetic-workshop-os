import sqlite3
import pytest
from pydantic import ValidationError
try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.clients import ClientDraft
from app.domain.ingredients import IngredientDraft
from app.domain.orders import OrderDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.domain.errors import DomainValidationError
from app.models.order import OrderStatus
from app.main import create_app
from app.schemas.orders import OrderCreateRequest, OrderUpdateRequest
from app.services.clients import ClientService
from app.services.database import initialize_database
from app.services.ingredients import IngredientService
from app.services.packaging_items import PackagingItemService
from app.services.recipes import RecipeService
from app.services.client_recipes import ClientRecipeService
from app.domain.client_recipes import ClientRecipeDraft
from app.services.orders import OrderClientInactiveError, OrderClientRecipeInactiveError, OrderClientRecipeMismatchError, OrderLifecycleError, OrderPackagingInactiveError, OrderService
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables

class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")

def config(tmp_path):
    c=DatabaseConfig(path=tmp_path/"orders.sqlite"); initialize_database(c); return c

def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con: return con.execute(sql, params).fetchone()[0]

def tables(c):
    with sqlite3.connect(c.path) as con: return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def indexes(c):
    with sqlite3.connect(c.path) as con: return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='index'")}

def seed(c):
    client=ClientService(c).create_client(ClientDraft.create(full_name="Анна"))
    ingredient=IngredientService(c).create_ingredient(IngredientDraft.create(name="Water", category="water_phase", default_unit="g"))
    template=RecipeService(c).create_template(RecipeTemplateDraft.create(name="Cream"))
    version=RecipeService(c).create_version(template.id, RecipeVersionDraft.create(title="v1", ingredients=[RecipeIngredientDraft.create(ingredient_id=ingredient.id, position=1, amount_value="100", amount_unit="percent")])).version
    packaging=PackagingItemService(c).create_packaging_item(PackagingItemDraft.create(name="Банка 50 мл", kind="jar", unit="pcs"))
    client_recipe=ClientRecipeService(c).create_from_recipe_version(ClientRecipeDraft.create(client_id=client.id, source_recipe_version_id=version.id, title="Анна cream")).client_recipe
    return client, version, client_recipe, packaging

def draft(client_id, version_id=None, client_recipe_id=None, **overrides):
    vals={"client_id":client_id,"recipe_version_id":version_id,"client_recipe_id":client_recipe_id,"product_name":"  Крем   дневной ","target_batch_size_value":"50","target_batch_size_unit":"g","notes":"  без   отдушки "}
    vals.update(overrides); return OrderDraft.create(**vals)

def test_migration_creates_orders_table_indexes_and_guards(tmp_path):
    c=config(tmp_path); names=tables(c)
    assert "orders" in names
    assert {"idx_orders_client_active","idx_orders_status_active","idx_orders_recipe_version","idx_orders_client_recipe","idx_orders_packaging_item"} <= indexes(c)
    assert_only_current_tables(names); assert_no_forbidden_future_tables(names)
    assert {"import_sources","import_drafts","purchase_suggestions","alerts"}.isdisjoint(names)

def test_order_domain_validation_and_normalization():
    good=draft(1, version_id=1, packaging_item_id=1, packaging_quantity="2", sale_price="100.50")
    assert good.product_name == "Крем дневной" and good.notes == "без отдушки"
    for kwargs in ({"client_id":None}, {"version_id":None}, {"version_id":1,"client_recipe_id":1}, {"version_id":1,"target_batch_size_value":"0"}, {"version_id":1,"target_batch_size_unit":"percent"}, {"version_id":1,"packaging_item_id":1,"packaging_quantity":"1.5"}, {"version_id":1,"packaging_quantity":"2"}, {"version_id":1,"sale_price":"-1"}):
        with pytest.raises(DomainValidationError):
            if "version_id" in kwargs: draft(kwargs.pop("client_id",1), **kwargs)
            else: draft(**kwargs)


def test_order_api_schemas_reject_generic_lifecycle_fields():
    payload={"client_id":1,"recipe_version_id":1,"product_name":"Крем","target_batch_size_value":"50","target_batch_size_unit":"g"}
    for field, value in (("status", "produced"), ("produced_at", "2026-06-30"), ("delivered_at", "2026-07-01")):
        with pytest.raises(ValidationError):
            OrderCreateRequest(**{**payload, field: value})
        with pytest.raises(ValidationError):
            OrderUpdateRequest(**{**payload, field: value})

def test_service_create_list_get_update_cancel_archive_and_safety(tmp_path):
    c=config(tmp_path); client, version, client_recipe, packaging=seed(c); service=OrderService(c)
    order=service.create(draft(client.id, version_id=version.id, packaging_item_id=packaging.id, packaging_quantity="1", sale_price="1200", status=OrderStatus.PRODUCED, produced_at="2026-06-30", delivered_at="2026-07-01"))
    assert order.status.value == "new" and order.produced_at is None and order.delivered_at is None
    assert scalar(c,"SELECT count(*) FROM stock_movements")==0 and scalar(c,"SELECT count(*) FROM packaging_stock_movements")==0
    cr_order=service.create(draft(client.id, client_recipe_id=client_recipe.id, product_name="Индивидуальный крем"))
    assert cr_order.client_recipe_id == client_recipe.id
    assert service.get_by_id(order.id).id == order.id
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE orders SET status='in_progress', produced_at='future-produced', delivered_at='future-delivered' WHERE id=?", (order.id,))
    updated=service.update(order.id, draft(client.id, version_id=version.id, product_name="Крем ночной", target_batch_size_value="75", status=OrderStatus.PRODUCED, produced_at="bad", delivered_at="bad"))
    assert updated.product_name == "Крем ночной"
    assert updated.status.value == "in_progress" and updated.produced_at == "future-produced" and updated.delivered_at == "future-delivered"
    assert scalar(c,"SELECT title FROM recipe_versions WHERE id=?", (version.id,)) == version.title
    assert scalar(c,"SELECT count(*) FROM client_recipe_ingredients WHERE client_recipe_id=?", (client_recipe.id,)) > 0
    cancelled=service.cancel(order.id); assert cancelled.status.value == "cancelled"; assert service.cancel(order.id).status.value == "cancelled"
    with pytest.raises(OrderLifecycleError): service.update(order.id, draft(client.id, version_id=version.id))
    archived=service.archive(cr_order.id); assert archived.status.value == "archived" and archived.is_active is False
    assert [o.id for o in service.list_orders(include_inactive=False)] == [order.id]
    assert {o.id for o in service.list_orders(include_inactive=True)} == {order.id, cr_order.id}

def test_service_rejects_inactive_and_mismatched_refs(tmp_path):
    c=config(tmp_path); client, version, client_recipe, packaging=seed(c); other=ClientService(c).create_client(ClientDraft.create(full_name="Мария")); inactive=ClientService(c).create_client(ClientDraft.create(full_name="Ольга")); service=OrderService(c)
    ClientService(c).deactivate_client(inactive.id)
    with pytest.raises(OrderClientInactiveError): service.create(draft(inactive.id, version_id=version.id))
    with pytest.raises(OrderClientRecipeMismatchError): service.create(draft(other.id, client_recipe_id=client_recipe.id))
    PackagingItemService(c).deactivate_packaging_item(packaging.id)
    with pytest.raises(OrderPackagingInactiveError): service.create(draft(client.id, version_id=version.id, packaging_item_id=packaging.id))
    ClientRecipeService(c).deactivate(client_recipe.id)
    with pytest.raises(OrderClientRecipeInactiveError): service.create(draft(client.id, client_recipe_id=client_recipe.id))

def test_audit_failure_rolls_back_writes(tmp_path):
    c=config(tmp_path); client, version, _, _=seed(c); service=OrderService(c); service.audit=FailingAuditRepository()
    with pytest.raises(RuntimeError): service.create(draft(client.id, version_id=version.id, product_name="Rollback create"))
    assert scalar(c,"SELECT count(*) FROM orders WHERE product_name='Rollback create'") == 0
    order=OrderService(c).create(draft(client.id, version_id=version.id))
    service.audit=FailingAuditRepository()
    for action in (lambda: service.update(order.id, draft(client.id, version_id=version.id, product_name="Rollback update")), lambda: service.cancel(order.id), lambda: service.archive(order.id)):
        with pytest.raises(RuntimeError): action()
    current=OrderService(c).get_by_id(order.id)
    assert current.status.value == "new" and current.is_active is True and current.product_name != "Rollback update"

@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_api_orders_endpoints(monkeypatch, tmp_path):
    db=tmp_path/"api-orders.sqlite"; monkeypatch.setenv(DATABASE_PATH_ENV, str(db)); c=DatabaseConfig(path=db); initialize_database(c); client, version, _, _=seed(c); api=TestClient(create_app())
    payload={"client_id":client.id,"recipe_version_id":version.id,"product_name":"Крем","target_batch_size_value":"50","target_batch_size_unit":"g"}
    for field, value in (("status", "produced"), ("produced_at", "2026-06-30"), ("delivered_at", "2026-07-01")):
        assert api.post("/api/orders", json={**payload, field: value}).status_code == 422
    created=api.post("/api/orders", json=payload); assert created.status_code == 201; order_id=created.json()["id"]
    assert created.json()["status"] == "new" and created.json()["produced_at"] is None and created.json()["delivered_at"] is None
    assert api.get("/api/orders").json()["orders"][0]["id"] == order_id
    assert api.get(f"/api/orders/{order_id}").status_code == 200
    for field, value in (("status", "produced"), ("produced_at", "2026-06-30"), ("delivered_at", "2026-07-01")):
        assert api.put(f"/api/orders/{order_id}", json={**payload, field: value}).status_code == 422
    assert api.put(f"/api/orders/{order_id}", json={**payload,"product_name":"Крем 2"}).json()["product_name"] == "Крем 2"
    assert api.get(f"/api/clients/{client.id}/orders").json()["orders"][0]["id"] == order_id
    assert api.post(f"/api/orders/{order_id}/cancel").json()["status"] == "cancelled"
    assert api.post(f"/api/orders/{order_id}/archive").json()["status"] == "archived"
    assert api.post("/api/orders", json={**payload,"recipe_version_id":None}).status_code == 422
    assert api.get("/api/orders/999").status_code == 404
    ClientService(c).deactivate_client(client.id)
    assert api.post("/api/orders", json=payload).status_code == 409
