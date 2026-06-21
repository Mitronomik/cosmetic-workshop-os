from fastapi import APIRouter

from app.schemas.settings import AppSettingsResponse, AppSettingResponse
from app.services.settings import read_app_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def get_settings() -> AppSettingsResponse:
    settings = [AppSettingResponse(**setting.__dict__) for setting in read_app_settings()]
    return AppSettingsResponse(settings=settings)
