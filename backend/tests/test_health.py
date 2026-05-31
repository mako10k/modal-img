from fastapi.testclient import TestClient

import app.main as main_module
from app.settings import get_settings


def create_test_client() -> TestClient:
    return TestClient(main_module.create_app())


def test_health_returns_ok(monkeypatch) -> None:
    async def fake_collect_dependency_health(
        _redis_client,
        _settings,
    ) -> dict[str, str]:
        return {"redis": "ok", "postgres": "ok", "comfyui": "ok"}

    monkeypatch.setattr(
        main_module,
        "collect_dependency_health",
        fake_collect_dependency_health,
    )
    get_settings.cache_clear()

    with create_test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
        "dependencies": {
            "redis": "ok",
            "postgres": "ok",
            "comfyui": "ok",
        },
    }


def test_health_returns_degraded(monkeypatch) -> None:
    async def fake_collect_dependency_health(
        _redis_client,
        _settings,
    ) -> dict[str, str]:
        return {
            "redis": "error:ConnectionError",
            "postgres": "ok",
            "comfyui": "ok",
        }

    monkeypatch.setattr(
        main_module,
        "collect_dependency_health",
        fake_collect_dependency_health,
    )
    get_settings.cache_clear()

    with create_test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "environment": "development",
        "dependencies": {
            "redis": "error:ConnectionError",
            "postgres": "ok",
            "comfyui": "ok",
        },
    }


def test_cors_allows_configured_frontend_origin(monkeypatch) -> None:
    monkeypatch.setenv("MODAL_IMG_FRONTEND_ORIGIN", "http://127.0.0.1:4173")
    get_settings.cache_clear()

    with create_test_client() as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:4173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:4173"
    )
