import modal

from app.main import app as fastapi_app


image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi>=0.115.12,<0.116",
    "httpx>=0.28.1,<0.29",
    "psycopg[binary]>=3.2.9,<3.3",
    "redis>=5.2,<5.3",
)
modal_app = modal.App("modal-img-api")
app = modal_app


@modal_app.function(image=image)
@modal.asgi_app()
def api():
    return fastapi_app
