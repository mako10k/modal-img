import os
from functools import lru_cache

from pydantic import BaseModel


DEFAULT_COMFYUI_BASE_URL = "http://127.0.0.1:8188"
DEFAULT_COMFYUI_TIMEOUT_SECONDS = 30.0
DEFAULT_COMFYUI_CHECKPOINT = "sd_xl_base_1.0.safetensors"
DEFAULT_COMFYUI_OUTPUT_PREFIX = "modal-img"


class Settings(BaseModel):
    app_env: str = "development"
    comfyui_base_url: str = DEFAULT_COMFYUI_BASE_URL
    comfyui_timeout_seconds: float = DEFAULT_COMFYUI_TIMEOUT_SECONDS
    comfyui_checkpoint: str = DEFAULT_COMFYUI_CHECKPOINT
    comfyui_output_prefix: str = DEFAULT_COMFYUI_OUTPUT_PREFIX
    redis_url: str = "redis://127.0.0.1:6379/0"
    postgres_dsn: str = (
        "postgresql://modal_img:modal_img@127.0.0.1:5432/modal_img"
    )
    generation_queue_key: str = "modal-img:generation-jobs"
    frontend_origin: str = "http://127.0.0.1:4173"


def load_settings_from_env() -> Settings:
    return Settings(
        app_env=os.getenv("MODAL_IMG_APP_ENV", "development"),
        comfyui_base_url=os.getenv(
            "MODAL_IMG_COMFYUI_BASE_URL",
            DEFAULT_COMFYUI_BASE_URL,
        ),
        comfyui_timeout_seconds=float(
            os.getenv(
                "MODAL_IMG_COMFYUI_TIMEOUT_SECONDS",
                str(DEFAULT_COMFYUI_TIMEOUT_SECONDS),
            )
        ),
        comfyui_checkpoint=os.getenv(
            "MODAL_IMG_COMFYUI_CHECKPOINT",
            DEFAULT_COMFYUI_CHECKPOINT,
        ),
        comfyui_output_prefix=os.getenv(
            "MODAL_IMG_COMFYUI_OUTPUT_PREFIX",
            DEFAULT_COMFYUI_OUTPUT_PREFIX,
        ),
        redis_url=os.getenv("MODAL_IMG_REDIS_URL", "redis://127.0.0.1:6379/0"),
        postgres_dsn=os.getenv(
            "MODAL_IMG_POSTGRES_DSN",
            "postgresql://modal_img:modal_img@127.0.0.1:5432/modal_img",
        ),
        generation_queue_key=os.getenv(
            "MODAL_IMG_GENERATION_QUEUE_KEY",
            "modal-img:generation-jobs",
        ),
        frontend_origin=os.getenv(
            "MODAL_IMG_FRONTEND_ORIGIN", "http://127.0.0.1:4173"
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings_from_env()
