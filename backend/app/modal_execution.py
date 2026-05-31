import asyncio
from collections.abc import Callable

import modal

from app.settings import Settings


def resolve_modal_text_to_image_function(settings: Settings):
    return modal.Function.from_name(
        settings.modal_app_name,
        settings.modal_text_to_image_function_name,
        environment_name=settings.modal_environment_name,
    )


def resolve_modal_function_call(execution_id: str):
    return modal.functions.FunctionCall.from_id(execution_id)


class ModalSubmissionGateway:
    def __init__(
        self,
        settings: Settings,
        function_resolver: Callable[[Settings], object] = (
            resolve_modal_text_to_image_function
        ),
    ):
        self._settings = settings
        self._function_resolver = function_resolver

    async def enqueue_workflow(self, workflow: dict[str, object]) -> str:
        function = await asyncio.to_thread(
            self._function_resolver,
            self._settings,
        )
        function_call = await asyncio.to_thread(function.spawn, workflow)
        execution_id = getattr(function_call, "object_id", None)
        if not isinstance(execution_id, str) or not execution_id:
            raise RuntimeError("Modal function call missing object_id")

        return execution_id

    async def get_result(
        self,
        execution_id: str,
        timeout_seconds: float = 0.1,
        function_call_resolver: Callable[[str], object] = (
            resolve_modal_function_call
        ),
    ) -> dict[str, object] | None:
        function_call = await asyncio.to_thread(
            function_call_resolver,
            execution_id,
        )
        getter = getattr(function_call, "get", None)
        if not callable(getter):
            raise RuntimeError("Modal function call cannot be resolved")

        try:
            result = await asyncio.to_thread(getter, timeout_seconds)
        except TimeoutError:
            return None

        if not isinstance(result, dict):
            raise RuntimeError("Modal function result must be a dictionary")

        return result


async def check_modal_execution_health(
    settings: Settings,
    function_resolver: Callable[[Settings], object] = (
        resolve_modal_text_to_image_function
    ),
) -> str:
    function = await asyncio.to_thread(function_resolver, settings)
    hydrate = getattr(function, "hydrate", None)
    if not callable(hydrate):
        raise RuntimeError("Modal function reference cannot be hydrated")

    await asyncio.to_thread(hydrate)
    return "ok"
