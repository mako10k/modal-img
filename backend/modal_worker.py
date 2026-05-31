import modal


image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi>=0.115.12,<0.116",
    "httpx>=0.28.1,<0.29",
    "psycopg[binary]>=3.2.9,<3.3",
    "redis>=5.2,<5.3",
)
app = modal.App("modal-img-execution")


@app.function(image=image)
def submit_text_to_image(workflow: dict[str, object]) -> dict[str, object]:
    return {
        "status": "accepted",
        "workflow_node_count": len(workflow),
    }
