from fastapi.testclient import TestClient

import app.main as main_module
from app.generation import (
    GenerationRequest,
    GenerationService,
    GenerationSubmissionError,
    create_generation_service_with_clients,
)
from app.settings import Settings


class FakeGateway:
    def __init__(self):
        self.workflow: dict[str, object] | None = None

    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        self.workflow = workflow
        return "modal-execution-1"


class FailingGateway:
    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        _ = workflow
        raise RuntimeError("Modal function call missing object_id")


class FakeRepository:
    def __init__(self):
        self.created = None
        self.queued = None
        self.failed = None
        self.queue_publish_failed = None
        self.queue_state_update_failed = None
        self.create_error = None
        self.queued_error = None
        self.queue_state_update_failed_error = None

    async def create_job(self, record) -> None:
        if self.create_error is not None:
            raise self.create_error
        self.created = record

    async def mark_job_queued(
        self,
        job_id: str,
        comfyui_prompt_id: str,
    ) -> None:
        if self.queued_error is not None:
            raise self.queued_error
        self.queued = (job_id, comfyui_prompt_id)

    async def mark_job_submission_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        self.failed = (job_id, error_message)

    async def mark_job_queue_publish_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        self.queue_publish_failed = (job_id, error_message)

    async def mark_job_queue_state_update_failed(
        self,
        job_id: str,
        comfyui_prompt_id: str,
        error_message: str,
    ) -> None:
        if self.queue_state_update_failed_error is not None:
            raise self.queue_state_update_failed_error
        self.queue_state_update_failed = (
            job_id,
            comfyui_prompt_id,
            error_message,
        )


class FakeQueuePublisher:
    def __init__(self):
        self.record = None
        self.error = None

    async def publish_job_requested(self, record) -> None:
        if self.error is not None:
            raise self.error
        self.record = record


def test_generation_service_builds_text_to_image_workflow() -> None:
    gateway = FakeGateway()
    repository = FakeRepository()
    queue_publisher = FakeQueuePublisher()
    service = GenerationService(gateway, repository, queue_publisher)

    response = run_submit(service)

    assert response.status == "queued"
    assert response.execution_id == "modal-execution-1"
    assert gateway.workflow == {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 40,
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
            "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 768, "height": 1024, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "high detail portrait", "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "blurry", "clip": ["4", 1]},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "modal-img"},
        },
    }
    assert repository.created.status == "submitting"
    assert repository.created.comfyui_prompt_id is None
    assert repository.queued[1] == "modal-execution-1"
    assert repository.queue_publish_failed is None
    assert queue_publisher.record.comfyui_prompt_id == "modal-execution-1"
    assert queue_publisher.record.status == "queued"


def test_create_generation_endpoint_uses_generation_service(
    monkeypatch,
) -> None:
    class FakeGenerationService:
        async def submit_text_to_image(self, request: GenerationRequest):
            assert request.prompt == "studio lighting"
            return {
                    "job_id": "job-123",
                    "status": "queued",
                    "execution_id": "fc-123",
            }

    monkeypatch.setattr(
        main_module,
        "create_generation_service_with_clients",
        lambda _settings, _redis_client: FakeGenerationService(),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/v1/generations",
            json={
                "prompt": "studio lighting",
                "width": 1024,
                "height": 1024,
                "steps": 28,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-123",
        "status": "queued",
        "execution_id": "fc-123",
    }


def test_create_generation_endpoint_returns_502_on_submission_failure(
    monkeypatch,
) -> None:
    class FakeGenerationService:
        async def submit_text_to_image(self, request: GenerationRequest):
            assert request.prompt == "studio lighting"
            raise GenerationSubmissionError(
                "job-500",
                "submission_failed",
                "RuntimeError: Modal function call missing object_id",
            )

    monkeypatch.setattr(
        main_module,
        "create_generation_service_with_clients",
        lambda _settings, _redis_client: FakeGenerationService(),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/v1/generations",
            json={
                "prompt": "studio lighting",
                "width": 1024,
                "height": 1024,
                "steps": 28,
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "job_id": "job-500",
            "status": "submission_failed",
            "message": "RuntimeError: Modal function call missing object_id",
        }
    }


def test_create_generation_endpoint_returns_502_on_persistence_failure(
    monkeypatch,
) -> None:
    class FakeGenerationService:
        async def submit_text_to_image(self, request: GenerationRequest):
            assert request.prompt == "studio lighting"
            raise GenerationSubmissionError(
                "job-499",
                "persistence_failed",
                "ConnectionTimeout: connection timeout expired",
            )

    monkeypatch.setattr(
        main_module,
        "create_generation_service_with_clients",
        lambda _settings, _redis_client: FakeGenerationService(),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/v1/generations",
            json={
                "prompt": "studio lighting",
                "width": 1024,
                "height": 1024,
                "steps": 28,
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "job_id": "job-499",
            "status": "persistence_failed",
            "message": "ConnectionTimeout: connection timeout expired",
        }
    }


def test_create_generation_endpoint_returns_502_on_queue_publish_failure(
    monkeypatch,
) -> None:
    class FakeGenerationService:
        async def submit_text_to_image(self, request: GenerationRequest):
            assert request.prompt == "studio lighting"
            raise GenerationSubmissionError(
                "job-501",
                "queue_publish_failed",
                "RuntimeError: redis push failed",
                execution_id="fc-123",
            )

    monkeypatch.setattr(
        main_module,
        "create_generation_service_with_clients",
        lambda _settings, _redis_client: FakeGenerationService(),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/v1/generations",
            json={
                "prompt": "studio lighting",
                "width": 1024,
                "height": 1024,
                "steps": 28,
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "job_id": "job-501",
            "status": "queue_publish_failed",
            "message": "RuntimeError: redis push failed",
            "execution_id": "fc-123",
        }
    }


def test_create_generation_endpoint_returns_502_on_queue_state_update_failure(
    monkeypatch,
) -> None:
    class FakeGenerationService:
        async def submit_text_to_image(self, request: GenerationRequest):
            assert request.prompt == "studio lighting"
            raise GenerationSubmissionError(
                "job-502",
                "queue_state_update_failed",
                "RuntimeError: postgres update failed",
                execution_id="fc-123",
            )

    monkeypatch.setattr(
        main_module,
        "create_generation_service_with_clients",
        lambda _settings, _redis_client: FakeGenerationService(),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/v1/generations",
            json={
                "prompt": "studio lighting",
                "width": 1024,
                "height": 1024,
                "steps": 28,
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "job_id": "job-502",
            "status": "queue_state_update_failed",
            "message": "RuntimeError: postgres update failed",
            "execution_id": "fc-123",
        }
    }


def test_generation_service_marks_submission_failed_without_queue_publish(
) -> None:
    repository = FakeRepository()
    queue_publisher = FakeQueuePublisher()
    service = GenerationService(FailingGateway(), repository, queue_publisher)

    try:
        run_submit(service)
    except GenerationSubmissionError as exc:
        assert exc.job_id == repository.created.job_id
        assert str(exc) == (
            "RuntimeError: Modal function call missing object_id"
        )
    else:
        raise AssertionError("GenerationSubmissionError was not raised")

    assert repository.created.status == "submitting"
    assert repository.failed == (
        repository.created.job_id,
        "RuntimeError: Modal function call missing object_id",
    )
    assert repository.queued is None
    assert repository.queue_publish_failed is None
    assert queue_publisher.record is None


def test_generation_service_returns_persistence_failure_before_gateway(
) -> None:
    repository = FakeRepository()
    repository.create_error = RuntimeError("postgres unavailable")
    queue_publisher = FakeQueuePublisher()
    gateway = FakeGateway()
    service = GenerationService(gateway, repository, queue_publisher)

    try:
        run_submit(service)
    except GenerationSubmissionError as exc:
        assert exc.status == "persistence_failed"
        assert str(exc) == "RuntimeError: postgres unavailable"
    else:
        raise AssertionError("GenerationSubmissionError was not raised")

    assert repository.created is None
    assert gateway.workflow is None
    assert repository.failed is None
    assert repository.queued is None
    assert queue_publisher.record is None


def test_generation_service_marks_queue_publish_failed() -> None:
    gateway = FakeGateway()
    repository = FakeRepository()
    queue_publisher = FakeQueuePublisher()
    queue_publisher.error = RuntimeError("redis push failed")
    service = GenerationService(gateway, repository, queue_publisher)

    try:
        run_submit(service)
    except GenerationSubmissionError as exc:
        assert exc.job_id == repository.created.job_id
        assert exc.status == "queue_publish_failed"
        assert str(exc) == "RuntimeError: redis push failed"
        assert exc.execution_id == "modal-execution-1"
    else:
        raise AssertionError("GenerationSubmissionError was not raised")

    assert repository.queued == (
        repository.created.job_id,
        "modal-execution-1",
    )
    assert repository.queue_publish_failed == (
        repository.created.job_id,
        "RuntimeError: redis push failed",
    )
    assert queue_publisher.record is None


def test_generation_service_marks_queue_state_update_failed() -> None:
    gateway = FakeGateway()
    repository = FakeRepository()
    repository.queued_error = RuntimeError("postgres update failed")
    queue_publisher = FakeQueuePublisher()
    service = GenerationService(gateway, repository, queue_publisher)

    try:
        run_submit(service)
    except GenerationSubmissionError as exc:
        assert exc.job_id == repository.created.job_id
        assert exc.status == "queue_state_update_failed"
        assert str(exc) == "RuntimeError: postgres update failed"
    else:
        raise AssertionError("GenerationSubmissionError was not raised")

    assert repository.created.status == "submitting"
    assert repository.queued is None
    assert repository.queue_state_update_failed == (
        repository.created.job_id,
        "modal-execution-1",
        "RuntimeError: postgres update failed",
    )
    assert repository.queue_publish_failed is None
    assert queue_publisher.record is None


def test_generation_service_reports_state_update_error_details() -> None:
    gateway = FakeGateway()
    repository = FakeRepository()
    repository.queued_error = RuntimeError("postgres update failed")
    repository.queue_state_update_failed_error = RuntimeError(
        "postgres unavailable"
    )
    queue_publisher = FakeQueuePublisher()
    service = GenerationService(gateway, repository, queue_publisher)

    try:
        run_submit(service)
    except GenerationSubmissionError as exc:
        assert exc.job_id == repository.created.job_id
        assert exc.status == "queue_state_update_failed"
        assert exc.execution_id == "modal-execution-1"
        assert str(exc) == (
            "RuntimeError: postgres update failed; "
            "state_update_error=RuntimeError: postgres unavailable"
        )
    else:
        raise AssertionError("GenerationSubmissionError was not raised")

    assert repository.queue_state_update_failed is None


def test_create_generation_service_with_clients_uses_settings_for_workflow(
) -> None:
    settings = Settings(
        comfyui_checkpoint="quality-model.safetensors",
        comfyui_output_prefix="modal-img-custom",
        generation_queue_key="modal-img:queue",
    )
    service = create_generation_service_with_clients(settings, object())

    workflow = service._workflow_factory(
        GenerationRequest(
            prompt="studio lighting",
            negative_prompt="blurry",
            width=1024,
            height=1024,
            steps=28,
        )
    )

    assert workflow["4"]["inputs"]["ckpt_name"] == "quality-model.safetensors"
    assert workflow["9"]["inputs"]["filename_prefix"] == "modal-img-custom"


def run_submit(service: GenerationService):
    import asyncio

    request = GenerationRequest(
        prompt="high detail portrait",
        negative_prompt="blurry",
        width=768,
        height=1024,
        steps=40,
    )

    return asyncio.run(service.submit_text_to_image(request))
