import json
import sqlite3
from contextlib import nullcontext

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session


class AuditLogRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def create_log(
        self,
        *,
        action: str,
        entity_type: str | None,
        entity_id: str | None,
        summary: str,
        actor_type: str = "system",
        metadata: dict[str, object] | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        with _connection_scope(self.config, connection) as connection:
            connection.execute(
                """
                INSERT INTO audit_logs (actor_type, action, entity_type, entity_id, summary, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (actor_type, action, entity_type, entity_id, summary, json.dumps(metadata or {}, ensure_ascii=False)),
            )


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
