"""`GET /api/audit-logs` wire contract, privacy exclusions and read-only behavior.

Durable contract: ``docs/audit-log.md`` § 4, § 5, § 8 and § 9.

The privacy assertions here deliberately search the *whole serialized response
text* rather than named fields. A leak that reaches the user through an
unexpected field is still a leak, so the check must not depend on knowing which
field went wrong.
"""

import json
import sqlite3

import pytest

try:
    from fastapi.testclient import TestClient
except (RuntimeError, ImportError):
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.main import create_app
from app.services.database import initialize_database

AUDIT_LOGS_URL = "/api/audit-logs"

TOP_LEVEL_FIELDS = {"items", "total", "limit", "offset", "filter_options"}
ITEM_FIELDS = {
    "id",
    "created_at",
    "action",
    "action_label",
    "entity_type",
    "entity_label",
    "display_summary",
    "actor_type",
    "actor_label",
}
FORBIDDEN_FIELDS = {"summary", "metadata_json", "entity_id", "source", "source_label"}

WISH_TITLE = "Убрать компонент X"
CLIENT_RECIPE_TITLE = "Крем от розацеа для Анны"

# Every class of § 11.5 is represented: an allowlisted business name, an
# ID-bearing technical summary, a wish title, an individual-recipe title, a known
# actor, an unknown actor, an unknown action and a null entity type.
SEEDED_ROWS = [
    ("2026-07-01 10:00:00", "system", "client.created", "client", "7", "Client created: Анна Иванова", '{"note": "секрет"}'),
    ("2026-07-02 10:00:00", "system", "ingredient_lot.created", "ingredient_lot", "12", "Ingredient lot created for ingredient #12", '{"ingredient_id": 12}'),
    ("2026-07-03 09:00:00", "system", "client_wish.created", "client_wish", "1", f"Client wish created: {WISH_TITLE}", '{"client_id": 4}'),
    ("2026-07-03 09:00:00", "system", "client_recipe.created", "client_recipe", "2", f"Client recipe created: {CLIENT_RECIPE_TITLE}", '{"client_id": 4}'),
    ("2026-07-03 09:00:00", "user", "tax_rate_setting_changed", "app_setting", "default_tax_rate", "Налоговая ставка изменена", '{"source": "settings"}'),
    ("2026-07-04 10:00:00", "system", "production_confirmed", "production_batch", "7", "Order #4 produced as batch #7", '{"order_id": 4}'),
    ("2026-07-05 10:00:00", "robot", "future.action", None, None, "Whatever the future writes", "{}"),
]

pytestmark = pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")


@pytest.fixture
def client(monkeypatch, tmp_path):
    database = tmp_path / "audit-logs-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database))
    initialize_database(DatabaseConfig(path=database))
    with sqlite3.connect(database) as connection:
        connection.executemany(
            "INSERT INTO audit_logs (created_at, actor_type, action, entity_type, entity_id, summary, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            SEEDED_ROWS,
        )
    test_client = TestClient(create_app())
    test_client.database_path = database  # type: ignore[attr-defined]
    return test_client


@pytest.fixture
def empty_client(monkeypatch, tmp_path):
    database = tmp_path / "audit-logs-api-empty.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database))
    initialize_database(DatabaseConfig(path=database))
    return TestClient(create_app())


def rows(client, sql: str, parameters: tuple = ()) -> list[sqlite3.Row]:
    with sqlite3.connect(client.database_path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(sql, parameters).fetchall()


def audit_snapshot(client) -> list[tuple]:
    return [tuple(row) for row in rows(client, "SELECT id, created_at, actor_type, action, entity_type, entity_id, summary, metadata_json FROM audit_logs ORDER BY id")]


def database_snapshot(client) -> dict[str, object]:
    tables = [row["name"] for row in rows(client, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    return {table: rows(client, f"SELECT COUNT(*) AS total FROM {table}")[0]["total"] for table in tables}


def settings_snapshot(client) -> list[tuple]:
    return [tuple(row) for row in rows(client, "SELECT key, value, value_type, updated_at FROM app_settings ORDER BY key")]


# --------------------------------------------------------------------------
# Endpoint surface
# --------------------------------------------------------------------------

def test_the_list_endpoint_is_registered(client):
    assert client.get(AUDIT_LOGS_URL).status_code == 200


def test_no_detail_endpoint_exists(client):
    routes = {route.path for route in client.app.routes}
    assert "/api/audit-logs" in routes
    assert "/api/audit-logs/{id}" not in routes
    assert "/api/audit-logs/{audit_log_id}" not in routes
    assert client.get(f"{AUDIT_LOGS_URL}/1").status_code == 404


def test_no_write_endpoint_exists(client):
    methods = {method for route in client.app.routes if route.path == "/api/audit-logs" for method in route.methods}
    assert methods == {"GET"}
    for send in (client.post, client.put, client.patch, client.delete):
        assert send(AUDIT_LOGS_URL).status_code in (404, 405)


# --------------------------------------------------------------------------
# Exact response shape
# --------------------------------------------------------------------------

def test_top_level_fields_are_exact(client):
    payload = client.get(AUDIT_LOGS_URL).json()
    assert set(payload) == TOP_LEVEL_FIELDS
    assert payload["total"] == 7
    assert payload["limit"] == 50
    assert payload["offset"] == 0


def test_item_fields_are_exact(client):
    for item in client.get(AUDIT_LOGS_URL).json()["items"]:
        assert set(item) == ITEM_FIELDS


def test_filter_options_use_the_exact_nested_value_label_shape(client):
    options = client.get(AUDIT_LOGS_URL).json()["filter_options"]
    assert set(options) == {"actions", "entity_types", "actor_types"}
    for group in options.values():
        for option in group:
            assert set(option) == {"value", "label"}
    assert {"value": "client", "label": "Клиент"} in options["entity_types"]
    assert {"value": "system", "label": "Система"} in options["actor_types"]


def test_created_at_is_iso_utc_and_never_the_storage_form(client):
    for item in client.get(AUDIT_LOGS_URL).json()["items"]:
        assert item["created_at"].endswith("Z")
        assert "T" in item["created_at"] and " " not in item["created_at"]
    assert client.get(f"{AUDIT_LOGS_URL}?action=client.created").json()["items"][0]["created_at"] == "2026-07-01T10:00:00Z"


def test_ordering_and_pagination_over_the_wire(client):
    first = client.get(f"{AUDIT_LOGS_URL}?limit=3&offset=0").json()
    second = client.get(f"{AUDIT_LOGS_URL}?limit=3&offset=3").json()
    assert first["total"] == second["total"] == 7
    assert (first["limit"], first["offset"]) == (3, 0)
    assert (second["limit"], second["offset"]) == (3, 3)
    identities = [item["id"] for item in first["items"] + second["items"]]
    assert identities == [7, 6, 5, 4, 3, 2]
    assert len(set(identities)) == 6


def test_filters_narrow_the_result_and_combine_with_and(client):
    assert client.get(f"{AUDIT_LOGS_URL}?actor_type=user").json()["total"] == 1
    assert client.get(f"{AUDIT_LOGS_URL}?entity_type=client_wish").json()["total"] == 1
    combined = client.get(f"{AUDIT_LOGS_URL}?actor_type=system&created_from=2026-07-03T00:00:00Z&created_before=2026-07-05T00:00:00Z").json()
    assert [item["action"] for item in combined["items"]] == ["production_confirmed", "client_recipe.created", "client_wish.created"]


def test_an_empty_database_returns_an_empty_but_complete_payload(empty_client):
    payload = empty_client.get(AUDIT_LOGS_URL).json()
    assert payload == {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0,
        "filter_options": {"actions": [], "entity_types": [], "actor_types": []},
    }


def test_unknown_persisted_codes_degrade_to_safe_labels(client):
    item = next(item for item in client.get(AUDIT_LOGS_URL).json()["items"] if item["action"] == "future.action")
    assert item["action_label"] == "Другое действие"
    assert item["entity_type"] is None
    assert item["entity_label"] == "Другая сущность"
    assert item["actor_label"] == "Другой инициатор"
    assert item["display_summary"] == "Другое действие"


def test_required_display_summary_examples_over_the_wire(client):
    summaries = {item["action"]: item["display_summary"] for item in client.get(AUDIT_LOGS_URL).json()["items"]}
    assert summaries["client.created"] == "Клиент создан: Анна Иванова"
    assert summaries["ingredient_lot.created"] == "Создана партия компонента"
    assert summaries["production_confirmed"] == "Производство заказа подтверждено"
    assert summaries["client_wish.created"] == "Пожелание клиента добавлено"


# --------------------------------------------------------------------------
# Privacy — nothing forbidden appears anywhere in the serialized response
# --------------------------------------------------------------------------

def test_forbidden_fields_are_absent_from_every_item(client):
    payload = client.get(AUDIT_LOGS_URL).json()
    for item in payload["items"]:
        assert FORBIDDEN_FIELDS.isdisjoint(item)
    assert FORBIDDEN_FIELDS.isdisjoint(payload)


@pytest.mark.parametrize(
    "leak",
    [
        "Client created: ",
        "Ingredient lot created",
        "produced as batch",
        "Whatever the future writes",
        WISH_TITLE,
        CLIENT_RECIPE_TITLE,
        "секрет",
        "metadata_json",
        "audit_logs",
        "#12",
        "#4",
        "#7",
        "default_tax_rate",
    ],
)
def test_no_raw_summary_metadata_id_or_table_name_appears_in_the_response(client, leak):
    response = client.get(AUDIT_LOGS_URL)
    assert leak not in response.text
    assert leak not in json.dumps(response.json(), ensure_ascii=False)


def test_the_serialized_response_contains_no_english_technical_prefix(client):
    payload = client.get(AUDIT_LOGS_URL).json()
    for item in payload["items"]:
        assert "created:" not in item["display_summary"].lower()
        assert "#" not in item["display_summary"]


def test_persisted_history_is_richer_than_what_the_api_returns(client):
    """The withheld values really are in the database — the API is what hides them."""
    stored = rows(client, "SELECT summary, entity_id, metadata_json FROM audit_logs WHERE action = 'client_wish.created'")[0]
    assert WISH_TITLE in stored["summary"]
    assert stored["entity_id"] == "1"
    assert "client_id" in stored["metadata_json"]
    assert WISH_TITLE not in client.get(AUDIT_LOGS_URL).text


# --------------------------------------------------------------------------
# Validation wire contract
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query,code",
    [
        ("limit=true", "non_integer_quantity"),
        ("limit=1.5", "non_integer_quantity"),
        ("limit=abc", "non_integer_quantity"),
        ("limit=-1", "negative_quantity"),
        ("offset=-1", "negative_quantity"),
        ("limit=0", "pagination_out_of_range"),
        ("limit=201", "pagination_out_of_range"),
    ],
)
def test_binding_pagination_examples_map_to_exactly_one_code(client, query, code):
    response = client.get(f"{AUDIT_LOGS_URL}?{query}")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code


@pytest.mark.parametrize("query", ["limit=200", "offset=0", "limit=1&offset=6"])
def test_accepted_pagination_examples(client, query):
    assert client.get(f"{AUDIT_LOGS_URL}?{query}").status_code == 200


def test_the_error_body_is_the_detail_envelope_and_not_pydantic_internals(client):
    payload = client.get(f"{AUDIT_LOGS_URL}?limit=0").json()
    assert set(payload) == {"detail"}
    assert set(payload["detail"]) == {"code", "message", "field", "value", "next_action"}
    assert isinstance(payload["detail"], dict)
    assert "type" not in payload["detail"]
    assert "loc" not in payload["detail"]
    assert "ctx" not in payload["detail"]


def test_malformed_dates_return_the_offending_field_and_value(client):
    response = client.get(f"{AUDIT_LOGS_URL}?created_from=2026-13-01T00:00:00Z")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_date"
    assert detail["field"] == "created_from"
    assert detail["value"] == "2026-13-01T00:00:00Z"


def test_the_date_range_conflict_names_created_before(client):
    response = client.get(f"{AUDIT_LOGS_URL}?created_from=2026-07-05T00:00:00Z&created_before=2026-07-01T00:00:00Z")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_date"
    assert detail["field"] == "created_before"
    assert detail["value"] == "2026-07-01T00:00:00Z"
    assert detail["message"] == "Конец периода должен быть позже его начала."
    assert detail["next_action"] == "Выберите дату окончания позже даты начала."


def test_validation_messages_are_russian_and_carry_no_technical_payload(client):
    for query in ("limit=abc", "offset=-1", "created_before=nope"):
        detail = client.get(f"{AUDIT_LOGS_URL}?{query}").json()["detail"]
        assert detail["message"] and detail["next_action"]
        for forbidden in ("Traceback", "SELECT", "sqlite", "/Users/", "pydantic"):
            assert forbidden not in json.dumps(detail, ensure_ascii=False)


# --------------------------------------------------------------------------
# Read-only guarantees
# --------------------------------------------------------------------------

def test_reads_change_no_audit_row_no_business_row_and_no_setting(client, tmp_path):
    audit_before = audit_snapshot(client)
    database_before = database_snapshot(client)
    settings_before = settings_snapshot(client)
    files_before = sorted(path.name for path in tmp_path.iterdir())

    for query in ("", "?limit=2", "?action=client.created", "?created_from=2026-07-01T00:00:00Z", "?limit=0"):
        client.get(f"{AUDIT_LOGS_URL}{query}")

    assert audit_snapshot(client) == audit_before
    assert database_snapshot(client) == database_before
    assert settings_snapshot(client) == settings_before
    assert sorted(path.name for path in tmp_path.iterdir()) == files_before


def test_reading_the_journal_is_never_itself_an_audited_event(client):
    before = len(audit_snapshot(client))
    for _ in range(5):
        client.get(AUDIT_LOGS_URL)
    assert len(audit_snapshot(client)) == before == 7


def test_historical_rows_are_never_normalized_or_re_summarized(client):
    """The English text and the internal IDs stay in the database, untouched."""
    before = audit_snapshot(client)
    client.get(AUDIT_LOGS_URL)
    after = audit_snapshot(client)
    assert after == before
    assert any("Ingredient lot created for ingredient #12" == row[6] for row in after)
