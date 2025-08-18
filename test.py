from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sso_service.database.repository import GroupRepository

import asyncio
from abc import ABC, abstractmethod
from functools import singledispatch
from uuid import UUID

from sso_service.core.base import BaseStore
from sso_service.core.domain import BaseCallback, Session, TokenPair, User, UserClaims, YandexCallback
from sso_service.core.constants import (
    DEFAULT_ROLES,
    USER_ACCESS_TOKEN_EXPIRE_IN,
    USER_REFRESH_TOKEN_EXPIRE_IN,
)
from sso_service.core.enums import TokenType
from sso_service.core.exceptions import UnauthorizedError, InvalidTokenError
from sso_service.core.utils import expires_at, current_timestamp
from sso_service.security import decode_token, issue_token


class BaseUserAuth(ABC):
    group_repository: GroupRepository
    session_store: BaseStore[Session]

    @singledispatch
    async def register(self, *args) -> User | TokenPair:
        raise NotImplementedError

    @register.register
    async def _(self, user: User) -> User:
        raise NotImplementedError

    @register.register
    async def _(self, realm: str, callback: BaseCallback) -> TokenPair:
        raise NotImplementedError

    @abstractmethod
    async def authenticate(self, realm: str, *args, **kwargs) -> TokenPair:
        raise NotImplementedError

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

    async def _give_roles(self, realm: str, user_id: UUID) -> list[str]:
        groups = await self.group_repository.get_by_user(realm, user_id)
        if not groups:
            return DEFAULT_ROLES
        roles: set[str] = {role for group in groups for role in group.roles}
        return list(roles)

    @staticmethod
    async def _generate_token_pair(
            payload: dict[str, Any], session_id: UUID
    ) -> TokenPair:
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


class BaseClientAuth(ABC):
    @abstractmethod
    async def authenticate(self, ) -> ...: ...

    @abstractmethod
    async def introspect(self, token: str, **kwargs) -> ...: ...


class TestUserAuth(BaseUserAuth):
    '''async def register(self, user: User) -> User:
        print(user)
        return ...'''

    async def register(self, realm: str, callback: YandexCallback) -> TokenPair:
        print(realm, callback)
        return ...

    async def authenticate(self, realm: str, *args, **kwargs) -> TokenPair:
        print(realm)
        return ...


auth = TestUserAuth()

user = User(email="andrey.kosov.05@inbox.ru")

asyncio.run(auth.register(realm="education", callback=YandexCallback(code="123", state="123")))
