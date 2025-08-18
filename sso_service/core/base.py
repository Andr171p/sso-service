from typing import Any, Generic, TypeVar

from abc import ABC, abstractmethod
from datetime import timedelta
from uuid import UUID

from pydantic import BaseModel

from .constants import DEFAULT_TTL
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


class BaseStore(Generic[T], ABC):
    """Базовый класс для хранилища данных.

    Определяет интерфейс для системы хранения данных типа "ключ-значение"
    с поддержкой времени жизни (TTL) записей.

    Параметр типа T представляет тип хранимого ресурса.
    """

    @abstractmethod
    def build_key(self, string: str | UUID | None) -> str:
        """Генерирует уникальный ключ для идентификации ресурсов в хранилище.
        Ключ должен быть уникальным и не допускать коллизий.

        :param string: Строка, которая может использоваться для составления ключа.
        :return Уникальный ключ объекта
        """
        raise NotImplementedError

    @abstractmethod
    async def add(
            self, key: str, schema: T, ttl: timedelta | int | None = DEFAULT_TTL
    ) -> None:
        """Добавляет объект в хранилище

        :param key: Уникальный ключ объекта.
        :param schema: Добавляемый объект.
        :param ttl: Время жизни объекта в хранилище.
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> T | None:
        """Получает объект из хранилища по ключу.

        :param key: Уникальный ключ объекта.
        :return: Найденный объект или None если объекта не нашлось.
        """
        raise NotImplementedError

    async def pop(self, key: str) -> T | None:
        """Извлекает и удаляет объект из хранилища по ключу.

        :param key: Уникальный ключ ресурса.
        :return: Возвращает объект если он был найден.
        """
        schema = await self.get(key)
        if schema is None:
            return None
        await self.delete(key)
        return schema

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Проверяет наличие объекта в хранилище по его ключу.

        :param key: Уникальный ключ
        :return: True если объект существует, False если нет.
        """
        raise NotImplementedError

    @abstractmethod
    async def refresh_ttl(self, key: str, ttl: timedelta) -> T | None:
        """Обновляет время жизни (TTL) для существующего объекта.

        :param key: Ключ объекта.
        :param ttl: Новое время жизни объекта.
        :return: Обновленный объект или None, если объект не найден.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удаляет объект из хранилища по ключу.

        :param key: Ключ объекта.
        :return: True если объект успешно удалён, False если нет.
        """
        raise NotImplementedError


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
