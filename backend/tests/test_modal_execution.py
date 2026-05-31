import pytest

from app.modal_execution import (
    ModalSubmissionGateway,
    check_modal_execution_health,
)
from app.settings import Settings


class FakeFunctionCall:
    def __init__(self, object_id: str):
        self.object_id = object_id


class FakeFunction:
    def __init__(self):
        self.calls: list[dict[str, object]] = []
        self.hydrated = False

    def spawn(self, workflow: dict[str, object]) -> FakeFunctionCall:
        self.calls.append(workflow)
        return FakeFunctionCall("fc-123")

    def hydrate(self):
        self.hydrated = True
        return self


@pytest.mark.anyio
async def test_modal_submission_gateway_spawns_modal_function() -> None:
    fake_function = FakeFunction()
    gateway = ModalSubmissionGateway(
        Settings(),
        function_resolver=lambda _settings: fake_function,
    )

    execution_id = await gateway.enqueue_workflow(
        {"4": {"class_type": "Test"}}
    )

    assert execution_id == "fc-123"
    assert fake_function.calls == [{"4": {"class_type": "Test"}}]


@pytest.mark.anyio
async def test_check_modal_execution_health_resolves_function() -> None:
    resolved: list[Settings] = []
    fake_function = FakeFunction()

    result = await check_modal_execution_health(
        Settings(),
        function_resolver=(
            lambda settings: resolved.append(settings) or fake_function
        ),
    )

    assert result == "ok"
    assert len(resolved) == 1
    assert fake_function.hydrated is True


@pytest.mark.anyio
async def test_check_modal_execution_health_requires_hydrate() -> None:
    with pytest.raises(RuntimeError, match="cannot be hydrated"):
        await check_modal_execution_health(
            Settings(),
            function_resolver=lambda _settings: object(),
        )
