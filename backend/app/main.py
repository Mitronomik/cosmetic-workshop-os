from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router

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
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(health_router)
    return app


app = create_app()
