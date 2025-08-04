from typing import Annotated

import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, Form, HTTPException, status

from src.auth_service.core.constants import CLIENT_ACCESS_TOKEN_EXPIRE
from src.auth_service.core.enums import GrantType, TokenType
from src.auth_service.core.exceptions import (
    InvalidCredentialsError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
)
from src.auth_service.core.schemas import ClientPayload
from src.auth_service.security import create_token
from src.auth_service.services import ClientAuthService, ClientJWTService

from ...schemas import ClientToken

logger = logging.getLogger(__name__)

realms_router = APIRouter(prefix="/realms", tags=["Auth"], route_class=DishkaRoute)


@realms_router.post(
    path="/{realm_id}/token",
    status_code=status.HTTP_200_OK,
    response_model=ClientToken,
    summary="Выдаёт токен клиенту",
)
async def get_token(
        realm_id: UUID,
        grant_type: Annotated[GrantType, Form(...)],
        client_id: Annotated[str, Form(...)],
        client_secret: Annotated[str, Form(...)],
        scope: Annotated[str, Form(...)],
        service: Depends[ClientAuthService]
) -> ClientToken:
    if grant_type != GrantType.CLIENT_CREDENTIALS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type",
        )
    try:
        client = await service.authenticate(realm_id, client_id, client_secret, scope)
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
    access_token = create_token(
        payload=client.payload,
        token_type=TokenType.ACCESS,
        expires_delta=CLIENT_ACCESS_TOKEN_EXPIRE,
    )
    return ClientToken(access_token=access_token)


@realms_router.post(
    path="/{realm_id}/introspect",
    status_code=status.HTTP_200_OK,
    response_model=ClientPayload,
    response_model_exclude_none=True,
    summary="Производит валидацию токена",
)
async def introspect_token(
        realm_id: UUID,
        token: Annotated[str, Form(...)],
        service: Depends[ClientJWTService]
) -> ClientPayload:
    return await service.validate(token, realm_id=realm_id)
