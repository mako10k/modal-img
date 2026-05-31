import asyncio

from redis.asyncio import Redis

from app.clients import open_postgres_connection
from app.modal_execution import check_modal_execution_health
from app.settings import Settings


async def _check_postgres(
    settings: Settings,
    connector=open_postgres_connection,
) -> str:
    connection = await connector(settings)

    try:
        async with connection.cursor() as cursor:
            await cursor.execute("select 1")
            row = await cursor.fetchone()
    finally:
        await connection.close()

    if row != (1,):
        raise RuntimeError("postgres health query returned unexpected payload")

    return "ok"


async def collect_dependency_health(
    redis_client: Redis,
    settings: Settings,
) -> dict[str, str]:
    health: dict[str, str] = {}
    timeout = settings.dependency_health_timeout_seconds

    try:
        await asyncio.wait_for(redis_client.ping(), timeout=timeout)
        health["redis"] = "ok"
    except Exception as exc:
        health["redis"] = f"error:{type(exc).__name__}"

    try:
        health["postgres"] = await asyncio.wait_for(
            _check_postgres(settings),
            timeout=timeout,
        )
    except Exception as exc:
        health["postgres"] = f"error:{type(exc).__name__}"

    try:
        health["modal"] = await asyncio.wait_for(
            check_modal_execution_health(settings),
            timeout=timeout,
        )
    except Exception as exc:
        health["modal"] = f"error:{type(exc).__name__}"

    return health
