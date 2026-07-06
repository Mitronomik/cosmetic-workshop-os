from __future__ import annotations

import json
import sqlite3
from collections import Counter

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.db.transactions import transaction
from app.repositories.audit import AuditLogRepository

DEMO_VERSION = "mvp-1"
DEMO_PREFIX = "Демо · "

BUSINESS_TABLES = (
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
    "client_recipe_ingredients",
    "client_wishes",
    "client_feedback",
    "orders",
    "production_batches",
    "production_batch_ingredients",
    "production_batch_packaging",
    "alerts",
    "purchase_suggestions",
)
DELETE_ORDER = (
    "purchase_suggestions",
    "alerts",
    "production_batch_packaging",
    "production_batch_ingredients",
    "production_batches",
    "orders",
    "client_feedback",
    "client_wishes",
    "client_recipe_ingredients",
    "client_recipes",
    "clients",
    "recipe_ingredients",
    "recipe_versions",
    "recipe_templates",
    "packaging_stock_movements",
    "packaging_items",
    "stock_movements",
    "ingredient_lots",
    "ingredients",
)


DIRECT_DEPENDENCY_CHECKS = (
    ("orders", "client_id", "clients"),
    ("orders", "recipe_version_id", "recipe_versions"),
    ("orders", "client_recipe_id", "client_recipes"),
    ("orders", "packaging_item_id", "packaging_items"),
    ("recipe_ingredients", "ingredient_id", "ingredients"),
    ("client_recipe_ingredients", "ingredient_id", "ingredients"),
    ("client_recipes", "client_id", "clients"),
    ("client_recipes", "source_recipe_version_id", "recipe_versions"),
    ("stock_movements", "ingredient_lot_id", "ingredient_lots"),
    ("packaging_stock_movements", "packaging_item_id", "packaging_items"),
    ("client_wishes", "client_id", "clients"),
    ("client_wishes", "client_recipe_id", "client_recipes"),
    ("client_feedback", "client_id", "clients"),
    ("client_feedback", "client_recipe_id", "client_recipes"),
    ("production_batches", "order_id", "orders"),
    ("production_batches", "recipe_version_id", "recipe_versions"),
    ("production_batches", "client_recipe_id", "client_recipes"),
    ("production_batch_ingredients", "ingredient_id", "ingredients"),
    ("production_batch_ingredients", "ingredient_lot_id", "ingredient_lots"),
    ("production_batch_packaging", "packaging_item_id", "packaging_items"),
)

GENERIC_REFERENCE_TARGETS = {
    "ingredient": "ingredients",
    "ingredients": "ingredients",
    "ingredient_lot": "ingredient_lots",
    "ingredient_lots": "ingredient_lots",
    "packaging": "packaging_items",
    "packaging_item": "packaging_items",
    "packaging_items": "packaging_items",
    "order": "orders",
    "orders": "orders",
    "client": "clients",
    "clients": "clients",
    "client_recipe": "client_recipes",
    "client_recipes": "client_recipes",
    "recipe_template": "recipe_templates",
    "recipe_templates": "recipe_templates",
    "recipe_version": "recipe_versions",
    "recipe_versions": "recipe_versions",
}

PURCHASE_ITEM_REFERENCE_TARGETS = {
    "ingredient": "ingredients",
    "ingredients": "ingredients",
    "packaging": "packaging_items",
    "packaging_item": "packaging_items",
    "packaging_items": "packaging_items",
}

COUNT_KEYS = {
    "ingredients": "ingredients",
    "ingredient_lots": "ingredient_lots",
    "stock_movements": "stock_movements",
    "packaging_items": "packaging_items",
    "packaging_stock_movements": "packaging_stock_movements",
    "recipe_templates": "recipe_templates",
    "recipe_versions": "recipe_versions",
    "recipe_ingredients": "recipe_ingredients",
    "clients": "clients",
    "client_recipes": "client_recipes",
    "client_recipe_ingredients": "client_recipe_ingredients",
    "orders": "orders",
}


class DemoDataConflictError(Exception):
    pass


class DemoDataConfirmationError(Exception):
    pass


class DemoDataService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def status(self) -> dict[str, object]:
        with session(self.config) as conn:
            return self._status(conn)

    def install(
        self, *, confirm_install: bool, understand_demo_data: bool
    ) -> dict[str, object]:
        if not confirm_install:
            raise DemoDataConfirmationError(
                "Перед установкой демо-данных нужно явно подтвердить действие."
            )
        if not understand_demo_data:
            raise DemoDataConfirmationError(
                "Перед установкой демо-данных нужно подтвердить, что это демонстрационные записи."
            )
        with transaction(self.config) as conn:
            st = self._status(conn)
            if st["is_installed"]:
                raise DemoDataConflictError("Демо-данные уже установлены.")
            if st["has_non_demo_business_data"]:
                raise DemoDataConflictError(
                    "Демо-данные можно установить только в пустую рабочую базу. В этой базе уже есть рабочие данные."
                )
            cur = conn.execute(
                "INSERT INTO demo_data_sessions (demo_version, status, summary_json) VALUES (?, 'active', ?)",
                (DEMO_VERSION, "{}"),
            )
            session_id = int(cur.lastrowid)
            counts = Counter()
            self._insert_dataset(conn, session_id, counts)
            counts_dict = dict(counts)
            conn.execute(
                "UPDATE demo_data_sessions SET summary_json = ? WHERE id = ?",
                (
                    json.dumps({"created_counts": counts_dict}, ensure_ascii=False),
                    session_id,
                ),
            )
            AuditLogRepository(self.config).create_log(
                action="demo_data.installed",
                entity_type="demo_data_session",
                entity_id=str(session_id),
                summary="Установлены демонстрационные данные.",
                metadata={"created_counts": counts_dict},
                connection=conn,
            )
            return {
                "session_id": session_id,
                "demo_version": DEMO_VERSION,
                "created_counts": counts_dict,
                "message": "Демо-данные установлены. Рабочие данные пользователя не изменялись.",
            }

    def clear(self, *, confirm_clear: bool) -> dict[str, object]:
        if not confirm_clear:
            raise DemoDataConfirmationError(
                "Перед удалением демо-данных нужно явно подтвердить действие."
            )
        with transaction(self.config) as conn:
            active = self._active_session(conn)
            if active is None:
                raise DemoDataConflictError(
                    "Демо-данные не установлены, удалять нечего."
                )
            session_id = int(active["id"])
            if self._has_untracked_dependencies(conn, session_id):
                raise DemoDataConflictError(
                    "Демо-данные нельзя удалить автоматически: на них уже ссылаются рабочие записи. Проверьте данные вручную."
                )
            deleted = Counter()
            for table in DELETE_ORDER:
                ids = [
                    r["record_id"]
                    for r in conn.execute(
                        "SELECT record_id FROM demo_data_records WHERE session_id = ? AND table_name = ?",
                        (session_id, table),
                    ).fetchall()
                ]
                for record_id in ids:
                    conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
                    deleted[COUNT_KEYS.get(table, table)] += 1
            conn.execute(
                "DELETE FROM demo_data_records WHERE session_id = ?", (session_id,)
            )
            conn.execute(
                "UPDATE demo_data_sessions SET status = 'cleared', cleared_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )
            deleted_dict = dict(deleted)
            AuditLogRepository(self.config).create_log(
                action="demo_data.cleared",
                entity_type="demo_data_session",
                entity_id=str(session_id),
                summary="Демонстрационные данные удалены.",
                metadata={"deleted_counts": deleted_dict},
                connection=conn,
            )
            return {
                "session_id": session_id,
                "deleted_counts": deleted_dict,
                "message": "Демо-данные удалены. Рабочие данные пользователя не удалялись.",
            }

    def _status(self, conn: sqlite3.Connection) -> dict[str, object]:
        active = self._active_session(conn)
        created_counts = self._created_counts(conn, int(active["id"])) if active else {}
        has_business = False
        has_non_demo = False
        for table in BUSINESS_TABLES:
            if not self._table_exists(conn, table):
                continue
            total = int(
                conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
            )
            if total:
                has_business = True
            non_demo = int(
                conn.execute(
                    f"SELECT COUNT(*) AS c FROM {table} b WHERE NOT EXISTS (SELECT 1 FROM demo_data_records r JOIN demo_data_sessions s ON s.id=r.session_id AND s.status='active' WHERE r.table_name=? AND r.record_id=b.id)",
                    (table,),
                ).fetchone()["c"]
            )
            if non_demo:
                has_non_demo = True
        has_unsafe_clear_dependencies = False
        if active:
            has_unsafe_clear_dependencies = self._has_untracked_dependencies(
                conn, int(active["id"])
            )
        blocking = []
        if active:
            blocking.append("Демо-данные уже установлены.")
        if has_non_demo:
            blocking.append(
                "Демо-данные можно установить только в пустую рабочую базу. В этой базе уже есть рабочие данные."
            )
        if has_unsafe_clear_dependencies:
            blocking.append(
                "Демо-данные нельзя удалить автоматически: на них уже ссылаются рабочие записи."
            )
        return {
            "is_installed": active is not None,
            "active_session_id": None if active is None else int(active["id"]),
            "demo_version": DEMO_VERSION,
            "can_install": active is None and not has_non_demo,
            "can_clear": active is not None and not has_unsafe_clear_dependencies,
            "has_business_data": has_business,
            "has_non_demo_business_data": has_non_demo,
            "created_counts": created_counts,
            "blocking_reasons": blocking,
            "message": (
                "Демо-данные установлены."
                if active
                else "Демо-данные ещё не установлены."
            ),
        }

    def _active_session(self, conn):
        return conn.execute(
            "SELECT * FROM demo_data_sessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def _created_counts(self, conn, session_id: int) -> dict[str, int]:
        rows = conn.execute(
            "SELECT table_name, COUNT(*) c FROM demo_data_records WHERE session_id = ? GROUP BY table_name",
            (session_id,),
        ).fetchall()
        return {
            COUNT_KEYS.get(r["table_name"], r["table_name"]): int(r["c"])
            for r in rows
            if r["table_name"] in COUNT_KEYS
        }

    def _track(
        self,
        conn,
        session_id: int,
        table: str,
        record_id: int,
        label: str,
        counts: Counter,
    ) -> None:
        conn.execute(
            "INSERT INTO demo_data_records (session_id, table_name, record_id, label) VALUES (?, ?, ?, ?)",
            (session_id, table, record_id, label),
        )
        counts[COUNT_KEYS.get(table, table)] += 1

    def _insert(
        self,
        conn,
        session_id: int,
        counts: Counter,
        table: str,
        label: str,
        sql: str,
        params: tuple,
    ) -> int:
        rid = int(conn.execute(sql, params).lastrowid)
        self._track(conn, session_id, table, rid, label, counts)
        return rid

    def _insert_dataset(self, conn, sid: int, counts: Counter) -> None:
        ing = {}
        for name, cat, unit, density, notes in [
            ("Масло ши", "butter", "g", None, "Демо: питательное масло для кремов."),
            ("Какао масло", "butter", "g", None, "Демо: плотное масло для бальзамов."),
            ("Глицерин", "active", "g", "1.2600", "Демо: увлажняющий компонент."),
            (
                "Вода дистиллированная",
                "water_phase",
                "ml",
                "1.0000",
                "Демо: водная фаза.",
            ),
            ("Эмульгатор", "emulsifier", "g", None, "Демо: эмульгатор для крема."),
        ]:
            label = DEMO_PREFIX + name
            ing[name] = self._insert(
                conn,
                sid,
                counts,
                "ingredients",
                label,
                "INSERT INTO ingredients (name, category, default_unit, density_g_per_ml, notes, supplier_hint) VALUES (?, ?, ?, ?, ?, ?)",
                (label, cat, unit, density, notes, "Демо-поставщик"),
            )
        lots = {}
        for name, qty, cost, exp in [
            ("Масло ши", "120", "0.55", "2027-03-15"),
            ("Какао масло", "45", "0.62", "2026-08-20"),
            ("Глицерин", "80", "0.20", "2027-11-01"),
            ("Эмульгатор", "18", "0.90", "2026-09-10"),
        ]:
            label = f"{DEMO_PREFIX}Партия {name}"
            lot = self._insert(
                conn,
                sid,
                counts,
                "ingredient_lots",
                label,
                "INSERT INTO ingredient_lots (ingredient_id, lot_code, supplier_name, purchased_at, expires_at, unit, unit_cost, notes) VALUES (?, ?, ?, ?, ?, 'g', ?, ?)",
                (
                    ing[name],
                    "DEMO-" + str(len(lots) + 1),
                    "Демо-поставщик",
                    "2026-07-01",
                    exp,
                    cost,
                    "Демо-партия",
                ),
            )
            lots[name] = lot
            self._insert(
                conn,
                sid,
                counts,
                "stock_movements",
                label,
                "INSERT INTO stock_movements (ingredient_lot_id, ingredient_id, movement_type, quantity, unit, direction, reason, source, note) VALUES (?, ?, 'receipt', ?, 'g', 'in', ?, 'system', ?)",
                (lot, ing[name], qty, "Демо-поступление", "Создано демо-режимом"),
            )
        pack = {}
        for name, kind, cap, cost, qty in [
            ("Баночка 30 мл", "jar", "30", "18.00", "4"),
            ("Баночка 50 мл", "jar", "50", "24.00", "1"),
            ("Этикетка косметическая", "label", None, "3.00", "6"),
        ]:
            label = DEMO_PREFIX + name
            pack[name] = self._insert(
                conn,
                sid,
                counts,
                "packaging_items",
                label,
                "INSERT INTO packaging_items (name, kind, capacity_value, capacity_unit, material, supplier_hint, unit_cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    label,
                    kind,
                    cap,
                    "ml" if cap else None,
                    "Пластик" if kind == "jar" else "Бумага",
                    "Демо-поставщик",
                    cost,
                    "Демо-тара",
                ),
            )
            self._insert(
                conn,
                sid,
                counts,
                "packaging_stock_movements",
                label,
                "INSERT INTO packaging_stock_movements (packaging_item_id, movement_type, quantity, direction, reason, source, notes) VALUES (?, 'receipt', ?, 'in', ?, 'system', ?)",
                (pack[name], qty, "Демо-поступление", "Создано демо-режимом"),
            )
        tpl1 = self._insert(
            conn,
            sid,
            counts,
            "recipe_templates",
            DEMO_PREFIX + "Базовый крем для лица",
            "INSERT INTO recipe_templates (name, product_type, description, notes) VALUES (?, ?, ?, ?)",
            (
                DEMO_PREFIX + "Базовый крем для лица",
                "Крем",
                "Демо-рецепт крема",
                "Демо",
            ),
        )
        ver1 = self._insert(
            conn,
            sid,
            counts,
            "recipe_versions",
            DEMO_PREFIX + "Базовый крем v1",
            "INSERT INTO recipe_versions (recipe_template_id, version_number, status, title, target_batch_size_value, target_batch_size_unit, change_note) VALUES (?, 1, 'active', ?, '30', 'g', ?)",
            (tpl1, "Версия 1", "Демо-версия"),
        )
        for pos, (name, pct, phase) in enumerate(
            [
                ("Вода дистиллированная", "70", "Водная"),
                ("Масло ши", "15", "Жирная"),
                ("Глицерин", "5", "Активная"),
                ("Эмульгатор", "10", "Эмульгатор"),
            ],
            1,
        ):
            self._insert(
                conn,
                sid,
                counts,
                "recipe_ingredients",
                DEMO_PREFIX + name,
                "INSERT INTO recipe_ingredients (recipe_version_id, ingredient_id, position, phase, amount_value, amount_unit, notes) VALUES (?, ?, ?, ?, ?, 'percent', ?)",
                (ver1, ing[name], pos, phase, pct, "Демо-строка"),
            )
        tpl2 = self._insert(
            conn,
            sid,
            counts,
            "recipe_templates",
            DEMO_PREFIX + "Питательный бальзам",
            "INSERT INTO recipe_templates (name, product_type, description, notes) VALUES (?, ?, ?, ?)",
            (
                DEMO_PREFIX + "Питательный бальзам",
                "Бальзам",
                "Демо-рецепт бальзама",
                "Демо",
            ),
        )
        ver2 = self._insert(
            conn,
            sid,
            counts,
            "recipe_versions",
            DEMO_PREFIX + "Питательный бальзам v1",
            "INSERT INTO recipe_versions (recipe_template_id, version_number, status, title, target_batch_size_value, target_batch_size_unit, change_note) VALUES (?, 1, 'active', ?, '50', 'g', ?)",
            (tpl2, "Версия 1", "Демо-версия"),
        )
        for pos, (name, pct, phase) in enumerate(
            [
                ("Какао масло", "60", "Жирная"),
                ("Масло ши", "35", "Жирная"),
                ("Эмульгатор", "5", "Добавки"),
            ],
            1,
        ):
            self._insert(
                conn,
                sid,
                counts,
                "recipe_ingredients",
                DEMO_PREFIX + name,
                "INSERT INTO recipe_ingredients (recipe_version_id, ingredient_id, position, phase, amount_value, amount_unit, notes) VALUES (?, ?, ?, ?, ?, 'percent', ?)",
                (ver2, ing[name], pos, phase, pct, "Демо-строка"),
            )
        anna = self._insert(
            conn,
            sid,
            counts,
            "clients",
            DEMO_PREFIX + "Анна Петрова",
            "INSERT INTO clients (full_name, phone, skin_notes, allergy_notes, preference_notes, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                DEMO_PREFIX + "Анна Петрова",
                "+7 900 000-00-01",
                "Сухая кожа",
                "Избегать сильных отдушек",
                "Лёгкая текстура",
                "Демо-клиент",
            ),
        )
        maria = self._insert(
            conn,
            sid,
            counts,
            "clients",
            DEMO_PREFIX + "Мария Иванова",
            "INSERT INTO clients (full_name, phone, skin_notes, preference_notes, notes) VALUES (?, ?, ?, ?, ?)",
            (
                DEMO_PREFIX + "Мария Иванова",
                "+7 900 000-00-02",
                "Нормальная кожа",
                "Плотный бальзам",
                "Демо-клиент",
            ),
        )
        cr = self._insert(
            conn,
            sid,
            counts,
            "client_recipes",
            DEMO_PREFIX + "Крем для Анны",
            "INSERT INTO client_recipes (client_id, source_recipe_version_id, title, status, target_batch_size_value, target_batch_size_unit, personalization_notes) VALUES (?, ?, ?, 'active', '30', 'g', ?)",
            (
                anna,
                ver1,
                DEMO_PREFIX + "Крем для Анны",
                "Демо-адаптация базового крема",
            ),
        )
        for row in conn.execute(
            "SELECT * FROM recipe_ingredients WHERE recipe_version_id=?", (ver1,)
        ).fetchall():
            self._insert(
                conn,
                sid,
                counts,
                "client_recipe_ingredients",
                DEMO_PREFIX + "Индивидуальная строка",
                "INSERT INTO client_recipe_ingredients (client_recipe_id, ingredient_id, source_recipe_ingredient_id, position, phase, amount_value, amount_unit, personalization_note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    cr,
                    row["ingredient_id"],
                    row["id"],
                    row["position"],
                    row["phase"],
                    row["amount_value"],
                    row["amount_unit"],
                    "Демо",
                ),
            )
        self._insert(
            conn,
            sid,
            counts,
            "orders",
            DEMO_PREFIX + "Заказ на крем для лица",
            "INSERT INTO orders (client_id, client_recipe_id, product_name, target_batch_size_value, target_batch_size_unit, packaging_item_id, packaging_quantity, status, sale_price, ordered_at, notes) VALUES (?, ?, ?, '30', 'g', ?, '1', 'new', '950.00', '2026-07-05', ?)",
            (
                anna,
                cr,
                DEMO_PREFIX + "Заказ на крем для лица",
                pack["Баночка 30 мл"],
                "Демо-заказ, можно проверить готовность",
            ),
        )
        self._insert(
            conn,
            sid,
            counts,
            "orders",
            DEMO_PREFIX + "Заказ на питательный бальзам",
            "INSERT INTO orders (client_id, recipe_version_id, product_name, target_batch_size_value, target_batch_size_unit, packaging_item_id, packaging_quantity, status, sale_price, ordered_at, notes) VALUES (?, ?, ?, '100', 'g', ?, '3', 'new', '1400.00', '2026-07-05', ?)",
            (
                maria,
                ver2,
                DEMO_PREFIX + "Заказ на питательный бальзам",
                pack["Баночка 50 мл"],
                "Демо-заказ с ожидаемой нехваткой",
            ),
        )

    def _has_untracked_dependencies(self, conn: sqlite3.Connection, sid: int) -> bool:
        for child_table, child_column, ref_table in DIRECT_DEPENDENCY_CHECKS:
            if self._has_untracked_fk_dependency(
                conn, sid, child_table, child_column, ref_table
            ):
                return True
        if self._has_untracked_generic_dependency(
            conn,
            sid,
            "alerts",
            "related_entity_type",
            "related_entity_id",
            GENERIC_REFERENCE_TARGETS,
        ):
            return True
        if self._has_untracked_generic_dependency(
            conn,
            sid,
            "purchase_suggestions",
            "item_type",
            "item_id",
            PURCHASE_ITEM_REFERENCE_TARGETS,
        ):
            return True
        if self._has_untracked_generic_dependency(
            conn,
            sid,
            "purchase_suggestions",
            "source_entity_type",
            "source_entity_id",
            GENERIC_REFERENCE_TARGETS,
        ):
            return True
        return False

    def _has_untracked_fk_dependency(
        self,
        conn: sqlite3.Connection,
        session_id: int,
        child_table: str,
        child_column: str,
        ref_table: str,
    ) -> bool:
        sql = f"""
            SELECT 1
            FROM {child_table} child
            JOIN demo_data_records ref
              ON ref.session_id = ?
             AND ref.table_name = ?
             AND ref.record_id = child.{child_column}
            WHERE child.{child_column} IS NOT NULL
              AND NOT EXISTS (
                SELECT 1
                FROM demo_data_records own
                WHERE own.session_id = ?
                  AND own.table_name = ?
                  AND own.record_id = child.id
              )
            LIMIT 1
        """
        return (
            conn.execute(
                sql, (session_id, ref_table, session_id, child_table)
            ).fetchone()
            is not None
        )

    def _has_untracked_generic_dependency(
        self,
        conn: sqlite3.Connection,
        session_id: int,
        child_table: str,
        type_column: str,
        id_column: str,
        type_to_table: dict[str, str],
    ) -> bool:
        for entity_type, ref_table in type_to_table.items():
            sql = f"""
                SELECT 1
                FROM {child_table} child
                JOIN demo_data_records ref
                  ON ref.session_id = ?
                 AND ref.table_name = ?
                 AND ref.record_id = child.{id_column}
                WHERE child.{type_column} = ?
                  AND child.{id_column} IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1
                    FROM demo_data_records own
                    WHERE own.session_id = ?
                      AND own.table_name = ?
                      AND own.record_id = child.id
                  )
                LIMIT 1
            """
            if conn.execute(
                sql, (session_id, ref_table, entity_type, session_id, child_table)
            ).fetchone():
                return True
        return False

    def _table_exists(self, conn, table: str) -> bool:
        return (
            conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            is not None
        )
