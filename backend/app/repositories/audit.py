import json

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
    ) -> None:
        with session(self.config) as connection:
            connection.execute(
                """
                INSERT INTO audit_logs (actor_type, action, entity_type, entity_id, summary, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (actor_type, action, entity_type, entity_id, summary, json.dumps(metadata or {}, ensure_ascii=False)),
            )
