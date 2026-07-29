"""The read-only `Журнал действий` query service.

Durable contract: ``docs/audit-log.md``.

Assembles the safe read model: validate the raw query, read `audit_logs`, and
resolve every user-facing value through the pure presenter. It performs no
write of any kind — no AuditLog row, no business mutation, no file, no setting,
no regeneration, and no cleanup or normalization of historical rows. Reading the
journal is never itself an audited event.
"""

import sqlite3

from app.db.config import DatabaseConfig
from app.domain.audit_log_presentation import action_label, actor_label, display_summary, entity_label
from app.domain.audit_log_query import AuditLogQuery, parse_audit_log_query
from app.domain.tax_rate_timestamps import api_timestamp
from app.repositories.audit import AuditLogRepository
from app.schemas.audit_logs import AuditLogFilterOption, AuditLogFilterOptions, AuditLogItem, AuditLogListResponse


class AuditLogsService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.repository = AuditLogRepository(config)

    def list_audit_logs(
        self,
        *,
        created_from: object = None,
        created_before: object = None,
        action: object = None,
        entity_type: object = None,
        actor_type: object = None,
        limit: object = None,
        offset: object = None,
    ) -> AuditLogListResponse:
        """Validate the raw query and return one safe page of history."""
        query = parse_audit_log_query(
            created_from=created_from,
            created_before=created_before,
            action=action,
            entity_type=entity_type,
            actor_type=actor_type,
            limit=limit,
            offset=offset,
        )
        rows, total = self.repository.list_logs(query)
        return AuditLogListResponse(
            items=[_item(row) for row in rows],
            total=total,
            limit=query.limit,
            offset=query.offset,
            filter_options=self._filter_options(),
        )

    def _filter_options(self) -> AuditLogFilterOptions:
        """Selectable filter values, labelled by the same resolver as the items.

        Because the labels come from the presenter, an unknown code persisted by
        an older local database stays selectable under its safe Russian fallback
        instead of being dropped or shown as a raw technical identifier.
        """
        values = self.repository.distinct_filter_values()
        return AuditLogFilterOptions(
            actions=[AuditLogFilterOption(value=value, label=action_label(value)) for value in values["action"]],
            entity_types=[AuditLogFilterOption(value=value, label=entity_label(value)) for value in values["entity_type"]],
            actor_types=[AuditLogFilterOption(value=value, label=actor_label(value)) for value in values["actor_type"]],
        )


def _item(row: sqlite3.Row) -> AuditLogItem:
    """One row reduced to the exact safe item shape of § 5.2.

    Every field is named explicitly rather than expanded from the row, so the
    persisted `summary` contributes only through the bounded presenter and no
    future column can leak by being added to the table.
    """
    return AuditLogItem(
        id=row["id"],
        created_at=api_timestamp(row["created_at"]) or "",
        action=row["action"],
        action_label=action_label(row["action"]),
        entity_type=row["entity_type"],
        entity_label=entity_label(row["entity_type"]),
        display_summary=display_summary(row["action"], row["summary"]),
        actor_type=row["actor_type"],
        actor_label=actor_label(row["actor_type"]),
    )


__all__ = ["AuditLogQuery", "AuditLogsService"]
