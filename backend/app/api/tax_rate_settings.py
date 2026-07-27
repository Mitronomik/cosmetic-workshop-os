from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.repositories.settings import SettingsNotInitializedError
from app.schemas.tax_rate_settings import TaxRateSettingResponse, TaxRateSettingUpdateRequest
from app.services.tax_rate_settings import TaxRateSettingPersistenceError, TaxRateSettingsService

router = APIRouter(prefix="/settings", tags=["settings"])

NOT_INITIALIZED_DETAIL = "Database is not initialized. Run explicit database initialization before reading settings."


@router.get("/tax-rate", response_model=TaxRateSettingResponse)
def get_tax_rate() -> TaxRateSettingResponse:
    try:
        return TaxRateSettingsService().get_tax_rate()
    except SettingsNotInitializedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NOT_INITIALIZED_DETAIL) from exc


@router.put("/tax-rate", response_model=TaxRateSettingResponse)
def update_tax_rate(payload: TaxRateSettingUpdateRequest) -> TaxRateSettingResponse:
    try:
        return TaxRateSettingsService().update_tax_rate(payload.tax_rate_percent)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except SettingsNotInitializedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NOT_INITIALIZED_DETAIL) from exc
    except TaxRateSettingPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "tax_rate_setting_not_saved",
                "message": "Не удалось сохранить налоговую ставку. Предыдущее значение сохранено без изменений.",
                "next_action": "Повторите сохранение. Если ошибка повторяется, проверьте, что локальное приложение работает.",
            },
        ) from exc
