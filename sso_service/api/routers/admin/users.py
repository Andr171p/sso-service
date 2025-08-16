from typing import Annotated

import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Query, status

from sso_service.core.domain import User
from sso_service.database.repository import UserRepository

from ...schemas import UserUpdate

logger = logging.getLogger(__name__)

users_router = APIRouter(prefix="/users", tags=["Users"], route_class=DishkaRoute)


@users_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[User],
    summary="Получает всех пользователей"
)
async def get_users(
        page: Annotated[int, Query(...)],
        limit: Annotated[int, Query(...)],
        repository: Depends[UserRepository]
) -> list[User]:
    return await repository.read_all(page, limit)


@users_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=User,
    summary="Получает конкретного пользователя"
)
async def get_user(id: UUID, repository: Depends[UserRepository]) -> User:  # noqa: A002
    user = await repository.read(id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )
    return user


@users_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=User,
    summary="Обновляет статус пользователя"
)
async def update_user(
        id: UUID, user: UserUpdate, repository: Depends[UserRepository]  # noqa: A002
) -> User:
    updated_user = await repository.update(id, status=user.status)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user
