from typing import Any

from uuid import UUID

from pydantic import EmailStr

from .core.base import BaseAuthService
from .core.constants import CLIENT_ACCESS_TOKEN_EXPIRE_IN
from .core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
    UnsupportedGrantTypeError,
)
from .core.domain import Token, ClientClaims, TokenPair, UserClaims
from .core.enums import TokenType, GrantType
from .core.utils import format_scope, current_timestamp, current_datetime
from .database.repository import ClientRepository, UserRepository
from .security import verify_secret, issue_token, decode_token
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

    async def introspect(self, token: str, **kwargs) -> ClientClaims:
        realm = kwargs.get("realm")
        if not realm:
            raise ValueError("Realm is required")
        try:
            payload = decode_token(token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token")
        if payload.get("realm") is None and payload.get("realm") != realm:
            raise UnauthorizedError("Invalid token in this realm")
        claims: dict[str, Any] = {}
        if "exp" in payload and payload["exp"] < current_timestamp():
            claims.update({
                "active": False, "cause": "Token expired"
            })
        claims.update(payload, active=True)
        return ClientClaims(**claims)


class UserAuthService(BaseAuthService[TokenPair, UserClaims]):
    def __init__(
            self, repository: UserRepository, session_store: RedisSessionStore
    ) -> None:
        self.repository = repository
        self.session_store = session_store

    async def authenticate(
            self, realm_id: UUID, email: EmailStr, password: str
    ) -> TokenPair:
        user = await self.repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email")
        if not user.active:
            raise NotEnabledError("User is not active")
        if not verify_secret(password, user.password.get_secret_value()):
            raise InvalidCredentialsError("Invalid password")
        return TokenPair()

    async def introspect(self, token: str, **kwargs) -> UserClaims:
        session_id: UUID = kwargs.get("session_id")
        return UserClaims()

    async def refresh(self, token: str) -> TokenPair:
        ...
