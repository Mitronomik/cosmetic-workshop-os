import sqlite3
import pytest

from app.db.config import DatabaseConfig
from app.services.database import initialize_database
from app.services.demo_data import (
    DemoDataConflictError,
    DemoDataConfirmationError,
    DemoDataService,
    DEMO_PREFIX,
)


def cfg(tmp_path):
    c = DatabaseConfig(path=tmp_path / "demo.sqlite")
    initialize_database(c)
    return c


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_status_on_empty_db_allows_install(tmp_path):
    st = DemoDataService(cfg(tmp_path)).status()
    assert st["can_install"] is True
    assert st["has_business_data"] is False
    assert st["has_non_demo_business_data"] is False


def test_status_with_real_business_data_blocks_install(tmp_path):
    c = cfg(tmp_path)
    with sqlite3.connect(c.path) as conn:
        conn.execute(
            "INSERT INTO ingredients (name, category, default_unit) VALUES ('Реальное масло', 'oil', 'g')"
        )
    st = DemoDataService(c).status()
    assert st["can_install"] is False
    assert st["has_non_demo_business_data"] is True


def test_install_requires_both_confirmations(tmp_path):
    service = DemoDataService(cfg(tmp_path))
    with pytest.raises(DemoDataConfirmationError):
        service.install(confirm_install=False, understand_demo_data=True)
    with pytest.raises(DemoDataConfirmationError):
        service.install(confirm_install=True, understand_demo_data=False)


def test_install_creates_tracked_labeled_business_data_without_batches_or_files(
    tmp_path,
):
    c = cfg(tmp_path)
    before_files = {p.name for p in tmp_path.iterdir()}
    result = DemoDataService(c).install(confirm_install=True, understand_demo_data=True)
    assert result["session_id"] > 0
    assert result["created_counts"]["ingredients"] == 5
    assert result["created_counts"]["ingredient_lots"] == 4
    assert result["created_counts"]["stock_movements"] == 4
    assert result["created_counts"]["packaging_items"] == 3
    assert result["created_counts"]["packaging_stock_movements"] == 3
    assert result["created_counts"]["recipe_templates"] == 2
    assert result["created_counts"]["recipe_versions"] == 2
    assert result["created_counts"]["recipe_ingredients"] == 7
    assert result["created_counts"]["clients"] == 2
    assert result["created_counts"]["client_recipes"] == 1
    assert result["created_counts"]["orders"] == 2
    with sqlite3.connect(c.path) as conn:
        assert count(conn, "production_batches") == 0
        assert count(conn, "demo_data_sessions") == 1
        assert count(conn, "demo_data_records") >= 36
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM ingredients WHERE name LIKE ?",
                (DEMO_PREFIX + "%",),
            ).fetchone()[0]
            == 5
        )
        assert (
            conn.execute(
                "SELECT MIN(CAST(quantity AS INTEGER)) FROM stock_movements"
            ).fetchone()[0]
            > 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM orders o LEFT JOIN clients c ON c.id=o.client_id WHERE c.id IS NULL"
            ).fetchone()[0]
            == 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM orders o LEFT JOIN packaging_items p ON p.id=o.packaging_item_id WHERE p.id IS NULL"
            ).fetchone()[0]
            == 0
        )
    assert {p.name for p in tmp_path.iterdir()} == before_files


def test_status_after_install_and_after_clear(tmp_path):
    c = cfg(tmp_path)
    service = DemoDataService(c)
    service.install(confirm_install=True, understand_demo_data=True)
    st = service.status()
    assert st["is_installed"] is True
    assert st["can_clear"] is True
    service.clear(confirm_clear=True)
    st = service.status()
    assert st["is_installed"] is False
    assert st["can_install"] is True


def test_install_rejects_non_empty_and_reinstall(tmp_path):
    c = cfg(tmp_path)
    service = DemoDataService(c)
    service.install(confirm_install=True, understand_demo_data=True)
    with pytest.raises(DemoDataConflictError):
        service.install(confirm_install=True, understand_demo_data=True)
    c2 = cfg(tmp_path / "real")
    with sqlite3.connect(c2.path) as conn:
        conn.execute(
            "INSERT INTO ingredients (name, category, default_unit) VALUES ('Реальное масло', 'oil', 'g')"
        )
    with pytest.raises(DemoDataConflictError):
        DemoDataService(c2).install(confirm_install=True, understand_demo_data=True)


def test_failed_install_rolls_back_session_tracking_and_business_rows(
    monkeypatch, tmp_path
):
    c = cfg(tmp_path)
    service = DemoDataService(c)

    def boom(conn, sid, counts):
        conn.execute(
            "INSERT INTO ingredients (name, category, default_unit) VALUES ('Демо · Сбой', 'oil', 'g')"
        )
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "_insert_dataset", boom)
    with pytest.raises(RuntimeError):
        service.install(confirm_install=True, understand_demo_data=True)
    with sqlite3.connect(c.path) as conn:
        assert count(conn, "demo_data_sessions") == 0
        assert count(conn, "demo_data_records") == 0
        assert count(conn, "ingredients") == 0


def test_clear_requires_confirmation_and_active_session(tmp_path):
    c = cfg(tmp_path)
    service = DemoDataService(c)
    with pytest.raises(DemoDataConfirmationError):
        service.clear(confirm_clear=False)
    with pytest.raises(DemoDataConflictError):
        service.clear(confirm_clear=True)


def test_clear_deletes_only_tracked_rows_and_marks_session(tmp_path):
    c = cfg(tmp_path)
    service = DemoDataService(c)
    result = service.install(confirm_install=True, understand_demo_data=True)
    sid = result["session_id"]
    with sqlite3.connect(c.path) as conn:
        conn.execute(
            "INSERT INTO audit_logs (actor_type, action, summary, metadata_json) VALUES ('system', 'test', 'real audit', '{}')"
        )
        audit_before = count(conn, "audit_logs")
    clear = service.clear(confirm_clear=True)
    assert clear["session_id"] == sid
    assert clear["deleted_counts"]["orders"] == 2
    with sqlite3.connect(c.path) as conn:
        for table in (
            "ingredients",
            "ingredient_lots",
            "stock_movements",
            "packaging_items",
            "packaging_stock_movements",
            "recipe_templates",
            "recipe_versions",
            "recipe_ingredients",
            "clients",
            "client_recipes",
            "orders",
        ):
            assert count(conn, table) == 0
        assert (
            conn.execute(
                "SELECT status FROM demo_data_sessions WHERE id=?", (sid,)
            ).fetchone()[0]
            == "cleared"
        )
        assert count(conn, "audit_logs") >= audit_before
    with pytest.raises(DemoDataConflictError):
        service.clear(confirm_clear=True)


def test_clear_blocks_untracked_records_referencing_demo_data(tmp_path):
    c = cfg(tmp_path)
    service = DemoDataService(c)
    service.install(confirm_install=True, understand_demo_data=True)
    with sqlite3.connect(c.path) as conn:
        client_id = conn.execute("SELECT id FROM clients LIMIT 1").fetchone()[0]
        version_id = conn.execute("SELECT id FROM recipe_versions LIMIT 1").fetchone()[
            0
        ]
        conn.execute(
            "INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit) VALUES (?, ?, 'Реальный заказ', '10', 'g')",
            (client_id, version_id),
        )
    with pytest.raises(DemoDataConflictError):
        service.clear(confirm_clear=True)
    with sqlite3.connect(c.path) as conn:
        assert count(conn, "orders") == 3
        assert (
            conn.execute(
                "SELECT status FROM demo_data_sessions WHERE status='active'"
            ).fetchone()
            is not None
        )


def test_failed_clear_rolls_back(monkeypatch, tmp_path):
    c = cfg(tmp_path)
    service = DemoDataService(c)
    service.install(confirm_install=True, understand_demo_data=True)
    monkeypatch.setattr(service, "_has_untracked_dependencies", lambda conn, sid: False)
    # Force a delete failure after transaction begins.
    with sqlite3.connect(c.path) as conn:
        conn.execute("DROP TABLE recipe_ingredients")
    with pytest.raises(sqlite3.OperationalError):
        service.clear(confirm_clear=True)
    with sqlite3.connect(c.path) as conn:
        assert count(conn, "demo_data_records") > 0
        assert (
            conn.execute(
                "SELECT status FROM demo_data_sessions WHERE status='active'"
            ).fetchone()
            is not None
        )
