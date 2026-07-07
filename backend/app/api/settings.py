from fastapi import APIRouter, HTTPException, status

from app.repositories.settings import SettingsNotInitializedError
from app.schemas.settings import AppSettingsResponse, AppSettingResponse, SettingsStatusResponse
from app.services.settings import get_settings_status, read_app_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def get_settings() -> AppSettingsResponse:
    try:
        settings = [AppSettingResponse(**setting.__dict__) for setting in read_app_settings()]
    except SettingsNotInitializedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database is not initialized. Run explicit database initialization before reading settings.",
        ) from exc
    return AppSettingsResponse(settings=settings)


@router.get("/status", response_model=SettingsStatusResponse)
def get_settings_status_endpoint() -> SettingsStatusResponse:
    return get_settings_status()
