import asyncio
from types import SimpleNamespace

from app.clients import create_redis_client, open_postgres_connection
from app.settings import Settings


def test_create_redis_client_uses_configured_connection_values() -> None:
    settings = Settings(
        redis_url="redis://cache.internal:6380/2",
        redis_timeout_seconds=4.5,
    )

    client = create_redis_client(settings)

    assert client.connection_pool.connection_kwargs["host"] == "cache.internal"
    assert client.connection_pool.connection_kwargs["port"] == 6380
    assert client.connection_pool.connection_kwargs["db"] == 2
    assert client.connection_pool.connection_kwargs["socket_timeout"] == 4.5
    assert (
        client.connection_pool.connection_kwargs["socket_connect_timeout"]
        == 4.5
    )

    asyncio.run(client.aclose())


def test_open_postgres_connection_uses_configured_timeout(monkeypatch) -> None:
    calls: list[tuple[str, float]] = []

    async def fake_connect(dsn: str, connect_timeout: float):
        calls.append((dsn, connect_timeout))
        return SimpleNamespace()

    monkeypatch.setattr("app.clients.AsyncConnection.connect", fake_connect)
    settings = Settings(
        postgres_dsn="postgresql://db.internal:5432/modal_img",
        postgres_connect_timeout_seconds=6.5,
    )

    connection = asyncio.run(open_postgres_connection(settings))

    assert calls == [("postgresql://db.internal:5432/modal_img", 6.5)]
    assert isinstance(connection, SimpleNamespace)
