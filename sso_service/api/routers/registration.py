import logging

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, status

from ...core.domain import User
from ...core.exceptions import AlreadyExistsError, CreationError
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
    try:
        user = User.model_validate(user)
        user = user.hash_password()
        return await service.register(user)
    except AlreadyExistsError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists with this email"
        ) from None
    except CreationError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while user registration"
        ) from None
