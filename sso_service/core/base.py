from typing import TYPE_CHECKING, Generic, TypeVar

from abc import ABC, abstractmethod
from datetime import timedelta
from logging import DEBUG, Formatter, Logger, StreamHandler, getLogger
from uuid import UUID

from pydantic import BaseModel

from .constants import SESSION_EXPIRE_IN
from .domain import BaseCallback, Claims, Session, TokenPair, User, UserIdentity
from .enums import UserStatus
from .exceptions import NotFoundHTTPError
from .utils import expires_at

if TYPE_CHECKING:
    from ..database.repository import (
        IdentityProviderRepository,
        UserIdentityRepository,
        UserRepository,
    )
    from ..services import UserAuthService
    from ..storage import RedisStorage

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

    async def add(self, schema: T) -> None:
        pass

    async def get(self, id: UUID | str) -> T | None:
        pass

    async def exists(self, id: UUID | str) -> bool:
        pass

    async def update(self, id: UUID | str, ttl: timedelta | None = None, **kwargs) -> T | None:
        pass

    async def delete(self, id: UUID | str) -> bool:
        pass


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


class BaseOauthAPI(LoggerMixin, ABC):
    logger = getLogger("rest")

    @abstractmethod
    async def get_access_token(self, schema: dict) -> BaseModel: ...

    @abstractmethod
    async def get_data(self, schema: dict) -> UserIdentity: ...


class BaseIdentityProvider(ABC):
    name: str

    async def register(self, realm: str, *args, **kwargs) -> TokenPair:
        """Регистрирует пользователя в системе после авторизации у провайдера

        P.S Пока *args **kwargs потому что хз, может Generic ебануть
        """
        raise NotImplementedError

    async def authenticate(self, realm: str, *args, **kwargs) -> TokenPair:
        """Аутентифицирует пользователя после авторизации у провайдера"""
        raise NotImplementedError


class BaseOAuthProvider(BaseIdentityProvider):
    def __init__(
        self,
        user_auth_service: "UserAuthService",
        user_repository: "UserRepository",
        user_identity_repository: "UserIdentityRepository",
        identity_repository: "IdentityProviderRepository",
        redis: "RedisStorage",
        api: BaseOauthAPI,
    ) -> None:
        self.user_auth_service = user_auth_service
        self.user_repository = user_repository
        self.user_identity_repository = user_identity_repository
        self.identity_repository = identity_repository
        self.redis = redis
        self.api = api

    @abstractmethod
    async def generate_url(self) -> str: ...

    async def callback(self, schema: BaseCallback) -> BaseModel:
        code_verifier = await self.redis.get_by_state(schema.state)
        print(code_verifier)
        return await self.api.get_access_token(schema.to_dict(code_verifier=code_verifier))

    async def register(self, realm: str, schema: BaseCallback) -> TokenPair:
        handle_callback = await self.callback(schema)
        provider_id = await self.identity_repository.get_by_name(self.name)
        user_data = await self.api.get_data(handle_callback.model_dump())
        if provider_id is None:
            raise NotFoundHTTPError("Provider not found")
        user = await self.user_repository.create(
            User(email=user_data.email, status=UserStatus.ACTIVE)
        )
        user_data.provider_id = provider_id
        user_data.user_id = user.id
        await self.user_identity_repository.create(user_data)
        roles = await self.user_auth_service._give_roles(realm, user.id)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(user_id=user.id, expires_at=expires_at(SESSION_EXPIRE_IN))
        await self.user_auth_service.session_store.add(session)
        return self.user_auth_service._generate_token_pair(payload, session.session_id)
