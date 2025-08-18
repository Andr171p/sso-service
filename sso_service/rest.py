from aiohttp import ClientSession

from .core.base import BaseOauthAPI
from .core.domain import UserIdentity, VKGetData, YandexGetData
from .core.utils import valid_answer
from .settings import settings


class VKApi(BaseOauthAPI):
    async def get_access_token(self, schema: dict) -> VKGetData:
        async with (
            ClientSession() as session,
            session.post(url=settings.vk_settings.vk_token_url, json=schema, ssl=False) as data,
        ):
            result = await valid_answer(data)
            self.logger.warning(result)
            return VKGetData(access_token=result["access_token"], user_id=str(result["user_id"]))

    async def get_data(self, schema: dict) -> UserIdentity:
        async with (
            ClientSession() as session,
            session.post(url=settings.vk_settings.vk_api_url, json=schema, ssl=False) as data,
        ):
            self.logger.warning(data)
            result = (await valid_answer(response=data))["user"]
            return UserIdentity(
                provider_user_id=result["user_id"],
                email=result["email"].lower(),
            )


class YandexApi(BaseOauthAPI):
    async def get_access_token(self, schema: dict) -> YandexGetData:
        async with (
            ClientSession() as session,
            session.post(
                url=settings.yandex_settings.yandex_token_url, data=schema, ssl=False
            ) as data,
        ):
            result = await valid_answer(response=data)
            self.logger.warning(result)
            return YandexGetData(oauth_token=result["access_token"])

    async def get_data(self, schema: dict) -> UserIdentity:
        async with (
            ClientSession() as session,
            session.get(
                url=settings.yandex_settings.yandex_api_url, params=schema, ssl=False
            ) as data,
        ):
            result = await valid_answer(response=data)
            self.logger.warning(result)
            return UserIdentity(
                provider_user_id=result["id"],
                email=result["default_email"].lower(),
            )
