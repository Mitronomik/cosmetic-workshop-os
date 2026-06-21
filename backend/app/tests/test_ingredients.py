from decimal import Decimal
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.domain.units import UnitCode
from app.main import create_app
from app.repositories.ingredients import IngredientRepository
from app.services.database import initialize_database
from app.services.ingredients import IngredientService

FORBIDDEN_TABLES = {
    "ingredient_lots",
    "stock_movements",
    "packaging_items",
    "recipes",
    "recipe_versions",
    "recipe_ingredients",
    "client_recipes",
    "client_recipe_ingredients",
    "clients",
    "client_wishes",
    "client_feedback",
    "orders",
    "production_batches",
    "import_sources",
    "import_drafts",
    "backup_records",
}


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def initialized_config(tmp_path):
    config = DatabaseConfig(path=tmp_path / "ingredients.sqlite")
    initialize_database(config)
    return config


def test_migration_creates_only_allowed_ingredients_business_table(tmp_path):
    config = initialized_config(tmp_path)

    tables = table_names(config.path)

    assert {"schema_migrations", "app_settings", "audit_logs", "ingredients"} <= tables
    assert not FORBIDDEN_TABLES & tables


def test_existing_infrastructure_tables_still_work(tmp_path):
    config = initialized_config(tmp_path)

    IngredientService(config).create_ingredient(
        IngredientDraft.create(name="Масло ши", category="butter", default_unit=UnitCode.GRAM)
    )

    with sqlite3.connect(config.path) as connection:
        setting = connection.execute("SELECT value FROM app_settings WHERE key = 'product.name'").fetchone()[0]
        audit_count = connection.execute("SELECT count(*) FROM audit_logs").fetchone()[0]
    assert setting == "Мастерская косметолога"
    assert audit_count == 1


def test_create_ingredient_accepts_missing_density(tmp_path):
    config = initialized_config(tmp_path)

    ingredient = IngredientService(config).create_ingredient(
        IngredientDraft.create(name="  Масло   жожоба  ", category="oil", default_unit="g")
    )

    assert ingredient.id > 0
    assert ingredient.name == "Масло жожоба"
    assert ingredient.density_g_per_ml is None


def test_reject_empty_name():
    with pytest.raises(DomainValidationError) as exc:
        IngredientDraft.create(name="  ", category="oil", default_unit="g")

    assert exc.value.issue.code == DomainIssueCode.REQUIRED_FIELD


def test_reject_invalid_category():
    with pytest.raises(DomainValidationError) as exc:
        IngredientDraft.create(name="Компонент", category="not_allowed", default_unit="g")

    assert exc.value.issue.code == DomainIssueCode.INVALID_CATEGORY


def test_reject_invalid_unit():
    with pytest.raises(DomainValidationError) as exc:
        IngredientDraft.create(name="Компонент", category="oil", default_unit="kg")

    assert exc.value.issue.code == DomainIssueCode.INVALID_UNIT


@pytest.mark.parametrize("density", ["0", "-1"])
def test_reject_non_positive_density(density):
    with pytest.raises(DomainValidationError) as exc:
        IngredientDraft.create(name="Компонент", category="oil", default_unit="ml", density_g_per_ml=density)

    assert exc.value.issue.code == DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY


def test_reject_float_density_to_avoid_binary_float_usage():
    with pytest.raises(DomainValidationError) as exc:
        IngredientDraft.create(name="Компонент", category="oil", default_unit="ml", density_g_per_ml=1.2)

    assert exc.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED


def test_density_is_stored_as_decimal_string_and_returned_as_decimal(tmp_path):
    config = initialized_config(tmp_path)

    ingredient = IngredientService(config).create_ingredient(
        IngredientDraft.create(name="Гидролат", category="water_phase", default_unit="ml", density_g_per_ml="0.997")
    )

    assert ingredient.density_g_per_ml == Decimal("0.9970")
    with sqlite3.connect(config.path) as connection:
        stored = connection.execute("SELECT density_g_per_ml FROM ingredients WHERE id = ?", (ingredient.id,)).fetchone()[0]
    assert stored == "0.9970"


def test_list_active_ingredients_excludes_deactivated(tmp_path):
    config = initialized_config(tmp_path)
    service = IngredientService(config)
    active = service.create_ingredient(IngredientDraft.create(name="A", category="oil", default_unit="g"))
    inactive = service.create_ingredient(IngredientDraft.create(name="B", category="active", default_unit="g"))

    service.deactivate_ingredient(inactive.id)

    assert [ingredient.id for ingredient in service.list_active_ingredients()] == [active.id]


def test_repository_get_by_id(tmp_path):
    config = initialized_config(tmp_path)
    created = IngredientRepository(config).create(IngredientDraft.create(name="Воск", category="wax", default_unit="g"))

    loaded = IngredientRepository(config).get_by_id(created.id)

    assert loaded.name == "Воск"


def test_ingredients_api_create_read_list_and_deactivate(monkeypatch, tmp_path):
    database_path = tmp_path / "api-ingredients.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    client = TestClient(create_app())

    create_response = client.post(
        "/api/ingredients",
        json={"name": "Масло ши", "category": "butter", "default_unit": "g", "density_g_per_ml": None},
    )
    assert create_response.status_code == 201
    ingredient_id = create_response.json()["id"]

    assert client.get(f"/api/ingredients/{ingredient_id}").json()["name"] == "Масло ши"
    assert len(client.get("/api/ingredients").json()["ingredients"]) == 1

    deactivate_response = client.post(f"/api/ingredients/{ingredient_id}/deactivate")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False
    assert client.get("/api/ingredients").json()["ingredients"] == []


def test_ingredients_api_rejects_invalid_input(monkeypatch, tmp_path):
    database_path = tmp_path / "api-invalid-ingredients.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    initialize_database(DatabaseConfig(path=database_path))
    client = TestClient(create_app())

    response = client.post(
        "/api/ingredients",
        json={"name": " ", "category": "oil", "default_unit": "g", "density_g_per_ml": "0"},
    )

    assert response.status_code == 422
