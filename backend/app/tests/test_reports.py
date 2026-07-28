import ast
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sqlite3

from app.db.config import DatabaseConfig
from app.domain import report_financials as report_financials_module
from app.services.database import initialize_database
from app.services import reports as reports_service_module
from app.services.reports import ReportsService
from app.services.tax_rate_settings import TaxRateSettingsService

BUSINESS_TABLES = ("ingredients","ingredient_lots","stock_movements","packaging_items","packaging_stock_movements","orders","production_batches","production_batch_ingredients","production_batch_packaging","alerts","purchase_suggestions","audit_logs","import_sources","import_drafts","demo_data_sessions","demo_data_records")


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "reports.sqlite")
    initialize_database(c)
    return c


def counts(c):
    with sqlite3.connect(c.path) as con:
        return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in BUSINESS_TABLES}


def scalar(c, sql):
    with sqlite3.connect(c.path) as con:
        return con.execute(sql).fetchone()[0]


def seed_inventory(c):
    today = date.today()
    with sqlite3.connect(c.path) as con:
        ing1 = con.execute("INSERT INTO ingredients (name, category, default_unit, minimum_stock) VALUES ('Масло', 'oil', 'g', '50')").lastrowid
        ing2 = con.execute("INSERT INTO ingredients (name, category, default_unit) VALUES ('Вода', 'water_phase', 'g')").lastrowid
        lot1 = con.execute("INSERT INTO ingredient_lots (ingredient_id, unit, expires_at) VALUES (?, 'g', ?)", (ing1, (today + timedelta(days=5)).isoformat())).lastrowid
        con.execute("INSERT INTO ingredient_lots (ingredient_id, unit, expires_at) VALUES (?, 'g', ?)", (ing2, (today - timedelta(days=1)).isoformat()))
        con.execute("INSERT INTO stock_movements (ingredient_lot_id, ingredient_id, movement_type, quantity, unit, direction) VALUES (?, ?, 'receipt', '10.500', 'g', 'in')", (lot1, ing1))
        pkg1 = con.execute("INSERT INTO packaging_items (name, kind, unit, minimum_stock) VALUES ('Банка', 'jar', 'pcs', '10')").lastrowid
        con.execute("INSERT INTO packaging_items (name, kind, unit) VALUES ('Флакон', 'bottle', 'pcs')")
        con.execute("INSERT INTO packaging_stock_movements (packaging_item_id, movement_type, quantity, direction) VALUES (?, 'receipt', '2', 'in')", (pkg1,))
        con.execute("INSERT INTO alerts (alert_key, type, severity, message, related_entity_type, related_entity_id, recommended_action) VALUES ('low-ing', 'low_ingredient_stock', 'warning', 'Низкий остаток', 'ingredient', ?, 'Добавьте в закупки')", (ing1,))
        con.execute("INSERT INTO purchase_suggestions (suggestion_key, item_type, item_id, item_name_snapshot, recommended_quantity, unit, reason, source_entity_type, message) VALUES ('buy-ing', 'ingredient', ?, 'Масло', '100', 'g', 'below_minimum_stock', 'alert', 'Купить масло')", (ing1,))


def seed_orders_and_production(c):
    with sqlite3.connect(c.path) as con:
        client = con.execute("INSERT INTO clients (full_name) VALUES ('Анна')").lastrowid
        ingredient = con.execute("INSERT INTO ingredients (name, category, default_unit) VALUES ('Вода', 'water_phase', 'g')").lastrowid
        template = con.execute("INSERT INTO recipe_templates (name, product_type) VALUES ('Крем', 'cream')").lastrowid
        version = con.execute("INSERT INTO recipe_versions (recipe_template_id, version_number, title, status) VALUES (?, 1, 'v1', 'draft')", (template,)).lastrowid
        for status in ("new", "waiting_for_materials", "ready_to_produce", "in_progress", "produced", "delivered", "cancelled", "archived"):
            con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status, is_active) VALUES (?, ?, ?, '50', 'g', ?, ?)", (client, version, f"Заказ {status}", status, 0 if status == "archived" else 1))
        order1 = con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status, sale_price) VALUES (?, ?, 'Продан', '50', 'g', 'produced', '1200.10')", (client, version)).lastrowid
        order2 = con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status) VALUES (?, ?, 'Без цены', '20', 'ml', 'produced')", (client, version)).lastrowid
        con.execute("INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, component_cost, packaging_cost, other_cost, total_cost, sale_price) VALUES (?, ?, '50.000', 'g', '100.05', '50.05', '0.00', '150.10', '1200.10')", (order1, version))
        con.execute("INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, other_cost) VALUES (?, ?, '20.000', 'ml', '0.00')", (order2, version))
        lot = con.execute("INSERT INTO ingredient_lots (ingredient_id, unit) VALUES (?, 'g')", (ingredient,)).lastrowid
        con.execute("INSERT INTO production_batch_ingredients (production_batch_id, ingredient_id, ingredient_lot_id, ingredient_name_snapshot, required_quantity, consumed_quantity, unit) VALUES (1, ?, ?, 'Вода', '10', '10', 'g')", (ingredient, lot))


def test_empty_reports_are_safe(tmp_path):
    service = ReportsService(config(tmp_path))
    assert service.get_overview().generated_at
    assert service.get_inventory_report().total_active_ingredients == 0
    assert service.get_orders_report().total_orders == 0
    assert service.get_production_report().total_production_batches == 0
    assert service.get_finance_report().produced_order_count == 0


def test_reports_are_read_only_and_do_not_regenerate_side_effects(tmp_path):
    c = config(tmp_path)
    before = counts(c)
    service = ReportsService(c)
    service.get_overview(); service.get_inventory_report(); service.get_orders_report(); service.get_production_report(); service.get_finance_report()
    assert counts(c) == before
    assert scalar(c, "SELECT COUNT(*) FROM audit_logs") == before["audit_logs"]


def test_inventory_report_counts_stock_health(tmp_path):
    c = config(tmp_path); seed_inventory(c)
    report = ReportsService(c).get_inventory_report()
    assert report.total_active_ingredients == 2
    assert report.total_active_ingredient_lots == 2
    assert report.ingredient_lots_with_positive_balance == 1
    assert report.expired_ingredient_lots == 1
    assert report.expiring_soon_ingredient_lots == 1
    assert report.active_packaging_items == 2
    assert report.packaging_items_with_positive_balance == 1
    assert report.open_low_stock_alerts == 1
    assert report.open_purchase_suggestions == 1


def test_orders_report_counts_statuses(tmp_path):
    c = config(tmp_path); seed_orders_and_production(c)
    report = ReportsService(c).get_orders_report()
    assert report.total_orders == 10
    assert report.active_orders == 9
    assert report.new_orders == 1
    assert report.waiting_for_materials == 1
    assert report.ready_to_produce == 1
    assert report.in_progress == 1
    assert report.produced == 3
    assert report.delivered == 1
    assert report.cancelled == 1
    assert report.archived == 1


def test_production_report_counts_batches_costs_and_mixed_units(tmp_path):
    c = config(tmp_path); seed_orders_and_production(c)
    report = ReportsService(c).get_production_report()
    assert report.total_production_batches == 2
    assert report.batches_in_period == 2
    assert report.produced_orders_count == 2
    assert {t.unit: t.quantity for t in report.produced_quantity_totals} == {"g": "50.000", "ml": "20.000"}
    assert report.total_known_cost == "150.10"
    assert report.missing_cost_count == 1
    assert {w.code for w in report.warnings} >= {"missing_production_cost", "mixed_units"}


def test_finance_report_sums_decimal_values_and_warns_for_missing_data(tmp_path):
    c = config(tmp_path); seed_orders_and_production(c)
    report = ReportsService(c).get_finance_report()
    assert report.produced_order_count == 2
    assert report.produced_orders_with_sale_price == 1
    assert report.known_revenue == "1200.10"
    assert report.known_production_cost == "150.10"
    assert report.complete_finance_record_count == 1
    assert report.incomplete_margin_count == 1
    # Both seeded rows are pre-`C2-II` shaped: no tax and no margin snapshot was
    # ever persisted. Reports must not rebuild a margin out of the paired sale
    # price and cost of the one complete row.
    assert report.known_margin is None
    assert report.known_margin_percent is None
    assert report.known_tax is None
    assert report.margin_snapshot_record_count == 0
    assert report.missing_margin_snapshot_count == 2
    assert report.tax_snapshot_record_count == 0
    assert report.missing_tax_snapshot_count == 2
    assert report.missing_sale_price_count == 1
    assert report.missing_cost_count == 1
    assert {w.code for w in report.warnings} >= {"missing_sale_price", "missing_production_cost", "margin_unavailable", "tax_unavailable"}


def seed_snapshot_batches(c, rows):
    """Insert one produced order plus batch per row of persisted snapshots.

    Each row is ``(sale_price, total_cost, tax, margin, margin_percent)`` and any
    entry may be ``None`` to model a batch that never saved that snapshot — the
    normal shape of every pre-`C2-II` row, because there was no backfill.
    """
    with sqlite3.connect(c.path) as con:
        client = con.execute("INSERT INTO clients (full_name) VALUES ('Анна')").lastrowid
        template = con.execute("INSERT INTO recipe_templates (name, product_type) VALUES ('Крем', 'cream')").lastrowid
        version = con.execute("INSERT INTO recipe_versions (recipe_template_id, version_number, title, status) VALUES (?, 1, 'v1', 'draft')", (template,)).lastrowid
        for index, (sale_price, total_cost, tax, margin, margin_percent) in enumerate(rows):
            order = con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status, sale_price) VALUES (?, ?, ?, '50', 'g', 'produced', ?)", (client, version, f"Партия {index}", sale_price)).lastrowid
            con.execute("INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, other_cost, total_cost, sale_price, tax, margin, margin_percent) VALUES (?, ?, '50.000', 'g', '0.00', ?, ?, ?, ?, ?)", (order, version, total_cost, sale_price, tax, margin, margin_percent))


def test_finance_report_reads_persisted_tax_and_margin_snapshots(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "400.00", "60.00", "540.00", "54.00"), ("500.00", "150.00", "30.00", "320.00", "64.00")])
    report = ReportsService(c).get_finance_report()
    assert report.known_revenue == "1500.00"
    assert report.known_production_cost == "550.00"
    assert report.known_tax == "90.00"
    assert report.known_margin == "860.00"
    assert report.tax_snapshot_record_count == 2
    assert report.margin_snapshot_record_count == 2
    assert report.missing_tax_snapshot_count == 0
    assert report.missing_margin_snapshot_count == 0
    assert report.warnings == []


def test_finance_report_does_not_reconstruct_margin_or_tax_from_price_and_cost(tmp_path):
    """A deliberately inconsistent persisted row proves nothing is derived.

    ``sale_price - total_cost`` is ``600.00`` and ``sale_price - total_cost -
    tax`` is ``540.00``. The persisted margin is ``111.11``, so a report that
    ever recalculated would show one of the first two numbers instead.
    """
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "400.00", "60.00", "111.11", "11.11")])
    report = ReportsService(c).get_finance_report()
    assert report.known_margin == "111.11"
    assert report.known_tax == "60.00"
    assert report.known_margin_percent == "11.11"


def test_finance_report_margin_percent_uses_only_the_sale_prices_of_margin_rows(tmp_path):
    """The 9000 of revenue without a margin snapshot stays out of the basis.

    Same-basis: ``300 ÷ 1000 = 30.00%``. Using the global known revenue would
    give ``3.00%``.
    """
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "640.00", "60.00", "300.00", "30.00"), ("9000.00", "5000.00", None, None, None)])
    report = ReportsService(c).get_finance_report()
    assert report.known_revenue == "10000.00"
    assert report.known_margin == "300.00"
    assert report.known_margin_percent == "30.00"
    assert {w.code for w in report.warnings} == {"partial_tax_basis", "partial_margin_basis"}


def test_finance_report_keeps_configured_zero_apart_from_a_missing_snapshot(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("100.00", "40.00", "0.00", "60.00", "60.00"), ("50.00", "20.00", None, None, None)])
    report = ReportsService(c).get_finance_report()
    assert report.known_tax == "0.00"
    assert report.tax_snapshot_record_count == 1
    assert report.missing_tax_snapshot_count == 1
    codes = {w.code for w in report.warnings}
    assert "partial_tax_basis" in codes
    assert "tax_unavailable" not in codes


def test_finance_report_keeps_a_zero_sale_row_out_of_the_percentage_basis(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "700.00", "60.00", "240.00", "24.00"), ("0.00", "40.00", "0.00", "-40.00", None)])
    report = ReportsService(c).get_finance_report()
    assert report.known_margin == "200.00"
    assert report.known_margin_percent == "20.00"
    assert report.margin_snapshot_record_count == 2


def test_finance_report_drops_the_percentage_when_every_margin_row_sells_for_zero(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("0.00", "40.00", "0.00", "-40.00", None)])
    report = ReportsService(c).get_finance_report()
    assert report.known_margin == "-40.00"
    assert report.known_margin_percent is None
    assert "margin_percent_unavailable_zero_basis" in {w.code for w in report.warnings}


def test_finance_report_warnings_use_russian_text_and_reference_report_fields(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("100.00", "40.00", "6.00", "54.00", "54.00"), (None, None, None, None, None)])
    warnings = {w.code: w for w in ReportsService(c).get_finance_report().warnings}
    assert warnings["partial_tax_basis"].field == "known_tax"
    assert warnings["partial_margin_basis"].field == "known_margin"
    assert warnings["missing_sale_price"].field == "known_revenue"
    assert warnings["missing_production_cost"].field == "known_production_cost"
    assert "зафиксирован при изготовлении" in warnings["partial_tax_basis"].message
    assert "зафиксирована при изготовлении" in warnings["partial_margin_basis"].message
    # No warning may claim reports calculated anything, or leak column names.
    for warning in warnings.values():
        assert "production_batches" not in warning.message
        assert "рассчитан" not in warning.message


def test_current_tax_rate_setting_never_changes_a_finance_report(tmp_path):
    """Changing, clearing or corrupting the setting leaves reports untouched."""
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "400.00", "60.00", "540.00", "54.00"), ("500.00", "200.00", None, None, None)])
    service = ReportsService(c)
    baseline = service.get_finance_report().model_dump(exclude={"generated_at"})

    TaxRateSettingsService(c).update_tax_rate("20")
    assert service.get_finance_report().model_dump(exclude={"generated_at"}) == baseline

    TaxRateSettingsService(c).update_tax_rate(None)
    assert service.get_finance_report().model_dump(exclude={"generated_at"}) == baseline

    with sqlite3.connect(c.path) as con:
        con.execute("UPDATE app_settings SET value='не число' WHERE key='default_tax_rate'")
    assert service.get_finance_report().model_dump(exclude={"generated_at"}) == baseline


def test_overview_finance_summary_is_the_same_snapshot_backed_finance_report(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "400.00", "60.00", "540.00", "54.00"), ("500.00", "200.00", None, None, None)])
    service = ReportsService(c)
    assert service.get_overview().finance_summary.model_dump(exclude={"generated_at"}) == service.get_finance_report().model_dump(exclude={"generated_at"})


def test_repeated_finance_and_overview_reads_mutate_nothing(tmp_path):
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "400.00", "60.00", "540.00", "54.00")])
    service = ReportsService(c)
    before = counts(c)
    settings_before = scalar(c, "SELECT COUNT(*) FROM app_settings")
    batches_before = batch_financials(c)
    first = service.get_finance_report().model_dump(exclude={"generated_at"})

    for _ in range(3):
        service.get_finance_report()
        service.get_overview()

    assert counts(c) == before
    assert scalar(c, "SELECT COUNT(*) FROM app_settings") == settings_before
    assert batch_financials(c) == batches_before
    assert service.get_finance_report().model_dump(exclude={"generated_at"}) == first


def test_reports_never_call_the_tax_rate_settings_service(tmp_path, monkeypatch):
    """Any read of the current rate from anywhere would fail this test."""
    def explode(*_args, **_kwargs):
        raise AssertionError("Reports must not read the current tax-rate setting.")

    monkeypatch.setattr(TaxRateSettingsService, "get_tax_rate", explode)
    c = config(tmp_path)
    seed_snapshot_batches(c, [("1000.00", "400.00", "60.00", "540.00", "54.00")])
    service = ReportsService(c)
    assert service.get_finance_report().known_tax == "60.00"
    assert service.get_overview().finance_summary.known_margin == "540.00"


def executable_source(module) -> str:
    """The module's code with comments and docstrings removed.

    Prose *about* a forbidden formula is exactly what the modules below are
    expected to contain; only real executable code should fail the guard.
    """
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:]
    return ast.unparse(tree)


def test_report_financial_code_contains_no_reconstruction_or_settings_lookup():
    """A source guard against the formulas and lookups reports must not have."""
    for module in (reports_service_module, report_financials_module):
        code = executable_source(module)
        assert "sale_price - total_cost" not in code
        assert "TaxRateSettingsService" not in code
        assert "get_tax_rate" not in code
        assert "default_tax_rate" not in code
        # The persisted per-row percentage is historical and is never read back
        # into an aggregate, so it is not even selected.
        assert 'row["margin_percent"]' not in code
    assert "SELECT sale_price, total_cost, tax, margin FROM production_batches" in executable_source(reports_service_module)


def batch_financials(c):
    with sqlite3.connect(c.path) as con:
        return con.execute("SELECT id, sale_price, total_cost, tax, margin, margin_percent FROM production_batches ORDER BY id").fetchall()


def test_finance_report_does_not_mix_unpaired_revenue_and_cost(tmp_path):
    c = config(tmp_path)
    with sqlite3.connect(c.path) as con:
        client = con.execute("INSERT INTO clients (full_name) VALUES ('Анна')").lastrowid
        ingredient = con.execute("INSERT INTO ingredients (name, category, default_unit) VALUES ('Вода', 'water_phase', 'g')").lastrowid
        template = con.execute("INSERT INTO recipe_templates (name, product_type) VALUES ('Крем', 'cream')").lastrowid
        version = con.execute("INSERT INTO recipe_versions (recipe_template_id, version_number, title, status) VALUES (?, 1, 'v1', 'draft')", (template,)).lastrowid
        order_with_sale = con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status, sale_price) VALUES (?, ?, 'Цена без себестоимости', '50', 'g', 'produced', '1000.00')", (client, version)).lastrowid
        order_with_cost = con.execute("INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, status) VALUES (?, ?, 'Себестоимость без цены', '50', 'g', 'produced')", (client, version)).lastrowid
        con.execute("INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, other_cost, sale_price) VALUES (?, ?, '50.000', 'g', '0.00', '1000.00')", (order_with_sale, version))
        con.execute("INSERT INTO production_batches (order_id, recipe_version_id, final_batch_value, final_batch_unit, other_cost, total_cost) VALUES (?, ?, '50.000', 'g', '0.00', '700.00')", (order_with_cost, version))
        con.execute("INSERT INTO ingredient_lots (ingredient_id, unit) VALUES (?, 'g')", (ingredient,))

    report = ReportsService(c).get_finance_report()

    assert report.produced_order_count == 2
    assert report.produced_orders_with_sale_price == 1
    assert report.known_revenue == "1000.00"
    assert report.known_production_cost == "700.00"
    assert report.complete_finance_record_count == 0
    assert report.incomplete_margin_count == 2
    assert report.known_margin is None
    assert report.known_margin_percent is None
    warning_codes = {w.code for w in report.warnings}
    assert "missing_sale_price" in warning_codes
    assert "missing_production_cost" in warning_codes
    assert "margin_unavailable" in warning_codes
    assert "partial_margin_basis" not in warning_codes
