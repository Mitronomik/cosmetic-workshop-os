import json
import sqlite3
from contextlib import nullcontext

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.audit_log_query import AuditLogQuery

# Read only what the safe read model of `docs/audit-log.md` § 5.2 can be built
# from. `entity_id` and `metadata_json` are deliberately absent from the select
# list, so no code path downstream can accidentally serialize them.
_READ_COLUMNS = "id, created_at, action, entity_type, summary, actor_type"

# `docs/audit-log.md` § 7.1. `created_at` has one-second precision, so ties are
# ordinary; `id DESC` is what makes the order deterministic and offset pagination
# stable. The existing `idx_audit_logs_created_at` index supports this and no new
# index is required.
_ORDER_BY = "ORDER BY created_at DESC, id DESC"


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
    ) -> int:
        """Insert one AuditLog row and return its row ID.

        `docs/decisions/0013-file-backed-artifact-audit-semantics.md` §
        "Required operation sequence". Returning the ID is a compatible
        extension: every parameter, the optional caller-owned connection and the
        insert itself are unchanged, and existing callers that ignore the return
        value keep behaving exactly as before.

        The ID exists because a durable artifact operation has to record *which*
        row it committed with, inside the same transaction as the insert. Reading
        it back by matching action and timestamp afterwards would be ambiguous
        and would need a second statement outside the write lock.
        """
        with _connection_scope(self.config, connection) as connection:
            cursor = connection.execute(
                """
                INSERT INTO audit_logs (actor_type, action, entity_type, entity_id, summary, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (actor_type, action, entity_type, entity_id, summary, json.dumps(metadata or {}, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def list_logs(self, query: AuditLogQuery, *, connection: sqlite3.Connection | None = None) -> tuple[list[sqlite3.Row], int]:
        """One page of history plus the pre-pagination total for the same filters.

        Reads `audit_logs` alone and joins no business table, so no client note,
        wish, feedback body or other business value can be reached from here. The
        query is parameterized throughout and writes nothing.
        """
        where, parameters = _filter_clause(query)
        with _connection_scope(self.config, connection) as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM audit_logs{where}", parameters).fetchone()[0]
            rows = connection.execute(
                f"SELECT {_READ_COLUMNS} FROM audit_logs{where} {_ORDER_BY} LIMIT ? OFFSET ?",
                (*parameters, query.limit, query.offset),
            ).fetchall()
        return list(rows), int(total)

    def distinct_filter_values(self, *, connection: sqlite3.Connection | None = None) -> dict[str, list[str]]:
        """The codes that actually exist as rows, ignoring the current filters.

        Derived from the whole table rather than from a hard-coded catalogue, so a
        fresh database yields short lists instead of 50 fabricated actions, and
        deliberately independent of the caller's filters, so the options do not
        shift under the user as they narrow a search.

        A `null` `entity_type` is omitted: `null` is not a query code and could
        not be selected without inventing a filter sentinel. Such rows stay fully
        readable as items carrying the unknown-entity label.
        """
        with _connection_scope(self.config, connection) as connection:
            return {
                column: [row[0] for row in connection.execute(
                    f"SELECT DISTINCT {column} FROM audit_logs WHERE {column} IS NOT NULL ORDER BY {column} ASC"
                ).fetchall()]
                for column in ("action", "entity_type", "actor_type")
            }


def _filter_clause(query: AuditLogQuery) -> tuple[str, tuple[object, ...]]:
    """The shared `WHERE` fragment, so the page and its total never disagree.

    `created_from` is inclusive and `created_before` is exclusive, and every
    supplied filter is combined with logical `AND`.
    """
    clauses: list[str] = []
    parameters: list[object] = []
    if query.created_from is not None:
        clauses.append("created_at >= ?")
        parameters.append(query.created_from)
    if query.created_before is not None:
        clauses.append("created_at < ?")
        parameters.append(query.created_before)
    for column, value in (("action", query.action), ("entity_type", query.entity_type), ("actor_type", query.actor_type)):
        if value is not None:
            clauses.append(f"{column} = ?")
            parameters.append(value)
    return (f" WHERE {' AND '.join(clauses)}" if clauses else ""), tuple(parameters)


def _connection_scope(config: DatabaseConfig, connection: sqlite3.Connection | None):
    return nullcontext(connection) if connection is not None else session(config)
