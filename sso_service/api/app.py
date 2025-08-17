from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from ..dependencies import container
from .routers import router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]: ...


def create_fastapi_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    setup_dishka(container=container, app=app)
    return app
