from datetime import date, timedelta
import sqlite3

import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.alerts import AlertCandidate
from app.main import create_app
from app.repositories.alerts import AlertNotFoundError, AlertRepository
from app.services.alerts import AlertGenerationService
from app.services.database import initialize_database
from app.tests.test_production_confirmation import counts, scalar, seed_ready


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "alerts.sqlite")
    initialize_database(c)
    return c


def set_thresholds(c, ingredient_id, packaging_id, *, ingredient_min="100", packaging_min="5", days=30):
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock=?, expiration_alert_days=? WHERE id=?", (ingredient_min, days, ingredient_id))
        con.execute("UPDATE packaging_items SET minimum_stock=? WHERE id=?", (packaging_min, packaging_id))


def alert_types(c, status="open"):
    return {a.type for a in AlertRepository(c).list_alerts(status=status)}


def test_regenerate_creates_mvp_alert_types_and_is_idempotent(tmp_path):
    c = config(tmp_path)
    _, ingredient, lot, packaging, order = seed_ready(c, lot_qty="10", packaging_qty=None)
    set_thresholds(c, ingredient.id, packaging.id)
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredient_lots SET expires_at=? WHERE id=?", ((date.today() + timedelta(days=5)).isoformat(), lot.id))

    first = AlertGenerationService(c).regenerate_alerts()
    second = AlertGenerationService(c).regenerate_alerts()

    assert first.created_count == 5
    assert second.created_count == 0
    assert second.updated_count == 5
    assert scalar(c, "SELECT COUNT(*) FROM alerts") == 5
    assert alert_types(c) == {"low_ingredient_stock", "low_packaging_stock", "ingredient_expiration_soon", "insufficient_materials_for_order", "insufficient_packaging_for_order"}


def test_expired_lot_alert_is_critical_and_not_soon(tmp_path):
    c = config(tmp_path)
    _, ingredient, lot, packaging, _ = seed_ready(c)
    set_thresholds(c, ingredient.id, packaging.id, ingredient_min="1", packaging_min="1")
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredient_lots SET expires_at=? WHERE id=?", ((date.today() - timedelta(days=1)).isoformat(), lot.id))
    AlertGenerationService(c).regenerate_alerts()

    alerts = AlertRepository(c).list_alerts(type="ingredient_expired")
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert "просрочена" in alerts[0].message
    assert "ingredient_expiration_soon" not in alert_types(c)


def test_condition_disappears_resolves_open_alert_and_resolved_is_not_reopened(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="10")
    set_thresholds(c, ingredient.id, packaging.id, ingredient_min="100", packaging_min="1")
    AlertGenerationService(c).regenerate_alerts()
    alert = AlertRepository(c).list_alerts(type="low_ingredient_stock")[0]

    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock='1' WHERE id=?", (ingredient.id,))
    result = AlertGenerationService(c).regenerate_alerts()
    assert result.resolved_count >= 1
    assert AlertRepository(c).get_alert(alert.id).status == "resolved"

    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock='100' WHERE id=?", (ingredient.id,))
    AlertGenerationService(c).regenerate_alerts()
    assert AlertRepository(c).get_alert(alert.id).status == "resolved"
    assert len(AlertRepository(c).list_alerts(status="all", type="low_ingredient_stock")) == 1


def test_dismissed_alert_is_not_reopened(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="10")
    set_thresholds(c, ingredient.id, packaging.id, ingredient_min="100", packaging_min="1")
    AlertGenerationService(c).regenerate_alerts()
    alert = AlertRepository(c).list_alerts(type="low_ingredient_stock")[0]
    AlertRepository(c).dismiss_alert(alert.id)

    AlertGenerationService(c).regenerate_alerts()

    assert AlertRepository(c).get_alert(alert.id).status == "dismissed"
    assert len(AlertRepository(c).list_alerts(status="all", type="low_ingredient_stock")) == 1


def test_produced_cancelled_archived_inactive_orders_do_not_create_order_shortage_alerts(tmp_path):
    c = config(tmp_path)
    for status in ("produced", "delivered", "cancelled", "archived"):
        *_, order = seed_ready(c, lot_qty="1", packaging_qty=None)
        with sqlite3.connect(c.path) as con:
            con.execute("UPDATE orders SET status=?, is_active=? WHERE id=?", (status, 0 if status == "archived" else 1, order.id))
    AlertGenerationService(c).regenerate_alerts()
    assert "insufficient_materials_for_order" not in alert_types(c)
    assert "insufficient_packaging_for_order" not in alert_types(c)


def test_regeneration_read_only_for_business_tables(tmp_path):
    c = config(tmp_path)
    _, ingredient, lot, packaging, order = seed_ready(c, lot_qty="10", packaging_qty=None)
    set_thresholds(c, ingredient.id, packaging.id)
    before_counts = counts(c)
    before = {table: scalar(c, f"SELECT COUNT(*) FROM {table}") for table in ["ingredients", "ingredient_lots", "packaging_items", "clients", "recipe_templates", "recipe_versions", "recipe_ingredients", "orders"]}
    status_before = scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,))
    lot_before = scalar(c, "SELECT expires_at FROM ingredient_lots WHERE id=?", (lot.id,))

    AlertGenerationService(c).regenerate_alerts()

    assert counts(c) == before_counts
    assert {table: scalar(c, f"SELECT COUNT(*) FROM {table}") for table in before} == before
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == status_before
    assert scalar(c, "SELECT expires_at FROM ingredient_lots WHERE id=?", (lot.id,)) == lot_before


def create_alert(repo, key, type="low_ingredient_stock"):
    alert, _, _ = repo.upsert_open_candidate(
        AlertCandidate(
            alert_key=key,
            type=type,
            severity="warning",
            message=f"Alert {key}",
            related_entity_type="ingredient",
            related_entity_id=1,
            recommended_action="Проверьте предупреждение.",
        )
    )
    return alert


def test_terminal_status_transitions_preserve_existing_terminal_state(tmp_path):
    c = config(tmp_path)
    repo = AlertRepository(c)
    resolved = create_alert(repo, "low_ingredient_stock:ingredient:101")
    dismissed = create_alert(repo, "low_packaging_stock:packaging:202", "low_packaging_stock")

    resolved_once = repo.resolve_alert(resolved.id)
    resolved_twice = repo.resolve_alert(resolved.id)
    resolved_after_dismiss_attempt = repo.dismiss_alert(resolved.id)
    dismissed_once = repo.dismiss_alert(dismissed.id)
    dismissed_twice = repo.dismiss_alert(dismissed.id)
    dismissed_after_resolve_attempt = repo.resolve_alert(dismissed.id)

    assert resolved_once.status == "resolved"
    assert resolved_twice == resolved_once
    assert resolved_after_dismiss_attempt == resolved_once
    assert resolved_twice.status == "resolved"
    assert resolved_after_dismiss_attempt.status == "resolved"
    assert resolved_after_dismiss_attempt.resolved_at is not None
    assert resolved_after_dismiss_attempt.dismissed_at is None
    assert dismissed_once.status == "dismissed"
    assert dismissed_twice == dismissed_once
    assert dismissed_after_resolve_attempt == dismissed_once
    assert dismissed_twice.status == "dismissed"
    assert dismissed_after_resolve_attempt.status == "dismissed"
    assert dismissed_after_resolve_attempt.dismissed_at is not None
    assert dismissed_after_resolve_attempt.resolved_at is None


def test_stale_resolution_is_scoped_to_managed_types(tmp_path):
    c = config(tmp_path)
    repo = AlertRepository(c)
    active_managed = create_alert(repo, "low_ingredient_stock:ingredient:1")
    stale_managed = create_alert(repo, "low_ingredient_stock:ingredient:2")
    unmanaged = create_alert(repo, "low_packaging_stock:packaging:3", "low_packaging_stock")
    resolved_terminal = repo.resolve_alert(create_alert(repo, "low_ingredient_stock:ingredient:4").id)
    dismissed_terminal = repo.dismiss_alert(create_alert(repo, "low_ingredient_stock:ingredient:5").id)

    changed = repo.mark_open_alerts_resolved_if_not_in_keys(
        {active_managed.alert_key},
        {"low_ingredient_stock"},
    )

    assert changed == 1
    assert repo.get_alert(active_managed.id).status == "open"
    assert repo.get_alert(stale_managed.id).status == "resolved"
    assert repo.get_alert(unmanaged.id).status == "open"
    assert repo.get_alert(resolved_terminal.id).status == "resolved"
    assert repo.get_alert(dismissed_terminal.id).status == "dismissed"


def test_stale_resolution_with_empty_active_keys_resolves_only_managed_open_alerts(tmp_path):
    c = config(tmp_path)
    repo = AlertRepository(c)
    managed = create_alert(repo, "ingredient_expired:ingredient_lot:1", "ingredient_expired")
    unmanaged = create_alert(repo, "low_packaging_stock:packaging:9", "low_packaging_stock")
    dismissed_managed = repo.dismiss_alert(create_alert(repo, "ingredient_expired:ingredient_lot:2", "ingredient_expired").id)

    changed = repo.mark_open_alerts_resolved_if_not_in_keys(set(), {"ingredient_expired"})

    assert changed == 1
    assert repo.get_alert(managed.id).status == "resolved"
    assert repo.get_alert(unmanaged.id).status == "open"
    assert repo.get_alert(dismissed_managed.id).status == "dismissed"
    assert repo.get_alert(dismissed_managed.id).resolved_at is None


def test_repository_status_transitions_and_not_found(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="10")
    set_thresholds(c, ingredient.id, packaging.id)
    AlertGenerationService(c).regenerate_alerts()
    repo = AlertRepository(c)
    alert = repo.list_alerts()[0]
    resolved = repo.resolve_alert(alert.id)
    assert resolved.status == "resolved"
    assert repo.resolve_alert(alert.id).status == "resolved"
    assert repo.dismiss_alert(alert.id).status == "resolved"
    assert repo.get_alert(alert.id).dismissed_at is None
    second = repo.list_alerts(status="open")[0]
    dismissed = repo.dismiss_alert(second.id)
    assert dismissed.status == "dismissed"
    assert repo.dismiss_alert(second.id).status == "dismissed"
    assert repo.resolve_alert(second.id).status == "dismissed"
    assert repo.get_alert(second.id).resolved_at is None
    with pytest.raises(AlertNotFoundError):
        repo.resolve_alert(999999)


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient dependencies are unavailable in this environment.")
def test_alert_api_list_regenerate_resolve_dismiss_and_validation(monkeypatch, tmp_path):
    db = tmp_path / "alerts-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="10")
    set_thresholds(c, ingredient.id, packaging.id)
    api = TestClient(create_app())

    assert api.post("/api/alerts/regenerate").status_code == 200
    body = api.get("/api/alerts").json()
    assert body["alerts"]
    first_id = body["alerts"][0]["id"]
    assert api.get("/api/alerts?status=all").status_code == 200
    assert api.post(f"/api/alerts/{first_id}/resolve").json()["status"] == "resolved"
    assert first_id not in [a["id"] for a in api.get("/api/alerts").json()["alerts"]]
    assert first_id in [a["id"] for a in api.get("/api/alerts?status=all").json()["alerts"]]
    open_id = api.get("/api/alerts").json()["alerts"][0]["id"]
    assert api.post(f"/api/alerts/{open_id}/dismiss").json()["status"] == "dismissed"
    assert api.post("/api/alerts/999999/resolve").status_code == 404
    assert api.get("/api/alerts?limit=0").status_code == 422
    assert api.get("/api/alerts?status=bad").status_code == 422
