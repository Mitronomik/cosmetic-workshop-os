from fastapi import APIRouter, HTTPException, status

from app.repositories.settings import SettingsNotInitializedError
from app.schemas.settings import AppSettingsResponse, AppSettingResponse, SettingsStatusResponse, WorkshopProfileResponse, WorkshopProfileUpdateRequest
from app.services.settings import WorkshopProfileSettingsService, WorkshopProfileValidationError, get_settings_status, read_app_settings

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


@router.get("/workshop-profile", response_model=WorkshopProfileResponse)
def get_workshop_profile() -> WorkshopProfileResponse:
    try:
        return WorkshopProfileSettingsService().get_profile()
    except SettingsNotInitializedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database is not initialized. Run explicit database initialization before reading settings.") from exc


@router.put("/workshop-profile", response_model=WorkshopProfileResponse)
def update_workshop_profile(request: WorkshopProfileUpdateRequest) -> WorkshopProfileResponse:
    try:
        return WorkshopProfileSettingsService().update_profile(request)
    except WorkshopProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except SettingsNotInitializedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database is not initialized. Run explicit database initialization before updating settings.") from exc
