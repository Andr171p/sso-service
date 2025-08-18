from time import time

from ..core.base import BaseOAuthProvider, BaseStore
from ..core.constants import SESSION_EXPIRE_IN
from ..core.domain import Codes, Session, TokenPair, YandexCallback, YandexRedirect
from ..core.exceptions import BadRequestHTTPError
from ..core.utils import expires_at
from ..database.repository import (
    IdentityProviderRepository,
    UserIdentityRepository,
    UserRepository,
)
from ..rest import YandexApi
from ..services import UserAuthService


class YandexControl(BaseOAuthProvider):
    name = "Yandex"

    def __init__(
        self,
        user_auth_service: UserAuthService,
        user_repository: UserRepository,
        user_identity_repository: UserIdentityRepository,
        identity_repository: IdentityProviderRepository,
        session_store: BaseStore[Session],
        codes_store: BaseStore[Codes],
        api: YandexApi,
    ) -> None:
        super().__init__(
            user_auth_service=user_auth_service,
            user_repository=user_repository,
            user_identity_repository=user_identity_repository,
            identity_repository=identity_repository,
            session_store=session_store,
            codes_store=codes_store,
            api=api,
        )

    async def generate_url(self) -> str:
        codes = Codes.generate()
        key = self.codes_store.build_key(codes.state)
        await self.codes_store.add(key, codes, ttl=200)
        return YandexRedirect().to_url(state=codes.state, code_challenge=codes.code_challenge)

    async def authenticate(self, realm: str, schema: YandexCallback) -> TokenPair:
        data = await self.callback(schema)
        user_data = await self.api.get_data(data.model_dump())
        user = await self.user_repository.get_by_provider(user_data.provider_user_id)  # type: ignore  # noqa: PGH003
        if user is None:
            raise BadRequestHTTPError("User not found")
        roles = await self.user_auth_service._give_roles(realm, user.id)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(user_id=user.id, expires_at=expires_at(SESSION_EXPIRE_IN))
        key = self.session_store.build_key(session.session_id)
        await self.session_store.add(key, session, ttl=int(session.expires_at - time.time()))
        return self.user_auth_service._generate_token_pair(payload, session.session_id)
