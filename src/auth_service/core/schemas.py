from __future__ import annotations

from typing import Any

import secrets
import string
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
    model_validator,
)

from .constants import (
    BYTES_COUNT,
    MAX_NAME_LENGTH,
    MIN_GRANT_TYPES_COUNT,
    ISSUER,
)
from .enums import ClientType, GrantType, TokenType
from .utils import current_time, current_timestamp, validate_scopes, format_scope


def generate_secret() -> str:
    """Генерирует произвольный секретный код"""
    return secrets.token_urlsafe(BYTES_COUNT)


def generate_public_id() -> str:
    """Генерирует произвольный публичный id"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(BYTES_COUNT))


class Realm(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=current_time)

    model_config = ConfigDict(from_attributes=True)


class Client(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    realm_id: UUID
    client_id: str = Field(
        default_factory=generate_public_id, description="Публичный идентификатор клиента",
    )
    client_secret: SecretStr = Field(
        default_factory=generate_secret, description="Секретный ключ"
    )
    expires_at: datetime | None = None
    name: str = Field(..., max_length=MAX_NAME_LENGTH)
    enabled: bool = True
    client_type: ClientType
    redirect_uris: list[HttpUrl] = Field(default_factory=list)
    grant_types: list[GrantType] = Field(
        default=[GrantType.CLIENT_CREDENTIALS], min_length=MIN_GRANT_TYPES_COUNT
    )
    scopes: list[str] = Field(default_factory=list, description="Области видимости, права")
    already_seen_secret: bool = False
    created_at: datetime = Field(default_factory=current_time)

    model_config = ConfigDict(from_attributes=True)

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "iss": ISSUER,
            "sub": self.client_id,
            "aud": self.name,
            "realm_id": str(self.realm_id),
            "scope": " ".join(self.scopes)
        }

    @model_validator(mode="after")
    def validate_client_config(self) -> Client:
        if (
            self.client_type == ClientType.PUBLIC
            and GrantType.CLIENT_CREDENTIALS in self.grant_types
        ):
            raise ValueError("Public clients cannot use client_credentials")
        return self

    @field_validator("scopes")
    def validate_scopes(cls, scopes: list[str]) -> list[str]:
        return validate_scopes(scopes)


class ClientCredentials(BaseModel):
    """Авторизационные данные клиента"""
    client_id: str
    client_secret: SecretStr
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    jti: str
    type: TokenType
    token: str
    expires_at: float
    created_at: float = Field(default_factory=current_timestamp)

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_expired(self) -> bool:
        return current_timestamp() > self.expires_at

    @field_validator("token", mode="before")
    def hash_token(cls, token: str) -> str:
        from ..security import hash_secret
        return hash_secret(token)

    @classmethod
    def from_payload(cls, token: str, payload: dict[str, Any]) -> Token:
        return cls(
            jti=payload["jti"],
            type=payload["type"],
            token=token,
            expires_at=payload["exp"]
        )


class Payload(BaseModel):
    """Декодированная полезная нагрузка токена"""
    active: bool = True
    scope: str | None = None
    iss: str | None = None
    sub: str | None = None
    aud: UUID | None = None
    exp: float | None = None
    iat: float | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("scope")
    def validate_scope(cls, scope: str) -> list[str]:
        return format_scope(scope)


class ClientPayload(Payload):
    """Полезная нагрузка токена клиента после валидации и декодирования"""
    realm_id: UUID | None = None
