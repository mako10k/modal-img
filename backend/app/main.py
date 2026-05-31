from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.clients import create_redis_client
from app.health import collect_dependency_health
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.redis = create_redis_client(settings)

    yield

    await app.state.redis.aclose()


app = FastAPI(title="modal-img", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health(request: Request) -> dict[str, object]:
    settings = get_settings()
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
