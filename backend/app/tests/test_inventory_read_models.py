from datetime import date, timedelta
from decimal import Decimal
import sqlite3

from app.api.inventory import get_inventory_overview, list_ingredient_lot_balances, list_packaging_balances
from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.domain.stock_movements import StockMovementDraft
from app.domain.units import UnitCode
from app.services.database import initialize_database
from app.services.ingredient_lots import IngredientLotService
from app.services.ingredients import IngredientService
from app.services.inventory import DEFAULT_EXPIRATION_WINDOW_DAYS, InventoryService
from app.services.packaging_items import PackagingItemService
from app.services.packaging_stock_movements import PackagingStockMovementService
from app.services.stock_movements import StockMovementService
from app.api.inventory import router as inventory_router
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def scalar(config, sql):
    with sqlite3.connect(config.path) as connection:
        return connection.execute(sql).fetchone()[0]


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "inventory.sqlite")
    initialize_database(config)
    return config


def create_lot(config, *, name="Масло ши", expires_at=None, active=True):
    ingredient = IngredientService(config).create_ingredient(IngredientDraft.create(name=name, category="oil", default_unit=UnitCode.GRAM))
    lot = IngredientLotService(config).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g", expires_at=expires_at, lot_code="L-1"))
    if not active:
        lot = IngredientLotService(config).deactivate_lot(lot.id)
    return lot


def create_packaging(config, *, name="Баночка", active=True):
    item = PackagingItemService(config).create_packaging_item(PackagingItemDraft.create(name=name, kind="jar"))
    if not active:
        item = PackagingItemService(config).deactivate_packaging_item(item.id)
    return item


def test_inventory_read_models_add_no_migrations_or_tables(tmp_path):
    config = initialized_config(tmp_path)
    tables = table_names(config.path)
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    assert "inventory_balances" not in tables
    assert "current_quantity" not in {row[1] for row in sqlite3.connect(config.path).execute("PRAGMA table_info(ingredient_lots)")}
    assert "remaining_quantity" not in {row[1] for row in sqlite3.connect(config.path).execute("PRAGMA table_info(packaging_items)")}


def test_empty_inventory_returns_empty_balances_and_zero_overview(tmp_path):
    service = InventoryService(initialized_config(tmp_path))
    assert service.list_ingredient_lot_balances() == []
    assert service.list_packaging_balances() == []
    overview = service.get_overview()
    assert overview.ingredient_lots_total == 0
    assert overview.packaging_items_total == 0
    assert overview.generated_at


def test_ingredient_lot_balances_are_derived_from_movements_and_filters(tmp_path):
    config = initialized_config(tmp_path)
    lot = create_lot(config)
    inactive = create_lot(config, name="Инактив", active=False)
    service = InventoryService(config)
    assert service.list_ingredient_lot_balances()[0].balance_quantity == "0"
    StockMovementService(config).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="100.125", unit="g"))
    StockMovementService(config).create_movement(
        StockMovementDraft.create(
            ingredient_lot_id=lot.id,
            movement_type="manual_adjustment_out",
            quantity="40.025",
            unit="g",
            reason="inventory balance reconciliation",
        )
    )
    balances = service.list_ingredient_lot_balances()
    assert [row.lot_id for row in balances] == [lot.id]
    assert balances[0].balance_quantity == "60.100"
    assert balances[0].has_positive_balance is True
    assert service.list_ingredient_lot_balances(only_positive=True)[0].lot_id == lot.id
    assert inactive.id in [row.lot_id for row in service.list_ingredient_lot_balances(include_inactive=True)]


def test_ingredient_expiration_flags(tmp_path):
    config = initialized_config(tmp_path)
    today = date.today()
    expired = create_lot(config, name="Expired", expires_at=today - timedelta(days=1))
    soon = create_lot(config, name="Soon", expires_at=today + timedelta(days=DEFAULT_EXPIRATION_WINDOW_DAYS))
    missing = create_lot(config, name="Missing")
    rows = {row.lot_id: row for row in InventoryService(config).list_ingredient_lot_balances()}
    assert rows[expired.id].is_expired is True
    assert rows[expired.id].expires_soon is False
    assert rows[soon.id].expires_soon is True
    assert rows[soon.id].days_until_expiration == DEFAULT_EXPIRATION_WINDOW_DAYS
    assert rows[missing.id].is_expired is False
    assert rows[missing.id].expires_soon is False
    assert rows[missing.id].days_until_expiration is None


def test_packaging_balances_are_derived_from_piece_movements_and_filters(tmp_path):
    config = initialized_config(tmp_path)
    item = create_packaging(config)
    inactive = create_packaging(config, name="Неактивная", active=False)
    service = InventoryService(config)
    assert service.list_packaging_balances()[0].balance_quantity == "0"
    PackagingStockMovementService(config).create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="50", unit="pcs"))
    PackagingStockMovementService(config).create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="write_off", quantity="5", unit="pcs"))
    balances = service.list_packaging_balances()
    assert [row.packaging_item_id for row in balances] == [item.id]
    assert balances[0].balance_quantity == "45"
    assert balances[0].unit == UnitCode.PIECE
    assert balances[0].kind_label == "Баночка"
    assert service.list_packaging_balances(only_positive=True)[0].packaging_item_id == item.id
    assert inactive.id in [row.packaging_item_id for row in service.list_packaging_balances(include_inactive=True)]


def test_inventory_overview_counts(tmp_path):
    config = initialized_config(tmp_path)
    positive_lot = create_lot(config, expires_at=date.today())
    create_lot(config, name="Zero", expires_at=date.today() - timedelta(days=1))
    positive_packaging = create_packaging(config)
    create_packaging(config, name="ZeroPackaging")
    StockMovementService(config).create_movement(StockMovementDraft.create(ingredient_lot_id=positive_lot.id, movement_type="receipt", quantity="1", unit="g"))
    PackagingStockMovementService(config).create_movement(PackagingStockMovementDraft.create(packaging_item_id=positive_packaging.id, movement_type="receipt", quantity="2", unit="pcs"))
    overview = InventoryService(config).get_overview()
    assert overview.ingredient_lots_total == 2
    assert overview.ingredient_lots_with_positive_balance == 1
    assert overview.ingredient_lots_zero_balance == 1
    assert overview.ingredient_lots_expired == 1
    assert overview.ingredient_lots_expiring_soon == 1
    assert overview.packaging_items_total == 2
    assert overview.packaging_items_with_positive_balance == 1
    assert overview.packaging_items_zero_balance == 1


def test_inventory_api_functions_are_read_only(monkeypatch, tmp_path):
    database_path = tmp_path / "inventory-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)
    lot = create_lot(config)
    item = create_packaging(config)
    StockMovementService(config).create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="3", unit="g"))
    PackagingStockMovementService(config).create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="4", unit="pcs"))
    before_audit = scalar(config, "SELECT count(*) FROM audit_logs")
    before_stock = scalar(config, "SELECT count(*) FROM stock_movements")
    before_packaging_stock = scalar(config, "SELECT count(*) FROM packaging_stock_movements")
    assert list_ingredient_lot_balances().ingredient_lot_balances[0].balance_quantity == "3.000"
    assert list_packaging_balances().packaging_balances[0].balance_quantity == "4"
    assert get_inventory_overview().ingredient_lots_total == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs") == before_audit
    assert scalar(config, "SELECT count(*) FROM stock_movements") == before_stock
    assert scalar(config, "SELECT count(*) FROM packaging_stock_movements") == before_packaging_stock


def test_inventory_get_routes_are_registered():
    routes = {(route.path, tuple(sorted(route.methods))) for route in inventory_router.routes if hasattr(route, "methods")}
    assert ("/inventory/overview", ("GET",)) in routes
    assert ("/inventory/ingredient-lot-balances", ("GET",)) in routes
    assert ("/inventory/packaging-balances", ("GET",)) in routes
