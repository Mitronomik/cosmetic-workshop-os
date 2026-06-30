from contextlib import nullcontext
import sqlite3

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.domain.alerts import AlertCandidate
from app.models.alert import Alert


class AlertNotFoundError(LookupError):
    pass


class AlertRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()

    def list_alerts(self, *, status: str | None = "open", type: str | None = None, limit: int = 100, offset: int = 0) -> list[Alert]:
        clauses=[]; params=[]
        if status not in (None, "all"):
            clauses.append("status=?"); params.append(status)
        if type is not None:
            clauses.append("type=?"); params.append(type)
        sql = "SELECT * FROM alerts" + (" WHERE "+" AND ".join(clauses) if clauses else "") + " ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'resolved' THEN 1 ELSE 2 END, CASE severity WHEN 'blocking' THEN 0 WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END, updated_at DESC, id DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        with session(self.config) as c:
            return [_row(r) for r in c.execute(sql, tuple(params)).fetchall()]

    def get_alert(self, alert_id: int, *, connection: sqlite3.Connection | None = None) -> Alert:
        with _scope(self.config, connection) as c:
            row = c.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
        if row is None:
            raise AlertNotFoundError(f"Alert {alert_id} was not found.")
        return _row(row)

    def upsert_open_candidate(self, candidate: AlertCandidate, *, connection: sqlite3.Connection | None = None) -> tuple[Alert, bool, bool]:
        with _scope(self.config, connection) as c:
            existing = c.execute("SELECT * FROM alerts WHERE alert_key=?", (candidate.alert_key,)).fetchone()
            if existing is None:
                cur = c.execute("""INSERT INTO alerts (alert_key, type, severity, message, related_entity_type, related_entity_id, recommended_action)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", (candidate.alert_key, candidate.type, candidate.severity, candidate.message, candidate.related_entity_type, candidate.related_entity_id, candidate.recommended_action))
                return self.get_alert(cur.lastrowid, connection=c), True, False
            if existing["status"] != "open":
                return _row(existing), False, False
            c.execute("""UPDATE alerts SET type=?, severity=?, message=?, related_entity_type=?, related_entity_id=?, recommended_action=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?""", (candidate.type, candidate.severity, candidate.message, candidate.related_entity_type, candidate.related_entity_id, candidate.recommended_action, existing["id"]))
            return self.get_alert(existing["id"], connection=c), False, True

    def resolve_alert(self, alert_id: int, *, connection: sqlite3.Connection | None = None) -> Alert:
        return self._set_status(alert_id, "resolved", connection=connection)

    def dismiss_alert(self, alert_id: int, *, connection: sqlite3.Connection | None = None) -> Alert:
        return self._set_status(alert_id, "dismissed", connection=connection)

    def _set_status(self, alert_id: int, status: str, *, connection=None) -> Alert:
        col = "resolved_at" if status == "resolved" else "dismissed_at"
        with _scope(self.config, connection) as c:
            if c.execute("SELECT 1 FROM alerts WHERE id=?", (alert_id,)).fetchone() is None:
                raise AlertNotFoundError(f"Alert {alert_id} was not found.")
            c.execute(f"UPDATE alerts SET status=?, {col}=COALESCE({col}, CURRENT_TIMESTAMP), updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, alert_id))
            return self.get_alert(alert_id, connection=c)

    def mark_open_alerts_resolved_if_not_in_keys(self, active_keys: set[str], *, connection: sqlite3.Connection | None = None) -> int:
        with _scope(self.config, connection) as c:
            if active_keys:
                placeholders=','.join('?' for _ in active_keys)
                cur=c.execute(f"UPDATE alerts SET status='resolved', resolved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE status='open' AND alert_key NOT IN ({placeholders})", tuple(active_keys))
            else:
                cur=c.execute("UPDATE alerts SET status='resolved', resolved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE status='open'")
            return cur.rowcount

    def count_open(self, *, connection: sqlite3.Connection | None = None) -> int:
        with _scope(self.config, connection) as c:
            return c.execute("SELECT COUNT(*) FROM alerts WHERE status='open'").fetchone()[0]


def _row(r) -> Alert:
    return Alert(r["id"], r["alert_key"], r["type"], r["severity"], r["message"], r["related_entity_type"], r["related_entity_id"], r["recommended_action"], r["status"], r["created_at"], r["updated_at"], r["resolved_at"], r["dismissed_at"])


def _scope(config, connection):
    return nullcontext(connection) if connection is not None else session(config)
