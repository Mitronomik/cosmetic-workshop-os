from fastapi import APIRouter, HTTPException, status

from app.schemas.demo_data import (
    DemoDataClearRequest,
    DemoDataClearResponse,
    DemoDataInstallRequest,
    DemoDataInstallResponse,
    DemoDataStatusResponse,
)
from app.services.demo_data import (
    DemoDataConfirmationError,
    DemoDataConflictError,
    DemoDataService,
)

router = APIRouter(prefix="/demo-data", tags=["demo-data"])


@router.get("/status", response_model=DemoDataStatusResponse)
def demo_data_status() -> DemoDataStatusResponse:
    return DemoDataStatusResponse(**DemoDataService().status())


@router.post(
    "/install",
    response_model=DemoDataInstallResponse,
    status_code=status.HTTP_201_CREATED,
)
def install_demo_data(payload: DemoDataInstallRequest) -> DemoDataInstallResponse:
    try:
        result = DemoDataService().install(
            confirm_install=payload.confirm_install,
            understand_demo_data=payload.understand_demo_data,
        )
    except DemoDataConfirmationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except DemoDataConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return DemoDataInstallResponse(**result)


@router.post("/clear", response_model=DemoDataClearResponse)
def clear_demo_data(payload: DemoDataClearRequest) -> DemoDataClearResponse:
    try:
        result = DemoDataService().clear(confirm_clear=payload.confirm_clear)
    except DemoDataConfirmationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except DemoDataConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return DemoDataClearResponse(**result)
