from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, Request, Response, status

from ...core.constants import SESSION_EXPIRE_IN
from ...core.domain import TokenPair, UserClaims
from ...providers import UserCredentialsProvider
from ...services import UserTokenService
from ..schemas import TokenIntrospect, TokenRefresh, UserLogin, UserRealmSwitch

auth_router = APIRouter(prefix="/{realm}/auth", tags=["Auth"], route_class=DishkaRoute)


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
        provider: Depends[UserCredentialsProvider]
) -> TokenPair:
    token_pair = await provider.authenticate(
        realm=realm,
        email=user.email,
        password=user.password,
    )
    response.set_cookie(
        key="session_id",
        value=str(token_pair.session_id),
        httponly=False,
        secure=False,  # False только для теста  #TODO
        samesite="lax",
        max_age=int(SESSION_EXPIRE_IN.total_seconds())
    )
    return token_pair


@auth_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=UserClaims,
    response_model_exclude_none=True,
    summary="Декодирует и валидирует токен"
)
async def introspect_token(
        realm: str,
        token: TokenIntrospect,
        request: Request,
        service: Depends[UserTokenService]
) -> UserClaims:
    session_id = request.cookies.get("session_id")
    return await service.introspect(
        token.token, realm=realm, session_id=UUID(session_id)
    )


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
        service: Depends[UserTokenService]
) -> TokenPair:
    session_id = request.cookies.get("session_id")
    token_pair = await service.refresh(token.refresh_token, realm, UUID(session_id))
    response.set_cookie(
        key="session_id",
        value=str(token_pair.session_id),
        httponly=False,
        secure=False,  # False только для теста  #TODO
        samesite="lax",
        max_age=int(SESSION_EXPIRE_IN.total_seconds())
    )
    return token_pair


@auth_router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход пользователя из системы"
)
async def logout_user(
        realm: str,  # noqa: ARG001
        request: Request,
        response: Response,
        service: Depends[UserTokenService]
) -> None:
    session_id = request.cookies.get("session_id")
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session id is missing in cookies"
        ) from None
    await service.revoke(UUID(session_id))
    response.delete_cookie("session_id")


@auth_router.post(
    path="/switch-realm",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
    summary="Осуществляет переход пользователя из одного realm в другой"
)
async def switch_realm(
        realm: str,
        user: UserRealmSwitch,
        request: Request,
        service: Depends[UserTokenService]
) -> TokenPair:
    session_id = request.cookies.get("session_id")
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session id is missing in cookies"
        ) from None
    return await service.switch_realm(
        current_realm=realm,
        target_realm=user.target_realm,
        refresh_token=user.refresh_token,
        session_id=UUID(session_id)
    )
