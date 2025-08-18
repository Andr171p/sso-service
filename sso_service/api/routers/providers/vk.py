from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status

from ....core.domain import TokenPair, VKCallback
from ....providers.vk import VKControl

vk_router = APIRouter(route_class=DishkaRoute, tags=["VK"])


@vk_router.get(path="/vk/link", status_code=status.HTTP_200_OK)
async def vk_generate_url(provider: Depends[VKControl]) -> str:
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
    provider: Depends[VKControl],
) -> TokenPair:
    return await provider.register(schema=schema, realm=realm)


@vk_router.post(
    "/{realm}/vk/authentication",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
)
async def vk_authentication(
    realm: str,
    schema: VKCallback,
    provider: Depends[VKControl],
) -> TokenPair:
    return await provider.authenticate(schema=schema, realm=realm)
