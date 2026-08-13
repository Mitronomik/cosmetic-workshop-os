from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.version import resolve_effective_app_version

router = APIRouter(tags=["health"])


def health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "cosmetic-workshop-os",
        "product_name": "Мастерская косметолога",
        "mode": "local-first",
        "version": resolve_effective_app_version(),
    }


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**health_payload())
