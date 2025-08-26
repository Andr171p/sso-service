from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, Response, status

from ....core.constants import SESSION_EXPIRE_IN
from ....core.domain import TokenPair, YandexCallback
from ....providers.yandex import YandexProvider

yandex_router = APIRouter(route_class=DishkaRoute, tags=["Yandex"])


@yandex_router.get(path="/yandex/link", status_code=status.HTTP_200_OK)
async def yandex_generate_url(provider: Depends[YandexProvider]) -> str:
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
    response: Response,
    provider: Depends[YandexProvider],
) -> TokenPair:
    token_pair = await provider.register(callback=schema, realm=realm)
    response.set_cookie(
        key="session_id",
        value=str(token_pair.session_id),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(SESSION_EXPIRE_IN.total_seconds()),
    )
    return token_pair


@yandex_router.post(
    "/{realm}/yandex/authentication",
    status_code=status.HTTP_200_OK,
    response_model=TokenPair,
    response_model_exclude={"session_id"},
)
async def yandex_authentication(
    realm: str,
    schema: YandexCallback,
    response: Response,
    provider: Depends[YandexProvider],
) -> TokenPair:
    token_pair = await provider.authenticate(callback=schema, realm=realm)
    response.set_cookie(
        key="session_id",
        value=str(token_pair.session_id),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(SESSION_EXPIRE_IN.total_seconds()),
    )
    return token_pair
