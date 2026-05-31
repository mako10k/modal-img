from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.clients import create_redis_client
from app.generation import (
    GenerationAccepted,
    GenerationRequest,
    create_generation_service_with_clients,
)
from app.health import collect_dependency_health
from app.settings import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = create_redis_client(settings)
    app.state.generation_service = create_generation_service_with_clients(
        settings,
        app.state.redis,
    )

    yield

    await app.state.redis.aclose()


app = FastAPI(title="modal-img", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health(request: Request) -> dict[str, object]:
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


@app.post("/v1/generations")
async def create_generation(
    request: GenerationRequest,
    http_request: Request,
) -> GenerationAccepted:
    generation_service = http_request.app.state.generation_service
    return await generation_service.submit_text_to_image(request)
