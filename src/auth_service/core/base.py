from typing import Any, Generic, TypeVar

from abc import ABC, abstractmethod

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseAuthService(Generic[T]):
    """Базовый класс для аутентификации,
    параметр T указывает на ресурс который нужно аутентифицировать.
    """

    @abstractmethod
    async def authenticate(self, *args) -> T:
        """Метод для аутентификации ресурса.

        :param args: Необходимые аргументы для аутентификации.
        :exception InvalidCredentialsError: Неверные авторизационные данные.
        :exception UnauthorizedError: Несанкционированный доступ.
        :exception NotEnabledError: Ресурс не доступен.
        :exception PermissionDeniedError: Не достаточно прав.
        :return: T аутентифицированный клиент.
        """
        raise NotImplementedError


class BaseJWTService(ABC):
    @abstractmethod
    async def is_revoked(self, jti: str) -> bool:
        """Проверяет отозван ли токен по его уникальному id"""
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, token: str, **kwargs) -> bool:
        """Отзывает токен"""
        raise NotImplementedError

    @abstractmethod
    async def validate(self, token: str, **kwargs) -> dict[str, Any]:
        """Валидирует токен, включая проверку отзыва"""
        raise NotImplementedError
