from typing import Any

from abc import ABC, abstractmethod
import time

from ..database.repository import IdentityProviderRepository, UserRepository
from ..core.base import BaseStore
from ..core.constants import SESSION_EXPIRE_IN
from ..core.domain import Session, IdentityProvider, BaseCallback, TokenPair, UserIdentity
from ..core.utils import expires_at
from ..services import generate_token_pair, give_roles


class BaseAuthProvider(ABC):
    provider_repository: IdentityProviderRepository
    user_repository: UserRepository
    session_store: BaseStore[Session]

    async def _get_provider(self) -> IdentityProvider:
        provider = await self.provider_repository.get_by_name(self.name)
        if provider is None:
            raise ...
        if not provider.enabled:
            raise ...
        return provider

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя провайдера"""
        raise NotImplementedError

    @abstractmethod
    async def _get_access_token(self) -> str:
        """Получает access token для отправки запросов к провайдеру"""
        raise NotImplementedError

    @abstractmethod
    async def get_userinfo(self, callback: BaseCallback) -> dict[str, Any]:
        """Получение информации о пользователе от провайдера"""
        raise NotImplementedError

    async def _handle_callback(self, callback: BaseCallback) -> str: ...

    async def register(self, realm: str, callback: BaseCallback) -> TokenPair:
        callback = await self._handle_callback(callback)
        userinfo = await self.get_userinfo(callback.model_dump())
        user = await self.user_repository.create_with_identity(UserIdentity(**userinfo))
        roles = await give_roles(realm, user.id, self.user_repository)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(user_id=user.id, expires_at=expires_at(SESSION_EXPIRE_IN))
        await self.session_store.add(
            str(session.session_id), session, ttl=int(session.expires_at - time.time())
        )
        return generate_token_pair(payload, session.session_id)

    async def authenticate(self, realm: str, callback: BaseCallback) -> TokenPair: ...
