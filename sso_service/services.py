from typing import Any

import time
import logging
from uuid import UUID

from pydantic import EmailStr

from .core.base import BaseAuthService
from .core.constants import (
    CLIENT_ACCESS_TOKEN_EXPIRE_IN,
    DEFAULT_ROLES,
    SESSION_EXPIRE_IN,
    SESSION_REFRESH_IN,
    SESSION_REFRESH_THRESHOLD,
    USER_ACCESS_TOKEN_EXPIRE_IN,
    USER_REFRESH_TOKEN_EXPIRE_IN,
)
from .core.domain import ClientClaims, Session, Token, TokenPair, User, UserClaims
from .core.enums import GrantType, TokenType, UserStatus
from .core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
    UnsupportedGrantTypeError,
)
from .core.utils import current_timestamp, expires_at, format_scope
from .database.repository import ClientRepository, GroupRepository, RealmRepository, UserRepository
from .security import decode_token, issue_token, verify_secret
from .storage import BaseStore

logger = logging.getLogger(__name__)


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
            expires_at=expires_at(CLIENT_ACCESS_TOKEN_EXPIRE_IN)
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
            realm_repository: RealmRepository,
            session_store: BaseStore[Session]
    ) -> None:
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.realm_repository = realm_repository
        self.session_store = session_store

    async def register(self, user: User) -> User:
        return await self.user_repository.create(user)

    async def authenticate(
            self, realm: str, email: EmailStr, password: str
    ) -> TokenPair:
        user = await self.user_repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email")
        if user.status == UserStatus.BANNED:
            raise NotEnabledError("User is banned")
        if not verify_secret(password, user.password.get_secret_value()):
            raise InvalidCredentialsError("Invalid password")
        roles = await self._give_roles(realm, user.id)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(
            user_id=user.id,
            expires_at=expires_at(SESSION_EXPIRE_IN)
        )
        key = self.session_store.build_key(session.session_id)
        await self.session_store.add(
            key, session, ttl=int(session.expires_at - time.time())
        )
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
            expires_at=expires_at(USER_ACCESS_TOKEN_EXPIRE_IN)
        )

    async def introspect(self, token: str, **kwargs) -> UserClaims:
        realm: str = kwargs.get("realm")
        session_id: UUID = kwargs.get("session_id")
        if not realm:
            raise ValueError("Realm is required")
        key = self.session_store.build_key(session_id)
        if not await self.session_store.exists(key) or session_id is None:
            raise UnauthorizedError("Session not found")
        try:
            payload = decode_token(token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token") from None
        if "realm" not in payload or payload.get("realm") != realm:
            return UserClaims(active=False, cause="Invalid token in this realm")
        if "exp" in payload and payload["exp"] < current_timestamp():
            return UserClaims(active=False, cause="Token expired")
        return UserClaims(**{"active": True, **payload})

    async def refresh(self, token: str, realm: str, session_id: UUID) -> TokenPair:
        """Выдаёт новую пару токенов access и refresh,
        продлевает пользовательскую сессию.

        :param token: Refresh токен пользователя.
        :param realm: Текущая область в которой находится пользователь.
        :param session_id: Текущая сессия пользователя.
        :return: Новая пара токенов access и refresh.
        """
        key = self.session_store.build_key(session_id)
        session = await self.session_store.get(key)
        if session is None:
            raise UnauthorizedError("Session not found or expired")
        claims = await self.introspect(token, realm=realm, session_id=session_id)
        if not claims.active:
            raise UnauthorizedError(claims.cause)
        roles = await self._give_roles(realm, UUID(claims.sub))
        claims.roles = roles
        session_delay = session.expires_at - current_timestamp()
        if session_delay < SESSION_REFRESH_THRESHOLD.total_seconds():
            await self.session_store.refresh_ttl(
                key, ttl=session_delay + SESSION_REFRESH_IN
            )
        return self._generate_token_pair(
            claims.model_dump(exclude_none=True), session_id
        )

    async def switch_realm(
            self,
            current_realm: str,
            target_realm: str,
            refresh_token: str,
            session_id: UUID | str
    ) -> TokenPair:
        """Осуществляет переход пользователя из одного realm в другой
        без повторной аутентификации.

        :param current_realm: Текущий realm в котором находится пользователь.
        :param target_realm: Realm в который нужно перейти.
        :param refresh_token: Refresh токен пользователя.
        :param session_id: Текущая сессия.
        :return: Новая парата токенов access и refresh.
        """
        if current_realm == target_realm:
            raise ValueError("Realms must be different!")
        session = await self.session_store.get(session_id)
        if not session:
            raise UnauthorizedError("Invalid session or session expired")
        claims = await self.introspect(
            refresh_token, realm=current_realm, session_id=session_id
        )
        if not claims.active:
            raise UnauthorizedError(claims.cause)
        if not await self._can_switch_realm(target_realm):
            raise PermissionDeniedError("Realm switching not allowed")
        user_id = UUID(claims.sub)
        roles = await self._give_roles(target_realm, user_id)
        user = await self.user_repository.read(user_id)
        if user.status == UserStatus.BANNED:
            raise PermissionDeniedError("User is banned")
        payload = user.to_payload(realm=target_realm, roles=roles)
        return self._generate_token_pair(payload, session_id)

    async def _can_switch_realm(self, target_realm: str) -> bool:
        """Проверяет возможность перехода в realm.

        :param target_realm: Realm в который нужно перейти.
        :return: True если такая возможность есть, False если нет.
        """
        realm = await self.realm_repository.get_by_slug(target_realm)
        if not realm:
            logger.warning("Realm doesn't exists!")
            return False
        if not realm.enabled:
            logger.warning("Realm is not enabled for switching!")
            return False
        return True
