import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

MODAL_WORKER_PATH = Path(__file__).resolve().parents[1] / "modal_worker.py"
SPEC = spec_from_file_location("modal_worker", MODAL_WORKER_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

_validate_dimension = MODULE._validate_dimension
_validate_steps = MODULE._validate_steps


def test_validate_dimension_accepts_contract_value() -> None:
    assert _validate_dimension("width", 768) == 768


def test_validate_dimension_rejects_non_multiple_of_64() -> None:
    with pytest.raises(
        ValueError,
        match="width must be between 512 and 1024 in multiples of 64",
    ):
        _validate_dimension("width", 1000)


def test_validate_steps_rejects_out_of_range_value() -> None:
    with pytest.raises(ValueError, match="steps must be between 12 and 30"):
        _validate_steps(64)
