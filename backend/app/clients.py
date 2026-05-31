from psycopg import AsyncConnection
from redis.asyncio import Redis

from app.settings import Settings


def create_redis_client(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def open_postgres_connection(settings: Settings) -> AsyncConnection:
    return await AsyncConnection.connect(settings.postgres_dsn)
