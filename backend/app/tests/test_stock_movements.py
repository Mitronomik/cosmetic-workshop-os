from decimal import Decimal
import sqlite3

import pytest
from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.stock_movements import StockMovementDraft
from app.domain.units import UnitCode
from app.main import create_app
from app.repositories.stock_movements import (
    StockMovementInactiveLotError,
    StockMovementInsufficientBalanceError,
    StockMovementLotMissingError,
)
from app.services.database import initialize_database
from app.services.ingredient_lots import IngredientLotService
from app.services.ingredients import IngredientService
from app.services.stock_movements import StockMovementService
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "stock-movements.sqlite")
    initialize_database(config)
    return config


def create_ingredient(config, *, name="Demo Oil"):
    return IngredientService(config).create_ingredient(IngredientDraft.create(name=name, category="oil", default_unit=UnitCode.GRAM))


def create_lot(config, *, unit="g", active=True):
    ingredient = create_ingredient(config)
    lot = IngredientLotService(config).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit=unit))
    if not active:
        lot = IngredientLotService(config).deactivate_lot(lot.id)
    return ingredient, lot


def test_migration_creates_only_stock_movements_as_new_allowed_table(tmp_path):
    config = initialized_config(tmp_path)
    tables = table_names(config.path)
    assert {"schema_migrations", "app_settings", "audit_logs", "ingredients", "ingredient_lots", "stock_movements"} <= tables
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    with sqlite3.connect(config.path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(ingredient_lots)")}
    assert "remaining_quantity" not in columns


def test_create_receipt_movement_for_existing_active_lot(tmp_path):
    config = initialized_config(tmp_path)
    ingredient, lot = create_lot(config)

    movement = StockMovementService(config).create_movement(
        StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="100.1254", unit="g", reason="purchase")
    )

    assert movement.id > 0
    assert movement.ingredient_lot_id == lot.id
    assert movement.ingredient_id == ingredient.id
    assert movement.quantity == Decimal("100.125")
    assert movement.direction == "in"


def test_reject_movement_for_missing_lot(tmp_path):
    config = initialized_config(tmp_path)
    with pytest.raises(StockMovementLotMissingError):
        StockMovementService(config).create_movement(StockMovementDraft.create(ingredient_lot_id=999, movement_type="receipt", quantity="1", unit="g"))


def test_reject_movement_for_inactive_lot(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config, active=False)
    with pytest.raises(StockMovementInactiveLotError):
        StockMovementService(config).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="1", unit="g"))


@pytest.mark.parametrize(("quantity", "code"), [("0", DomainIssueCode.ZERO_QUANTITY), ("-1", DomainIssueCode.NEGATIVE_QUANTITY)])
def test_reject_zero_and_negative_quantity(quantity, code):
    with pytest.raises(DomainValidationError) as exc:
        StockMovementDraft.create(ingredient_lot_id=1, movement_type="receipt", quantity=quantity, unit="g")
    assert exc.value.issue.code == code


def test_reject_float_quantity():
    with pytest.raises(DomainValidationError) as exc:
        StockMovementDraft.create(ingredient_lot_id=1, movement_type="receipt", quantity=1.25, unit="g")
    assert exc.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED


def test_reject_percent_unit_and_fractional_pieces():
    with pytest.raises(DomainValidationError) as percent_exc:
        StockMovementDraft.create(ingredient_lot_id=1, movement_type="receipt", quantity="1", unit="percent")
    assert percent_exc.value.issue.code == DomainIssueCode.INVALID_UNIT
    with pytest.raises(DomainValidationError) as pieces_exc:
        StockMovementDraft.create(ingredient_lot_id=1, movement_type="receipt", quantity="1.5", unit="pcs")
    assert pieces_exc.value.issue.code == DomainIssueCode.NON_INTEGER_QUANTITY


def test_accept_decimal_grams_and_milliliters():
    grams = StockMovementDraft.create(ingredient_lot_id=1, movement_type="receipt", quantity="1.2345", unit="g")
    milliliters = StockMovementDraft.create(ingredient_lot_id=1, movement_type="receipt", quantity="2.3456", unit="ml")
    assert grams.quantity == Decimal("1.235")
    assert milliliters.quantity == Decimal("2.346")


def test_calculate_balance_and_outgoing_reduces_balance(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config)
    service = StockMovementService(config)
    service.create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="10", unit="g"))
    service.create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="write_off", quantity="2.5", unit="g"))
    assert service.calculate_lot_quantity(lot.id) == Decimal("7.500")


def test_outgoing_movement_cannot_make_balance_negative(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config)
    service = StockMovementService(config)
    service.create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="1", unit="g"))
    with pytest.raises(StockMovementInsufficientBalanceError):
        service.create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="write_off", quantity="2", unit="g"))


def test_stock_movements_are_immutable_no_update_delete_repository_methods():
    assert not hasattr(StockMovementService, "update_movement")
    assert not hasattr(StockMovementService, "delete_movement")


def test_stock_movements_api_create_read_list_balance_and_validation(monkeypatch, tmp_path):
    database_path = tmp_path / "api-stock-movements.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)
    _, lot = create_lot(config)
    from fastapi.testclient import TestClient

    client = TestClient(create_app())

    receipt = client.post("/api/stock-movements", json={"ingredient_lot_id": lot.id, "movement_type": "receipt", "quantity": "10", "unit": "g"})
    assert receipt.status_code == 201
    movement_id = receipt.json()["id"]
    assert client.get(f"/api/stock-movements/{movement_id}").json()["quantity"] == "10.000"
    assert len(client.get("/api/stock-movements").json()["movements"]) == 1
    assert len(client.get(f"/api/ingredient-lots/{lot.id}/movements").json()["movements"]) == 1
    assert client.get(f"/api/ingredient-lots/{lot.id}/balance").json()["quantity"] == "10.000"

    outgoing = client.post("/api/stock-movements", json={"ingredient_lot_id": lot.id, "movement_type": "write_off", "quantity": "3", "unit": "g"})
    assert outgoing.status_code == 201
    assert client.get(f"/api/ingredient-lots/{lot.id}/balance").json()["quantity"] == "7.000"

    assert client.post("/api/stock-movements", json={"ingredient_lot_id": lot.id, "movement_type": "write_off", "quantity": "99", "unit": "g"}).status_code == 409
    assert client.post("/api/stock-movements", json={"ingredient_lot_id": 999, "movement_type": "receipt", "quantity": "1", "unit": "g"}).status_code == 404
    assert client.post("/api/stock-movements", json={"ingredient_lot_id": lot.id, "movement_type": "receipt", "quantity": 1.2, "unit": "g"}).status_code == 422
