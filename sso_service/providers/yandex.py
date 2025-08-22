import time

from aiohttp import ClientSession

from ..core.base import BaseStore
from ..core.constants import PATH_YANDEX, SESSION_EXPIRE_IN
from ..core.domain import BaseCallback, Codes, Session, TokenPair, UserIdentity, YandexRedirect
from ..core.exceptions import BadRequestHTTPError
from ..core.utils import expires_at, valid_answer
from ..database.repository import (
    IdentityProviderRepository,
    UserRepository,
)
from ..services import generate_token_pair, give_roles
from .base import BaseOAuthProvider, BaseProvider


class YandexProvider(BaseOAuthProvider, BaseProvider):
    @property
    def name(self) -> str:
        return "Yandex"

    def __init__(
        self,
        provider_repository: IdentityProviderRepository,
        user_repository: UserRepository,
        codes_store: BaseStore[Codes],
        session_store: BaseStore[Session],
    ) -> None:
        super().__init__(
            provider_repository=provider_repository,
            user_repository=user_repository,
            session_store=session_store,
            codes_store=codes_store,
        )

    async def _get_access_token(self, params: dict) -> str:
        async with (
            ClientSession() as session,
            session.post(url=f"{PATH_YANDEX}token", data=params, ssl=False) as data,
        ):
            self.logger.warning(data)
            result = await valid_answer(data)
            return result["access_token"]

    async def _get_userinfo(self, access_token: str) -> UserIdentity:
        async with (
            ClientSession() as session,
            session.get(
                url="https://login.yandex.ru/info",
                params={"oauth_token": access_token, "format": "json"},
                ssl=False,
            ) as data,
        ):
            self.logger.warning(data)
            result = await valid_answer(response=data)
            return UserIdentity(
                provider_user_id=result["id"],
                email=result["default_email"].lower(),
            )

    async def generate_url(self) -> str:
        codes = Codes.generate()
        await self.codes_store.add(key=codes.state, ttl=200, schema=codes)
        return YandexRedirect().to_url(state=codes.state, code_challenge=codes.code_challenge)

    async def _handle_callback(self, callback: BaseCallback) -> str:
        codes = await self.codes_store.pop(callback.state)
        if codes is None:
            raise BadRequestHTTPError
        return await self._get_access_token(
            params=callback.to_dict(code_verifier=codes.code_verifier)
        )

    async def authenticate(self, realm: str, callback: BaseCallback) -> TokenPair:
        access_token = await self._handle_callback(callback)
        userinfo = await self._get_userinfo(access_token)
        user = await self.user_repository.get_by_provider(userinfo.provider_user_id)
        if user is None:
            raise BadRequestHTTPError("User not found")
        roles = await give_roles(realm, user.id, self.user_repository)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(user_id=user.id, expires_at=expires_at(SESSION_EXPIRE_IN))
        await self.session_store.add(
            str(session.session_id), session, ttl=int(session.expires_at - time.time())
        )
        return generate_token_pair(payload, session.session_id)
