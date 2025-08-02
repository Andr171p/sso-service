from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from ..dependencies import container
from .routers import router


def create_fastapi_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    setup_dishka(container=container, app=app)
    return app
