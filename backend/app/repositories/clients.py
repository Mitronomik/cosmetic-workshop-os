from contextlib import nullcontext
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.clients import ClientDraft
from app.models.client import Client


class ClientNotFoundError(LookupError):
    pass


class ClientRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create(self, draft: ClientDraft, *, connection: sqlite3.Connection | None = None) -> Client:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                INSERT INTO clients (
                    full_name, phone, email, address, birthday, skin_notes,
                    allergy_notes, preference_notes, contraindication_notes, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _draft_values(draft),
            )
            row = connection.execute("SELECT * FROM clients WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_client(row)

    def get_by_id(self, client_id: int) -> Client:
        with session(self.config) as connection:
            row = connection.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if row is None:
            raise ClientNotFoundError(f"Client {client_id} was not found.")
        return _row_to_client(row)

    def list_clients(self, *, include_inactive: bool = False) -> list[Client]:
        with session(self.config) as connection:
            if include_inactive:
                rows = connection.execute("SELECT * FROM clients ORDER BY full_name, id").fetchall()
            else:
                rows = connection.execute("SELECT * FROM clients WHERE is_active = 1 ORDER BY full_name, id").fetchall()
        return [_row_to_client(row) for row in rows]

    def update_basic(self, client_id: int, draft: ClientDraft, *, connection: sqlite3.Connection | None = None) -> Client:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                UPDATE clients
                SET full_name = ?, phone = ?, email = ?, address = ?, birthday = ?,
                    skin_notes = ?, allergy_notes = ?, preference_notes = ?,
                    contraindication_notes = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*_draft_values(draft), client_id),
            )
            if cursor.rowcount == 0:
                raise ClientNotFoundError(f"Client {client_id} was not found.")
            row = connection.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return _row_to_client(row)

    def deactivate(self, client_id: int, *, connection: sqlite3.Connection | None = None) -> Client:
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                "UPDATE clients SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (client_id,),
            )
            if cursor.rowcount == 0:
                raise ClientNotFoundError(f"Client {client_id} was not found.")
            row = connection.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return _row_to_client(row)


def _draft_values(draft: ClientDraft):
    return (
        draft.full_name,
        draft.phone,
        draft.email,
        draft.address,
        None if draft.birthday is None else draft.birthday.isoformat(),
        draft.skin_notes,
        draft.allergy_notes,
        draft.preference_notes,
        draft.contraindication_notes,
        draft.notes,
    )


def _row_to_client(row) -> Client:
    return Client(
        id=row["id"], full_name=row["full_name"], phone=row["phone"], email=row["email"],
        address=row["address"], birthday=row["birthday"], skin_notes=row["skin_notes"],
        allergy_notes=row["allergy_notes"], preference_notes=row["preference_notes"],
        contraindication_notes=row["contraindication_notes"], notes=row["notes"],
        is_active=bool(row["is_active"]), created_at=row["created_at"], updated_at=row["updated_at"],
    )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
