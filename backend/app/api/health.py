from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


def health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "cosmetic-workshop-os",
        "product_name": "Мастерская косметолога",
        "mode": "local-first",
        "version": "0.1.0",
    }


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**health_payload())
