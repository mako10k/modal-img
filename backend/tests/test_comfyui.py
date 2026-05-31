import pytest

from app.comfyui import ComfyUISubmissionGateway, check_comfyui_health
from app.settings import Settings


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class FakeClient:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload
        self.calls: list[tuple[str, object]] = []

    async def post(self, path: str, json: dict[str, object]) -> FakeResponse:
        self.calls.append((path, json))
        return FakeResponse(self.payload)

    async def get(self, path: str) -> FakeResponse:
        self.calls.append((path, None))
        return FakeResponse(self.payload)


@pytest.mark.anyio
async def test_comfyui_gateway_posts_prompt_payload() -> None:
    fake_client = FakeClient({"prompt_id": "prompt-123"})
    gateway = ComfyUISubmissionGateway(
        Settings(),
        client_factory=lambda: fake_client,
    )

    comfyui_prompt_id = await gateway.enqueue_workflow(
        {"4": {"class_type": "Test"}}
    )

    assert comfyui_prompt_id == "prompt-123"
    assert fake_client.calls == [
        ("/prompt", {"prompt": {"4": {"class_type": "Test"}}})
    ]


@pytest.mark.anyio
async def test_comfyui_gateway_rejects_missing_prompt_id() -> None:
    gateway = ComfyUISubmissionGateway(
        Settings(),
        client_factory=lambda: FakeClient({"node_errors": {}}),
    )

    with pytest.raises(RuntimeError, match="missing prompt_id"):
        await gateway.enqueue_workflow({"4": {"class_type": "Test"}})


@pytest.mark.anyio
async def test_check_comfyui_health_uses_system_stats_endpoint() -> None:
    fake_client = FakeClient({"system": {"status": "ok"}})

    result = await check_comfyui_health(
        Settings(),
        client_factory=lambda: fake_client,
    )

    assert result == "ok"
    assert fake_client.calls == [("/system_stats", None)]


@pytest.mark.anyio
async def test_check_comfyui_health_uses_health_timeout_setting(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class CapturingClient:
        def __init__(self, base_url: str, timeout: float):
            captured["base_url"] = base_url
            captured["timeout"] = timeout

        async def get(self, path: str) -> FakeResponse:
            captured["path"] = path
            return FakeResponse({"system": {"status": "ok"}})

        async def aclose(self) -> None:
            captured["closed"] = True

    monkeypatch.setattr("app.comfyui.httpx.AsyncClient", CapturingClient)

    result = await check_comfyui_health(
        Settings(comfyui_health_timeout_seconds=3.5),
    )

    assert result == "ok"
    assert captured == {
        "base_url": "http://127.0.0.1:8188",
        "timeout": 3.5,
        "path": "/system_stats",
        "closed": True,
    }
