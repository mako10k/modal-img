import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    app_env: str = "development"
    redis_url: str = "redis://127.0.0.1:6379/0"
    postgres_dsn: str = (
        "postgresql://modal_img:modal_img@127.0.0.1:5432/modal_img"
    )
    generation_queue_key: str = "modal-img:generation-jobs"
    frontend_origin: str = "http://127.0.0.1:4173"


def load_settings_from_env() -> Settings:
    return Settings(
        app_env=os.getenv("MODAL_IMG_APP_ENV", "development"),
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
