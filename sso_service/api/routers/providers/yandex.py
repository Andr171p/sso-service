from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, status

from ....core.domain import TokenPair, YandexCallback
from ....providers.yandex import YandexControl

yandex_router = APIRouter(route_class=DishkaRoute)


@yandex_router.get(path="/yandex/link", status_code=status.HTTP_200_OK)
async def yandex_generate_url(provider: Depends[YandexControl]) -> str:
    return await provider.generate_url()


@yandex_router.post(
    path="/{realm}/yandex/registration",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
)
async def yandex_registration(
    realm: str,
    schema: YandexCallback,
    provider: Depends[YandexControl],
) -> TokenPair:
    return await provider.register(schema=schema, realm=realm)


@yandex_router.post(
    "/{realm}/yandex/authentication",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
)
async def yandex_authentication(
    realm: str,
    schema: YandexCallback,
    provider: Depends[YandexControl],
) -> TokenPair:
    return await provider.authenticate(schema=schema, realm=realm)
