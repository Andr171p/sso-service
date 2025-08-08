import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, status

from src.sso_service.core.domain import Group
from src.sso_service.core.exceptions import DeletionError, ReadingError, UpdateError
from src.sso_service.database.repository import GroupRepository

from ...schemas import GroupUpdate

logger = logging.getLogger(__name__)

groups_router = APIRouter(prefix="/groups", tags=["Groups"], route_class=DishkaRoute)


@groups_router.post(
    path="/{id}",
    status_code=status.HTTP_201_CREATED,
    response_model=Group,
    summary="Получает группу",
)
async def get_group(id: UUID, repository: Depends[GroupRepository]) -> Group:
    try:
        group = await repository.read(id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            ) from None
    except ReadingError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while receiving group"
        ) from None
    else:
        return group


@groups_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Group,
    summary="Обновляет атрибуты группы"
)
async def update_group(
        id: UUID, group_update: GroupUpdate, repository: Depends[GroupRepository]
) -> Group:
    try:
        group = await repository.update(
            id, **group_update.model_dump(exclude_none=True)
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            ) from None
    except UpdateError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while updating group"
        ) from None
    else:
        return group


@groups_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет группу вместе пользовательскими привязками"
)
async def delete_group(id: UUID, repository: Depends[GroupRepository]) -> None:
    try:
        is_deleted = await repository.delete(id)
        if not is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            ) from None
    except DeletionError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error while deleting group"
        ) from None
