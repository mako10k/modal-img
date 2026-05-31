import modal

from app.main import app as fastapi_app


image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi>=0.115.12,<0.116"
)
modal_app = modal.App("modal-img-api")


@modal_app.function(image=image)
@modal.asgi_app()
def api():
    return fastapi_app
