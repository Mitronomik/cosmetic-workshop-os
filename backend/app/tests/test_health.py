import asyncio
import json

from app.api.health import health_payload
from app.main import app


def test_api_health_endpoint_returns_local_first_status_payload():
    assert health_payload() == {
        "status": "ok",
        "app": "cosmetic-workshop-os",
        "product_name": "Мастерская косметолога",
        "mode": "local-first",
        "version": "0.1.0",
    }


def test_asgi_health_endpoint_is_available_for_simple_smoke_checks():
    sent_messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent_messages.append(message)

    asyncio.run(app({"type": "http", "method": "GET", "path": "/api/health"}, receive, send))

    assert sent_messages[0]["status"] == 200
    assert json.loads(sent_messages[1]["body"].decode("utf-8"))["mode"] == "local-first"
