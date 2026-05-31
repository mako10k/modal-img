from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from app.comfyui import ComfyUISubmissionGateway
from app.persistence import (
    PostgresGenerationJobRepository,
    RedisGenerationQueuePublisher,
)
from app.settings import (
    DEFAULT_COMFYUI_CHECKPOINT,
    DEFAULT_COMFYUI_OUTPUT_PREFIX,
    Settings,
)


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    steps: int = Field(default=30, ge=1, le=100)


class GenerationAccepted(BaseModel):
    job_id: str
    status: str
    comfyui_prompt_id: str


class GenerationJobRecord(BaseModel):
    job_id: str
    comfyui_prompt_id: str | None
    status: str
    error_message: str | None = None
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

    async def mark_job_queued(
        self,
        job_id: str,
        comfyui_prompt_id: str,
    ) -> None:
        pass

    async def mark_job_submission_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        pass

    async def mark_job_queue_publish_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        pass

    async def mark_job_queue_state_update_failed(
        self,
        job_id: str,
        comfyui_prompt_id: str,
        error_message: str,
    ) -> None:
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

    async def mark_job_queued(
        self,
        job_id: str,
        comfyui_prompt_id: str,
    ) -> None:
        _ = (job_id, comfyui_prompt_id)

    async def mark_job_submission_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        _ = (job_id, error_message)

    async def mark_job_queue_publish_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        _ = (job_id, error_message)

    async def mark_job_queue_state_update_failed(
        self,
        job_id: str,
        comfyui_prompt_id: str,
        error_message: str,
    ) -> None:
        _ = (job_id, comfyui_prompt_id, error_message)


class StubGenerationQueuePublisher:
    async def publish_job_requested(self, record: GenerationJobRecord) -> None:
        _ = record


def build_text_to_image_workflow(
    request: GenerationRequest,
    checkpoint_name: str = DEFAULT_COMFYUI_CHECKPOINT,
    output_prefix: str = DEFAULT_COMFYUI_OUTPUT_PREFIX,
) -> dict[str, object]:
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": request.steps,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint_name},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": request.width,
                "height": request.height,
                "batch_size": 1,
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": request.prompt,
                "clip": ["4", 1],
            },
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": request.negative_prompt or "",
                "clip": ["4", 1],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2],
            },
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": output_prefix,
            },
        },
    }


class GenerationSubmissionError(Exception):
    def __init__(
        self,
        job_id: str,
        status: str,
        message: str,
        comfyui_prompt_id: str | None = None,
    ):
        super().__init__(message)
        self.job_id = job_id
        self.status = status
        self.comfyui_prompt_id = comfyui_prompt_id


class GenerationService:
    def __init__(
        self,
        gateway: ComfySubmissionGateway,
        repository: GenerationJobRepository,
        queue_publisher: GenerationQueuePublisher,
        workflow_factory=build_text_to_image_workflow,
    ):
        self._gateway = gateway
        self._repository = repository
        self._queue_publisher = queue_publisher
        self._workflow_factory = workflow_factory

    async def submit_text_to_image(
        self,
        request: GenerationRequest,
    ) -> GenerationAccepted:
        job_id = str(uuid4())
        record = GenerationJobRecord(
            job_id=job_id,
            comfyui_prompt_id=None,
            status="submitting",
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
        )

        try:
            await self._repository.create_job(record)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            raise GenerationSubmissionError(
                job_id,
                "persistence_failed",
                error_message,
            ) from exc

        try:
            workflow = self._workflow_factory(request)
            comfyui_prompt_id = await self._gateway.enqueue_workflow(workflow)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            error_message = await self._record_failure_status(
                self._repository.mark_job_submission_failed,
                job_id,
                error_message,
            )
            raise GenerationSubmissionError(
                job_id,
                "submission_failed",
                error_message,
            ) from exc

        try:
            await self._repository.mark_job_queued(job_id, comfyui_prompt_id)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            error_message = await self._record_queue_state_update_failure(
                job_id,
                comfyui_prompt_id,
                error_message,
            )
            raise GenerationSubmissionError(
                job_id,
                "queue_state_update_failed",
                error_message,
                comfyui_prompt_id=comfyui_prompt_id,
            ) from exc

        queued_record = record.model_copy(
            update={
                "comfyui_prompt_id": comfyui_prompt_id,
                "status": "queued",
            }
        )

        try:
            await self._queue_publisher.publish_job_requested(queued_record)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            error_message = await self._record_failure_status(
                self._repository.mark_job_queue_publish_failed,
                job_id,
                error_message,
            )
            raise GenerationSubmissionError(
                job_id,
                "queue_publish_failed",
                error_message,
                comfyui_prompt_id=comfyui_prompt_id,
            ) from exc

        return GenerationAccepted(
            job_id=job_id,
            status="queued",
            comfyui_prompt_id=comfyui_prompt_id,
        )

    async def _record_failure_status(
        self,
        recorder,
        job_id: str,
        error_message: str,
    ) -> str:
        try:
            await recorder(job_id, error_message)
        except Exception as state_exc:
            return (
                f"{error_message}; "
                f"state_update_error={type(state_exc).__name__}: "
                f"{state_exc}"
            )

        return error_message

    async def _record_queue_state_update_failure(
        self,
        job_id: str,
        comfyui_prompt_id: str,
        error_message: str,
    ) -> str:
        try:
            await self._repository.mark_job_queue_state_update_failed(
                job_id,
                comfyui_prompt_id,
                error_message,
            )
        except Exception as state_exc:
            return (
                f"{error_message}; "
                f"state_update_error={type(state_exc).__name__}: "
                f"{state_exc}"
            )

        return error_message


def create_generation_service() -> GenerationService:
    return GenerationService(
        StubComfySubmissionGateway(),
        StubGenerationJobRepository(),
        StubGenerationQueuePublisher(),
    )


def create_generation_service_with_clients(
    settings: Settings,
    redis_client,
) -> GenerationService:
    return GenerationService(
        ComfyUISubmissionGateway(settings),
        PostgresGenerationJobRepository(settings),
        RedisGenerationQueuePublisher(
            redis_client,
            settings.generation_queue_key,
        ),
        workflow_factory=lambda request: build_text_to_image_workflow(
            request,
            checkpoint_name=settings.comfyui_checkpoint,
            output_prefix=settings.comfyui_output_prefix,
        ),
    )
