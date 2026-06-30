from contextlib import nullcontext
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.client_wishes_feedback import ClientFeedbackDraft, ClientWishDraft
from app.models.client_wishes_feedback import ClientFeedback, ClientFeedbackSentiment, ClientFeedbackType, ClientWish, ClientWishCategory, ClientWishPriority, ClientWishStatus


class ClientWishNotFoundError(LookupError):
    pass


class ClientFeedbackNotFoundError(LookupError):
    pass


class ClientWishRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: ClientWishDraft, *, connection: sqlite3.Connection | None = None) -> ClientWish:
        with _scope(self.config, connection) as c:
            cur = c.execute(
                """
                INSERT INTO client_wishes (client_id, client_recipe_id, title, description, category, priority)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (draft.client_id, draft.client_recipe_id, draft.title, draft.description, draft.category.value, draft.priority.value),
            )
            row = c.execute("SELECT * FROM client_wishes WHERE id=?", (cur.lastrowid,)).fetchone()
        return _wish(row)

    def list_for_client(self, client_id: int, *, include_inactive: bool = False) -> list[ClientWish]:
        with session(self.config) as c:
            if include_inactive:
                rows = c.execute("SELECT * FROM client_wishes WHERE client_id=? ORDER BY is_active DESC, updated_at DESC, id DESC", (client_id,)).fetchall()
            else:
                rows = c.execute("SELECT * FROM client_wishes WHERE client_id=? AND is_active=1 ORDER BY updated_at DESC, id DESC", (client_id,)).fetchall()
        return [_wish(r) for r in rows]

    def get(self, wish_id: int, *, connection: sqlite3.Connection | None = None) -> ClientWish:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM client_wishes WHERE id=?", (wish_id,)).fetchone()
        if row is None:
            raise ClientWishNotFoundError(f"Client wish {wish_id} was not found.")
        return _wish(row)

    def update_status(self, wish_id: int, status: ClientWishStatus, *, connection: sqlite3.Connection | None = None) -> ClientWish:
        if status == ClientWishStatus.RESOLVED:
            resolved_value_sql = "CURRENT_TIMESTAMP"
        else:
            resolved_value_sql = "NULL"
        with _scope(self.config, connection) as c:
            cur = c.execute(
                f"UPDATE client_wishes SET status=?, is_active=1, updated_at=CURRENT_TIMESTAMP, resolved_at={resolved_value_sql} WHERE id=?",
                (status.value, wish_id),
            )
            if cur.rowcount == 0:
                raise ClientWishNotFoundError(f"Client wish {wish_id} was not found.")
            row = c.execute("SELECT * FROM client_wishes WHERE id=?", (wish_id,)).fetchone()
        return _wish(row)

    def archive(self, wish_id: int, *, connection: sqlite3.Connection | None = None) -> ClientWish:
        with _scope(self.config, connection) as c:
            cur = c.execute("UPDATE client_wishes SET status='archived', is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?", (wish_id,))
            if cur.rowcount == 0:
                raise ClientWishNotFoundError(f"Client wish {wish_id} was not found.")
            row = c.execute("SELECT * FROM client_wishes WHERE id=?", (wish_id,)).fetchone()
        return _wish(row)


class ClientFeedbackRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: ClientFeedbackDraft, *, connection: sqlite3.Connection | None = None) -> ClientFeedback:
        with _scope(self.config, connection) as c:
            cur = c.execute(
                """
                INSERT INTO client_feedback (client_id, client_recipe_id, feedback_type, sentiment, rating, text, follow_up_needed, follow_up_note, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (draft.client_id, draft.client_recipe_id, draft.feedback_type.value, draft.sentiment.value, draft.rating, draft.text, 1 if draft.follow_up_needed else 0, draft.follow_up_note, draft.occurred_at),
            )
            row = c.execute("SELECT * FROM client_feedback WHERE id=?", (cur.lastrowid,)).fetchone()
        return _feedback(row)

    def list_for_client(self, client_id: int) -> list[ClientFeedback]:
        with session(self.config) as c:
            rows = c.execute("SELECT * FROM client_feedback WHERE client_id=? ORDER BY created_at DESC, id DESC", (client_id,)).fetchall()
        return [_feedback(r) for r in rows]

    def get(self, feedback_id: int, *, connection: sqlite3.Connection | None = None) -> ClientFeedback:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM client_feedback WHERE id=?", (feedback_id,)).fetchone()
        if row is None:
            raise ClientFeedbackNotFoundError(f"Client feedback {feedback_id} was not found.")
        return _feedback(row)


def _wish(r) -> ClientWish:
    return ClientWish(r["id"], r["client_id"], r["client_recipe_id"], r["title"], r["description"], ClientWishCategory(r["category"]), ClientWishPriority(r["priority"]), ClientWishStatus(r["status"]), bool(r["is_active"]), r["created_at"], r["updated_at"], r["resolved_at"])


def _feedback(r) -> ClientFeedback:
    return ClientFeedback(r["id"], r["client_id"], r["client_recipe_id"], ClientFeedbackType(r["feedback_type"]), ClientFeedbackSentiment(r["sentiment"]), r["rating"], r["text"], bool(r["follow_up_needed"]), r["follow_up_note"], r["occurred_at"], r["created_at"])


def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
