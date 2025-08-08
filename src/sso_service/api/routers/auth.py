# from typing import Annotated

import logging

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status, Request, Response
from pydantic import EmailStr

from ...core.domain import User, TokenPair, UserClaims
from ...services import UserAuthService
from ..schemas import TokenRefresh, TokenIntrospect

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Auth"], route_class=DishkaRoute)


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    summary="Осуществляет регистрацию пользователя",
)
async def register_user(
        user: User, service: Depends[UserAuthService]
) -> User: ...


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    summary="Аутентифицирует пользователя"
)
async def login_user(
        email: EmailStr, password: str, service: Depends[UserAuthService]
) -> TokenPair: ...


@auth_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=UserClaims,
    summary="Декодирует и валидирует токен"
)
async def introspect_token(
        data: TokenIntrospect, service: Depends[UserAuthService]
) -> UserClaims: ...


@auth_router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    summary="Обновляет токены пользователя"
)
async def refresh_token(
        data: TokenRefresh,
        request: Request,
        response: Response,
        service: Depends[UserAuthService]
) -> TokenPair: ...


@auth_router.post(
    path="/logout",
    status_code=status.HTTP_200_OK,
    summary="Выход пользователя из системы"
)
async def logout_user(response: Response) -> None: ...
