from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status

from ...core.domain import User
from ...providers import UserCredentialsProvider
from ..schemas import UserRegistration

registration_router = APIRouter(
    prefix="/registration",
    tags=["Registration"],
    route_class=DishkaRoute
)


@registration_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    response_model_exclude={"password"},
    summary="Регистрирует пользователя"
)
async def register_user(
        user: UserRegistration, provider: Depends[UserCredentialsProvider]
) -> User:
    user = User.model_validate(user)
    return await provider.register(user)
