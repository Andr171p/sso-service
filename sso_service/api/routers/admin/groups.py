from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, status

from sso_service.core.domain import Group
from sso_service.database.repository import GroupRepository

from ...schemas import GroupUpdate

groups_router = APIRouter(prefix="/groups", tags=["Groups"], route_class=DishkaRoute)


@groups_router.post(
    path="/{id}",
    status_code=status.HTTP_201_CREATED,
    response_model=Group,
    summary="Получает группу",
)
async def get_group(id: UUID, repository: Depends[GroupRepository]) -> Group:  # noqa: A002
    group = await repository.read(id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found",
        ) from None
    return group


@groups_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Group,
    summary="Обновляет атрибуты группы"
)
async def update_group(
        id: UUID, group_update: GroupUpdate, repository: Depends[GroupRepository]  # noqa: A002
) -> Group:
    group = await repository.update(
        id, **group_update.model_dump(exclude_none=True)
    )
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        ) from None
    return group


@groups_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет группу вместе пользовательскими привязками"
)
async def delete_group(id: UUID, repository: Depends[GroupRepository]) -> None:  # noqa: A002
    is_deleted = await repository.delete(id)
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        ) from None