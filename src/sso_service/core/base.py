from typing import Generic, TypeVar

from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel

from .domain import Claims

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

    async def delete(self, id: UUID | str) -> bool: pass
