import asyncio

from app.generation import (
    GenerationJobRecord,
    GenerationRequest,
    GenerationService,
)


class FakeGateway:
    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        _ = workflow
        return "workflow-redis-postgres"


class FakeRepository:
    def __init__(self):
        self.created_records: list[GenerationJobRecord] = []
        self.queued: list[tuple[str, str]] = []
        self.failed: list[tuple[str, str]] = []
        self.queue_publish_failed: list[tuple[str, str]] = []
        self.queue_state_update_failed: list[tuple[str, str, str]] = []

    async def create_job(self, record: GenerationJobRecord) -> None:
        self.created_records.append(record)

    async def mark_job_queued(
        self,
        job_id: str,
        comfyui_prompt_id: str,
    ) -> None:
        self.queued.append((job_id, comfyui_prompt_id))

    async def mark_job_submission_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        self.failed.append((job_id, error_message))

    async def mark_job_queue_publish_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        self.queue_publish_failed.append((job_id, error_message))

    async def mark_job_queue_state_update_failed(
        self,
        job_id: str,
        comfyui_prompt_id: str,
        error_message: str,
    ) -> None:
        self.queue_state_update_failed.append(
            (job_id, comfyui_prompt_id, error_message)
        )


class FakeQueuePublisher:
    def __init__(self):
        self.records: list[GenerationJobRecord] = []

    async def publish_job_requested(self, record: GenerationJobRecord) -> None:
        self.records.append(record)


def test_generation_service_persists_job_and_publishes_queue_message() -> None:
    repository = FakeRepository()
    queue_publisher = FakeQueuePublisher()
    service = GenerationService(
        gateway=FakeGateway(),
        repository=repository,
        queue_publisher=queue_publisher,
    )

    response = asyncio.run(
        service.submit_text_to_image(
            GenerationRequest(
                prompt="cinematic city skyline",
                negative_prompt="low contrast",
                width=1024,
                height=768,
                steps=4,
            )
        )
    )

    assert response.status == "queued"
    assert len(repository.created_records) == 1
    assert repository.created_records[0].status == "submitting"
    assert repository.created_records[0].comfyui_prompt_id is None
    assert repository.queued == [(response.job_id, "workflow-redis-postgres")]
    assert repository.failed == []
    assert repository.queue_publish_failed == []
    assert repository.queue_state_update_failed == []
    assert len(queue_publisher.records) == 1
    assert (
        queue_publisher.records[0].comfyui_prompt_id
        == "workflow-redis-postgres"
    )
    assert queue_publisher.records[0].status == "queued"
    assert queue_publisher.records[0].prompt == "cinematic city skyline"
