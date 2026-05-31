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

    monkeypatch.setattr("app.health._check_postgres", fake_postgres_check)
    health = asyncio.run(
        collect_dependency_health(FakeRedisClient(), Settings())
    )

    assert health == {"redis": "ok", "postgres": "ok"}


def test_collect_dependency_health_reports_failures(monkeypatch) -> None:
    async def fake_postgres_check(_settings: Settings) -> str:
        raise RuntimeError("postgres unavailable")

    monkeypatch.setattr("app.health._check_postgres", fake_postgres_check)
    health = asyncio.run(
        collect_dependency_health(
            FakeRedisClient(should_fail=True),
            Settings(),
        )
    )

    assert health == {
        "redis": "error:ConnectionError",
        "postgres": "error:RuntimeError",
    }
