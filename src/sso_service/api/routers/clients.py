from typing import Annotated

import logging

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status, Form, HTTPException

from ...core.domain import Token, ClientClaims
from ...core.enums import GrantType
from ...core.exceptions import (
    InvalidCredentialsError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
    UnsupportedGrantTypeError
)
from ...services import ClientAuthService

logger = logging.getLogger(__name__)

clients_router = APIRouter(prefix="/{realm}/clients", tags=["Clients auth"], route_class=DishkaRoute)


@clients_router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    response_model_exclude_none=True,
    summary="Выдаёт токен клиенту",
)
async def issue_token(
        realm: str,
        grant_type: Annotated[GrantType, Form(...)],
        client_id: Annotated[str, Form(...)],
        client_secret: Annotated[str, Form(...)],
        scope: Annotated[str, Form(...)],
        service: Depends[ClientAuthService]
) -> Token:
    try:
        token = await service.authenticate(
            realm=realm,
            grant_type=grant_type,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )
    except UnsupportedGrantTypeError as e:
        logger.exception(f"Unsupported grant type: %s", grant_type)
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


@clients_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=ClientClaims,
    response_model_exclude_none=True,
    summary="Декодирует и валидирует токен"
)
async def introspect_token(
        realm: str,
        token: Annotated[str, Form(...)],
        service: Depends[ClientAuthService]
) -> ClientClaims:
    try:
        return await service.introspect(token, realm=realm)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
