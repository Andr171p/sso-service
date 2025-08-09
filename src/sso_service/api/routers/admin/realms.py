from typing import Annotated

import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Query, status

from src.sso_service.core.domain import Client, Group, Realm
from src.sso_service.core.exceptions import (
    AlreadyExistsError,
    CreationError,
    DeletionError,
    ReadingError,
    UpdateError,
)
from src.sso_service.database.repository import ClientRepository, GroupRepository, RealmRepository

from ...schemas import GroupCreate, RealmCreate, RealmUpdate

logger = logging.getLogger(__name__)

realms_router = APIRouter(prefix="/realms", tags=["Realms"], route_class=DishkaRoute)


@realms_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=Realm,
    summary="Создание области админом",
)
async def create_realm(realm_create: RealmCreate, repository: Depends[RealmRepository]) -> Realm:
    try:
        return await repository.create(Realm.model_validate(realm_create))
    except AlreadyExistsError:
        logger.exception("Realm already exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This realm is already registered"
        ) from None
    except CreationError:
        logger.exception("Error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error while creation realm"
        ) from None


@realms_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[Realm],
    summary="Получает все области созданные админом",
)
async def get_realms(
    limit: Annotated[int, Query(..., ge=0)],
    page: Annotated[int, Query(..., ge=0)],
    repository: Depends[RealmRepository],
) -> list[Realm]:
    try:
        return await repository.read_all(limit, page)
    except ReadingError:
        logger.exception("Occurred error while reading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Occurred error while reading realms",
        ) from None


@realms_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Realm,
    summary="Получает область по её уникальному имени"
)
async def get_realm(id: UUID, repository: Depends[RealmRepository]) -> Realm:
    try:
        realm = await repository.read(id)
        if not realm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Realm not found"
            ) from None
    except ReadingError:
        logger.exception("Occurred error while reading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Occurred error while reading realm",
        ) from None
    else:
        return realm


@realms_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Realm,
    summary="Обновляет заданные поля области"
)
async def update_realm(
        id: UUID, realm_update: RealmUpdate, repository: Depends[RealmRepository]
) -> Realm:
    try:
        updated_realm = await repository.update(
            id, **realm_update.model_dump(exclude_none=True)
        )
        if not updated_realm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Realm not found"
            ) from None
        return updated_realm
    except UpdateError:
        logger.exception("Occurred error while updating: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Occurred error while updating realm",
        ) from None


@realms_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет области по её id",
)
async def delete_realm(id: UUID, repository: Depends[RealmRepository]) -> None:
    try:
        id_deleted = await repository.delete(id)
        if not id_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Realm not found"
            ) from None
    except DeletionError:
        logger.exception("Occurred error while deleting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Occurred error while deleting realm",
        ) from None
    else:
        return


@realms_router.get(
    path="/{id}/clients",
    status_code=status.HTTP_200_OK,
    response_model=list[Client],
    summary="Получает всех клинтов в заданной области"
)
async def get_client_by_realm(
        id: UUID, repository: Depends[ClientRepository]
) -> list[Client]:
    try:
        return await repository.get_by_realm(id)
    except ReadingError:
        logger.exception("Occurred error while reading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Occurred error while reading clients in realm",
        ) from None


@realms_router.post(
    path="/{id}/groups",
    status_code=status.HTTP_201_CREATED,
    response_model=Group,
    summary="Создаёт группу в указанной области"
)
async def create_group(
        id: UUID, group_create: GroupCreate, repository: Depends[GroupRepository]
) -> Group:
    try:
        group = Group(**group_create.model_dump(), realm_id=id)
        return await repository.create(group)
    except CreationError:
        logger.exception("Occurred error while creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Occurred error while creating group",
        ) from None
