from typing import Literal
from fastapi import APIRouter, HTTPException, Query

from app.domain.alerts import ALERT_TYPES
from app.repositories.alerts import AlertNotFoundError, AlertRepository
from app.schemas.alerts import AlertGenerationResponse, AlertListResponse, AlertResponse
from app.services.alerts import AlertGenerationService

router = APIRouter(tags=["alerts"])
AlertStatusQuery = Literal["open", "resolved", "dismissed", "all"]


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(status: AlertStatusQuery = "open", type: str | None = None, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    if type is not None and type not in ALERT_TYPES:
        raise HTTPException(422, detail="Unknown alert type.")
    rows = AlertRepository().list_alerts(status=status, type=type, limit=limit, offset=offset)
    return AlertListResponse(alerts=[_response(a) for a in rows], limit=limit, offset=offset)


@router.post("/alerts/regenerate", response_model=AlertGenerationResponse)
def regenerate_alerts():
    result = AlertGenerationService().regenerate_alerts()
    return AlertGenerationResponse(**result.__dict__)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int):
    try:
        return _response(AlertRepository().resolve_alert(alert_id))
    except AlertNotFoundError as exc:
        raise HTTPException(404, detail="Alert was not found.") from exc


@router.post("/alerts/{alert_id}/dismiss", response_model=AlertResponse)
def dismiss_alert(alert_id: int):
    try:
        return _response(AlertRepository().dismiss_alert(alert_id))
    except AlertNotFoundError as exc:
        raise HTTPException(404, detail="Alert was not found.") from exc


def _response(a) -> AlertResponse:
    return AlertResponse(**a.__dict__)
