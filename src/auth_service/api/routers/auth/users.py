from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, status, Form

users_router = APIRouter(prefix="/users", tags=["Users auth"])


@users_router.post(
    path="/login",
    status_code=status.HTTP_201_CREATED,
    response_model=...,
    summary="Выдаёт токены пользователю",
)
async def login_user(
        realm_id: Annotated[UUID, Form(...)], username: str, password: str
) -> ...:
    ...
