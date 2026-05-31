from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    steps: int = Field(default=30, ge=1, le=100)


class GenerationAccepted(BaseModel):
    job_id: str
    status: str
    workflow_id: str


class GenerationJobRecord(BaseModel):
    job_id: str
    workflow_id: str
    status: str
    prompt: str
    negative_prompt: str | None
    width: int
    height: int
    steps: int


class ComfySubmissionGateway(Protocol):
    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        pass


class GenerationJobRepository(Protocol):
    async def create_job(self, record: GenerationJobRecord) -> None:
        pass


class GenerationQueuePublisher(Protocol):
    async def publish_job_requested(self, record: GenerationJobRecord) -> None:
        pass


class StubComfySubmissionGateway:
    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        _ = workflow
        return "stub-workflow"


class StubGenerationJobRepository:
    async def create_job(self, record: GenerationJobRecord) -> None:
        _ = record


class StubGenerationQueuePublisher:
    async def publish_job_requested(self, record: GenerationJobRecord) -> None:
        _ = record


def build_text_to_image_workflow(
    request: GenerationRequest,
) -> dict[str, object]:
    return {
        "kind": "text_to_image",
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt,
        "image": {
            "width": request.width,
            "height": request.height,
        },
        "sampling": {
            "steps": request.steps,
        },
    }


class GenerationService:
    def __init__(
        self,
        gateway: ComfySubmissionGateway,
        repository: GenerationJobRepository,
        queue_publisher: GenerationQueuePublisher,
    ):
        self._gateway = gateway
        self._repository = repository
        self._queue_publisher = queue_publisher

    async def submit_text_to_image(
        self,
        request: GenerationRequest,
    ) -> GenerationAccepted:
        job_id = str(uuid4())
        workflow = build_text_to_image_workflow(request)
        workflow_id = await self._gateway.enqueue_workflow(workflow)
        record = GenerationJobRecord(
            job_id=job_id,
            workflow_id=workflow_id,
            status="accepted",
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
        )
        await self._repository.create_job(record)
        await self._queue_publisher.publish_job_requested(record)

        return GenerationAccepted(
            job_id=job_id,
            status="accepted",
            workflow_id=workflow_id,
        )


def create_generation_service() -> GenerationService:
    return GenerationService(
        StubComfySubmissionGateway(),
        StubGenerationJobRepository(),
        StubGenerationQueuePublisher(),
    )
