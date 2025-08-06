from typing import Annotated

import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, Form, HTTPException, status

from src.auth_service.core.dto import ClientTokenIntrospection
from src.auth_service.core.enums import GrantType
from src.auth_service.core.exceptions import (
    InvalidCredentialsError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
)
from src.auth_service.core.domain import Tokens
from src.auth_service.services import ClientAuthService

logger = logging.getLogger(__name__)

clients_router = APIRouter(prefix="/clients", tags=["Clients"], route_class=DishkaRoute)


@clients_router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    response_model=Tokens,
    response_model_exclude_none=True,
    summary="Выдаёт токен клиенту",
)
async def get_token(
        realm_id: Annotated[UUID, Form(...)],
        grant_type: Annotated[GrantType, Form(...)],
        client_id: Annotated[str, Form(...)],
        client_secret: Annotated[str, Form(...)],
        scope: Annotated[str, Form(...)],
        service: Depends[ClientAuthService]
) -> Tokens:
    if grant_type != GrantType.CLIENT_CREDENTIALS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type",
        )
    try:
        tokens = await service.authenticate(realm_id, client_id, client_secret, scope)
    except InvalidCredentialsError:
        logger.exception("Invalid credentials: {e}")
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
        return tokens


@clients_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=ClientTokenIntrospection,
    response_model_exclude_none=True,
    summary="Производит интроспекцию токена",
)
async def introspect_token(
        token: Annotated[str, Form(...)], service: Depends[ClientAuthService]
) -> ClientTokenIntrospection:
    try:
        return await service.introspect_token(token)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
