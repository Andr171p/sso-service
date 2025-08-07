from typing import Annotated

from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status, HTTPException, Form, Response
from pydantic import EmailStr

from src.sso_service.core.domain import User
from src.sso_service.core.exceptions import CreationError, UnauthorizedError
from src.sso_service.database.repository import UserRepository
from src.sso_service.services import UserAuthService

users_router = APIRouter(prefix="/realm", tags=["Users auth"], route_class=DishkaRoute)


@users_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    summary="Регистрирует пользователя",
)
async def register_user(
        user: User, repository: Depends[UserRepository]
) -> User:
    try:
        user = user.hash_password()
        return await repository.create(user)
    except CreationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while registering user",
        ) from None


@users_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=Tokens,
    response_model_exclude_none=True,
    summary="Аутентифицирует пользователя"
)
async def login_user(
        realm: Annotated[UUID, Form(...)],
        email: Annotated[EmailStr, Form(...)],
        password: Annotated[str, Form(...)],
        response: Response,
        service: Depends[UserAuthService]
) -> Tokens:
    try:
        return await service.authenticate()
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
