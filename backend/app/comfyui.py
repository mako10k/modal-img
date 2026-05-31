from collections.abc import Callable

import httpx

from app.settings import Settings


class ComfyUISubmissionGateway:
    def __init__(
        self,
        settings: Settings,
        client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ):
        self._settings = settings
        self._client_factory = client_factory

    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        if self._client_factory is None:
            client = httpx.AsyncClient(
                base_url=self._settings.comfyui_base_url,
                timeout=self._settings.comfyui_timeout_seconds,
            )
            should_close = True
        else:
            client = self._client_factory()
            should_close = False

        try:
            response = await client.post(
                "/prompt",
                json={"prompt": workflow},
            )
            response.raise_for_status()
            payload = response.json()
        finally:
            if should_close:
                await client.aclose()

        prompt_id = payload.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise RuntimeError("ComfyUI response missing prompt_id")

        return prompt_id


async def check_comfyui_health(
    settings: Settings,
    client_factory: Callable[[], httpx.AsyncClient] | None = None,
) -> str:
    if client_factory is None:
        client = httpx.AsyncClient(
            base_url=settings.comfyui_base_url,
            timeout=settings.comfyui_timeout_seconds,
        )
        should_close = True
    else:
        client = client_factory()
        should_close = False

    try:
        response = await client.get("/system_stats")
        response.raise_for_status()
    finally:
        if should_close:
            await client.aclose()

    return "ok"
