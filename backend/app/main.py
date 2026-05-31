from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.clients import create_redis_client
from app.generation import (
    GenerationAccepted,
    GenerationRequest,
    GenerationSubmissionError,
    create_generation_service_with_clients,
)
from app.health import collect_dependency_health
from app.settings import get_settings


router = APIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.redis = create_redis_client(settings)
    app.state.generation_service = create_generation_service_with_clients(
        settings,
        app.state.redis,
    )

    yield

    await app.state.redis.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="modal-img", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    return app


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    dependencies = await collect_dependency_health(
        request.app.state.redis,
        settings,
    )
    status = (
        "ok"
        if all(value == "ok" for value in dependencies.values())
        else "degraded"
    )

    return {
        "status": status,
        "environment": settings.app_env,
        "dependencies": dependencies,
    }


@router.post("/v1/generations")
async def create_generation(
    request: GenerationRequest,
    http_request: Request,
) -> GenerationAccepted:
    generation_service = http_request.app.state.generation_service
    try:
        return await generation_service.submit_text_to_image(request)
    except GenerationSubmissionError as exc:
        detail = {
            "job_id": exc.job_id,
            "status": exc.status,
            "message": str(exc),
        }
        if exc.comfyui_prompt_id is not None:
            detail["comfyui_prompt_id"] = exc.comfyui_prompt_id

        raise HTTPException(status_code=502, detail=detail) from exc


app = create_app()
