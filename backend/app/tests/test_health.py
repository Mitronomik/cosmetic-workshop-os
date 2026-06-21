from fastapi.testclient import TestClient

from app.api.health import health_payload
from app.main import create_app

EXPECTED_HEALTH_PAYLOAD = {
    "status": "ok",
    "app": "cosmetic-workshop-os",
    "product_name": "Мастерская косметолога",
    "mode": "local-first",
    "version": "0.1.0",
}


def test_health_payload_stays_stable():
    assert health_payload() == EXPECTED_HEALTH_PAYLOAD


def test_api_health_endpoint_returns_local_first_status():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == EXPECTED_HEALTH_PAYLOAD


def test_root_health_endpoint_returns_local_first_status():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == EXPECTED_HEALTH_PAYLOAD
