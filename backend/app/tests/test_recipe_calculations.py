import sqlite3

import pytest
from fastapi import HTTPException

from app.api.recipes import calculate_recipe_version as api_calculate_recipe_version
from app.db.config import DatabaseConfig, DATABASE_PATH_ENV
from app.domain.errors import DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.services.database import initialize_database
from app.services.ingredients import IngredientService
from app.services.recipe_calculations import RecipeCalculationService
from app.services.recipes import RecipeService
from app.tests.table_guards import assert_no_forbidden_future_tables, assert_only_current_tables


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "recipe-calculations.sqlite")
    initialize_database(c)
    return c


def scalar(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql, params).fetchone()[0]


def rows(c, sql, params=()):
    with sqlite3.connect(c.path) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(sql, params).fetchall()]


def tables(c):
    with sqlite3.connect(c.path) as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def ingredient(c, name="Oil"):
    return IngredientService(c).create_ingredient(IngredientDraft.create(name=name, category="oil", default_unit="g"))


def recipe_with_lines(c, line_specs, *, target_value=None, target_unit=None):
    service = RecipeService(c)
    template = service.create_template(RecipeTemplateDraft.create(name="Base cream"))
    drafts = []
    for position, spec in enumerate(line_specs, start=1):
        ing = ingredient(c, spec.get("name", f"Ingredient {position}"))
        drafts.append(RecipeIngredientDraft.create(ingredient_id=ing.id, position=spec.get("position", position), amount_value=spec["amount"], amount_unit=spec["unit"], phase=spec.get("phase", "")))
    return service.create_version(template.id, RecipeVersionDraft.create(target_batch_size_value=target_value, target_batch_size_unit=target_unit, ingredients=drafts))


def calculate(c, detail, **kwargs):
    return RecipeCalculationService(c).calculate_version(detail.version.id, **kwargs)


def test_table_scope_has_no_new_tables(tmp_path):
    c = config(tmp_path)
    names = tables(c)
    assert_only_current_tables(names)
    assert_no_forbidden_future_tables(names)


@pytest.mark.parametrize("unit,amount", [("g", "10"), ("ml", "5.5"), ("pcs", "2")])
def test_fixed_amount_line_returns_same_amount_and_unit(tmp_path, unit, amount):
    c = config(tmp_path)
    result = calculate(c, recipe_with_lines(c, [{"amount": amount, "unit": unit}]))
    assert result.can_calculate is True
    assert result.lines[0].source_amount_unit == unit
    assert result.lines[0].calculated_amount_unit == unit
    assert result.lines[0].calculated_amount_value == result.lines[0].source_amount_value


def test_fixed_line_order_and_totals_grouped_by_unit(tmp_path):
    c = config(tmp_path)
    detail = recipe_with_lines(c, [{"amount": "2", "unit": "ml", "position": 2}, {"amount": "1", "unit": "g", "position": 1}, {"amount": "3", "unit": "pcs", "position": 3}])
    result = calculate(c, detail)
    assert [line.position for line in result.lines] == [1, 2, 3]
    totals = {t.unit: t.total_value for t in result.totals_by_unit}
    assert totals["g"] == result.lines[0].calculated_amount_value
    assert totals["ml"] == result.lines[1].calculated_amount_value
    assert totals["pcs"] == result.lines[2].calculated_amount_value


def test_percent_lines_calculate_from_explicit_targets_and_decimal_total(tmp_path):
    c = config(tmp_path)
    detail = recipe_with_lines(c, [{"amount": "5", "unit": "percent"}, {"amount": "95", "unit": "percent"}])
    result_100 = calculate(c, detail, target_batch_size_value="100", target_batch_size_unit="g")
    result_500 = calculate(c, detail, target_batch_size_value="500", target_batch_size_unit="g")
    assert [line.calculated_amount_value for line in result_100.lines] == [pytest.approx(5), pytest.approx(95)]
    assert str(result_100.lines[0].calculated_amount_value) == "5.000"
    assert str(result_500.lines[0].calculated_amount_value) == "25.000"
    assert str(result_100.percent_total) == "100.00"
    assert not [i for i in result_100.issues if i.code.startswith("percent_total_")]


def test_percent_total_warning_error_and_missing_target_issue(tmp_path):
    c = config(tmp_path)
    below = calculate(c, recipe_with_lines(c, [{"amount": "40", "unit": "percent"}]), target_batch_size_value="100", target_batch_size_unit="g")
    above = calculate(c, recipe_with_lines(c, [{"amount": "120", "unit": "percent"}]), target_batch_size_value="100", target_batch_size_unit="g")
    missing = calculate(c, recipe_with_lines(c, [{"amount": "10", "unit": "percent"}]))
    assert any(i.severity == "warning" and i.code == "percent_total_below_100" for i in below.issues)
    assert any(i.severity == "error" and i.code == "percent_total_above_100" for i in above.issues)
    assert any(i.code == "missing_target_batch_size" for i in missing.issues)
    assert missing.can_calculate is False
    assert missing.lines[0].calculated_amount_value is None


@pytest.mark.parametrize("value,unit", [("0", "g"), ("-1", "g"), (1.2, "g"), ("100", "percent"), ("100", "bad")])
def test_target_validation_rejects_invalid_values(tmp_path, value, unit):
    c = config(tmp_path)
    detail = recipe_with_lines(c, [{"amount": "10", "unit": "percent"}])
    with pytest.raises(DomainValidationError):
        calculate(c, detail, target_batch_size_value=value, target_batch_size_unit=unit)


def test_stored_target_used_and_explicit_target_overrides(tmp_path):
    c = config(tmp_path)
    detail = recipe_with_lines(c, [{"amount": "10", "unit": "percent"}], target_value="200", target_unit="g")
    stored = calculate(c, detail)
    explicit = calculate(c, detail, target_batch_size_value="500", target_batch_size_unit="g")
    assert str(stored.lines[0].calculated_amount_value) == "20.000"
    assert str(explicit.lines[0].calculated_amount_value) == "50.000"


def test_mixed_units_do_not_convert_ml_g_or_pcs(tmp_path):
    c = config(tmp_path)
    detail = recipe_with_lines(c, [{"amount": "10", "unit": "percent"}, {"amount": "3", "unit": "ml"}, {"amount": "2", "unit": "pcs"}])
    result = calculate(c, detail, target_batch_size_value="100", target_batch_size_unit="g")
    assert result.lines[0].calculated_amount_unit == "g"
    assert result.lines[1].calculated_amount_unit == "ml"
    assert result.lines[2].calculated_amount_unit == "pcs"
    assert {t.unit for t in result.totals_by_unit} == {"g", "ml", "pcs"}


def test_api_calculation_query_missing_version_validation_and_read_only(monkeypatch, tmp_path):
    db = tmp_path / "api-calc.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(db))
    c = DatabaseConfig(path=db)
    initialize_database(c)
    detail = recipe_with_lines(c, [{"amount": "10", "unit": "percent"}])
    before_audit = scalar(c, "SELECT count(*) FROM audit_logs")
    before_versions = rows(c, "SELECT * FROM recipe_versions")
    before_lines = rows(c, "SELECT * FROM recipe_ingredients")
    response = api_calculate_recipe_version(detail.version.id, target_batch_size_value="500", target_batch_size_unit="g")
    assert response.lines[0].calculated_amount_value == "50.000"
    assert response.percent_total == "10.00"
    with pytest.raises(HTTPException) as missing:
        api_calculate_recipe_version(999)
    assert missing.value.status_code == 404
    with pytest.raises(HTTPException) as invalid:
        api_calculate_recipe_version(detail.version.id, target_batch_size_value="0", target_batch_size_unit="g")
    assert invalid.value.status_code == 422
    assert scalar(c, "SELECT count(*) FROM audit_logs") == before_audit
    assert rows(c, "SELECT * FROM recipe_versions") == before_versions
    assert rows(c, "SELECT * FROM recipe_ingredients") == before_lines
