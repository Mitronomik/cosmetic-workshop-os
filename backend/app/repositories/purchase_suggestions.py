from contextlib import nullcontext
import sqlite3
from uuid import uuid4

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.purchase_suggestions import PurchaseSuggestionCandidate
from app.models.purchase_suggestion import PurchaseSuggestion


class PurchaseSuggestionNotFoundError(LookupError):
    pass


class PurchaseSuggestionRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def list_suggestions(self, *, status: str | None = "open", reason: str | None = None, item_type: str | None = None, limit: int = 100, offset: int = 0) -> list[PurchaseSuggestion]:
        clauses=[]; params=[]
        if status not in (None, "all"):
            clauses.append("status=?"); params.append(status)
        if reason is not None:
            clauses.append("reason=?"); params.append(reason)
        if item_type is not None:
            clauses.append("item_type=?"); params.append(item_type)
        sql = "SELECT * FROM purchase_suggestions" + (" WHERE "+" AND ".join(clauses) if clauses else "") + " ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'purchased' THEN 1 WHEN 'dismissed' THEN 2 ELSE 3 END, CASE reason WHEN 'insufficient_for_order' THEN 0 WHEN 'below_minimum_stock' THEN 1 WHEN 'expiration_replacement' THEN 2 WHEN 'predicted_shortage' THEN 3 ELSE 4 END, updated_at DESC, id DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        with session(self.config) as c:
            return [_row(r) for r in c.execute(sql, tuple(params)).fetchall()]

    def get_suggestion(self, suggestion_id: int, *, connection: sqlite3.Connection | None = None) -> PurchaseSuggestion:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM purchase_suggestions WHERE id=?", (suggestion_id,)).fetchone()
        if row is None:
            raise PurchaseSuggestionNotFoundError(f"Purchase suggestion {suggestion_id} was not found.")
        return _row(row)

    def upsert_open_candidate(self, candidate: PurchaseSuggestionCandidate, *, connection: sqlite3.Connection | None = None) -> tuple[PurchaseSuggestion, bool, bool]:
        with _scope(self.config, connection) as c:
            existing = c.execute("SELECT * FROM purchase_suggestions WHERE suggestion_key=?", (candidate.suggestion_key,)).fetchone()
            values = (candidate.suggestion_key, candidate.item_type, candidate.item_id, candidate.item_name_snapshot, candidate.recommended_quantity, candidate.unit, candidate.reason, candidate.source_entity_type, candidate.source_entity_id, candidate.message, candidate.notes)
            if existing is None:
                cur = c.execute("""INSERT INTO purchase_suggestions (suggestion_key, item_type, item_id, item_name_snapshot, recommended_quantity, unit, reason, source_entity_type, source_entity_id, message, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
                return self.get_suggestion(cur.lastrowid, connection=c), True, False
            if existing["status"] != "open":
                return _row(existing), False, False
            c.execute("""UPDATE purchase_suggestions SET item_type=?, item_id=?, item_name_snapshot=?, recommended_quantity=?, unit=?, reason=?, source_entity_type=?, source_entity_id=?, message=?, notes=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?""", values[1:] + (existing["id"],))
            return self.get_suggestion(existing["id"], connection=c), False, True

    def create_manual_suggestion(self, *, item_type: str, item_id: int, item_name_snapshot: str, recommended_quantity: str, unit: str, notes: str, connection: sqlite3.Connection | None = None) -> PurchaseSuggestion:
        key = f"manual:{item_type}:{item_id}:{uuid4().hex}"
        message = f"Купить {'компонент' if item_type == 'ingredient' else 'тару'} «{item_name_snapshot}»: вручную добавлено {recommended_quantity} {unit}."
        candidate = PurchaseSuggestionCandidate(key, item_type, item_id, item_name_snapshot, recommended_quantity, unit, "manual", "manual", None, message, notes)
        suggestion, _, _ = self.upsert_open_candidate(candidate, connection=connection)
        return suggestion

    def update_open_suggestion(self, suggestion_id: int, *, recommended_quantity: str, unit: str, notes: str, connection: sqlite3.Connection | None = None) -> PurchaseSuggestion:
        with _scope(self.config, connection) as c:
            current = self.get_suggestion(suggestion_id, connection=c)
            if current.status != "open":
                return current
            c.execute("UPDATE purchase_suggestions SET recommended_quantity=?, unit=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (recommended_quantity, unit, notes, suggestion_id))
            return self.get_suggestion(suggestion_id, connection=c)

    def mark_purchased(self, suggestion_id: int, *, connection: sqlite3.Connection | None = None) -> PurchaseSuggestion:
        return self._set_terminal_status(suggestion_id, "purchased", connection=connection)

    def dismiss_suggestion(self, suggestion_id: int, *, connection: sqlite3.Connection | None = None) -> PurchaseSuggestion:
        return self._set_terminal_status(suggestion_id, "dismissed", connection=connection)

    def _set_terminal_status(self, suggestion_id: int, status: str, *, connection=None) -> PurchaseSuggestion:
        with _scope(self.config, connection) as c:
            current = self.get_suggestion(suggestion_id, connection=c)
            if current.status != "open":
                return current
            c.execute("UPDATE purchase_suggestions SET status=?, resolved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, suggestion_id))
            return self.get_suggestion(suggestion_id, connection=c)

    def archive_open_suggestions_if_not_in_keys(self, active_keys: set[str], managed_reasons: set[str], *, connection: sqlite3.Connection | None = None) -> int:
        if not managed_reasons:
            return 0
        with _scope(self.config, connection) as c:
            reason_ph = ','.join('?' for _ in managed_reasons)
            params = list(managed_reasons)
            key_clause = ""
            if active_keys:
                key_ph = ','.join('?' for _ in active_keys)
                key_clause = f" AND suggestion_key NOT IN ({key_ph})"
                params.extend(active_keys)
            cur = c.execute(f"UPDATE purchase_suggestions SET status='archived', resolved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE status='open' AND reason IN ({reason_ph}){key_clause}", tuple(params))
            return cur.rowcount

    def count_open(self, *, connection: sqlite3.Connection | None = None) -> int:
        with _scope(self.config, connection) as c:
            return c.execute("SELECT COUNT(*) FROM purchase_suggestions WHERE status='open'").fetchone()[0]


def _row(r) -> PurchaseSuggestion:
    return PurchaseSuggestion(r["id"], r["suggestion_key"], r["item_type"], r["item_id"], r["item_name_snapshot"], r["recommended_quantity"], r["unit"], r["reason"], r["source_entity_type"], r["source_entity_id"], r["message"], r["status"], r["notes"], r["created_at"], r["updated_at"], r["resolved_at"])


def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
