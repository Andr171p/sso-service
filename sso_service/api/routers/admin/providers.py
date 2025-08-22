from typing import Annotated

from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Query, status

from sso_service.core.domain import IdentityProvider
from sso_service.database.repository import IdentityProviderRepository

from ...schemas import IdentityProviderCreate

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
        provider_create: IdentityProviderCreate, repository: Depends[IdentityProviderRepository]
) -> IdentityProvider:
    return await repository.create(IdentityProvider.model_validate(provider_create))


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
    return await repository.read_all(limit, page)


@providers_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=IdentityProvider,
    summary="Получает конкретного провайдера по его id"
)
async def get_provider(
        id: UUID, repository: Depends[IdentityProviderRepository]  # noqa: A002
) -> IdentityProvider:
    provider = await repository.read(id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return provider


@providers_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет провайдера по его d"
)
async def delete_provider(
        id: UUID, repository: Depends[IdentityProviderRepository]  # noqa: A002
) -> None:
    is_deleted = await repository.delete(id)
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
