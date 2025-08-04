from datetime import datetime
from uuid import UUID

from .core.base import BaseAuthService
from .core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
)
from .core.schemas import Client, ClientPayload, UserPayload
from .core.utils import format_scope
from .database.repository import ClientRepository
from .security import decode_token, verify_secret
from .settings import moscow_tz


class ClientAuthService(BaseAuthService[Client]):
    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    async def authenticate(
            self, realm_id: UUID, client_id: str, client_secret: str, scope: str
    ) -> Client:
        scopes = format_scope(scope)
        client = await self.repository.get_by_client_id(realm_id, client_id)
        if client is None:
            raise UnauthorizedError("Client unauthorized in this realm")
        if not client.enabled:
            raise NotEnabledError("Client not enabled yet")
        if verify_secret(client_secret, str(client.client_secret)):
            raise InvalidCredentialsError("Client credentials invalid")
        valid_scopes = self._validate_scopes(scopes, client.scopes)
        if not valid_scopes:
            raise PermissionDeniedError("Client permission denied")
        return client

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


def validate_client_token(token: str, realm_id: UUID) -> ClientPayload:
    """Скрывает ошибки согласно RFC 7662, при ошибках поле active=false"""
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        return ClientPayload(active=False)
    token_realm_id = payload.get("realm_id")
    if token_realm_id is None or str(realm_id) != token_realm_id:
        return ClientPayload(
            active=False, sub=payload.get("sub"), realm_id=realm_id,
        )
    if "exp" in payload and payload["exp"] < datetime.now(tz=moscow_tz).timestamp():
        return ClientPayload(
            active=False, sub=payload.get("sub"), realm_id=realm_id
        )
    return ClientPayload.model_validate(payload)


def validate_user_token(token: str) -> UserPayload:
    ...
