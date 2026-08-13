from fastapi.testclient import TestClient

from app.api.health import health_payload
from app.main import create_app
from app.version import resolve_effective_app_version


def expected_health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "cosmetic-workshop-os",
        "product_name": "Мастерская косметолога",
        "mode": "local-first",
        "version": resolve_effective_app_version(),
    }


def test_health_payload_stays_stable():
    assert health_payload() == expected_health_payload()


def test_fastapi_metadata_uses_the_same_effective_runtime_version():
    assert create_app().version == resolve_effective_app_version()


def test_api_health_endpoint_returns_local_first_status():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == expected_health_payload()


def test_root_health_endpoint_returns_local_first_status():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == expected_health_payload()
