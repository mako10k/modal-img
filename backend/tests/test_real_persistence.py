import asyncio

from app.generation import GenerationJobRecord
from app.persistence import (
    PostgresGenerationJobRepository,
    RedisGenerationQueuePublisher,
)
from app.settings import Settings


class FakeCursor:
    def __init__(self):
        self.statement = None
        self.params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement, params) -> None:
        self.statement = statement
        self.params = params


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    async def commit(self) -> None:
        self.committed = True

    async def close(self) -> None:
        self.closed = True


class FakeRedis:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def rpush(self, key: str, payload: str) -> None:
        self.calls.append((key, payload))


def test_postgres_repository_inserts_generation_job() -> None:
    connection = FakeConnection()

    async def fake_connector(_settings: Settings):
        return connection

    repository = PostgresGenerationJobRepository(
        Settings(),
        connector=fake_connector,
    )

    asyncio.run(repository.create_job(build_record()))

    assert (
        "insert into generation_jobs"
        in connection.cursor_instance.statement
    )
    assert connection.cursor_instance.params == (
        "job-1",
        "workflow-1",
        "accepted",
        "sunrise over mountains",
        "low quality",
        1024,
        768,
        28,
    )
    assert connection.committed is True
    assert connection.closed is True


def test_redis_queue_publisher_pushes_serialized_job() -> None:
    redis_client = FakeRedis()
    publisher = RedisGenerationQueuePublisher(
        redis_client,
        "modal-img:test-generation-jobs",
    )

    asyncio.run(publisher.publish_job_requested(build_record()))

    assert redis_client.calls == [
        (
            "modal-img:test-generation-jobs",
            "{"
            '"job_id":"job-1",'
            '"workflow_id":"workflow-1",'
            '"status":"accepted",'
            '"prompt":"sunrise over mountains",'
            '"negative_prompt":"low quality",'
            '"width":1024,'
            '"height":768,'
            '"steps":28'
            "}",
        )
    ]


def build_record() -> GenerationJobRecord:
    return GenerationJobRecord(
        job_id="job-1",
        workflow_id="workflow-1",
        status="accepted",
        prompt="sunrise over mountains",
        negative_prompt="low quality",
        width=1024,
        height=768,
        steps=28,
    )
