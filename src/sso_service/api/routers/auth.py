from typing import Annotated

import logging

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, status, Form
from pydantic import EmailStr

from ...core.domain import User, TokenPair

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Auth"], route_class=DishkaRoute)


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    summary="Осуществляет регистрацию пользователя",
)
async def register_user(user: User) -> User: ...


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    summary="Аутентифицирует пользователя"
)
async def login_user(email: EmailStr, password: str) -> TokenPair: ...
