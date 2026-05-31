import asyncio

from app.clients import create_redis_client
from app.settings import Settings


def test_create_redis_client_uses_configured_connection_values() -> None:
    settings = Settings(redis_url="redis://cache.internal:6380/2")

    client = create_redis_client(settings)

    assert client.connection_pool.connection_kwargs["host"] == "cache.internal"
    assert client.connection_pool.connection_kwargs["port"] == 6380
    assert client.connection_pool.connection_kwargs["db"] == 2

    asyncio.run(client.aclose())
