from typing import TypeVar

from abc import ABC, abstractmethod
from datetime import timedelta
from logging import DEBUG, Formatter, Logger, StreamHandler, getLogger
from uuid import UUID

from pydantic import BaseModel

from .constants import DEFAULT_TTL

T = TypeVar("T", bound=BaseModel)


class BaseStore[T: BaseModel](ABC):
    """Базовый класс для хранилища данных.

    Определяет интерфейс для системы хранения данных типа "ключ-значение"
    с поддержкой времени жизни (TTL) записей.

    Параметр типа T представляет тип хранимого ресурса.
    """

    @abstractmethod
    def _build_key(self, string: str | UUID) -> str:
        """Генерирует уникальный ключ для идентификации ресурсов в хранилище.
        Ключ должен быть уникальным и не допускать коллизий.

        :param string: Строка, которая может использоваться для составления ключа.
        :return Уникальный ключ объекта
        """
        raise NotImplementedError

    @abstractmethod
    async def add(
            self, key: str | UUID, schema: T, ttl: timedelta | int | None = DEFAULT_TTL
    ) -> None:
        """Добавляет объект в хранилище

        :param key: Уникальный ключ объекта.
        :param schema: Добавляемый объект.
        :param ttl: Время жизни объекта в хранилище.
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str | UUID) -> T | None:
        """Получает объект из хранилища по ключу.

        :param key: Уникальный ключ объекта.
        :return: Найденный объект или None если объекта не нашлось.
        """
        raise NotImplementedError

    async def pop(self, key: str | UUID) -> T | None:
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
    async def exists(self, key: str | UUID) -> bool:
        """Проверяет наличие объекта в хранилище по его ключу.

        :param key: Уникальный ключ
        :return: True если объект существует, False если нет.
        """
        raise NotImplementedError

    @abstractmethod
    async def refresh_ttl(self, key: str | UUID, ttl: timedelta) -> T | None:
        """Обновляет время жизни (TTL) для существующего объекта.

        :param key: Ключ объекта.
        :param ttl: Новое время жизни объекта.
        :return: Обновленный объект или None, если объект не найден.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str | UUID) -> bool:
        """Удаляет объект из хранилища по ключу.

        :param key: Ключ объекта.
        :return: True если объект успешно удалён, False если нет.
        """
        raise NotImplementedError


class LoggerMixin:
    logger: Logger = getLogger()

    @staticmethod
    def config_logging(logger: Logger) -> Logger:
        if not logger.handlers:
            handler = StreamHandler()
            formatter = Formatter(
                fmt="%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s",  # noqa: E501
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(DEBUG)
        return logger

    def __new__(cls, *_, **__):
        obj = super().__new__(cls)
        obj.logger = cls.logger.getChild(f"{cls.__name__}")
        cls.config_logging(obj.logger)
        return obj
