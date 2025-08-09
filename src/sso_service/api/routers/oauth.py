import logging

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, status

from ...core.domain import ClientClaims, Token
from ...core.exceptions import (
    InvalidCredentialsError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
    UnsupportedGrantTypeError,
)
from ...services import ClientAuthService
from ..schemas import ClientCredentials, TokenIntrospect

logger = logging.getLogger(__name__)

oauth_router = APIRouter(prefix="/{realm}/oauth", tags=["OAuth"], route_class=DishkaRoute)


@oauth_router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    response_model_exclude_none=True,
    summary="Выдаёт токен клиенту",
)
async def issue_token(
        realm: str,
        credentials: ClientCredentials,
        service: Depends[ClientAuthService]
) -> Token:
    try:
        token = await service.authenticate(
            realm=realm,
            grant_type=credentials.grant_type,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scope=credentials.scope,
        )
    except UnsupportedGrantTypeError as e:
        logger.exception("Unsupported grant type: %s", credentials.grant_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except InvalidCredentialsError:
        logger.exception("Error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from None
    except (UnauthorizedError, NotEnabledError, PermissionDeniedError) as e:
        logger.exception("Access forbidden: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    else:
        return token


@oauth_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=ClientClaims,
    response_model_exclude_none=True,
    summary="Декодирует и валидирует токен"
)
async def introspect_token(
        realm: str,
        token: TokenIntrospect,
        service: Depends[ClientAuthService]
) -> ClientClaims:
    try:
        return await service.introspect(token.token, realm=realm)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
