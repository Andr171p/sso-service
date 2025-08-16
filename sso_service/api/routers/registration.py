import logging

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status

from ...core.domain import User
from ...services import UserAuthService
from ..schemas import UserRegistration

logger = logging.getLogger(__name__)

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
        user: UserRegistration, service: Depends[UserAuthService]
) -> User:
    user = User.model_validate(user)
    user = user.hash_password()
    return await service.register(user)
