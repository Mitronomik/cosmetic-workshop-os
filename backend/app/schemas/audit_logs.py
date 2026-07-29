"""Response schemas for `GET /api/audit-logs`.

Durable contract: ``docs/audit-log.md`` § 5 and § 7.5.

The shapes here are exact. `extra="forbid"` is set on every model so a field the
contract excludes — the raw persisted `summary`, `metadata_json`, `entity_id`,
or any `source` / `source_label` — cannot reach a response by being passed in
accidentally: construction fails loudly instead of serializing a value the user
must never see.
"""

from pydantic import BaseModel, ConfigDict


class AuditLogItem(BaseModel):
    """One safe history entry — exactly the nine fields of § 5.2.

    `id` is an internal row identity kept for list keying and stable ordering,
    never presented as a business value. `action`, `entity_type` and `actor_type`
    are stable codes carried for filtering and forward compatibility; the
    `*_label` fields and `display_summary` are what the user actually reads.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    created_at: str
    action: str
    action_label: str
    entity_type: str | None
    entity_label: str
    display_summary: str
    actor_type: str
    actor_label: str


class AuditLogFilterOption(BaseModel):
    """One selectable filter value paired with its Russian label."""

    model_config = ConfigDict(extra="forbid")

    value: str
    label: str


class AuditLogFilterOptions(BaseModel):
    """The filter values that actually exist as rows in `audit_logs`.

    Derived from the whole table rather than the current page, so the options do
    not change merely because the result filters changed. `entity_types` omits
    `null`, because `null` is not an authorized query code and could not be
    selected without inventing a filter sentinel; rows with no entity type stay
    readable as items carrying the unknown-entity label.
    """

    model_config = ConfigDict(extra="forbid")

    actions: list[AuditLogFilterOption]
    entity_types: list[AuditLogFilterOption]
    actor_types: list[AuditLogFilterOption]


class AuditLogListResponse(BaseModel):
    """The exact five top-level fields of § 5.1.

    `total` counts the rows matching the current filters *before* `limit` and
    `offset` apply. `limit` and `offset` echo the effective applied values, which
    differ from the request only when a parameter was omitted and its default
    applied — invalid values are rejected rather than clamped.
    """

    model_config = ConfigDict(extra="forbid")

    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int
    filter_options: AuditLogFilterOptions
