import pytest

pytest.importorskip(
    "httpx", reason="FastAPI TestClient requires httpx in this environment"
)
from fastapi.testclient import TestClient

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.main import create_app
from app.services.database import initialize_database


def client_for(monkeypatch, tmp_path):
    path = tmp_path / "api-demo.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(path))
    initialize_database(DatabaseConfig(path=path))
    return TestClient(create_app())


def test_demo_data_status_install_clear_api(monkeypatch, tmp_path):
    client = client_for(monkeypatch, tmp_path)
    status = client.get("/api/demo-data/status")
    assert status.status_code == 200
    assert status.json()["can_install"] is True

    rejected = client.post(
        "/api/demo-data/install",
        json={"confirm_install": False, "understand_demo_data": True},
    )
    assert rejected.status_code == 400

    installed = client.post(
        "/api/demo-data/install",
        json={"confirm_install": True, "understand_demo_data": True},
    )
    assert installed.status_code == 201
    assert installed.json()["created_counts"]["ingredients"] == 5

    status = client.get("/api/demo-data/status").json()
    assert status["is_installed"] is True
    assert status["can_clear"] is True

    reinstall = client.post(
        "/api/demo-data/install",
        json={"confirm_install": True, "understand_demo_data": True},
    )
    assert reinstall.status_code == 409

    clear_rejected = client.post("/api/demo-data/clear", json={"confirm_clear": False})
    assert clear_rejected.status_code == 400

    cleared = client.post("/api/demo-data/clear", json={"confirm_clear": True})
    assert cleared.status_code == 200
    assert cleared.json()["deleted_counts"]["orders"] == 2
    assert client.get("/api/demo-data/status").json()["is_installed"] is False


def test_demo_install_api_blocks_real_workspace(monkeypatch, tmp_path):
    client = client_for(monkeypatch, tmp_path)
    created = client.post(
        "/api/ingredients",
        json={
            "name": "Реальное масло",
            "category": "oil",
            "default_unit": "g",
            "density_g_per_ml": None,
        },
    )
    assert created.status_code == 201
    response = client.post(
        "/api/demo-data/install",
        json={"confirm_install": True, "understand_demo_data": True},
    )
    assert response.status_code == 409
    assert "пустую рабочую базу" in response.json()["detail"]
