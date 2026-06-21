from importlib.util import find_spec
from typing import Any

from app.schemas.health import HealthResponse


def health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "cosmetic-workshop-os",
        "product_name": "Мастерская косметолога",
        "mode": "local-first",
        "version": "0.1.0",
    }


def health() -> HealthResponse:
    return HealthResponse(**health_payload())


if find_spec("fastapi"):
    from fastapi import APIRouter

    router: Any = APIRouter(tags=["health"])
    router.get("/health", response_model=HealthResponse)(health)
else:
    router = None
