import sqlite3
import pytest
try:
    from fastapi.testclient import TestClient
except RuntimeError:
    TestClient = None

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.purchase_suggestions import PurchaseSuggestionCandidate
from app.main import create_app
from app.repositories.purchase_suggestions import PurchaseSuggestionNotFoundError, PurchaseSuggestionRepository
from app.services.database import initialize_database
from app.services.purchase_suggestions import PurchaseSuggestionCommandService, PurchaseSuggestionGenerationService, PurchaseSuggestionValidationError
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables
from app.tests.test_production_confirmation import counts, scalar, seed_ready


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "purchase-suggestions.sqlite")
    initialize_database(c)
    return c


def tables(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def indexes(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='index'")}


def set_thresholds(c, ingredient_id, packaging_id, *, ingredient_min="100", packaging_min="5"):
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock=? WHERE id=?", (ingredient_min, ingredient_id))
        con.execute("UPDATE packaging_items SET minimum_stock=? WHERE id=?", (packaging_min, packaging_id))


def reasons(c, status="open"):
    return {s.reason for s in PurchaseSuggestionRepository(c).list_suggestions(status=status)}


def create_candidate(repo, key="below_minimum_stock:ingredient:1", reason="below_minimum_stock"):
    suggestion, _, _ = repo.upsert_open_candidate(PurchaseSuggestionCandidate(key, "ingredient", 1, "Water", "10", "g", reason, "ingredient", 1, "Купить компонент «Water»: не хватает 10 g.", "note"))
    return suggestion


def test_migration_creates_purchase_suggestions_table_indexes_and_guards(tmp_path):
    c = config(tmp_path); names = tables(c)
    assert "purchase_suggestions" in names
    assert {"idx_purchase_suggestions_key", "idx_purchase_suggestions_status_reason", "idx_purchase_suggestions_item"} <= indexes(c)
    assert_only_current_tables(names); assert_no_forbidden_future_tables(names)


def test_repository_list_get_and_not_found(tmp_path):
    c = config(tmp_path); repo = PurchaseSuggestionRepository(c)
    s = create_candidate(repo)
    assert repo.list_suggestions()[0].id == s.id
    assert repo.get_suggestion(s.id).suggestion_key == s.suggestion_key
    with pytest.raises(PurchaseSuggestionNotFoundError):
        repo.get_suggestion(999999)


def test_api_list_not_found_and_invalid_pagination(tmp_path, monkeypatch):
    if TestClient is None:
        pytest.skip("FastAPI TestClient is unavailable with the installed dependency set.")
    c = config(tmp_path); create_candidate(PurchaseSuggestionRepository(c))
    monkeypatch.setenv(DATABASE_PATH_ENV, str(c.path))
    client = TestClient(create_app())
    assert client.get("/api/purchase-suggestions").status_code == 200
    assert client.post("/api/purchase-suggestions/999999/mark-purchased").status_code == 404
    assert client.get("/api/purchase-suggestions?limit=0").status_code == 422
    assert client.get("/api/purchase-suggestions?status=bad").status_code == 422


def test_low_stock_and_order_shortages_generate_suggestions_and_quantities(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, order = seed_ready(c, lot_qty="10", packaging_qty=None)
    set_thresholds(c, ingredient.id, packaging.id, ingredient_min="100", packaging_min="5")
    result = PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    rows = PurchaseSuggestionRepository(c).list_suggestions(status="open")
    keys = {s.suggestion_key: s for s in rows}
    assert result.created_count == 4
    assert reasons(c) == {"below_minimum_stock", "insufficient_for_order"}
    assert keys[f"below_minimum_stock:ingredient:{ingredient.id}"].recommended_quantity == "90"
    assert keys[f"below_minimum_stock:packaging:{packaging.id}"].recommended_quantity == "5"
    assert keys[f"insufficient_for_order:ingredient:{ingredient.id}:order:{order.id}"].recommended_quantity == "40"
    assert keys[f"insufficient_for_order:packaging:{packaging.id}:order:{order.id}"].recommended_quantity == "1"


def test_invalid_zero_and_negative_minimum_stock_values_are_ignored(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="60", packaging_qty="2")
    invalid_values = ("not-a-number", "", "0", "-5")

    for value in invalid_values:
        with sqlite3.connect(c.path) as con:
            con.execute("UPDATE purchase_suggestions SET status='archived' WHERE status='open'")
            con.execute("UPDATE ingredients SET minimum_stock=? WHERE id=?", (value, ingredient.id))
            con.execute("UPDATE packaging_items SET minimum_stock=? WHERE id=?", (value, packaging.id))

        result = PurchaseSuggestionGenerationService(c).regenerate_suggestions()

        assert result.created_count == 0
        assert not PurchaseSuggestionRepository(c).list_suggestions(
            status="open",
            reason="below_minimum_stock",
        )


def test_valid_minimum_stock_still_generates_below_minimum_suggestions(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="10", packaging_qty="2")
    set_thresholds(c, ingredient.id, packaging.id, ingredient_min="15", packaging_min="3")

    PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    suggestions = {
        (suggestion.item_type, suggestion.item_id): suggestion
        for suggestion in PurchaseSuggestionRepository(c).list_suggestions(
            status="open",
            reason="below_minimum_stock",
        )
    }

    assert suggestions[("ingredient", ingredient.id)].recommended_quantity == "5"
    assert suggestions[("packaging", packaging.id)].recommended_quantity == "1"


def test_terminal_orders_do_not_create_order_based_suggestions(tmp_path):
    c = config(tmp_path)
    for status in ("produced", "delivered", "cancelled", "archived"):
        *_, order = seed_ready(c, lot_qty="1", packaging_qty=None)
        with sqlite3.connect(c.path) as con:
            con.execute("UPDATE orders SET status=?, is_active=? WHERE id=?", (status, 0 if status == "archived" else 1, order.id))
    PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    assert "insufficient_for_order" not in reasons(c)


def test_regeneration_is_idempotent_updates_open_archives_stale_and_preserves_terminal_manual(tmp_path):
    c = config(tmp_path)
    _, ingredient, _, packaging, _ = seed_ready(c, lot_qty="10", packaging_qty="10")
    set_thresholds(c, ingredient.id, packaging.id, ingredient_min="100", packaging_min="20")
    first = PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    second = PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    assert first.created_count == 3
    assert second.created_count == 0 and second.updated_count == 3
    assert scalar(c, "SELECT COUNT(*) FROM purchase_suggestions") == 3
    ing = PurchaseSuggestionRepository(c).list_suggestions(reason="below_minimum_stock", item_type="ingredient")[0]
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock='50' WHERE id=?", (ingredient.id,))
    PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    updated = PurchaseSuggestionRepository(c).get_suggestion(ing.id)
    assert updated.status == "open" and updated.recommended_quantity == "40"
    PurchaseSuggestionRepository(c).mark_purchased(ing.id)
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock='200' WHERE id=?", (ingredient.id,))
    PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    assert PurchaseSuggestionRepository(c).get_suggestion(ing.id).status == "purchased"
    manual = PurchaseSuggestionCommandService(c).create_manual(item_type="ingredient", item_id=ingredient.id, recommended_quantity="12", unit="g", notes="manual")
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE packaging_items SET minimum_stock='1' WHERE id=?", (packaging.id,))
    result = PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    assert result.archived_count >= 1
    assert PurchaseSuggestionRepository(c).get_suggestion(manual.id).status == "open"


def test_manual_update_and_terminal_status_preservation(tmp_path):
    c = config(tmp_path); _, ingredient, _, packaging, _ = seed_ready(c)
    service = PurchaseSuggestionCommandService(c)
    manual = service.create_manual(item_type="ingredient", item_id=ingredient.id, recommended_quantity="100", unit="g", notes="Нужно для идеи")
    assert manual.reason == "manual" and manual.status == "open"
    updated = service.update_open(manual.id, recommended_quantity="150", unit="g", notes="optional")
    assert updated.recommended_quantity == "150" and updated.notes == "optional"
    purchased = PurchaseSuggestionRepository(c).mark_purchased(manual.id)
    assert purchased.status == "purchased" and purchased.resolved_at is not None
    assert PurchaseSuggestionRepository(c).dismiss_suggestion(manual.id).status == "purchased"
    dismissed = service.create_manual(item_type="packaging", item_id=packaging.id, recommended_quantity="2", unit="pcs")
    assert PurchaseSuggestionRepository(c).dismiss_suggestion(dismissed.id).status == "dismissed"
    assert PurchaseSuggestionRepository(c).mark_purchased(dismissed.id).status == "dismissed"
    with pytest.raises(PurchaseSuggestionValidationError):
        service.create_manual(item_type="ingredient", item_id=99999, recommended_quantity="1", unit="g")
    with pytest.raises(PurchaseSuggestionValidationError):
        service.create_manual(item_type="packaging", item_id=packaging.id, recommended_quantity="0", unit="pcs")


def test_regeneration_and_mark_purchased_are_read_only_for_business_tables(tmp_path):
    c = config(tmp_path)
    _, ingredient, lot, packaging, order = seed_ready(c, lot_qty="10", packaging_qty=None)
    set_thresholds(c, ingredient.id, packaging.id)
    before_counts = counts(c)
    before = {table: scalar(c, f"SELECT COUNT(*) FROM {table}") for table in ["ingredients", "ingredient_lots", "packaging_items", "clients", "recipe_templates", "recipe_versions", "recipe_ingredients", "orders", "alerts"]}
    order_status = scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,))
    lot_count = scalar(c, "SELECT COUNT(*) FROM ingredient_lots")
    movement_count = scalar(c, "SELECT COUNT(*) FROM stock_movements")
    packaging_movement_count = scalar(c, "SELECT COUNT(*) FROM packaging_stock_movements")

    PurchaseSuggestionGenerationService(c).regenerate_suggestions()
    suggestion = PurchaseSuggestionRepository(c).list_suggestions()[0]
    PurchaseSuggestionRepository(c).mark_purchased(suggestion.id)

    assert counts(c) == before_counts
    assert {table: scalar(c, f"SELECT COUNT(*) FROM {table}") for table in before} == before
    assert scalar(c, "SELECT status FROM orders WHERE id=?", (order.id,)) == order_status
    assert scalar(c, "SELECT COUNT(*) FROM ingredient_lots") == lot_count
    assert scalar(c, "SELECT COUNT(*) FROM stock_movements") == movement_count
    assert scalar(c, "SELECT COUNT(*) FROM packaging_stock_movements") == packaging_movement_count
    assert scalar(c, "SELECT id FROM ingredient_lots WHERE id=?", (lot.id,)) == lot.id


def test_manual_api_smoke(tmp_path, monkeypatch):
    if TestClient is None:
        pytest.skip("FastAPI TestClient is unavailable with the installed dependency set.")
    c = config(tmp_path); _, ingredient, _, _, _ = seed_ready(c, lot_qty="0", packaging_qty="2")
    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE ingredients SET minimum_stock='10' WHERE id=?", (ingredient.id,))
    monkeypatch.setenv(DATABASE_PATH_ENV, str(c.path))
    client = TestClient(create_app())
    assert client.post("/api/purchase-suggestions/regenerate").json()["created_count"] >= 1
    open_rows = client.get("/api/purchase-suggestions").json()["purchase_suggestions"]
    assert open_rows
    sid = open_rows[0]["id"]
    stock_count_before = scalar(c, "SELECT COUNT(*) FROM stock_movements")
    packaging_stock_count_before = scalar(c, "SELECT COUNT(*) FROM packaging_stock_movements")
    lot_count_before = scalar(c, "SELECT COUNT(*) FROM ingredient_lots")
    assert client.post(f"/api/purchase-suggestions/{sid}/mark-purchased").json()["status"] == "purchased"
    assert all(row["id"] != sid for row in client.get("/api/purchase-suggestions").json()["purchase_suggestions"])
    assert any(row["id"] == sid for row in client.get("/api/purchase-suggestions?status=all").json()["purchase_suggestions"])
    assert scalar(c, "SELECT COUNT(*) FROM stock_movements") == stock_count_before
    assert scalar(c, "SELECT COUNT(*) FROM packaging_stock_movements") == packaging_stock_count_before
    assert scalar(c, "SELECT COUNT(*) FROM ingredient_lots") == lot_count_before
