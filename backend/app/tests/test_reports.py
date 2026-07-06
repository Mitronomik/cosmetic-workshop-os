from datetime import date, timedelta
from decimal import Decimal
import sqlite3

from app.db.config import DatabaseConfig
from app.services.database import initialize_database
from app.services.reports import ReportsService

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
    assert report.known_margin == "1050.00"
    assert report.known_margin_percent == "87.49"
    assert report.missing_sale_price_count == 1
    assert report.missing_cost_count == 1
    assert {w.code for w in report.warnings} >= {"missing_sale_price", "missing_production_cost"}
