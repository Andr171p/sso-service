from typing import Annotated

import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Query, status

from sso_service.core.domain import IdentityProvider
from sso_service.core.exceptions import (
    AlreadyExistsError,
    CreationError,
    DeletionError,
    ReadingError,
)
from sso_service.database.repository import IdentityProviderRepository

logger = logging.getLogger(__name__)

providers_router = APIRouter(
    prefix="/providers", tags=["Identity Providers"], route_class=DishkaRoute
)


@providers_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=IdentityProvider,
    summary="Создаёт провайдера для аутентификации"
)
async def create_provider(
        provider: IdentityProvider, repository: Depends[IdentityProviderRepository]
) -> IdentityProvider:
    try:
        return await repository.create(provider)
    except AlreadyExistsError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Provider already exists"
        ) from None
    except CreationError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while provider creation"
        ) from None


@providers_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[IdentityProvider],
    summary="Получает все провайдеры аутентификации"
)
async def get_providers(
        limit: Annotated[int, Query(..., description="Лимит провайдеров на одной странице")],
        page: Annotated[int, Query(..., description="Страница с провайдерами")],
        repository: Depends[IdentityProviderRepository]
) -> list[IdentityProvider]:
    try:
        return await repository.read_all(limit, page)
    except ReadingError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while reading providers"
        ) from None


@providers_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=IdentityProvider,
    summary="Получает конкретного провайдера по его id"
)
async def get_provider(
        id: UUID, repository: Depends[IdentityProviderRepository]
) -> IdentityProvider:
    try:
        provider = await repository.read(id)
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
            )
    except ReadingError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while reading provider"
        ) from None
    else:
        return provider


@providers_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет провайдера по его d"
)
async def delete_provider(
        id: UUID, repository: Depends[IdentityProviderRepository]
) -> None:
    try:
        is_deleted = await repository.delete(id)
        if not is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
            )
    except DeletionError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while deleting provider"
        ) from None
