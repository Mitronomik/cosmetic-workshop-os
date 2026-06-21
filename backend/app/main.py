from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.database import router as database_router
from app.api.health import router as health_router
from app.api.ingredients import router as ingredients_router
from app.api.onboarding import router as onboarding_router
from app.api.settings import router as settings_router

APP_NAME = "cosmetic-workshop-os"
PRODUCT_NAME = "Мастерская косметолога"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(
        title=PRODUCT_NAME,
        version=APP_VERSION,
        description="Local-first API for the cosmetic workshop app shell.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(health_router)
    app.include_router(database_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(ingredients_router, prefix="/api")
    app.include_router(onboarding_router, prefix="/api")
    return app


app = create_app()
