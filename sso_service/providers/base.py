import time
from abc import ABC, abstractmethod
from logging import getLogger

from ..core.base import BaseStore, LoggerMixin
from ..core.constants import SESSION_EXPIRE_IN
from ..core.domain import BaseCallback, Codes, Session, TokenPair, UserIdentity
from ..core.exceptions import NotFoundHTTPError
from ..core.utils import expires_at
from ..database.repository import IdentityProviderRepository, UserRepository
from ..services import generate_token_pair, give_roles

CACHE_MAXSIZE = 128
PROVIDER_TTL = 60 * 60


class BaseProvider(LoggerMixin):
    logger = getLogger("provider")


class BaseOAuthProvider(ABC):
    """Базовый класс для реализации логики регистрации и аутентификации
    через OAuth2 и OIDC провайдеров.

    Для имплементации нового класса нужно наследоваться от BaseOAuthProvider
    и реализовать все необходимые методы.
    """

    def __init__(
        self,
        provider_repository: IdentityProviderRepository,
        user_repository: UserRepository,
        session_store: BaseStore[Session],
        codes_store: BaseStore[Codes],
    ) -> None:
        self.provider_repository = provider_repository
        self.user_repository = user_repository
        self.session_store = session_store
        self.codes_store = codes_store

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя провайдера, например: 'VK', 'Google', ..."""
        raise NotImplementedError

    @abstractmethod
    async def _get_access_token(self, params: dict) -> str:
        """Получает access token для отправки запросов к провайдеру"""
        raise NotImplementedError

    @abstractmethod
    async def _get_userinfo(self, *args) -> UserIdentity:
        """Получение информации о пользователе от провайдера"""
        raise NotImplementedError

    @abstractmethod
    async def _handle_callback(self, callback: BaseCallback) -> str:
        raise NotImplementedError

    async def register(self, realm: str, callback: BaseCallback) -> TokenPair:
        provider = await self.provider_repository.get_by_name(self.name)
        if provider is None:
            raise NotFoundHTTPError("Provider not found")
        access_token = await self._handle_callback(callback)
        userinfo = await self._get_userinfo(access_token)
        userinfo.provider_id = provider.id
        user = await self.user_repository.create_with_identity(userinfo)
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
