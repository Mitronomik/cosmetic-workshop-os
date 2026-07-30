"""The single authorized AuditLog endpoint.

Durable contract: ``docs/audit-log.md`` § 4.

Read-only. No detail endpoint, and no `POST` / `PUT` / `PATCH` / `DELETE`
surface: the `docs/roadmap.md` § PR27 proposal `GET /api/audit-logs/{id}` is
explicitly superseded for the MVP.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.domain.errors import DomainValidationError
from app.schemas.audit_logs import AuditLogListResponse
from app.services.audit_logs import AuditLogsService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    created_from: str | None = Query(default=None),
    created_before: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    actor_type: str | None = Query(default=None),
    limit: str | None = Query(default=None),
    offset: str | None = Query(default=None),
) -> AuditLogListResponse:
    """Return one safe, filtered, bounded page of `Журнал действий`.

    Every parameter is accepted as raw text and validated by the project's own
    domain path. Typing `limit` and `offset` as integers here would let FastAPI
    answer `limit=abc` with Pydantic's validation body, losing the structured
    Russian `DomainIssue` the contract requires — and would also collapse the
    ordered precedence that makes `limit=-1` `negative_quantity` and `limit=0`
    `pagination_out_of_range`.
    """
    try:
        return AuditLogsService().list_audit_logs(
            created_from=created_from,
            created_before=created_before,
            action=action,
            entity_type=entity_type,
            actor_type=actor_type,
            limit=limit,
            offset=offset,
        )
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
