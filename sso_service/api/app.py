import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.exceptions import (
    AlreadyExistsError,
    CreationError,
    DeletionError,
    InvalidCredentialsError,
    ReadingError,
    UnauthorizedError,
    UpdateError,
)
from ..database.base import create_tables
from ..dependencies import container
from .routers import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    await create_tables()
    yield


def create_fastapi_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    setup_middleware(app)
    setup_errors_handlers(app)
    setup_dishka(container=container, app=app)
    return app


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://frontend-project-1-isjz.onrender.com/"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_errors_handlers(app: FastAPI) -> None:
    @app.exception_handler(CreationError)
    def handle_creation_error(
        request: Request,  # noqa: ARG001
        exc: CreationError,
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error while resource creation"},
        )

    @app.exception_handler(ReadingError)
    def handle_reading_error(
        request: Request,  # noqa: ARG001
        exc: ReadingError,
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error while resource reading"},
        )

    @app.exception_handler(UpdateError)
    def handle_update_error(
        request: Request,  # noqa: ARG001
        exc: UpdateError,
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error while resource update"},
        )

    @app.exception_handler(AlreadyExistsError)
    def handle_already_exists_error(
        request: Request,  # noqa: ARG001
        exc: AlreadyExistsError,
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"detail": "Resource already exists"}
        )

    @app.exception_handler(DeletionError)
    def handle_deletion_error(
        request: Request,  # noqa: ARG001
        exc: DeletionError,
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error while resource deletion"},
        )

    @app.exception_handler(InvalidCredentialsError)
    def handle_unsupported_grant_type_error(
        request: Request,  # noqa: ARG001
        exc: InvalidCredentialsError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(UnauthorizedError)
    def handle_unauthorized_error(
        request: Request,  # noqa: ARG001
        exc: UnauthorizedError,
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})
