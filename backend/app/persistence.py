from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from psycopg import AsyncConnection
from redis.asyncio import Redis

from app.clients import open_postgres_connection
from app.settings import Settings


if TYPE_CHECKING:
    from app.generation import GenerationJobRecord


class PostgresGenerationJobRepository:
    def __init__(
        self,
        settings: Settings,
        connector: Callable[[Settings], Awaitable[AsyncConnection]] = (
            open_postgres_connection
        ),
    ):
        self._settings = settings
        self._connector = connector

    async def create_job(self, record: GenerationJobRecord) -> None:
        connection = await self._connector(self._settings)

        try:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    insert into generation_jobs (
                        job_id,
                        workflow_id,
                        status,
                        prompt,
                        negative_prompt,
                        width,
                        height,
                        steps
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.job_id,
                        record.workflow_id,
                        record.status,
                        record.prompt,
                        record.negative_prompt,
                        record.width,
                        record.height,
                        record.steps,
                    ),
                )

            await connection.commit()
        finally:
            await connection.close()


class RedisGenerationQueuePublisher:
    def __init__(self, redis_client: Redis, queue_key: str):
        self._redis_client = redis_client
        self._queue_key = queue_key

    async def publish_job_requested(self, record: GenerationJobRecord) -> None:
        await self._redis_client.rpush(
            self._queue_key,
            record.model_dump_json(),
        )
