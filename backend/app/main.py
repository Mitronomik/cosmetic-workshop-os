from collections.abc import Awaitable, Callable
import json
from typing import Any

from app.api.health import health_payload

APP_NAME = "cosmetic-workshop-os"
PRODUCT_NAME = "Мастерская косметолога"
APP_VERSION = "0.1.0"


def create_app() -> Any:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from app.api.health import router as health_router

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


class HealthAsgiApp:
    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[None]]) -> None:
        if scope.get("type") != "http":
            return
        path = scope.get("path")
        method = scope.get("method")
        if method == "GET" and path in {"/health", "/api/health"}:
            body = json.dumps(health_payload(), ensure_ascii=False).encode("utf-8")
            await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json; charset=utf-8")]})
            await send({"type": "http.response.body", "body": body})
            return
        await send({"type": "http.response.start", "status": 404, "headers": [(b"content-type", b"application/json; charset=utf-8")]})
        await send({"type": "http.response.body", "body": b'{"detail":"Not found"}'})


from importlib.util import find_spec

app = create_app() if find_spec("fastapi") else HealthAsgiApp()
