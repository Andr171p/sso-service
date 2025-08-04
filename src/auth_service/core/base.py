from typing import Generic, TypeVar

from abc import abstractmethod
from uuid import UUID

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


class BaseStore(Generic[T]):
    """Базовый класс хранилища данных,
    параметр T указывает на ресурс над которым нужно провести операции
    """
    async def add(self, schema: T) -> None: pass

    async def get(self, id: UUID | str) -> T | None: pass

    async def delete(self, id: UUID | str) -> bool: pass
