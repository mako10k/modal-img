import base64
from io import BytesIO

import modal


MODEL_ID = "stabilityai/sd-turbo"
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


def _clamp_dimension(value: int) -> int:
    return max(512, min(1024, value // 64 * 64))


def _load_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE

    import torch
    from diffusers import AutoPipelineForText2Image

    _PIPELINE = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
    )
    _PIPELINE = _PIPELINE.to("cuda")
    _PIPELINE.set_progress_bar_config(disable=True)
    return _PIPELINE


@app.function(image=image, gpu="T4", timeout=900)
def submit_text_to_image(workflow: dict[str, object]) -> dict[str, object]:
    pipeline = _load_pipeline()
    prompt = _extract_text(workflow, "6") or "high detail photograph"
    negative_prompt = _extract_text(workflow, "7")
    width = _clamp_dimension(_extract_int(workflow, "5", "width", 512))
    height = _clamp_dimension(_extract_int(workflow, "5", "height", 512))
    steps = max(1, min(_extract_int(workflow, "3", "steps", 2), 4))

    image_result = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        num_inference_steps=steps,
        guidance_scale=0.0,
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
    }
