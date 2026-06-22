from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.catalog import router as catalog_router
from app.api.catalog_assignments import router as catalog_assignments_router
from app.api.client_recipes import router as client_recipes_router
from app.api.clients import router as clients_router
from app.api.database import router as database_router
from app.api.health import router as health_router
from app.api.ingredients import router as ingredients_router
from app.api.ingredient_lots import router as ingredient_lots_router
from app.api.inventory import router as inventory_router
from app.api.onboarding import router as onboarding_router
from app.api.packaging_items import router as packaging_items_router
from app.api.packaging_stock_movements import router as packaging_stock_movements_router
from app.api.recipes import router as recipes_router
from app.api.settings import router as settings_router
from app.api.stock_movements import router as stock_movements_router

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
    app.include_router(ingredient_lots_router, prefix="/api")
    app.include_router(stock_movements_router, prefix="/api")
    app.include_router(packaging_items_router, prefix="/api")
    app.include_router(packaging_stock_movements_router, prefix="/api")
    app.include_router(inventory_router, prefix="/api")
    app.include_router(recipes_router, prefix="/api")
    app.include_router(catalog_router, prefix="/api")
    app.include_router(catalog_assignments_router, prefix="/api")
    app.include_router(clients_router, prefix="/api")
    app.include_router(client_recipes_router, prefix="/api")
    app.include_router(onboarding_router, prefix="/api")
    return app


app = create_app()
