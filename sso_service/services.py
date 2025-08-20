from typing import Any

import logging
import time
from uuid import UUID

from pydantic import EmailStr

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
    async def introspect(self, token: str, realm: str) -> Token: ...


class UserTokenService:
    async def introspect(self, token: str, realm: str, session_id: UUID) -> UserClaims: ...

    async def refresh(self, token: str, realm: str, session_id: UUID) -> TokenPair: ...

    async def switch_realm(
            self, current_realm: str, target_realm: str, refresh_token: str, session_id: UUID | str
    ) -> TokenPair: ...
