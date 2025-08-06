from uuid import UUID

from pydantic import BaseModel, HttpUrl

from .enums import UserRole, TokenType


class BaseTokenIntrospection(BaseModel):
    """Базовая модель для интроспекции JWT"""
    active: bool = False
    token_type: TokenType | None = None
    iss: HttpUrl | None = None
    sub: str | None = None
    aud: str | None = None
    exp: int | None = None
    iat: int | None = None
    jti: UUID | None = None


class ClientTokenIntrospection(BaseTokenIntrospection):
    realm_id: UUID | None = None
    scopes: list[str] | None = None
    client_id: str | None = None


class UserTokenIntrospection(BaseTokenIntrospection):
    realm_id: UUID | None = None
    user_id: UUID | None = None
    role: UserRole | None = None
