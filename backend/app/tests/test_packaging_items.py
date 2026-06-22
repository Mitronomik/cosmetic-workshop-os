from decimal import Decimal
import sqlite3

import pytest
from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.packaging_items import PackagingItemDraft
from app.domain.units import UnitCode
from app.main import create_app
from app.services.database import initialize_database
from app.services.packaging_items import PackagingItemService
from app.tests.table_guards import CURRENT_ALLOWED_TABLES, FORBIDDEN_FUTURE_TABLES, assert_no_forbidden_future_tables, assert_only_current_tables


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def columns(database_path, table):
    with sqlite3.connect(database_path) as connection:
        return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "packaging-items.sqlite")
    initialize_database(config)
    return config


def test_table_guards_treat_packaging_as_current_and_future_tables_forbidden():
    assert "packaging_items" in CURRENT_ALLOWED_TABLES
    assert "packaging_items" not in FORBIDDEN_FUTURE_TABLES
    assert {"recipes", "orders", "production_batches", "import_drafts", "backup_records"} <= FORBIDDEN_FUTURE_TABLES


def test_migration_creates_packaging_items_without_future_tables_or_balance_columns(tmp_path):
    config = initialized_config(tmp_path)
    tables = table_names(config.path)
    assert {"schema_migrations", "app_settings", "audit_logs", "ingredients", "ingredient_lots", "stock_movements", "packaging_items"} <= tables
    assert_only_current_tables(tables)
    assert_no_forbidden_future_tables(tables)
    item_columns = columns(config.path, "packaging_items")
    assert "remaining_quantity" not in item_columns
    assert "current_quantity" not in item_columns
    assert "packaging_stock_movements" in tables


def test_create_get_list_update_and_deactivate_packaging_item(tmp_path):
    config = initialized_config(tmp_path)
    service = PackagingItemService(config)
    created = service.create_packaging_item(PackagingItemDraft.create(name="  Баночка   30 мл ", kind="jar", capacity_value="30", capacity_unit="ml", unit_cost="12.345", material="  стекло "))
    assert created.id > 0
    assert created.name == "Баночка 30 мл"
    assert created.capacity_value == Decimal("30.000")
    assert created.unit_cost == Decimal("12.35")
    assert created.material == "стекло"
    assert service.get_packaging_item(created.id).name == "Баночка 30 мл"
    assert [item.id for item in service.list_active_packaging_items()] == [created.id]

    updated = service.update_packaging_item(created.id, PackagingItemDraft.create(name="Флакон 50 мл", kind="bottle", capacity_value="50", capacity_unit="ml"))
    assert updated.kind == "bottle"
    assert updated.capacity_value == Decimal("50.000")

    deactivated = service.deactivate_packaging_item(created.id)
    assert deactivated.is_active is False
    assert service.list_active_packaging_items() == []


@pytest.mark.parametrize("name", ["", "   "])
def test_reject_empty_name(name):
    with pytest.raises(DomainValidationError) as exc:
        PackagingItemDraft.create(name=name, kind="jar")
    assert exc.value.issue.code == DomainIssueCode.REQUIRED_FIELD


def test_reject_invalid_kind():
    with pytest.raises(DomainValidationError) as exc:
        PackagingItemDraft.create(name="Тара", kind="bucket")
    assert exc.value.issue.code == DomainIssueCode.INVALID_CATEGORY


@pytest.mark.parametrize("unit", ["kg", "g", "ml", "percent"])
def test_reject_invalid_or_non_piece_units(unit):
    with pytest.raises(DomainValidationError) as exc:
        PackagingItemDraft.create(name="Тара", kind="jar", unit=unit)
    assert exc.value.issue.code == DomainIssueCode.INVALID_UNIT


def test_accept_missing_capacity():
    item = PackagingItemDraft.create(name="Этикетка", kind="label")
    assert item.capacity_value is None
    assert item.capacity_unit is None


def test_reject_capacity_value_without_capacity_unit():
    with pytest.raises(DomainValidationError) as exc:
        PackagingItemDraft.create(name="Тара", kind="jar", capacity_value="30")
    assert exc.value.issue.code == DomainIssueCode.REQUIRED_FIELD


@pytest.mark.parametrize("capacity", ["0", "-1"])
def test_reject_non_positive_capacity(capacity):
    with pytest.raises(DomainValidationError) as exc:
        PackagingItemDraft.create(name="Тара", kind="jar", capacity_value=capacity, capacity_unit="ml")
    assert exc.value.issue.code == DomainIssueCode.ZERO_QUANTITY


def test_reject_float_capacity_and_float_unit_cost():
    with pytest.raises(DomainValidationError) as capacity_exc:
        PackagingItemDraft.create(name="Тара", kind="jar", capacity_value=30.5, capacity_unit="ml")
    assert capacity_exc.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED
    with pytest.raises(DomainValidationError) as cost_exc:
        PackagingItemDraft.create(name="Тара", kind="jar", unit_cost=1.2)
    assert cost_exc.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED


def test_reject_negative_unit_cost():
    with pytest.raises(DomainValidationError) as exc:
        PackagingItemDraft.create(name="Тара", kind="jar", unit_cost="-0.01")
    assert exc.value.issue.code == DomainIssueCode.NEGATIVE_QUANTITY


def test_packaging_item_api_route_functions_create_read_list_update_deactivate_and_validate(monkeypatch, tmp_path):
    from fastapi import HTTPException

    from app.api.packaging_items import create_packaging_item, deactivate_packaging_item, get_packaging_item, list_active_packaging_items, update_packaging_item
    from app.schemas.packaging_items import PackagingItemCreateRequest, PackagingItemUpdateRequest

    database_path = tmp_path / "api-packaging.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))

    created = create_packaging_item(PackagingItemCreateRequest(name="Баночка 30 мл", kind="jar", capacity_value="30", capacity_unit="ml", unit_cost="10.5"))
    assert created.id > 0
    assert created.unit == UnitCode.PIECE
    assert get_packaging_item(created.id).name == "Баночка 30 мл"
    assert len(list_active_packaging_items().packaging_items) == 1

    updated = update_packaging_item(created.id, PackagingItemUpdateRequest(name="Флакон 50 мл", kind="bottle", capacity_value="50", capacity_unit="ml"))
    assert updated.name == "Флакон 50 мл"

    with pytest.raises(HTTPException) as invalid_name:
        create_packaging_item(PackagingItemCreateRequest(name=" ", kind="jar"))
    assert invalid_name.value.status_code == 422

    with pytest.raises(HTTPException) as invalid_unit:
        create_packaging_item(PackagingItemCreateRequest(name="Тара", kind="jar", unit="percent"))
    assert invalid_unit.value.status_code == 422

    deactivated = deactivate_packaging_item(created.id)
    assert deactivated.is_active is False
    assert list_active_packaging_items().packaging_items == []


def test_packaging_item_api_responses_include_catalog_assignments(monkeypatch, tmp_path):
    from app.api.catalog_assignments import packaging_category, packaging_tags
    from app.api.packaging_items import create_packaging_item, get_packaging_item, list_active_packaging_items, update_packaging_item
    from app.domain.catalog import CatalogCategoryDraft, CatalogTagDraft
    from app.schemas.catalog import CatalogCategoryAssignmentRequest, CatalogTagsAssignmentRequest
    from app.schemas.packaging_items import PackagingItemCreateRequest, PackagingItemUpdateRequest
    from app.services.catalog import CatalogService

    database_path = tmp_path / "api-packaging-catalog.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)

    created = create_packaging_item(PackagingItemCreateRequest(name="Баночка 30 мл", kind="jar"))
    assert created.catalog_category_id is None
    assert created.catalog_tag_ids == []

    catalog = CatalogService(config)
    category = catalog.create_category(CatalogCategoryDraft.create(scope="packaging", name="Баночки"))
    tag_one = catalog.create_tag(CatalogTagDraft.create(scope="packaging", name="Для кремов"))
    tag_two = catalog.create_tag(CatalogTagDraft.create(scope="packaging", name="Стекло"))

    packaging_category(created.id, CatalogCategoryAssignmentRequest(catalog_category_id=category.id))
    packaging_tags(created.id, CatalogTagsAssignmentRequest(tag_ids=[tag_two.id, tag_one.id, tag_one.id]))

    listed = list_active_packaging_items().packaging_items[0]
    loaded = get_packaging_item(created.id)
    assert listed.catalog_category_id == category.id
    assert listed.catalog_tag_ids == [tag_one.id, tag_two.id]
    assert loaded.catalog_category_id == category.id
    assert loaded.catalog_tag_ids == [tag_one.id, tag_two.id]

    updated = update_packaging_item(
        created.id,
        PackagingItemUpdateRequest(name="Флакон 50 мл", kind="bottle", capacity_value="50", capacity_unit="ml"),
    )
    assert updated.name == "Флакон 50 мл"
    assert updated.catalog_category_id == category.id
    assert updated.catalog_tag_ids == [tag_one.id, tag_two.id]
