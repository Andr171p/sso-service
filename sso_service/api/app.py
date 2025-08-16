import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ..core.exceptions import (
    AlreadyExistsError,
    CreationError,
    DeletionError,
    InvalidCredentialsError,
    NotEnabledError,
    PermissionDeniedError,
    ReadingError,
    UnauthorizedError,
    UnsupportedGrantTypeError,
    UpdateError,
)
from ..dependencies import container
from .routers import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]: ...


def create_fastapi_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    setup_dishka(container=container, app=app)
    setup_errors_handlers(app)
    return app


def setup_errors_handlers(app: FastAPI) -> None:
    @app.exception_handler(CreationError)
    def handle_creation_error(
            request: Request, exc: CreationError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error while resource creation"}
        )

    @app.exception_handler(ReadingError)
    def handle_reading_error(
            request: Request, exc: ReadingError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error while resource reading"}
        )

    @app.exception_handler(UpdateError)
    def handle_update_error(
            request: Request, exc: UpdateError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error while resource update"}
        )

    @app.exception_handler(AlreadyExistsError)
    def handle_already_exists_error(
            request: Request, exc: AlreadyExistsError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"message": "Resource already exists"}
        )

    @app.exception_handler(DeletionError)
    def handle_deletion_error(
            request: Request, exc: DeletionError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error while resource deletion"}
        )

    @app.exception_handler(UnsupportedGrantTypeError)
    def handle_unsupported_grant_type_error(
            request: Request, exc: UnsupportedGrantTypeError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)}
        )

    @app.exception_handler(UnauthorizedError)
    def handle_unauthorized_error(
            request: Request, exc: UnauthorizedError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(exc)}
        )

    @app.exception_handler(NotEnabledError)
    def handle_invalid_credentials_error(
            request: Request, exc: InvalidCredentialsError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(exc)}
        )

    @app.exception_handler(PermissionDeniedError)
    def handle_permission_denied_error(
            request: Request, exc: InvalidCredentialsError  # noqa: ARG001
    ) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(exc)}
        )
