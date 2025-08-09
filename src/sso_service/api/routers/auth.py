import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Request, Response, status

from ...core.constants import SESSION_EXPIRE_IN
from ...core.domain import TokenPair, User, UserClaims
from ...core.exceptions import (
    CreationError,
    InvalidCredentialsError,
    NotEnabledError,
    UnauthorizedError,
)
from ...services import UserAuthService
from ...storage import RedisSessionStore
from ..schemas import TokenIntrospect, TokenRefresh, UserLogin

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/{realm}/auth", tags=["Auth"], route_class=DishkaRoute)


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    response_model_exclude={"password"},
    summary="Осуществляет регистрацию пользователя",
)
async def register_user(
        realm: str, user: User, service: Depends[UserAuthService]
) -> User:
    try:
        return await service.register(user, realm)
    except CreationError:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while user registration"
        ) from None


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
    summary="Аутентифицирует пользователя"
)
async def login_user(
        realm: str,
        user: UserLogin,
        response: Response,
        service: Depends[UserAuthService]
) -> TokenPair:
    try:
        token_pair = await service.authenticate(
            realm=realm,
            email=user.email,
            password=user.password,
        )
        response.set_cookie(
            key="session_id",
            value=str(token_pair.session_id),
            httponly=True,
            secure=False,  # False только для теста  #TODO
            samesite="lax",
            max_age=int(SESSION_EXPIRE_IN.total_seconds())
        )
    except (InvalidCredentialsError, NotEnabledError) as e:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    else:
        return token_pair


@auth_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=UserClaims,
    summary="Декодирует и валидирует токен"
)
async def introspect_token(
        realm: str,
        token: TokenIntrospect,
        request: Request,
        service: Depends[UserAuthService]
) -> UserClaims:
    session_id = request.cookies.get("session_id")
    try:
        return await service.introspect(
            token.token, realm=realm, session_id=session_id
        )
    except UnauthorizedError as e:
        logger.exception("{e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e


@auth_router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
    summary="Обновляет токены пользователя"
)
async def refresh_token(
        realm: str,
        token: TokenRefresh,
        request: Request,
        response: Response,
        service: Depends[UserAuthService]
) -> TokenPair:
    session_id = request.cookies.get("session_id")
    try:
        token_pair = await service.refresh(token.token, realm, UUID(session_id))
        response.set_cookie(
            key="session_id",
            value=str(token_pair.session_id),
            httponly=True,
            secure=False,  # False только для теста  #TODO
            samesite="lax",
            max_age=int(SESSION_EXPIRE_IN.total_seconds())
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e
    else:
        return token_pair


@auth_router.post(
    path="/logout",
    status_code=status.HTTP_200_OK,
    summary="Выход пользователя из системы"
)
async def logout_user(
        realm: str,
        request: Request,
        response: Response,
        session_store: Depends[RedisSessionStore]
) -> None:
    session_id = request.cookies.get("session_id")
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session id is missing in cookies"
        ) from None
    is_deleted = await session_store.delete(UUID(session_id))
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, maybe already logout"
        ) from None
    response.delete_cookie("session_id")
