"""API behavior, transaction boundaries and historical safety for the C1 tax rate."""

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
from app.services.demo_data import DemoDataService
from app.services.tax_rate_settings import DEFAULT_TAX_RATE_KEY

LEGACY_KEY = "tax.default_rate"
TAX_RATE_URL = "/api/settings/tax-rate"

pytestmark = pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")


@pytest.fixture
def client(monkeypatch, tmp_path):
    database = tmp_path / "tax-rate-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database))
    initialize_database(DatabaseConfig(path=database))
    test_client = TestClient(create_app())
    test_client.database_path = database  # type: ignore[attr-defined]
    return test_client


def rows(client, sql: str, parameters: tuple = ()) -> list[sqlite3.Row]:
    with sqlite3.connect(client.database_path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(sql, parameters).fetchall()


def setting_row(client, key: str = DEFAULT_TAX_RATE_KEY):
    found = rows(client, "SELECT key, value, value_type, description, updated_at FROM app_settings WHERE key = ?", (key,))
    return found[0] if found else None


def tax_audit_rows(client) -> list[sqlite3.Row]:
    return rows(client, "SELECT entity_id, summary, metadata_json, created_at FROM audit_logs WHERE action = 'tax_rate_setting_changed' ORDER BY id")


def without_timestamps(value: object) -> object:
    """Drop generation timestamps so report payloads compare on data only."""
    if isinstance(value, dict):
        return {key: without_timestamps(item) for key, item in value.items() if key != "generated_at"}
    if isinstance(value, list):
        return [without_timestamps(item) for item in value]
    return value


def business_snapshot(client) -> dict[str, object]:
    tables = [row["name"] for row in rows(client, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT IN ('app_settings','audit_logs')")]
    counts = {table: rows(client, f"SELECT COUNT(*) AS total FROM {table}")[0]["total"] for table in tables}
    batches = [dict(row) for row in rows(client, "SELECT * FROM production_batches ORDER BY id")]
    orders = [dict(row) for row in rows(client, "SELECT * FROM orders ORDER BY id")]
    movements = [dict(row) for row in rows(client, "SELECT * FROM stock_movements ORDER BY id")]
    packaging = [dict(row) for row in rows(client, "SELECT * FROM packaging_stock_movements ORDER BY id")]
    return {"counts": counts, "batches": batches, "orders": orders, "movements": movements, "packaging": packaging}


def seed_production_batch(client) -> dict[str, object]:
    """Seed one real production batch through the supported API flow."""
    DemoDataService(DatabaseConfig(path=client.database_path)).install(confirm_install=True, understand_demo_data=True)
    lot = client.post("/api/ingredient-lots", json={"ingredient_id": 4, "unit": "g", "unit_cost": "0.50"})
    assert lot.status_code == 201
    movement = client.post("/api/stock-movements", json={"ingredient_lot_id": lot.json()["id"], "movement_type": "receipt", "quantity": "1000", "unit": "g", "reason": "Подготовка производства", "source": "manual"})
    assert movement.status_code == 201
    readiness = client.post("/api/orders/1/check-production-readiness")
    assert readiness.json()["can_produce"] is True
    # No rate is configured at this point, so the honest C2-II confirmation
    # context is the explicit no-valid-rate pair.
    produced = client.post("/api/orders/1/produce", json={"confirm": True, "expected_tax_rate_percent": None, "expected_tax_rate_effective_at": None})
    assert produced.status_code == 200
    return produced.json()


def test_routes_are_registered_under_the_existing_settings_namespace():
    routes = {(route.path, tuple(sorted(route.methods))) for route in create_app().routes if hasattr(route, "methods")}
    assert (TAX_RATE_URL, ("GET",)) in routes
    assert (TAX_RATE_URL, ("PUT",)) in routes


def test_get_initial_state_is_unconfigured_and_leaves_the_legacy_row_intact(client):
    response = client.get(TAX_RATE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "tax_rate_percent": None,
        "is_configured": False,
        "effective_at": None,
        "message": "Налоговая ставка для расчётов пока не настроена.",
    }
    assert setting_row(client, LEGACY_KEY)["value"] == "0.06"
    assert setting_row(client) is None


def test_get_is_not_audited(client):
    client.get(TAX_RATE_URL)
    client.get(TAX_RATE_URL)

    assert tax_audit_rows(client) == []


@pytest.mark.parametrize(("payload", "canonical"), [("6", "6.00"), ("6.0", "6.00"), ("6.00", "6.00"), ("0", "0.00"), ("100", "100.00")])
def test_put_persists_and_returns_the_canonical_two_decimal_string(client, payload, canonical):
    response = client.put(TAX_RATE_URL, json={"tax_rate_percent": payload})

    assert response.status_code == 200
    body = response.json()
    assert body["tax_rate_percent"] == canonical
    assert body["is_configured"] is True
    assert body["effective_at"].endswith("Z")
    assert setting_row(client)["value"] == canonical
    assert client.get(TAX_RATE_URL).json()["tax_rate_percent"] == canonical


def test_api_timestamp_is_iso_utc_while_storage_stays_sqlite_text(client):
    effective_at = client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"}).json()["effective_at"]

    stored = setting_row(client)["updated_at"]
    assert "T" not in stored and stored.endswith(tuple("0123456789"))
    assert len(stored) == 19
    assert effective_at == f"{stored.replace(' ', 'T')}Z"


@pytest.mark.parametrize("payload", ["-1", "101", "100.01", "6.005", "6e1", "", "   ", "NaN", "Infinity", "6,5", "не число", "6%"])
def test_put_rejects_invalid_strings_with_structured_russian_errors(client, payload):
    response = client.put(TAX_RATE_URL, json={"tax_rate_percent": payload})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["field"] == "tax_rate_percent"
    assert detail["code"].startswith(("invalid_tax_rate", "tax_rate"))
    assert detail["message"]
    assert detail["next_action"]
    assert setting_row(client) is None
    assert tax_audit_rows(client) == []


@pytest.mark.parametrize("payload", [6, 6.0, 0, True, False, [], {}])
def test_put_rejects_json_numbers_bool_and_containers(client, payload):
    response = client.put(TAX_RATE_URL, json={"tax_rate_percent": payload})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_tax_rate_type"
    assert setting_row(client) is None
    assert tax_audit_rows(client) == []


@pytest.mark.parametrize("raw", ['{"tax_rate_percent": NaN}', '{"tax_rate_percent": Infinity}', '{"tax_rate_percent": -Infinity}'])
def test_put_rejects_non_finite_json_literals(client, raw):
    response = client.put(TAX_RATE_URL, content=raw.encode(), headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert setting_row(client) is None
    assert tax_audit_rows(client) == []


def test_invalid_request_changes_nothing_that_was_already_configured(client):
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})
    before = dict(setting_row(client))

    assert client.put(TAX_RATE_URL, json={"tax_rate_percent": "6.005"}).status_code == 422

    assert dict(setting_row(client)) == before
    assert setting_row(client)["value"] == "6.00"
    assert len(tax_audit_rows(client)) == 1


def test_first_configuration_and_real_change_are_each_audited_exactly_once(client):
    first = client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"}).json()
    second = client.put(TAX_RATE_URL, json={"tax_rate_percent": "0"}).json()

    audit = tax_audit_rows(client)
    assert len(audit) == 2
    assert [row["summary"] for row in audit] == ["Настроена налоговая ставка для расчётов.", "Изменена налоговая ставка для расчётов."]
    assert all(row["entity_id"] == DEFAULT_TAX_RATE_KEY for row in audit)
    assert second["tax_rate_percent"] == "0.00"
    assert second["is_configured"] is True
    assert first["effective_at"] < second["effective_at"]


def test_noop_save_preserves_value_and_timestamp_without_audit_or_changed_message(client):
    configured = client.put(TAX_RATE_URL, json={"tax_rate_percent": "6.00"}).json()

    repeated = client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})

    assert repeated.status_code == 200
    body = repeated.json()
    assert body["tax_rate_percent"] == "6.00"
    assert body["effective_at"] == configured["effective_at"]
    assert body["message"] == "Налоговая ставка уже сохранена без изменений."
    assert len(tax_audit_rows(client)) == 1


def test_clear_deletes_only_the_tax_rate_row_and_is_audited_once(client):
    configured = client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"}).json()

    cleared = client.put(TAX_RATE_URL, json={"tax_rate_percent": None})

    assert cleared.status_code == 200
    assert cleared.json() == {
        "tax_rate_percent": None,
        "is_configured": False,
        "effective_at": None,
        "message": "Налоговая ставка для расчётов очищена.",
    }
    assert setting_row(client) is None
    assert setting_row(client, LEGACY_KEY)["value"] == "0.06"
    audit = tax_audit_rows(client)
    assert len(audit) == 2
    metadata = json.loads(audit[1]["metadata_json"])
    assert metadata["previous_effective_at"] == configured["effective_at"]
    assert metadata["new_effective_at"] is None
    assert audit[1]["created_at"]


def test_noop_clear_performs_no_delete_and_no_audit(client):
    response = client.put(TAX_RATE_URL, json={"tax_rate_percent": None})

    assert response.status_code == 200
    assert response.json()["message"] == "Налоговая ставка уже не настроена."
    assert tax_audit_rows(client) == []
    assert setting_row(client, LEGACY_KEY)["value"] == "0.06"


def test_empty_string_is_not_a_substitute_for_clear(client):
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})

    assert client.put(TAX_RATE_URL, json={"tax_rate_percent": ""}).status_code == 422

    assert setting_row(client)["value"] == "6.00"


def test_missing_field_is_rejected_and_never_treated_as_clear(client):
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})

    assert client.put(TAX_RATE_URL, json={}).status_code == 422

    assert setting_row(client)["value"] == "6.00"
    assert len(tax_audit_rows(client)) == 1


def test_legacy_key_stays_byte_for_byte_unchanged_across_configure_change_and_clear(client):
    before = dict(setting_row(client, LEGACY_KEY))

    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})
    assert dict(setting_row(client, LEGACY_KEY)) == before
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "7"})
    assert dict(setting_row(client, LEGACY_KEY)) == before
    client.put(TAX_RATE_URL, json={"tax_rate_percent": None})
    assert dict(setting_row(client, LEGACY_KEY)) == before


def test_rapid_successive_changes_receive_strictly_increasing_effective_times(client):
    effective_times = [client.put(TAX_RATE_URL, json={"tax_rate_percent": str(value)}).json()["effective_at"] for value in (1, 2, 3, 4)]

    assert effective_times == sorted(set(effective_times))
    assert len(tax_audit_rows(client)) == 4


def test_settings_status_marks_default_tax_rate_editable_and_nothing_else(client):
    groups = client.get("/api/settings/status").json()["setting_groups"]

    editable = {item["id"] for group in groups for item in group["items"] if item["status"] == "editable_now"}
    assert editable == {"workshop_name", "master_name", "workshop_contact_text", "workshop_note", "default_tax_rate"}
    calculation = next(group for group in groups if group["id"] == "calculation_sensitive_candidates")
    tax_item = next(item for item in calculation["items"] if item["id"] == "default_tax_rate")
    assert tax_item["affects_calculations"] is True
    assert tax_item["affects_historical_data"] is True
    assert tax_item["requires_backend_service"] is True
    assert "не пересчитываются" in tax_item["safety_note"]
    assert {item["id"] for item in calculation["items"] if item["status"] != "requires_backend_rules"} == {"default_tax_rate"}


def test_workshop_profile_behavior_is_unchanged_by_the_tax_setting(client):
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})

    saved = client.put("/api/settings/workshop-profile", json={"workshop_name": "Мастерская", "master_name": "Мария", "workshop_contact_text": "Телефон", "workshop_note": "Уход"})

    assert saved.status_code == 200
    assert saved.json()["profile"]["workshop_name"] == "Мастерская"
    assert client.get(TAX_RATE_URL).json()["tax_rate_percent"] == "6.00"
    assert len(tax_audit_rows(client)) == 1
    assert rows(client, "SELECT COUNT(*) AS total FROM audit_logs WHERE action LIKE 'workshop%'")[0]["total"] == 0


def test_tax_setting_never_mutates_orders_batches_movements_or_report_data(client):
    batch = seed_production_batch(client)
    before = business_snapshot(client)
    reports_before = {name: client.get(f"/api/reports/{name}").json() for name in ("overview", "inventory", "orders", "production", "finance")}

    assert client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"}).status_code == 200
    assert client.put(TAX_RATE_URL, json={"tax_rate_percent": "0"}).status_code == 200
    assert client.put(TAX_RATE_URL, json={"tax_rate_percent": "6.005"}).status_code == 422
    assert client.put(TAX_RATE_URL, json={"tax_rate_percent": None}).status_code == 200
    client.get(TAX_RATE_URL)

    after = business_snapshot(client)
    assert after == before
    assert after["batches"][0]["tax"] is None
    assert after["batches"][0]["margin"] is None
    assert after["batches"][0]["margin_percent"] is None
    assert after["batches"][0]["sale_price"] == batch["sale_price"]
    assert after["batches"][0]["total_cost"] == batch["total_cost"]
    for name, before_report in reports_before.items():
        assert without_timestamps(client.get(f"/api/reports/{name}").json()) == without_timestamps(before_report)


def test_configured_rate_does_not_populate_existing_batch_financials(client):
    seed_production_batch(client)
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})

    detail = client.get("/api/production-batches/1").json()

    assert detail["tax"] is None
    assert detail["margin"] is None
    assert detail["margin_percent"] is None


def test_readiness_tax_estimate_remains_c2_work(client):
    """Configuring a rate never reaches back into an already-produced batch.

    This assertion first proved that readiness ignored the C1 setting, then that
    `C2-I` estimated without persisting. Under `C2-II` it proves historical
    immutability: the batch was produced under the no-valid-rate context, so its
    financial snapshots stay `null` even though readiness now estimates with the
    rate configured afterwards.
    """
    seed_production_batch(client)
    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})

    readiness = client.post("/api/orders/2/check-production-readiness").json()

    assert readiness["tax_rate_percent"] == "6.00"
    assert readiness["sale_price"] == "1400.00"
    assert readiness["estimated_tax"] == "84.00"
    assert readiness["estimated_margin"] == "1192.35"
    assert readiness["financial_estimate_status"] == "available"
    assert business_snapshot(client)["batches"][0]["tax"] is None
    assert business_snapshot(client)["batches"][0]["margin"] is None
    assert business_snapshot(client)["batches"][0]["margin_percent"] is None


def test_no_new_table_or_migration_is_introduced(client):
    tables = {row["name"] for row in rows(client, "SELECT name FROM sqlite_master WHERE type='table'")}
    before_migrations = [dict(row) for row in rows(client, "SELECT migration_id, applied_at FROM schema_migrations ORDER BY migration_id")]

    client.put(TAX_RATE_URL, json={"tax_rate_percent": "6"})
    client.put(TAX_RATE_URL, json={"tax_rate_percent": None})

    assert {row["name"] for row in rows(client, "SELECT name FROM sqlite_master WHERE type='table'")} == tables
    assert [dict(row) for row in rows(client, "SELECT migration_id, applied_at FROM schema_migrations ORDER BY migration_id")] == before_migrations
    assert not {"tax_rate_history", "tax_periods", "tax_rate_versions"} & tables


def test_production_batches_table_has_no_tax_snapshot_columns_yet(client):
    """Historical node ID deliberately preserved; the contract it guards changed.

    The name dates from C1, when the assertion was that neither snapshot column
    existed. `C2-II` authorizes exactly two nullable columns, so the assertions
    now check the opposite — both exist, nullable, with nothing else added.

    The node ID is kept unchanged on purpose so every previously collected
    backend test node is still collected, rather than renaming the test and
    losing it from the collected set. Only the body moved forward.
    """
    columns = {row["name"]: row for row in rows(client, "PRAGMA table_info(production_batches)")}

    assert "tax_rate_percent_snapshot" in columns
    assert "tax_rate_effective_at_snapshot" in columns
    for name in ("tax_rate_percent_snapshot", "tax_rate_effective_at_snapshot"):
        assert columns[name]["type"] == "TEXT"
        assert columns[name]["notnull"] == 0
        assert columns[name]["dflt_value"] is None
    assert not {"sale_price_snapshot", "total_cost_snapshot", "tax_amount_snapshot", "margin_amount_snapshot", "taxable_amount_snapshot"} & set(columns)
