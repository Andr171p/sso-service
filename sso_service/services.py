from typing import Any

import logging
from uuid import UUID

from .core.base import BaseStore
from .core.constants import (
    DEFAULT_ROLES,
    SESSION_REFRESH_IN,
    SESSION_REFRESH_THRESHOLD,
    USER_ACCESS_TOKEN_EXPIRE_IN,
    USER_REFRESH_TOKEN_EXPIRE_IN,
)
from .core.domain import ClientClaims, Session, TokenPair, UserClaims
from .core.enums import TokenType, UserStatus
from .core.exceptions import (
    InvalidTokenError,
    PermissionDeniedError,
    UnauthorizedError,
)
from .core.utils import current_timestamp, expires_at
from .database.repository import RealmRepository, UserRepository
from .security import decode_token, issue_token

logger = logging.getLogger(__name__)


def generate_token_pair(payload: dict[str, Any], session_id: UUID) -> TokenPair:
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


async def give_roles(
        realm: str,
        user_id: UUID,
        user_repository: UserRepository
) -> list[str]:
    """Возвращает список ролей пользователя в указанном realm.

    Получает все группы пользователя в realm и собирает их роли в единый список.
    Если пользователь не состоит ни в одной группе, возвращает роли по умолчанию.

    :param realm: Идентификатор realm (например: education, admission, ...)
    :param user_id: Уникальный идентификатор пользователя.
    :param user_repository: Репозиторий для работы с пользователями.
    :return Список ролей пользователя.
    """
    groups = await user_repository.get_groups(realm, user_id)
    if not groups:
        return DEFAULT_ROLES
    roles: set[str] = {role for group in groups for role in group.roles}
    return list(roles)


class ClientTokenService:
    @staticmethod
    async def introspect(token: str, realm: str) -> ClientClaims:
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


class UserTokenService:
    def __init__(
            self,
            user_repository: UserRepository,
            realm_repository: RealmRepository,
            session_store: BaseStore[Session]
    ) -> None:
        self.user_repository = user_repository
        self.realm_repository = realm_repository
        self.session_store = session_store

    async def introspect(self, token: str, realm: str, session_id: UUID) -> UserClaims:
        if not realm:
            raise ValueError("Realm is required")
        if not await self.session_store.exists(session_id) or session_id is None:
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
        session = await self.session_store.get(session_id)
        if session is None:
            raise UnauthorizedError("Session not found or expired")
        claims = await self.introspect(token, realm=realm, session_id=session_id)
        if not claims.active:
            raise UnauthorizedError(claims.cause)
        roles = await give_roles(realm, UUID(claims.sub))
        claims.roles = roles
        session_delay = session.expires_at - current_timestamp()
        if session_delay < SESSION_REFRESH_THRESHOLD.total_seconds():
            await self.session_store.refresh_ttl(
                session_id, ttl=session_delay + SESSION_REFRESH_IN
            )
        return generate_token_pair(claims.model_dump(exclude_none=True), session_id)

    async def switch_realm(
            self, current_realm: str, target_realm: str, refresh_token: str, session_id: UUID | str
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
        claims = await self.introspect(refresh_token, realm=current_realm, session_id=session_id)
        if not claims.active:
            raise UnauthorizedError(claims.cause)
        if not await self._can_switch_realm(target_realm):
            raise PermissionDeniedError("Realm switching not allowed")
        user_id = UUID(claims.sub)
        roles = await give_roles(target_realm, user_id)
        user = await self.user_repository.read(user_id)
        if user.status == UserStatus.BANNED:
            raise PermissionDeniedError("User is banned")
        payload = user.to_payload(realm=target_realm, roles=roles)
        return generate_token_pair(payload, session_id)

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
