from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.alerts import router as alerts_router
from app.api.audit_logs import router as audit_logs_router
from app.api.backups import router as backups_router
from app.api.catalog import router as catalog_router
from app.api.catalog_assignments import router as catalog_assignments_router
from app.api.client_recipes import router as client_recipes_router
from app.api.client_wishes_feedback import router as client_wishes_feedback_router
from app.api.clients import router as clients_router
from app.api.database import router as database_router
from app.api.demo_data import router as demo_data_router
from app.api.exports import router as exports_router
from app.api.health import router as health_router
from app.api.ingredients import router as ingredients_router
from app.api.imports import router as imports_router
from app.api.ingredient_lots import router as ingredient_lots_router
from app.api.inventory import router as inventory_router
from app.api.onboarding import router as onboarding_router
from app.api.orders import router as orders_router
from app.api.packaging_items import router as packaging_items_router
from app.api.packaging_stock_movements import router as packaging_stock_movements_router
from app.api.production_readiness import router as production_readiness_router
from app.api.production_confirmation import router as production_confirmation_router
from app.api.production_batches import router as production_batches_router
from app.api.purchase_suggestions import router as purchase_suggestions_router
from app.api.recipes import router as recipes_router
from app.api.report_documents import router as report_documents_router
from app.api.reports import router as reports_router
from app.api.settings import router as settings_router
from app.api.stock_movements import router as stock_movements_router
from app.api.tax_rate_settings import router as tax_rate_settings_router
from app.services.backend_liveness import acquire_backend_liveness_lock
from app.domain.production_tax_context import (
    EXPECTED_EFFECTIVE_AT_FIELD,
    EXPECTED_PERCENT_FIELD,
    missing_tax_rate_context_error,
)
from app.version import resolve_effective_app_version

APP_NAME = "cosmetic-workshop-os"
PRODUCT_NAME = "Мастерская косметолога"
APP_VERSION = resolve_effective_app_version()

TAX_RATE_CONTEXT_BODY_FIELDS = frozenset({EXPECTED_PERCENT_FIELD, EXPECTED_EFFECTIVE_AT_FIELD})


def _omits_tax_rate_context(exc: RequestValidationError) -> bool:
    """Whether this request left out a required production tax-context key."""
    return any(
        error.get("type") == "missing"
        and tuple(error.get("loc", ()))[:1] == ("body",)
        and tuple(error.get("loc", ()))[-1] in TAX_RATE_CONTEXT_BODY_FIELDS
        for error in exc.errors()
    )


async def _validation_error_response(request: Request, exc: RequestValidationError):
    """Give an omitted confirmation tax context the stable structured code.

    An outdated client that omits `expected_tax_rate_percent` or
    `expected_tax_rate_effective_at` must learn that from the repository's own
    error contract rather than from raw Pydantic internals. Every other
    validation error keeps FastAPI's existing response byte for byte.
    """
    if not _omits_tax_rate_context(exc):
        return await request_validation_exception_handler(request, exc)
    issue = missing_tax_rate_context_error().issue
    return JSONResponse(
        status_code=422,
        content={"detail": {"code": str(issue.code), "message": issue.message, "field": issue.field, "next_action": issue.next_action}},
    )


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Hold the backend-liveness lock for this process's whole serving lifetime.

    The launcher assigns the lock path; when it is absent — the ordinary test
    client, a developer importing the app — nothing is taken and nothing is
    claimed. When it is present and the lock cannot be taken, another application
    backend is already alive against this workspace, and startup fails rather
    than putting a second writer on one SQLite database.

    Nothing releases the lock on shutdown on purpose: process exit releases it,
    and that is precisely the property a launcher needs after a *hard* crash,
    when no cleanup code of ours runs at all.
    """
    acquire_backend_liveness_lock()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=PRODUCT_NAME,
        version=APP_VERSION,
        description="Local-first API for the cosmetic workshop app shell.",
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["*"],
    )
    app.add_exception_handler(RequestValidationError, _validation_error_response)
    app.include_router(alerts_router, prefix="/api")
    app.include_router(audit_logs_router, prefix="/api")
    app.include_router(backups_router, prefix="/api")
    app.include_router(exports_router, prefix="/api")
    app.include_router(imports_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(health_router)
    app.include_router(database_router, prefix="/api")
    app.include_router(demo_data_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(tax_rate_settings_router, prefix="/api")
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
    app.include_router(client_wishes_feedback_router, prefix="/api")
    app.include_router(orders_router, prefix="/api")
    app.include_router(production_readiness_router, prefix="/api")
    app.include_router(production_confirmation_router, prefix="/api")
    app.include_router(production_batches_router, prefix="/api")
    app.include_router(purchase_suggestions_router, prefix="/api")
    app.include_router(onboarding_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    app.include_router(report_documents_router, prefix="/api")
    return app


app = create_app()
