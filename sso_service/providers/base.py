from typing import Any

import time
from abc import ABC, abstractmethod

from ..core.base import BaseStore
from ..core.constants import SESSION_EXPIRE_IN
from ..core.domain import BaseCallback, IdentityProvider, Session, TokenPair, UserIdentity
from ..core.exceptions import NotEnabledError, NotRegisteredResourceError
from ..core.utils import expires_at
from ..database.repository import IdentityProviderRepository, UserRepository
from ..services import generate_token_pair, give_roles


class BaseOAuthProvider(ABC):
    """Базовый класс для реализации логики регистрации и аутентификации
    через OAuth2 и OIDC провайдеров.

    Для имплементации нового класса нужно наследоваться от BaseOAuthProvider
    и реализовать все необходимые методы.
    """
    provider_repository: IdentityProviderRepository
    user_repository: UserRepository
    session_store: BaseStore[Session]

    async def _get_provider(self) -> IdentityProvider:
        """Получает провайдера по его уникальному имени"""
        provider = await self.provider_repository.get_by_name(self.name)
        if provider is None:
            raise NotRegisteredResourceError("Provider not registered or not found")
        if not provider.enabled:
            raise NotEnabledError("Provider not enabled!")
        return provider

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя провайдера, например: 'VK', 'Google', ..."""
        raise NotImplementedError

    @abstractmethod
    async def _get_access_token(self) -> str:
        """Получает access token для отправки запросов к провайдеру"""
        raise NotImplementedError

    @abstractmethod
    async def get_userinfo(self, callback: BaseCallback) -> dict[str, Any]:
        """Получение информации о пользователе от провайдера"""
        raise NotImplementedError

    @abstractmethod
    async def _handle_callback(self, callback: BaseCallback) -> str:
        """Обрабатывает callback и возвращает access token"""
        raise NotImplementedError

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

    @abstractmethod
    async def authenticate(self, realm: str, callback: BaseCallback) -> TokenPair:
        """Реализует логику аутентификации пользователя.

        :param realm: Область в которой будет аутентифицирован пользователь.
        :param callback: Callback после авторизации пользователя на стороне провайдера.
        :return Пара токенов access и refresh.
        """
        raise NotImplementedError
