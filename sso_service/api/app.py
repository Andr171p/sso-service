import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from ..core.exceptions import (
    AlreadyExistsError,
    CreationError,
    DeletionError,
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


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_errors_handlers(app: FastAPI) -> None:
    @app.exception_handler(CreationError)
    def handle_creation_error(
        request: Request,  # noqa: ARG001
        exc: CreationError,
    ) -> HTTPException:
        logger.error(exc)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while resource creation",
        )

    @app.exception_handler(ReadingError)
    def handle_reading_error(
        request: Request,  # noqa: ARG001
        exc: ReadingError,
    ) -> HTTPException:
        logger.error(exc)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while resource reading",
        )

    @app.exception_handler(UpdateError)
    def handle_update_error(
        request: Request,  # noqa: ARG001
        exc: UpdateError,
    ) -> HTTPException:
        logger.error(exc)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while resource update",
        )

    @app.exception_handler(AlreadyExistsError)
    def handle_already_exists_error(
        request: Request,  # noqa: ARG001
        exc: AlreadyExistsError,
    ) -> HTTPException:
        logger.error(exc)
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Resource already exists"
        )

    @app.exception_handler(DeletionError)
    def handle_deletion_error(
        request: Request,  # noqa: ARG001
        exc: DeletionError,
    ) -> HTTPException:
        logger.error(exc)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while resource deletion",
        )

    @app.exception_handler(UnsupportedGrantTypeError)
    def handle_unsupported_grant_type_error(
        request: Request,  # noqa: ARG001
        exc: UnsupportedGrantTypeError,
    ) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )

    @app.exception_handler(UnauthorizedError)
    def handle_unauthorized_error(
        request: Request,  # noqa: ARG001
        exc: UnauthorizedError,
    ) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )
