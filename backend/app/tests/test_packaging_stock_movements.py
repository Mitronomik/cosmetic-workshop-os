from decimal import Decimal
import sqlite3

import pytest

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.packaging_items import PackagingItemDraft
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.domain.units import UnitCode
from app.services.database import initialize_database
from app.services.packaging_items import PackagingItemService
from app.services.packaging_stock_movements import (
    PackagingStockMovementInactiveItemError,
    PackagingStockMovementInsufficientBalanceError,
    PackagingStockMovementItemMissingError,
    PackagingStockMovementService,
)
from app.tests.table_guards import CURRENT_ALLOWED_TABLES, FORBIDDEN_FUTURE_TABLES, assert_no_forbidden_future_tables, assert_only_current_tables


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def columns(database_path, table):
    with sqlite3.connect(database_path) as connection:
        return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def scalar(config, sql, params=()):
    with sqlite3.connect(config.path) as connection:
        return connection.execute(sql, params).fetchone()[0]


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "packaging-stock.sqlite")
    initialize_database(config)
    return config


def create_item(config):
    return PackagingItemService(config).create_packaging_item(PackagingItemDraft.create(name="Баночка 30 мл", kind="jar"))


def test_migration_creates_packaging_stock_movements_only_current_scope(tmp_path):
    config = initialized_config(tmp_path)
    tables = table_names(config.path)
    assert "packaging_stock_movements" in tables
    assert "packaging_stock_movements" in CURRENT_ALLOWED_TABLES
    assert {"recipes", "backup_records"} <= FORBIDDEN_FUTURE_TABLES
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    assert "packaging_lots" not in tables
    item_columns = columns(config.path, "packaging_items")
    assert "current_quantity" not in item_columns
    assert "remaining_quantity" not in item_columns


def test_valid_receipt_and_outgoing_movements_update_derived_balance(tmp_path):
    config = initialized_config(tmp_path)
    item = create_item(config)
    service = PackagingStockMovementService(config)
    receipt = service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="100", unit="pcs"))
    assert receipt.id > 0
    assert service.calculate_packaging_item_quantity(item.id) == Decimal("100")
    out = service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="manual_adjustment_out", quantity="25", unit="pcs", reason="inventory recount"))
    assert out.id > 0
    assert service.calculate_packaging_item_quantity(item.id) == Decimal("75")


@pytest.mark.parametrize(
    ("movement_type", "expected"),
    [
        ("receipt", Decimal("10")),
        ("manual_adjustment_in", Decimal("10")),
        ("manual_adjustment_out", Decimal("5")),
        ("write_off", Decimal("5")),
        ("return_to_supplier", Decimal("5")),
    ],
)
def test_movement_types_affect_balance_by_direction(tmp_path, movement_type, expected):
    config = initialized_config(tmp_path)
    item = create_item(config)
    service = PackagingStockMovementService(config)
    if movement_type not in {"receipt", "manual_adjustment_in"}:
        service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="10", unit="pcs"))
    service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type=movement_type, quantity="5" if expected == Decimal("5") else "10", unit="pcs", reason="inventory recount"))
    assert service.calculate_packaging_item_quantity(item.id) == expected


@pytest.mark.parametrize("item_id", [0, -1, "", True, None])
def test_reject_empty_or_invalid_packaging_item_id_uses_packaging_message(item_id):
    with pytest.raises(DomainValidationError) as exc:
        PackagingStockMovementDraft.create(packaging_item_id=item_id, movement_type="receipt", quantity="1", unit="pcs")
    assert exc.value.issue.code == DomainIssueCode.REQUIRED_FIELD
    assert exc.value.issue.field == "packaging_item_id"
    assert "тар" in exc.value.issue.message.lower() or "упаков" in exc.value.issue.message.lower()
    assert "тар" in exc.value.issue.next_action.lower() or "упаков" in exc.value.issue.next_action.lower()
    assert "ингредиент" not in exc.value.issue.message.lower()
    assert "компонент" not in exc.value.issue.message.lower()
    assert "ингредиент" not in exc.value.issue.next_action.lower()
    assert "компонент" not in exc.value.issue.next_action.lower()


def test_reject_missing_and_inactive_packaging_item(tmp_path):
    config = initialized_config(tmp_path)
    service = PackagingStockMovementService(config)
    with pytest.raises(PackagingStockMovementItemMissingError):
        service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=999, movement_type="receipt", quantity="1", unit="pcs"))
    item = create_item(config)
    PackagingItemService(config).deactivate_packaging_item(item.id)
    with pytest.raises(PackagingStockMovementInactiveItemError):
        service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="1", unit="pcs"))


@pytest.mark.parametrize("movement_type", ["", "purchase", "production_usage"])
def test_reject_invalid_movement_type(movement_type):
    with pytest.raises(DomainValidationError):
        PackagingStockMovementDraft.create(packaging_item_id=1, movement_type=movement_type, quantity="1", unit="pcs")


@pytest.mark.parametrize(("quantity", "code"), [("0", DomainIssueCode.ZERO_QUANTITY), ("-1", DomainIssueCode.NEGATIVE_QUANTITY), ("2.5", DomainIssueCode.NON_INTEGER_QUANTITY), (10.5, DomainIssueCode.FLOAT_NOT_ALLOWED)])
def test_reject_invalid_quantities(quantity, code):
    with pytest.raises(DomainValidationError) as exc:
        PackagingStockMovementDraft.create(packaging_item_id=1, movement_type="receipt", quantity=quantity, unit="pcs")
    assert exc.value.issue.code == code


@pytest.mark.parametrize("unit", ["percent", "ml", "g", "box"])
def test_reject_non_piece_units(unit):
    with pytest.raises(DomainValidationError) as exc:
        PackagingStockMovementDraft.create(packaging_item_id=1, movement_type="receipt", quantity="1", unit=unit)
    assert exc.value.issue.code == DomainIssueCode.INVALID_UNIT


def test_negative_balance_rejected_without_movement_or_audit(tmp_path):
    config = initialized_config(tmp_path)
    item = create_item(config)
    before_audit = scalar(config, "SELECT count(*) FROM audit_logs")
    service = PackagingStockMovementService(config)
    with pytest.raises(PackagingStockMovementInsufficientBalanceError):
        service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="write_off", quantity="1", unit="pcs"))
    assert scalar(config, "SELECT count(*) FROM packaging_stock_movements") == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == before_audit


def test_packaging_stock_movement_api_route_functions(monkeypatch, tmp_path):
    from fastapi import HTTPException

    from app.api.packaging_stock_movements import create_packaging_stock_movement, get_packaging_item_balance, get_packaging_stock_movement, list_packaging_stock_movements, list_packaging_stock_movements_by_item
    from app.schemas.packaging_stock_movements import PackagingStockMovementCreateRequest

    database_path = tmp_path / "api-packaging-stock.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)
    item = create_item(config)

    created = create_packaging_stock_movement(PackagingStockMovementCreateRequest(packaging_item_id=item.id, movement_type="receipt", quantity="10", unit=UnitCode.PIECE))
    assert created.id > 0
    assert get_packaging_stock_movement(created.id).id == created.id
    assert len(list_packaging_stock_movements().movements) == 1
    assert len(list_packaging_stock_movements_by_item(item.id).movements) == 1
    assert get_packaging_item_balance(item.id).quantity == "10"

    with pytest.raises(HTTPException) as negative:
        create_packaging_stock_movement(PackagingStockMovementCreateRequest(packaging_item_id=item.id, movement_type="write_off", quantity="11", unit=UnitCode.PIECE))
    assert negative.value.status_code == 409

@pytest.mark.parametrize("movement_type", ["manual_adjustment_in", "manual_adjustment_out"])
@pytest.mark.parametrize("reason", ["", "   "])
def test_packaging_manual_adjustment_requires_reason_domain(movement_type, reason):
    with pytest.raises(DomainValidationError) as exc:
        PackagingStockMovementDraft.create(packaging_item_id=1, movement_type=movement_type, quantity="1", unit="pcs", reason=reason)
    assert exc.value.issue.field == "reason"
    assert exc.value.issue.message == "Укажите причину ручной корректировки склада."


def test_packaging_manual_adjustment_without_reason_api_is_structured_422_and_writes_nothing(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app

    database_path = tmp_path / "api-packaging-manual-reason.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)
    item = create_item(config)
    client = TestClient(create_app())

    receipt = client.post("/api/packaging-stock-movements", json={"packaging_item_id": item.id, "movement_type": "receipt", "quantity": "5", "unit": "pcs", "reason": "seed"})
    assert receipt.status_code == 201

    rejected = client.post("/api/packaging-stock-movements", json={"packaging_item_id": item.id, "movement_type": "manual_adjustment_out", "quantity": "1", "unit": "pcs", "reason": "   "})
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["field"] == "reason"
    assert rejected.json()["detail"]["message"] == "Укажите причину ручной корректировки склада."
    assert len(client.get(f"/api/packaging-items/{item.id}/stock-movements").json()["movements"]) == 1
    assert client.get(f"/api/packaging-items/{item.id}/balance").json()["quantity"] == "5"

    accepted = client.post("/api/packaging-stock-movements", json={"packaging_item_id": item.id, "movement_type": "manual_adjustment_out", "quantity": "1", "unit": "pcs", "reason": "inventory recount"})
    assert accepted.status_code == 201
    assert len(client.get(f"/api/packaging-items/{item.id}/stock-movements").json()["movements"]) == 2
