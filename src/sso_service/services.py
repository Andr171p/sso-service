from typing import Any

from uuid import UUID

from pydantic import EmailStr

from .core.base import BaseAuthService
from .core.constants import (
    CLIENT_ACCESS_TOKEN_EXPIRE_IN,
    DEFAULT_ROLES,
    USER_ACCESS_TOKEN_EXPIRE_IN,
    USER_REFRESH_TOKEN_EXPIRE_IN,
    SESSION_EXPIRE_IN,
    SESSION_REFRESH_THRESHOLD,
    SESSION_REFRESH_IN,
)
from .core.domain import ClientClaims, Token, TokenPair, UserClaims, User, Session
from .core.enums import GrantType, TokenType
from .core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
    UnsupportedGrantTypeError,
)
from .core.utils import current_datetime, current_timestamp, format_scope
from .database.repository import ClientRepository, UserRepository, GroupRepository
from .security import decode_token, issue_token, verify_secret
from .storage import RedisSessionStore


class ClientAuthService(BaseAuthService[Token, ClientClaims]):
    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    async def authenticate(
            self,
            realm: str,
            grant_type: str,
            client_id: str,
            client_secret: str,
            scope: str
    ) -> Token:
        if grant_type != GrantType.CLIENT_CREDENTIALS:
            raise UnsupportedGrantTypeError("Unsupported grant type")
        client = await self.repository.get_by_client_id(realm, client_id)
        if client is None:
            raise UnauthorizedError("Client unauthorized in this realm")
        if not client.enabled:
            raise NotEnabledError("Client not enabled yet")
        if not verify_secret(client_secret, client.client_secret.get_secret_value()):
            raise InvalidCredentialsError("Client credentials invalid")
        valid_scopes = self._validate_scopes(format_scope(scope), client.scopes)
        if not valid_scopes:
            raise PermissionDeniedError("Client permission denied")
        access_token = issue_token(
            token_type=TokenType.ACCESS,
            payload=client.to_payload(realm=realm),
            expires_in=CLIENT_ACCESS_TOKEN_EXPIRE_IN,
        )
        return Token(
            access_token=access_token,
            expires_at=(
                    current_datetime() + CLIENT_ACCESS_TOKEN_EXPIRE_IN
            ).timestamp(),
        )

    @staticmethod
    def _validate_scopes(
            requested_scopes: list[str], client_scopes: list[str], strict_mode: bool = False
    ) -> list[str] | None:
        """Сверяет запрошенный права с разрешёнными.

        :param requested_scopes: Список запрашиваемых прав, например: ['api:read', 'api:write']
        :param client_scopes: Список разрешённых прав.
        :param strict_mode: Если True - все запрошенные права должны быть разрешены.
        Если False - то только пересечение.
        :return: Список валидных прав или None если проверка не пройдена.
        """
        valid_scopes: list[str] = [
            requested_scope
            for requested_scope in requested_scopes
            if requested_scope in client_scopes
        ]
        if strict_mode and set(requested_scopes) - set(valid_scopes):
            return None
        return valid_scopes or None

    async def introspect(self, token: str, **kwargs) -> ClientClaims:  # noqa: PLR6301
        realm = kwargs.get("realm")
        if not realm:
            raise ValueError("Realm is required")
        try:
            payload = decode_token(token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token") from None
        if payload.get("realm") is None or payload.get("realm") != realm:
            raise UnauthorizedError("Invalid token in this realm")
        if "exp" in payload and payload["exp"] < current_timestamp():
            return ClientClaims(active=False, cause="Token expired")
        return ClientClaims(active=True, **payload)


class UserAuthService(BaseAuthService[TokenPair, UserClaims]):
    def __init__(
            self,
            user_repository: UserRepository,
            group_repository: GroupRepository,
            session_store: RedisSessionStore
    ) -> None:
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.session_store = session_store

    async def register(self, user: User) -> None:
        await self.user_repository.create(user)
        # Some logic ...

    async def authenticate(
            self, realm: str, email: EmailStr, password: str
    ) -> TokenPair:
        user = await self.user_repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email")
        if not user.active:
            raise NotEnabledError("User is not active")
        if not verify_secret(password, user.password.get_secret_value()):
            raise InvalidCredentialsError("Invalid password")
        roles = await self._give_roles(realm, user.id)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(
            user_id=user.id,
            expires_at=(current_datetime() + SESSION_EXPIRE_IN).timestamp()
        )
        await self.session_store.add(session)
        return self._generate_token_pair(payload, session.session_id)

    async def _give_roles(self, realm: str, user_id: UUID) -> list[str]:
        """Возвращает список ролей пользователя в указанном realm.

        Получает все группы пользователя в realm и собирает их роли в единый список.
        Если пользователь не состоит ни в одной группе, возвращает роли по умолчанию.

        :param realm: Идентификатор realm (например: education, admission, ...)
        :param user_id: Уникальный идентификатор пользователя.
        :return Список ролей пользователя.
        """
        groups = await self.group_repository.get_by_user(realm, user_id)
        if not groups:
            return DEFAULT_ROLES
        roles: set[str] = {role for group in groups for role in group.roles}
        return list(roles)

    @staticmethod
    def _generate_token_pair(payload: dict[str, Any], session_id: UUID) -> TokenPair:
        """Генерирует пару JWT токенов (access и refresh)
        для аутентифицированного пользователя.

        :param payload: Полезная нагрузка для JWT
        :param session_id: Уникальный идентификатор сессии
        :return: Объект с access/refresh и прочими метаданными.
        """
        access_token = issue_token(
            token_type=TokenType.ACCESS,
            payload=payload,
            expires_in=USER_ACCESS_TOKEN_EXPIRE_IN
        )
        refresh_token = issue_token(
            token_type=TokenType.REFRESH,
            payload=payload,
            expires_in=USER_REFRESH_TOKEN_EXPIRE_IN
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            expires_at=(current_datetime() + USER_ACCESS_TOKEN_EXPIRE_IN).timestamp()
        )

    async def introspect(self, token: str, **kwargs) -> UserClaims:
        realm: str = kwargs.get("realm")
        session_id: UUID = kwargs.get("session_id")
        if not realm:
            raise ValueError("Realm is required")
        if await self.session_store.get(session_id) is None:
            raise UnauthorizedError("Session not found")
        try:
            payload = decode_token(token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token")
        if "token_type" in payload and payload["token_type"] != TokenType.ACCESS:
            return UserClaims(active=False, cause="Invalid token type")
        if "realm" not in payload or payload.get("realm") != realm:
            return UserClaims(active=False, cause="Invalid token in this realm")
        if "exp" in payload and payload["exp"] < current_timestamp():
            return UserClaims(active=False, cause="Token expired")
        return UserClaims(active=True, **payload)

    async def refresh(self, token: str, realm: str, session_id: UUID) -> TokenPair:
        session = await self.session_store.get(session_id)
        if session is None:
            raise UnauthorizedError("Session not found")
        try:
            payload = decode_token(token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token")
        if "token_type" in payload and payload["token_type"] != TokenType.REFRESH:
            raise UnauthorizedError("Invalid token type")
        if "realm" in payload and payload["realm"] != realm:
            raise UnauthorizedError("Invalid token in this realm")
        if "exp" in payload and payload["exp"] < current_timestamp():
            raise UnauthorizedError("Token expired")
        roles = await self._give_roles(realm, payload["sub"])
        payload["roles"] = roles
        session_delay = session.expires_at - current_timestamp()
        if session_delay < SESSION_REFRESH_THRESHOLD:
            await self.session_store.update(
                session_id, ttl=session_delay + SESSION_REFRESH_IN
            )
        return self._generate_token_pair(payload, session_id)
