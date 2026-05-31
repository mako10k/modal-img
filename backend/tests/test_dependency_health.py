import asyncio

from app.health import collect_dependency_health
from app.settings import Settings


class FakeRedisClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def ping(self) -> bool:
        if self.should_fail:
            raise ConnectionError("redis unavailable")

        return True


def test_collect_dependency_health_reports_ok_for_both_backends(
    monkeypatch,
) -> None:
    async def fake_postgres_check(_settings: Settings) -> str:
        return "ok"

    async def fake_comfyui_health(_settings: Settings) -> str:
        return "ok"

    monkeypatch.setattr("app.health._check_postgres", fake_postgres_check)
    monkeypatch.setattr("app.health.check_comfyui_health", fake_comfyui_health)
    health = asyncio.run(
        collect_dependency_health(FakeRedisClient(), Settings())
    )

    assert health == {"redis": "ok", "postgres": "ok", "comfyui": "ok"}


def test_collect_dependency_health_reports_failures(monkeypatch) -> None:
    async def fake_postgres_check(_settings: Settings) -> str:
        raise RuntimeError("postgres unavailable")

    async def fake_comfyui_health(_settings: Settings) -> str:
        raise RuntimeError("comfyui unavailable")

    monkeypatch.setattr("app.health._check_postgres", fake_postgres_check)
    monkeypatch.setattr("app.health.check_comfyui_health", fake_comfyui_health)
    health = asyncio.run(
        collect_dependency_health(
            FakeRedisClient(should_fail=True),
            Settings(),
        )
    )

    assert health == {
        "redis": "error:ConnectionError",
        "postgres": "error:RuntimeError",
        "comfyui": "error:RuntimeError",
    }


def test_collect_dependency_health_uses_configured_timeout(
    monkeypatch,
) -> None:
    timeouts: list[float] = []

    async def fake_wait_for(awaitable, timeout: float):
        timeouts.append(timeout)
        return await awaitable

    async def fake_postgres_check(_settings: Settings) -> str:
        return "ok"

    async def fake_comfyui_health(_settings: Settings) -> str:
        return "ok"

    monkeypatch.setattr("app.health.asyncio.wait_for", fake_wait_for)
    monkeypatch.setattr("app.health._check_postgres", fake_postgres_check)
    monkeypatch.setattr("app.health.check_comfyui_health", fake_comfyui_health)
    health = asyncio.run(
        collect_dependency_health(
            FakeRedisClient(),
            Settings(dependency_health_timeout_seconds=1.5),
        )
    )

    assert health == {"redis": "ok", "postgres": "ok", "comfyui": "ok"}
    assert timeouts == [1.5, 1.5, 1.5]
