from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from app.modal_execution import ModalSubmissionGateway
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
    width: int = Field(default=768, ge=512, le=1024, multiple_of=64)
    height: int = Field(default=768, ge=512, le=1024, multiple_of=64)
    steps: int = Field(default=24, ge=12, le=30)


class GenerationAccepted(BaseModel):
    job_id: str
    status: str
    execution_id: str


class GenerationStatus(BaseModel):
    job_id: str
    status: str
    execution_id: str | None
    error_message: str | None = None
    result_image_data_url: str | None = None
    result_mime_type: str | None = None


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
    result_image_data_url: str | None = None
    result_mime_type: str | None = None


class ExecutionGateway(Protocol):
    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        pass

    async def get_result(self, execution_id: str) -> dict[str, object] | None:
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

    async def get_job(self, job_id: str) -> GenerationJobRecord | None:
        pass

    async def mark_job_completed(
        self,
        job_id: str,
        result_image_data_url: str,
        result_mime_type: str,
    ) -> None:
        pass

    async def mark_job_execution_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        pass


class GenerationQueuePublisher(Protocol):
    async def publish_job_requested(self, record: GenerationJobRecord) -> None:
        pass


class StubExecutionGateway:
    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        _ = workflow
        return "stub-execution"

    async def get_result(self, execution_id: str) -> dict[str, object] | None:
        _ = execution_id
        return None


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

    async def get_job(self, job_id: str) -> GenerationJobRecord | None:
        _ = job_id
        return None

    async def mark_job_completed(
        self,
        job_id: str,
        result_image_data_url: str,
        result_mime_type: str,
    ) -> None:
        _ = (job_id, result_image_data_url, result_mime_type)

    async def mark_job_execution_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        _ = (job_id, error_message)


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
        execution_id: str | None = None,
    ):
        super().__init__(message)
        self.job_id = job_id
        self.status = status
        self.execution_id = execution_id


class GenerationNotFoundError(Exception):
    def __init__(self, job_id: str):
        super().__init__(f"generation job not found: {job_id}")
        self.job_id = job_id


class GenerationService:
    def __init__(
        self,
        gateway: ExecutionGateway,
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
            execution_id = await self._gateway.enqueue_workflow(workflow)
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
            await self._repository.mark_job_queued(job_id, execution_id)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            error_message = await self._record_queue_state_update_failure(
                job_id,
                execution_id,
                error_message,
            )
            raise GenerationSubmissionError(
                job_id,
                "queue_state_update_failed",
                error_message,
                execution_id=execution_id,
            ) from exc

        queued_record = record.model_copy(
            update={
                "comfyui_prompt_id": execution_id,
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
                execution_id=execution_id,
            ) from exc

        return GenerationAccepted(
            job_id=job_id,
            status="queued",
            execution_id=execution_id,
        )

    async def get_generation_status(self, job_id: str) -> GenerationStatus:
        record = await self._repository.get_job(job_id)
        if record is None:
            raise GenerationNotFoundError(job_id)

        execution_id = record.comfyui_prompt_id
        if execution_id is None:
            return self._build_generation_status(record)

        if record.status in {
            "completed",
            "submission_failed",
            "execution_failed",
        }:
            return self._build_generation_status(record)

        try:
            result = await self._gateway.get_result(execution_id)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            await self._repository.mark_job_execution_failed(
                job_id,
                error_message,
            )
            return self._build_generation_status(
                record.model_copy(
                    update={
                        "status": "execution_failed",
                        "error_message": error_message,
                    }
                )
            )

        if result is None:
            return self._build_generation_status(record)

        result_image_data_url = result.get("result_image_data_url")
        result_mime_type = result.get("result_mime_type")
        if (
            not isinstance(result_image_data_url, str)
            or not result_image_data_url
        ):
            raise RuntimeError(
                "Modal function result missing result_image_data_url"
            )
        if not isinstance(result_mime_type, str) or not result_mime_type:
            raise RuntimeError(
                "Modal function result missing result_mime_type"
            )

        await self._repository.mark_job_completed(
            job_id,
            result_image_data_url,
            result_mime_type,
        )
        return self._build_generation_status(
            record.model_copy(
                update={
                    "status": "completed",
                    "error_message": None,
                    "result_image_data_url": result_image_data_url,
                    "result_mime_type": result_mime_type,
                }
            )
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

    def _build_generation_status(
        self,
        record: GenerationJobRecord,
    ) -> GenerationStatus:
        return GenerationStatus(
            job_id=record.job_id,
            status=record.status,
            execution_id=record.comfyui_prompt_id,
            error_message=record.error_message,
            result_image_data_url=record.result_image_data_url,
            result_mime_type=record.result_mime_type,
        )


def create_generation_service() -> GenerationService:
    return GenerationService(
        StubExecutionGateway(),
        StubGenerationJobRepository(),
        StubGenerationQueuePublisher(),
    )


def create_generation_service_with_clients(
    settings: Settings,
    redis_client,
) -> GenerationService:
    return GenerationService(
        ModalSubmissionGateway(settings),
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
