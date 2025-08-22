import time

from pydantic import EmailStr

from ..core.base import BaseStore
from ..core.constants import CLIENT_ACCESS_TOKEN_EXPIRE_IN, SESSION_EXPIRE_IN
from ..core.domain import Session, Token, TokenPair, User
from ..core.enums import GrantType, TokenType, UserStatus
from ..core.exceptions import (
    InvalidCredentialsError,
    NotEnabledError,
    PermissionDeniedError,
    UnauthorizedError,
    UnsupportedGrantTypeError,
)
from ..core.utils import expires_at, format_scope
from ..database.repository import ClientRepository, UserRepository
from ..security import issue_token, verify_secret
from ..services import generate_token_pair, give_roles


class ClientCredentialsProvider:
    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    async def authenticate(
        self, realm: str, grant_type: str, client_id: str, client_secret: str, scope: str
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
            access_token=access_token, expires_at=expires_at(CLIENT_ACCESS_TOKEN_EXPIRE_IN)
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


class UserCredentialsProvider:
    def __init__(self, repository: UserRepository, session_store: BaseStore[Session]) -> None:
        self.repository = repository
        self.session_store = session_store

    async def register(self, user: User) -> User:
        user.hash_password()
        return await self.repository.create(user)

    async def authenticate(self, realm: str, email: EmailStr, password: str) -> TokenPair:
        user = await self.repository.get_by_email(email)
        if user is None or user.password is None:
            raise InvalidCredentialsError("Invalid email")
        if user.status == UserStatus.BANNED:
            raise NotEnabledError("User is banned")
        if not verify_secret(password, user.password.get_secret_value()):
            raise InvalidCredentialsError("Invalid password")
        roles = await give_roles(realm, user.id, self.repository)
        payload = user.to_payload(realm=realm, roles=roles)
        session = Session(user_id=user.id, expires_at=expires_at(SESSION_EXPIRE_IN))
        await self.session_store.add(
            session.session_id, session, ttl=int(session.expires_at - time.time())
        )
        return generate_token_pair(payload, session.session_id)
