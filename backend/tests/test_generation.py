from fastapi.testclient import TestClient

import app.main as main_module
from app.generation import GenerationRequest, GenerationService


class FakeGateway:
    def __init__(self):
        self.workflow: dict[str, object] | None = None

    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        self.workflow = workflow
        return "comfy-workflow-1"


def test_generation_service_builds_text_to_image_workflow() -> None:
    gateway = FakeGateway()
    service = GenerationService(gateway)

    response = run_submit(service)

    assert response.status == "accepted"
    assert response.workflow_id == "comfy-workflow-1"
    assert gateway.workflow == {
        "kind": "text_to_image",
        "prompt": "high detail portrait",
        "negative_prompt": "blurry",
        "image": {"width": 768, "height": 1024},
        "sampling": {"steps": 40},
    }


def test_create_generation_endpoint_uses_generation_service(
    monkeypatch,
) -> None:
    class FakeGenerationService:
        async def submit_text_to_image(self, request: GenerationRequest):
            assert request.prompt == "studio lighting"
            return {
                "job_id": "job-123",
                "status": "accepted",
                "workflow_id": "workflow-123",
            }

    monkeypatch.setattr(
        main_module,
        "create_generation_service",
        lambda: FakeGenerationService(),
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
        "status": "accepted",
        "workflow_id": "workflow-123",
    }


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
