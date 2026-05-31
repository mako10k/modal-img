from fastapi import FastAPI

from app.settings import get_settings


app = FastAPI(title="modal-img", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "environment": settings.app_env}
