from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, Response, status

from ....core.constants import SESSION_EXPIRE_IN
from ....core.domain import TokenPair, VKCallback
from ....providers.vk import VKProvider

vk_router = APIRouter(route_class=DishkaRoute, tags=["VK"])


@vk_router.get(path="/vk/link", status_code=status.HTTP_200_OK)
async def vk_generate_url(provider: Depends[VKProvider]) -> str:
    return await provider.generate_url()


@vk_router.post(
    path="/{realm}/vk/registration",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
)
async def vk_registration(
    realm: str,
    schema: VKCallback,
    response: Response,
    provider: Depends[VKProvider],
) -> TokenPair:
    token_pair = await provider.register(callback=schema, realm=realm)
    response.set_cookie(
        key="session_id",
        value=str(token_pair.session_id),
        httponly=False,
        secure=False,
        samesite="lax",
        max_age=int(SESSION_EXPIRE_IN.total_seconds()),
    )
    return token_pair


@vk_router.post(
    "/{realm}/vk/authentication",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
)
async def vk_authentication(
    realm: str,
    schema: VKCallback,
    response: Response,
    provider: Depends[VKProvider],
) -> TokenPair:
    token_pair = await provider.authenticate(callback=schema, realm=realm)
    response.set_cookie(
        key="session_id",
        value=str(token_pair.session_id),
        httponly=False,
        secure=False,
        samesite="lax",
        max_age=int(SESSION_EXPIRE_IN.total_seconds()),
    )
    return token_pair
