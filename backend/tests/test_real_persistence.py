from pathlib import Path

import asyncio
import pytest

from app.generation import GenerationJobRecord
from app.persistence import (
    PostgresGenerationJobRepository,
    RedisGenerationQueuePublisher,
)
from app.settings import Settings


class FakeCursor:
    def __init__(self, rowcount: int = 1):
        self.statement = None
        self.params = None
        self.rowcount = rowcount

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement, params) -> None:
        self.statement = statement
        self.params = params


class FakeConnection:
    def __init__(self, rowcount: int = 1):
        self.cursor_instance = FakeCursor(rowcount=rowcount)
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
        None,
        "submitting",
        None,
        "sunrise over mountains",
        "low quality",
        1024,
        768,
        28,
    )
    assert connection.committed is True
    assert connection.closed is True


def test_postgres_repository_marks_job_queued() -> None:
    connection = FakeConnection()

    async def fake_connector(_settings: Settings):
        return connection

    repository = PostgresGenerationJobRepository(
        Settings(),
        connector=fake_connector,
    )

    asyncio.run(repository.mark_job_queued("job-1", "prompt-1"))

    assert "update generation_jobs" in connection.cursor_instance.statement
    assert connection.cursor_instance.params == (
        "prompt-1",
        "queued",
        "job-1",
    )
    assert connection.committed is True
    assert connection.closed is True


def test_postgres_repository_marks_submission_failure() -> None:
    connection = FakeConnection()

    async def fake_connector(_settings: Settings):
        return connection

    repository = PostgresGenerationJobRepository(
        Settings(),
        connector=fake_connector,
    )

    asyncio.run(
        repository.mark_job_submission_failed(
            "job-1",
            "RuntimeError: ComfyUI response missing prompt_id",
        )
    )

    assert "update generation_jobs" in connection.cursor_instance.statement
    assert connection.cursor_instance.params == (
        "submission_failed",
        "RuntimeError: ComfyUI response missing prompt_id",
        "job-1",
    )
    assert connection.committed is True
    assert connection.closed is True


def test_postgres_repository_marks_queue_publish_failure() -> None:
    connection = FakeConnection()

    async def fake_connector(_settings: Settings):
        return connection

    repository = PostgresGenerationJobRepository(
        Settings(),
        connector=fake_connector,
    )

    asyncio.run(
        repository.mark_job_queue_publish_failed(
            "job-1",
            "RuntimeError: redis push failed",
        )
    )

    assert "update generation_jobs" in connection.cursor_instance.statement
    assert connection.cursor_instance.params == (
        "queue_publish_failed",
        "RuntimeError: redis push failed",
        "job-1",
    )
    assert connection.committed is True
    assert connection.closed is True


def test_postgres_repository_marks_queue_state_update_failure() -> None:
    connection = FakeConnection()

    async def fake_connector(_settings: Settings):
        return connection

    repository = PostgresGenerationJobRepository(
        Settings(),
        connector=fake_connector,
    )

    asyncio.run(
        repository.mark_job_queue_state_update_failed(
            "job-1",
            "prompt-1",
            "RuntimeError: postgres update failed",
        )
    )

    assert "update generation_jobs" in connection.cursor_instance.statement
    assert connection.cursor_instance.params == (
        "prompt-1",
        "submitting",
        "RuntimeError: postgres update failed",
        "job-1",
    )
    assert connection.committed is True
    assert connection.closed is True


def test_postgres_repository_raises_when_status_update_hits_no_rows() -> None:
    connection = FakeConnection(rowcount=0)

    async def fake_connector(_settings: Settings):
        return connection

    repository = PostgresGenerationJobRepository(
        Settings(),
        connector=fake_connector,
    )

    with pytest.raises(
        RuntimeError,
        match="did not affect exactly one row",
    ):
        asyncio.run(repository.mark_job_queued("job-1", "prompt-1"))

    assert connection.committed is False
    assert connection.closed is True


def test_redis_queue_publisher_pushes_serialized_job() -> None:
    redis_client = FakeRedis()
    publisher = RedisGenerationQueuePublisher(
        redis_client,
        "modal-img:test-generation-jobs",
    )

    asyncio.run(publisher.publish_job_requested(build_queued_record()))

    assert redis_client.calls == [
        (
            "modal-img:test-generation-jobs",
            "{"
            '"job_id":"job-1",'
            '"comfyui_prompt_id":"prompt-1",'
            '"status":"queued",'
            '"prompt":"sunrise over mountains",'
            '"negative_prompt":"low quality",'
            '"width":1024,'
            '"height":768,'
            '"steps":28'
            "}",
        )
    ]


def test_upgrade_sql_covers_old_generation_jobs_schema() -> None:
    migration = Path("sql/upgrade_generation_jobs.sql").read_text()

    def normalize_sql(sql: str) -> str:
        return " ".join(sql.split())

    normalized_migration = normalize_sql(migration)

    blocks = [
        "begin;",
        """do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_name = 'generation_jobs'
          and column_name = 'workflow_id'
    ) and not exists (
        select 1
        from information_schema.columns
        where table_name = 'generation_jobs'
          and column_name = 'comfyui_prompt_id'
    ) then
        alter table generation_jobs
            rename column workflow_id to comfyui_prompt_id;
    end if;
end $$;""",
        """alter table generation_jobs
    add column if not exists comfyui_prompt_id text,
    add column if not exists error_message text,
    add column if not exists created_at timestamptz not null default now(),
    add column if not exists updated_at timestamptz not null default now();""",
        """alter table generation_jobs
    alter column comfyui_prompt_id drop not null;""",
        """update generation_jobs
set status = 'queued'
where status = 'accepted';""",
        "commit;",
    ]

    previous_index = -1
    for block in blocks:
        current_index = normalized_migration.find(normalize_sql(block))
        assert current_index > previous_index
        previous_index = current_index


def test_init_sql_matches_repository_contract() -> None:
    schema = Path("sql/init_generation_jobs.sql").read_text()

    expected = """create table if not exists generation_jobs (
    job_id text primary key,
    comfyui_prompt_id text,
    status text not null,
    error_message text,
    prompt text not null,
    negative_prompt text,
    width integer not null,
    height integer not null,
    steps integer not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);"""

    assert schema.strip() == expected


def build_record() -> GenerationJobRecord:
    return GenerationJobRecord(
        job_id="job-1",
        comfyui_prompt_id=None,
        status="submitting",
        prompt="sunrise over mountains",
        negative_prompt="low quality",
        width=1024,
        height=768,
        steps=28,
    )


def build_queued_record() -> GenerationJobRecord:
    return GenerationJobRecord(
        job_id="job-1",
        comfyui_prompt_id="prompt-1",
        status="queued",
        prompt="sunrise over mountains",
        negative_prompt="low quality",
        width=1024,
        height=768,
        steps=28,
    )
