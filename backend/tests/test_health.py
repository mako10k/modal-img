from fastapi.testclient import TestClient

import app.main as main_module
from app.settings import get_settings


def test_health_returns_ok(monkeypatch) -> None:
    async def fake_collect_dependency_health(_redis_client, _settings) -> dict[str, str]:
        return {"redis": "ok", "postgres": "ok"}

    monkeypatch.setattr(
        main_module,
        "collect_dependency_health",
        fake_collect_dependency_health,
    )
    get_settings.cache_clear()

    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
        "dependencies": {"redis": "ok", "postgres": "ok"},
    }


def test_health_returns_degraded(monkeypatch) -> None:
    async def fake_collect_dependency_health(_redis_client, _settings) -> dict[str, str]:
        return {"redis": "error:ConnectionError", "postgres": "ok"}

    monkeypatch.setattr(
        main_module,
        "collect_dependency_health",
        fake_collect_dependency_health,
    )
    get_settings.cache_clear()

    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "environment": "development",
        "dependencies": {
            "redis": "error:ConnectionError",
            "postgres": "ok",
        },
    }
