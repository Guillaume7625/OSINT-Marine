from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.core.dependencies import require_api_token
from app.main import app


def test_api_token_is_optional_when_not_configured(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "")
    from app.core.config import get_settings

    get_settings.cache_clear()
    require_api_token()


def test_api_token_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "secret-token")
    from app.core.config import get_settings

    get_settings.cache_clear()

    try:
        require_api_token("Bearer wrong-token")
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Unauthorized"
    else:
        raise AssertionError("Expected HTTPException for invalid token")


def test_api_token_accepts_valid_bearer_token(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "secret-token")
    from app.core.config import get_settings

    get_settings.cache_clear()
    require_api_token("Bearer secret-token")


def test_api_routes_require_bearer_when_token_set(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "secret-token")
    from app.core.config import get_settings

    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/api/conversations")
    assert response.status_code == 401


def test_api_routes_reject_invalid_bearer_when_token_set(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "secret-token")
    from app.core.config import get_settings

    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/api/conversations", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401
