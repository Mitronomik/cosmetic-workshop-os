from fastapi import APIRouter

from app.schemas.database import DatabaseStatusResponse
from app.services.database import database_status

router = APIRouter(prefix="/database", tags=["database"])


@router.get("/status", response_model=DatabaseStatusResponse)
def get_database_status() -> DatabaseStatusResponse:
    return DatabaseStatusResponse(**database_status())
