from datetime import date, timedelta
import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError as exc:
    TestClient = None
    TESTCLIENT_IMPORT_ERROR = exc
else:
    TESTCLIENT_IMPORT_ERROR = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.clients import ClientDraft
from app.domain.errors import DomainValidationError
from app.main import create_app
from app.services.clients import ClientService
from app.services.database import initialize_database
from app.tests.table_guards import CURRENT_ALLOWED_TABLES, FORBIDDEN_FUTURE_TABLES, assert_no_forbidden_future_tables, assert_only_current_tables


class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "clients.sqlite")
    initialize_database(config)
    return config


def scalar(config, sql, params=()):
    with sqlite3.connect(config.path) as connection:
        return connection.execute(sql, params).fetchone()[0]


def table_names(config):
    with sqlite3.connect(config.path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def valid_draft(**overrides):
    values = {"full_name": "  Анна   Иванова  ", "phone": " +7 999 123-45-67 ", "email": " ANNA@EXAMPLE.COM ", "address": "  Москва,  дом  1 ", "birthday": "1990-05-20", "skin_notes": " сухая   кожа ", "allergy_notes": "  нет ", "preference_notes": " без  запаха ", "contraindication_notes": "  нет ", "notes": " доставить вечером "}
    values.update(overrides)
    return ClientDraft.create(**values)


def test_migration_creates_clients_and_no_forbidden_tables(tmp_path):
    config = initialized_config(tmp_path)
    tables = table_names(config)
    assert "clients" in tables
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    assert "clients" in CURRENT_ALLOWED_TABLES
    assert "clients" not in FORBIDDEN_FUTURE_TABLES
    assert {"orders", "production_batches", "import_sources", "import_drafts"}.isdisjoint(tables)
    assert {"client_recipes", "client_recipe_ingredients"} <= tables


def test_create_get_list_update_and_deactivate_client(tmp_path):
    config = initialized_config(tmp_path)
    service = ClientService(config)
    client = service.create_client(valid_draft())
    assert client.full_name == "Анна Иванова"
    assert client.email == "anna@example.com"
    assert client.address == "Москва, дом 1"
    assert client.notes == "доставить вечером"
    assert service.get_client(client.id).id == client.id
    assert [item.id for item in service.list_clients()] == [client.id]

    updated = service.update_client(client.id, valid_draft(full_name=" Мария ", email="maria@example.com", birthday=None))
    assert updated.full_name == "Мария"
    assert updated.birthday is None

    deactivated = service.deactivate_client(client.id)
    assert deactivated.is_active is False
    assert service.list_clients() == []
    assert [item.id for item in service.list_clients(include_inactive=True)] == [client.id]


def test_missing_optional_fields_are_allowed(tmp_path):
    client = ClientService(initialized_config(tmp_path)).create_client(ClientDraft.create(full_name="Анна"))
    assert client.phone == ""
    assert client.email == ""
    assert client.birthday is None


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_full_name_rejected(name):
    with pytest.raises(DomainValidationError):
        ClientDraft.create(full_name=name)


def test_update_empty_full_name_rejected(tmp_path):
    config = initialized_config(tmp_path)
    service = ClientService(config)
    client = service.create_client(ClientDraft.create(full_name="Анна"))
    with pytest.raises(DomainValidationError):
        service.update_client(client.id, ClientDraft.create(full_name=" "))


def test_invalid_email_rejected():
    with pytest.raises(DomainValidationError):
        ClientDraft.create(full_name="Анна", email="not-email")


def test_future_birthday_rejected():
    with pytest.raises(DomainValidationError):
        ClientDraft.create(full_name="Анна", birthday=date.today() + timedelta(days=1))


def test_successful_create_writes_client_and_audit(tmp_path):
    config = initialized_config(tmp_path)
    client = ClientService(config).create_client(ClientDraft.create(full_name="Анна"))
    assert client.id > 0
    assert scalar(config, "SELECT count(*) FROM clients") == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs WHERE action = 'client.created'") == 1


def test_audit_failure_during_create_rolls_back_client(tmp_path):
    config = initialized_config(tmp_path)
    service = ClientService(config)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_client(ClientDraft.create(full_name="Rollback"))
    assert scalar(config, "SELECT count(*) FROM clients") == 0


def test_audit_failure_during_update_rolls_back_client_update(tmp_path):
    config = initialized_config(tmp_path)
    service = ClientService(config)
    client = service.create_client(ClientDraft.create(full_name="Анна"))
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.update_client(client.id, ClientDraft.create(full_name="Мария"))
    assert service.get_client(client.id).full_name == "Анна"


def test_audit_failure_during_deactivate_rolls_back_deactivation(tmp_path):
    config = initialized_config(tmp_path)
    service = ClientService(config)
    client = service.create_client(ClientDraft.create(full_name="Анна"))
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.deactivate_client(client.id)
    assert service.get_client(client.id).is_active is True


def test_validation_failure_creates_no_audit(tmp_path):
    config = initialized_config(tmp_path)
    with pytest.raises(DomainValidationError):
        ClientDraft.create(full_name=" ")
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_clients_api_create_list_get_update_deactivate_and_errors(monkeypatch, tmp_path):
    database_path = tmp_path / "api-clients.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    api = TestClient(create_app())

    response = api.post("/api/clients", json={"full_name": " Анна ", "email": "ANNA@EXAMPLE.COM"})
    assert response.status_code == 201
    client_id = response.json()["id"]
    assert response.json()["email"] == "anna@example.com"
    assert len(api.get("/api/clients").json()["clients"]) == 1
    assert api.get(f"/api/clients/{client_id}").json()["full_name"] == "Анна"

    update = api.put(f"/api/clients/{client_id}", json={"full_name": "Мария", "email": "maria@example.com"})
    assert update.status_code == 200
    assert update.json()["full_name"] == "Мария"
    assert api.post(f"/api/clients/{client_id}/deactivate").json()["is_active"] is False
    assert api.get("/api/clients").json()["clients"] == []
    assert len(api.get("/api/clients?include_inactive=true").json()["clients"]) == 1

    assert api.post("/api/clients", json={"full_name": "Bad", "email": "bad"}).status_code == 422
    assert api.get("/api/clients/999").status_code == 404
