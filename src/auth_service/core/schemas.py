from __future__ import annotations

from typing import Any

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
    model_validator
)

from .constants import MAX_NAME_LENGTH, MIN_GRANT_TYPES_COUNT, ISSUER
from .enums import ClientType, GrantType
from .utils import current_time, validate_scopes, format_scope, generate_id, generate_secret


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
        default_factory=generate_id, description="Публичный идентификатор клиента",
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


class Session(BaseModel):
    """Пользовательская сессия"""
    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    expires_at: int | float
    ip_address: str


class Payload(BaseModel):
    """Декодированная полезная нагрузка токена"""
    active: bool = True
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
    scope: str | None = None
    realm_id: UUID | None = None


class UserPayload(Payload):
    realm_id: UUID | None = None
    ...
