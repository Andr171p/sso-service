from typing import Any, Generic, TypeVar

from abc import ABC, abstractmethod
from datetime import timedelta
from uuid import UUID

from pydantic import BaseModel

from .domain import Claims, OAuthTokens

T = TypeVar("T", bound=BaseModel)
C = TypeVar("C", bound=Claims)


class BaseAuthService(ABC, Generic[T, C]):
    """Базовый класс для аутентификации.
    Параметр T указывает на модель данных токена,
    которую нужно вернуть при аутентификации.
    Параметр C указывает декодированную полезную нагрузку токена.
    """

    @abstractmethod
    async def authenticate(self, *args) -> T:
        """Метод для аутентификации ресурса.

        :param args: Необходимые аргументы для аутентификации.
        :exception InvalidCredentialsError: Неверные авторизационные данные.
        :exception UnauthorizedError: Несанкционированный доступ.
        :exception NotEnabledError: Ресурс не доступен.
        :exception PermissionDeniedError: Не достаточно прав.
        :return: JWT аутентифицированного клиента.
        """
        raise NotImplementedError

    @abstractmethod
    async def introspect(self, token: str, **kwargs) -> C:
        """Производит декодирование и валидацию токена.

        :param token: Выданный токен.
        :param kwargs: Дополнительные параметры для валидации токена.
        :return: Декодированная полезная нагрузка токена.
        """
        raise NotImplementedError


class BaseStore(Generic[T]):
    """Базовый класс хранилища данных,
    параметр T указывает на ресурс над которым нужно провести операции
    """

    async def add(self, schema: T) -> None: pass

    async def get(self, id: UUID | str) -> T | None: pass

    async def exists(self, id: UUID | str) -> bool: pass

    async def update(
            self, id: UUID | str, ttl: timedelta | None = None, **kwargs
    ) -> T | None: pass

    async def delete(self, id: UUID | str) -> bool: pass


class BaseIdentityProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя провайдера (например 'Google', 'VK', 'Yandex')"""
        raise NotImplementedError

    @property
    @abstractmethod
    def protocol(self) -> str:
        """Протокол для авторизации, который использует провайдер
        (например 'oauth2', 'openid', 'ldap')
        """

    async def register(self, *args, **kwargs) -> ...:
        """Регистрирует пользователя в системе после авторизации у провайдера

        P.S Пока *args **kwargs потому что хз, может Generic ебануть
        """
        raise NotImplementedError

    async def authenticate(self, *args, **kwargs) -> ...:
        """Аутентифицирует пользователя после авторизации у провайдера"""
        raise NotImplementedError


class BaseOAuthProvider(BaseIdentityProvider):
    @abstractmethod
    async def generate_authorization_url(self) -> str:
        """Генерирует URL для авторизации пользователя"""
        raise NotImplementedError

    @abstractmethod
    async def handle_callback(self, code: str, state: str) -> OAuthTokens:
        """Обрабатывает callback после аутентификации"""
        raise NotImplementedError

    async def userinfo(self, access_token: str) -> dict[str, Any]:
        """Получает информацию о пользователя от провайдера"""
        raise NotImplementedError
