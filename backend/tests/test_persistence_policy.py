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
        self.records: list[GenerationJobRecord] = []

    async def create_job(self, record: GenerationJobRecord) -> None:
        self.records.append(record)


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
                width=1280,
                height=720,
                steps=35,
            )
        )
    )

    assert response.status == "accepted"
    assert len(repository.records) == 1
    assert len(queue_publisher.records) == 1
    assert repository.records[0] == queue_publisher.records[0]
    assert repository.records[0].workflow_id == "workflow-redis-postgres"
    assert repository.records[0].prompt == "cinematic city skyline"
