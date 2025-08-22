from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status

from ...core.domain import ClientClaims, Token
from ...providers import ClientCredentialsProvider
from ...services import ClientTokenService
from ..schemas import ClientCredentials, TokenIntrospect

oauth_router = APIRouter(prefix="/{realm}/oauth", tags=["OAuth"], route_class=DishkaRoute)


@oauth_router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    response_model_exclude_none=True,
    summary="Выдаёт токен клиенту",
)
async def issue_token(
    realm: str, credentials: ClientCredentials, provider: Depends[ClientCredentialsProvider]
) -> Token:
    return await provider.authenticate(
        realm=realm,
        grant_type=credentials.grant_type,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scope=credentials.scope,
    )


@oauth_router.post(
    path="/introspect",
    status_code=status.HTTP_200_OK,
    response_model=ClientClaims,
    response_model_exclude_none=True,
    summary="Декодирует и валидирует токен",
)
async def introspect_token(
    realm: str, token: TokenIntrospect, service: Depends[ClientTokenService]
) -> ClientClaims:
    return await service.introspect(token.token, realm=realm)
