from fastapi.testclient import TestClient

from app.main import app


def test_health_smoke():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_stays_public_when_api_token_is_configured(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "secret-token")
    from app.core.config import get_settings

    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
