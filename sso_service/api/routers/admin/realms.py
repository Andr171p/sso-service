from typing import Annotated

from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Query, status

from sso_service.core.constants import MIN_LIMIT, MIN_PAGE
from sso_service.core.domain import Client, Group, Realm
from sso_service.database.repository import ClientRepository, GroupRepository, RealmRepository

from ...schemas import GroupCreate, RealmCreate, RealmUpdate

realms_router = APIRouter(prefix="/realms", tags=["Realms"], route_class=DishkaRoute)


@realms_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=Realm,
    summary="Создание области админом",
)
async def create_realm(realm_create: RealmCreate, repository: Depends[RealmRepository]) -> Realm:
    return await repository.create(Realm.model_validate(realm_create))


@realms_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[Realm],
    summary="Получает все области созданные админом",
)
async def get_realms(
    limit: Annotated[int, Query(..., ge=MIN_LIMIT)],
    page: Annotated[int, Query(..., ge=MIN_PAGE)],
    repository: Depends[RealmRepository],
) -> list[Realm]:
    return await repository.read_all(limit, page)


@realms_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Realm,
    summary="Получает область по её уникальному имени"
)
async def get_realm(id: UUID, repository: Depends[RealmRepository]) -> Realm:  # noqa: A002
    realm = await repository.read(id)
    if not realm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Realm not found"
        ) from None
    return realm


@realms_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Realm,
    summary="Обновляет заданные поля области"
)
async def update_realm(
        id: UUID, realm_update: RealmUpdate, repository: Depends[RealmRepository]  # noqa: A002
) -> Realm:
    updated_realm = await repository.update(
        id, **realm_update.model_dump(exclude_none=True)
    )
    if not updated_realm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Realm not found"
        ) from None
    return updated_realm


@realms_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет области по её id",
)
async def delete_realm(id: UUID, repository: Depends[RealmRepository]) -> None:  # noqa: A002
    id_deleted = await repository.delete(id)
    if not id_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Realm not found"
        ) from None


@realms_router.get(
    path="/{id}/clients",
    status_code=status.HTTP_200_OK,
    response_model=list[Client],
    summary="Получает всех клинтов в заданной области"
)
async def get_clients_by_realm(
        id: UUID, repository: Depends[ClientRepository]  # noqa: A002
) -> list[Client]:
    return await repository.get_by_realm(id)


@realms_router.post(
    path="/{id}/groups",
    status_code=status.HTTP_201_CREATED,
    response_model=Group,
    summary="Создаёт группу в указанной области"
)
async def create_group(
        id: UUID, group_create: GroupCreate, repository: Depends[GroupRepository]  # noqa: A002
) -> Group:
    group = Group(**group_create.model_dump(), realm_id=id)
    return await repository.create(group)
