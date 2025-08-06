from typing import Generic, TypeVar

from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel

from .domain import Tokens
from .dto import BaseTokenIntrospection

T = TypeVar("T", bound=BaseModel)
I = TypeVar("I", bound=BaseTokenIntrospection)


class BaseAuthService(ABC, Generic[I]):
    """Базовый класс для аутентификации,
    параметр T указывает на ресурс который нужно аутентифицировать.
    """

    @abstractmethod
    async def authenticate(self, *args) -> Tokens:
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
    async def introspect(self, token: str, **kwargs) -> I: pass


class BaseStore(Generic[T]):
    """Базовый класс хранилища данных,
    параметр T указывает на ресурс над которым нужно провести операции
    """
    async def add(self, schema: T) -> None: pass

    async def get(self, id: UUID | str) -> T | None: pass

    async def delete(self, id: UUID | str) -> bool: pass
