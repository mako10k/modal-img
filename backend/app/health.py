from app.comfyui import check_comfyui_health
from redis.asyncio import Redis

from app.clients import open_postgres_connection
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

    try:
        await redis_client.ping()
        health["redis"] = "ok"
    except Exception as exc:
        health["redis"] = f"error:{type(exc).__name__}"

    try:
        health["postgres"] = await _check_postgres(settings)
    except Exception as exc:
        health["postgres"] = f"error:{type(exc).__name__}"

    try:
        health["comfyui"] = await check_comfyui_health(settings)
    except Exception as exc:
        health["comfyui"] = f"error:{type(exc).__name__}"

    return health
