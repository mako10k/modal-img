import base64
from io import BytesIO

import modal


MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
DEFAULT_PROMPT = (
    "cinematic editorial portrait, natural skin texture, moody practical "
    "lighting, 85mm lens, shallow depth of field, highly detailed, "
    "photorealistic"
)
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768
DEFAULT_STEPS = 24
MIN_STEPS = 12
MAX_STEPS = 30
GUIDANCE_SCALE = 6.5
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.4,<2.8",
    "diffusers>=0.30,<0.36",
    "transformers>=4.44,<4.53",
    "accelerate>=0.33,<1.1",
    "safetensors>=0.4,<0.6",
    "Pillow>=10.4,<12",
    gpu="T4",
)
app = modal.App("modal-img-execution")

_PIPELINE = None


def _extract_text(workflow: dict[str, object], node_id: str) -> str:
    node = workflow.get(node_id)
    if not isinstance(node, dict):
        return ""
    inputs = node.get("inputs")
    if not isinstance(inputs, dict):
        return ""
    value = inputs.get("text")
    return value if isinstance(value, str) else ""


def _extract_int(
    workflow: dict[str, object],
    node_id: str,
    input_name: str,
    fallback: int,
) -> int:
    node = workflow.get(node_id)
    if not isinstance(node, dict):
        return fallback
    inputs = node.get("inputs")
    if not isinstance(inputs, dict):
        return fallback
    value = inputs.get(input_name)
    return value if isinstance(value, int) else fallback


def _validate_dimension(name: str, value: int) -> int:
    if value < 512 or value > 1024 or value % 64 != 0:
        raise ValueError(
            f"{name} must be between 512 and 1024 in multiples of 64"
        )
    return value


def _validate_steps(value: int) -> int:
    if value < MIN_STEPS or value > MAX_STEPS:
        raise ValueError(
            f"steps must be between {MIN_STEPS} and {MAX_STEPS}"
        )
    return value


def _load_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE

    import torch
    from diffusers import (
        AutoPipelineForText2Image,
        DPMSolverMultistepScheduler,
    )

    _PIPELINE = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )
    _PIPELINE.scheduler = DPMSolverMultistepScheduler.from_config(
        _PIPELINE.scheduler.config,
        use_karras_sigmas=True,
    )
    _PIPELINE.enable_model_cpu_offload()
    _PIPELINE.enable_attention_slicing()
    _PIPELINE.set_progress_bar_config(disable=True)
    return _PIPELINE


@app.function(image=image, gpu="T4", timeout=900)
def submit_text_to_image(workflow: dict[str, object]) -> dict[str, object]:
    pipeline = _load_pipeline()
    prompt = _extract_text(workflow, "6") or DEFAULT_PROMPT
    negative_prompt = _extract_text(workflow, "7")
    width = _validate_dimension(
        "width",
        _extract_int(workflow, "5", "width", DEFAULT_WIDTH)
    )
    height = _validate_dimension(
        "height",
        _extract_int(workflow, "5", "height", DEFAULT_HEIGHT)
    )
    steps = _validate_steps(
        _extract_int(workflow, "3", "steps", DEFAULT_STEPS)
    )

    image_result = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        num_inference_steps=steps,
        guidance_scale=GUIDANCE_SCALE,
        width=width,
        height=height,
    ).images[0]
    buffer = BytesIO()
    image_result.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    return {
        "status": "completed",
        "workflow_node_count": len(workflow),
        "result_mime_type": "image/png",
        "result_image_data_url": f"data:image/png;base64,{image_base64}",
        "model_id": MODEL_ID,
        "width": width,
        "height": height,
        "steps": steps,
        "guidance_scale": GUIDANCE_SCALE,
    }
