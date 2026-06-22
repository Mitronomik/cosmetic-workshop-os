from decimal import Decimal
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.domain.errors import DomainValidationError
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.stock_movements import StockMovementDraft
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.domain.units import UnitCode
from app.services.database import initialize_database
from app.services.ingredient_lots import IngredientLotService
from app.services.ingredients import IngredientService
from app.services.onboarding import ONBOARDING_SETTING_KEY, OnboardingService, OnboardingStepError
from app.services.packaging_items import PackagingItemService
from app.services.packaging_stock_movements import PackagingStockMovementInsufficientBalanceError, PackagingStockMovementService
from app.services.stock_movements import StockMovementInsufficientBalanceError, StockMovementService
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables


class FailingAuditRepository:
    def create_log(self, **kwargs):
        raise RuntimeError("simulated audit failure")


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "transactions.sqlite")
    initialize_database(config)
    return config


def scalar(config, sql, params=()):
    with sqlite3.connect(config.path) as connection:
        return connection.execute(sql, params).fetchone()[0]


def table_names(config):
    with sqlite3.connect(config.path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def create_ingredient(config):
    return IngredientService(config).create_ingredient(
        IngredientDraft.create(name="Demo Oil", category="oil", default_unit=UnitCode.GRAM)
    )


def create_lot(config):
    ingredient = create_ingredient(config)
    lot = IngredientLotService(config).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g"))
    return ingredient, lot


def test_successful_ingredient_create_writes_ingredient_and_audit(tmp_path):
    config = initialized_config(tmp_path)
    ingredient = create_ingredient(config)
    assert ingredient.id > 0
    assert scalar(config, "SELECT count(*) FROM ingredients") == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs WHERE action = 'ingredient.created'") == 1


def test_audit_failure_rolls_back_ingredient_create(tmp_path):
    config = initialized_config(tmp_path)
    service = IngredientService(config)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError, match="simulated audit failure"):
        service.create_ingredient(IngredientDraft.create(name="Rollback Oil", category="oil", default_unit="g"))
    assert scalar(config, "SELECT count(*) FROM ingredients WHERE name = 'Rollback Oil'") == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_ingredient_validation_failure_writes_no_audit(tmp_path):
    config = initialized_config(tmp_path)
    with pytest.raises(DomainValidationError):
        IngredientDraft.create(name=" ", category="oil", default_unit="g")
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_successful_lot_create_writes_lot_and_audit(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config)
    assert lot.id > 0
    assert scalar(config, "SELECT count(*) FROM ingredient_lots") == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs WHERE action = 'ingredient_lot.created'") == 1


def test_audit_failure_rolls_back_lot_create(tmp_path):
    config = initialized_config(tmp_path)
    ingredient = create_ingredient(config)
    before_audit_count = scalar(config, "SELECT count(*) FROM audit_logs")
    service = IngredientLotService(config)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g"))
    assert scalar(config, "SELECT count(*) FROM ingredient_lots") == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == before_audit_count


def test_lot_missing_ingredient_writes_no_audit(tmp_path):
    config = initialized_config(tmp_path)
    with pytest.raises(LookupError):
        IngredientLotService(config).create_lot(IngredientLotDraft.create(ingredient_id=999, unit="g"))
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_successful_stock_movement_create_writes_movement_and_audit(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config)
    movement = StockMovementService(config).create_movement(
        StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="10", unit="g")
    )
    assert movement.id > 0
    assert scalar(config, "SELECT count(*) FROM stock_movements") == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs WHERE action = 'stock_movement.created'") == 1


def test_audit_failure_rolls_back_stock_movement_and_balance(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config)
    movement_service = StockMovementService(config)
    movement_service.create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="receipt", quantity="10", unit="g"))
    before_balance = movement_service.calculate_lot_quantity(lot.id)
    before_count = scalar(config, "SELECT count(*) FROM stock_movements")
    movement_service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        movement_service.create_movement(StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="write_off", quantity="2", unit="g"))
    assert scalar(config, "SELECT count(*) FROM stock_movements") == before_count
    assert movement_service.calculate_lot_quantity(lot.id) == before_balance == Decimal("10.000")


def test_negative_outgoing_stock_movement_writes_no_movement_or_audit(tmp_path):
    config = initialized_config(tmp_path)
    _, lot = create_lot(config)
    before_audit_count = scalar(config, "SELECT count(*) FROM audit_logs")
    with pytest.raises(StockMovementInsufficientBalanceError):
        StockMovementService(config).create_movement(
            StockMovementDraft.create(ingredient_lot_id=lot.id, movement_type="write_off", quantity="1", unit="g")
        )
    assert scalar(config, "SELECT count(*) FROM stock_movements") == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == before_audit_count


def test_successful_packaging_item_create_writes_item_and_audit(tmp_path):
    config = initialized_config(tmp_path)
    item = PackagingItemService(config).create_packaging_item(PackagingItemDraft.create(name="Demo Jar", kind="jar"))
    assert item.id > 0
    assert scalar(config, "SELECT count(*) FROM packaging_items") == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs WHERE action = 'packaging_item.created'") == 1


def test_audit_failure_rolls_back_packaging_item_create(tmp_path):
    config = initialized_config(tmp_path)
    service = PackagingItemService(config)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_packaging_item(PackagingItemDraft.create(name="Rollback Jar", kind="jar"))
    assert scalar(config, "SELECT count(*) FROM packaging_items") == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_packaging_validation_failure_writes_no_audit(tmp_path):
    config = initialized_config(tmp_path)
    with pytest.raises(DomainValidationError):
        PackagingItemDraft.create(name=" ", kind="jar")
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_successful_packaging_stock_movement_create_writes_movement_and_audit(tmp_path):
    config = initialized_config(tmp_path)
    item = PackagingItemService(config).create_packaging_item(PackagingItemDraft.create(name="Demo Jar", kind="jar"))
    movement = PackagingStockMovementService(config).create_movement(
        PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="10", unit="pcs")
    )
    assert movement.id > 0
    assert scalar(config, "SELECT count(*) FROM packaging_stock_movements") == 1
    assert scalar(config, "SELECT count(*) FROM audit_logs WHERE action = 'packaging_stock_movement.created'") == 1


def test_audit_failure_rolls_back_packaging_stock_movement_and_balance(tmp_path):
    config = initialized_config(tmp_path)
    item = PackagingItemService(config).create_packaging_item(PackagingItemDraft.create(name="Demo Jar", kind="jar"))
    service = PackagingStockMovementService(config)
    service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="receipt", quantity="10", unit="pcs"))
    before_balance = service.calculate_packaging_item_quantity(item.id)
    before_count = scalar(config, "SELECT count(*) FROM packaging_stock_movements")
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.create_movement(PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="write_off", quantity="2", unit="pcs"))
    assert scalar(config, "SELECT count(*) FROM packaging_stock_movements") == before_count
    assert service.calculate_packaging_item_quantity(item.id) == before_balance == Decimal("10")


def test_negative_outgoing_packaging_stock_movement_writes_no_movement_or_audit(tmp_path):
    config = initialized_config(tmp_path)
    item = PackagingItemService(config).create_packaging_item(PackagingItemDraft.create(name="Demo Jar", kind="jar"))
    before_audit_count = scalar(config, "SELECT count(*) FROM audit_logs")
    with pytest.raises(PackagingStockMovementInsufficientBalanceError):
        PackagingStockMovementService(config).create_movement(
            PackagingStockMovementDraft.create(packaging_item_id=item.id, movement_type="write_off", quantity="1", unit="pcs")
        )
    assert scalar(config, "SELECT count(*) FROM packaging_stock_movements") == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == before_audit_count


def test_audit_failure_rolls_back_onboarding_start(tmp_path):
    config = initialized_config(tmp_path)
    service = OnboardingService(config)
    service.audit = FailingAuditRepository()
    with pytest.raises(RuntimeError):
        service.start()
    assert scalar(config, "SELECT count(*) FROM app_settings WHERE key = ?", (ONBOARDING_SETTING_KEY,)) == 0
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_invalid_onboarding_step_writes_no_audit(tmp_path):
    config = initialized_config(tmp_path)
    with pytest.raises(OnboardingStepError):
        OnboardingService(config).complete_step("unknown")
    assert scalar(config, "SELECT count(*) FROM audit_logs") == 0


def test_no_new_business_tables_or_migrations_for_transaction_foundation(tmp_path):
    config = initialized_config(tmp_path)
    tables = table_names(config)
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    assert scalar(config, "SELECT count(*) FROM schema_migrations") == 9
