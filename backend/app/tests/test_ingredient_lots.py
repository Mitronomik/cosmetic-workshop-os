from decimal import Decimal
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.ingredient_lots import IngredientLotDraft
from app.domain.ingredients import IngredientDraft
from app.domain.units import UnitCode
from app.main import create_app
from app.repositories.ingredient_lots import (
    IngredientLotInactiveIngredientError,
    IngredientLotIngredientMissingError,
)
from app.repositories.database import ALLOWED_CURRENT_TABLES, FORBIDDEN_FUTURE_TABLES
from app.services.database import initialize_database
from app.services.ingredient_lots import IngredientLotService
from app.services.ingredients import IngredientService

ALLOWED_TABLES = ALLOWED_CURRENT_TABLES
FORBIDDEN_TABLES = FORBIDDEN_FUTURE_TABLES


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "ingredient-lots.sqlite")
    initialize_database(config)
    return config


def create_ingredient(config, *, name="Demo Shea Butter"):
    return IngredientService(config).create_ingredient(
        IngredientDraft.create(name=name, category="butter", default_unit=UnitCode.GRAM)
    )


def test_migration_creates_only_allowed_ingredient_lots_table(tmp_path):
    config = initialized_config(tmp_path)

    tables = table_names(config.path)

    assert {"schema_migrations", "app_settings", "audit_logs", "ingredients", "ingredient_lots"} <= tables
    assert tables <= ALLOWED_TABLES
    assert not FORBIDDEN_TABLES & tables


def test_create_lot_for_existing_active_ingredient_accepts_missing_density_and_costs(tmp_path):
    config = initialized_config(tmp_path)
    ingredient = create_ingredient(config)

    lot = IngredientLotService(config).create_lot(
        IngredientLotDraft.create(
            ingredient_id=ingredient.id,
            lot_code="  LOT  001 ",
            supplier_name=" Demo  Supplier ",
            purchased_at=None,
            expires_at=None,
            unit="g",
            density_g_per_ml=None,
            unit_cost=None,
            total_cost=None,
        )
    )

    assert lot.id > 0
    assert lot.ingredient_id == ingredient.id
    assert lot.lot_code == "LOT 001"
    assert lot.supplier_name == "Demo Supplier"
    assert lot.density_g_per_ml is None
    assert lot.unit_cost is None
    assert lot.total_cost is None


def test_reject_lot_for_missing_ingredient(tmp_path):
    config = initialized_config(tmp_path)

    with pytest.raises(IngredientLotIngredientMissingError):
        IngredientLotService(config).create_lot(IngredientLotDraft.create(ingredient_id=999, unit="g"))


def test_reject_lot_for_inactive_ingredient(tmp_path):
    config = initialized_config(tmp_path)
    ingredient = create_ingredient(config)
    IngredientService(config).deactivate_ingredient(ingredient.id)

    with pytest.raises(IngredientLotInactiveIngredientError):
        IngredientLotService(config).create_lot(IngredientLotDraft.create(ingredient_id=ingredient.id, unit="g"))


@pytest.mark.parametrize("density", ["0", "-0.2"])
def test_reject_non_positive_density(density):
    with pytest.raises(DomainValidationError) as exc:
        IngredientLotDraft.create(ingredient_id=1, unit="ml", density_g_per_ml=density)

    assert exc.value.issue.code == DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY


def test_reject_float_density():
    with pytest.raises(DomainValidationError) as exc:
        IngredientLotDraft.create(ingredient_id=1, unit="ml", density_g_per_ml=1.01)

    assert exc.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED


@pytest.mark.parametrize("field", ["unit_cost", "total_cost"])
def test_reject_negative_costs(field):
    payload = {field: "-1"}

    with pytest.raises(DomainValidationError) as exc:
        IngredientLotDraft.create(ingredient_id=1, unit="g", **payload)

    assert exc.value.issue.code == DomainIssueCode.NEGATIVE_QUANTITY


def test_reject_expires_at_earlier_than_purchased_at():
    from datetime import date

    with pytest.raises(DomainValidationError):
        IngredientLotDraft.create(
            ingredient_id=1,
            unit="g",
            purchased_at=date(2026, 6, 2),
            expires_at=date(2026, 6, 1),
        )


def test_reject_percent_unit_for_lot():
    with pytest.raises(DomainValidationError) as exc:
        IngredientLotDraft.create(ingredient_id=1, unit="percent")

    assert exc.value.issue.code == DomainIssueCode.INVALID_UNIT


def test_list_active_lots_and_lots_by_ingredient_exclude_deactivated(tmp_path):
    config = initialized_config(tmp_path)
    first_ingredient = create_ingredient(config, name="Ingredient A")
    second_ingredient = create_ingredient(config, name="Ingredient B")
    service = IngredientLotService(config)
    active_first = service.create_lot(IngredientLotDraft.create(ingredient_id=first_ingredient.id, unit="g"))
    inactive_first = service.create_lot(IngredientLotDraft.create(ingredient_id=first_ingredient.id, unit="g"))
    active_second = service.create_lot(IngredientLotDraft.create(ingredient_id=second_ingredient.id, unit="ml", density_g_per_ml="0.997"))

    service.deactivate_lot(inactive_first.id)

    assert [lot.id for lot in service.list_active_lots()] == [active_first.id, active_second.id]
    assert [lot.id for lot in service.list_active_lots_by_ingredient(first_ingredient.id)] == [active_first.id]


def test_decimal_costs_and_density_are_stored_as_strings(tmp_path):
    config = initialized_config(tmp_path)
    ingredient = create_ingredient(config)

    lot = IngredientLotService(config).create_lot(
        IngredientLotDraft.create(
            ingredient_id=ingredient.id,
            unit="ml",
            unit_cost="12.345",
            total_cost="99.999",
            density_g_per_ml="0.9972",
        )
    )

    assert lot.unit_cost == Decimal("12.35")
    assert lot.total_cost == Decimal("100.00")
    assert lot.density_g_per_ml == Decimal("0.9972")
    with sqlite3.connect(config.path) as connection:
        stored = connection.execute(
            "SELECT unit_cost, total_cost, density_g_per_ml FROM ingredient_lots WHERE id = ?", (lot.id,)
        ).fetchone()
    assert stored == ("12.35", "100.00", "0.9972")


def test_ingredient_lots_api_create_read_list_update_and_deactivate(monkeypatch, tmp_path):
    database_path = tmp_path / "api-ingredient-lots.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)
    ingredient = create_ingredient(config)
    client = TestClient(create_app())

    create_response = client.post(
        "/api/ingredient-lots",
        json={
            "ingredient_id": ingredient.id,
            "lot_code": "L-1",
            "supplier_name": "Supplier",
            "purchased_at": "2026-06-01",
            "expires_at": "2027-06-01",
            "unit": "g",
            "unit_cost": "10.5",
            "total_cost": None,
            "density_g_per_ml": None,
            "notes": "",
        },
    )
    assert create_response.status_code == 201
    lot_id = create_response.json()["id"]

    assert client.get(f"/api/ingredient-lots/{lot_id}").json()["lot_code"] == "L-1"
    assert len(client.get("/api/ingredient-lots").json()["lots"]) == 1
    assert len(client.get(f"/api/ingredients/{ingredient.id}/lots").json()["lots"]) == 1

    update_response = client.put(
        f"/api/ingredient-lots/{lot_id}",
        json={"ingredient_id": ingredient.id, "lot_code": "L-2", "supplier_name": "", "unit": "ml", "density_g_per_ml": "1.0100"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["lot_code"] == "L-2"

    deactivate_response = client.post(f"/api/ingredient-lots/{lot_id}/deactivate")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False
    assert client.get("/api/ingredient-lots").json()["lots"] == []


def test_ingredient_lots_api_rejects_missing_inactive_and_invalid_inputs(monkeypatch, tmp_path):
    database_path = tmp_path / "api-invalid-ingredient-lots.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    config = DatabaseConfig(path=database_path)
    initialize_database(config)
    ingredient = create_ingredient(config)
    IngredientService(config).deactivate_ingredient(ingredient.id)
    client = TestClient(create_app())

    assert client.post("/api/ingredient-lots", json={"ingredient_id": 999, "unit": "g"}).status_code == 404
    assert client.post("/api/ingredient-lots", json={"ingredient_id": ingredient.id, "unit": "g"}).status_code == 409
    assert client.post("/api/ingredient-lots", json={"ingredient_id": 1, "unit": "percent"}).status_code == 422
    assert client.post("/api/ingredient-lots", json={"ingredient_id": 1, "unit": "ml", "density_g_per_ml": 1.1}).status_code == 422
    assert client.post(
        "/api/ingredient-lots",
        json={"ingredient_id": 1, "unit": "g", "purchased_at": "2026-06-02", "expires_at": "2026-06-01"},
    ).status_code == 422
