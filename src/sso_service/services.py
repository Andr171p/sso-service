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
)
from .core.domain import Tokens
from .core.dto import ClientTokenIntrospection
from .core.enums import TokenType
from .core.utils import format_scope, current_timestamp
from .database.repository import ClientRepository, UserRepository
from .security import verify_secret, issue_token, decode_token
from .storage import RedisSessionStore


class ClientAuthService(BaseAuthService[ClientTokenIntrospection]):
    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    async def authenticate(
            self, realm_id: UUID, client_id: str, client_secret: str, scope: str
    ) -> Tokens:
        scopes = format_scope(scope)
        client = await self.repository.get_by_client_id(realm_id, client_id)
        if client is None:
            raise UnauthorizedError("Client unauthorized in this realm")
        if not client.enabled:
            raise NotEnabledError("Client not enabled yet")
        if verify_secret(client_secret, client.client_secret.get_secret_value()):
            raise InvalidCredentialsError("Client credentials invalid")
        valid_scopes = self._validate_scopes(scopes, client.scopes)
        if not valid_scopes:
            raise PermissionDeniedError("Client permission denied")
        access_token = issue_token(
            token_type=TokenType.ACCESS,
            payload=client.payload,
            expires_delta=CLIENT_ACCESS_TOKEN_EXPIRE_IN,
        )
        return Tokens(access_token=access_token)

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

    async def introspect_token(self, token: str, **kwargs) -> ClientTokenIntrospection:
        try:
            payload = decode_token(token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token")
        introspection_params: dict[str, Any] = {}
        if "exp" in payload and payload["exp"] < current_timestamp():
            introspection_params.update({
                "active": False, "cause": "Token expired"
            })
        introspection_params.update(payload, active=True)
        return ClientTokenIntrospection(**introspection_params)


class UserAuthService(BaseAuthService):
    def __init__(
            self, repository: UserRepository, session_store: RedisSessionStore
    ) -> None:
        self.repository = repository
        self.session_store = session_store

    async def authenticate(
            self, realm_id: UUID, email: EmailStr, password: str
    ) -> Tokens:
        user = await self.repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email")
        if not user.active:
            raise NotEnabledError("User is not active")
        if not verify_secret(password, user.password.get_secret_value()):
            raise InvalidCredentialsError("Invalid password")
        ...

    async def introspect_token(self, token: str, **kwargs) -> Tokens:
        session_id: UUID = kwargs.get("session_id")

    async def refresh_token(self) -> ...:
        ...
