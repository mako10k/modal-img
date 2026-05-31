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
                        comfyui_prompt_id,
                        status,
                        error_message,
                        prompt,
                        negative_prompt,
                        width,
                        height,
                        steps
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.job_id,
                        record.comfyui_prompt_id,
                        record.status,
                        record.error_message,
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

    async def mark_job_queued(
        self,
        job_id: str,
        comfyui_prompt_id: str,
    ) -> None:
        await self._execute_status_update(
            """
            update generation_jobs
            set comfyui_prompt_id = %s,
                status = %s,
                error_message = null,
                updated_at = now()
            where job_id = %s
            """,
            (comfyui_prompt_id, "queued", job_id),
        )

    async def mark_job_submission_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        await self._execute_status_update(
            """
            update generation_jobs
            set status = %s,
                error_message = %s,
                updated_at = now()
            where job_id = %s
            """,
            ("submission_failed", error_message, job_id),
        )

    async def mark_job_queue_publish_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        await self._execute_status_update(
            """
            update generation_jobs
            set status = %s,
                error_message = %s,
                updated_at = now()
            where job_id = %s
            """,
            ("queue_publish_failed", error_message, job_id),
        )

    async def mark_job_queue_state_update_failed(
        self,
        job_id: str,
        comfyui_prompt_id: str,
        error_message: str,
    ) -> None:
        await self._execute_status_update(
            """
            update generation_jobs
            set comfyui_prompt_id = %s,
                status = %s,
                error_message = %s,
                updated_at = now()
            where job_id = %s
            """,
            (comfyui_prompt_id, "submitting", error_message, job_id),
        )

    async def _execute_status_update(
        self,
        statement: str,
        params: tuple[object, ...],
    ) -> None:
        connection = await self._connector(self._settings)

        try:
            async with connection.cursor() as cursor:
                await cursor.execute(statement, params)
                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "generation_jobs row update did not affect "
                        "exactly one row"
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
            record.model_dump_json(exclude_none=True),
        )
