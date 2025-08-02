from __future__ import annotations

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
)
from .enums import ClientType, GrantType


def generate_secret() -> str:
    """Генерирует произвольный секретный код"""
    return secrets.token_urlsafe(BYTES_COUNT)


def generate_id() -> str:
    """Генерирует произвольный публичный id"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(BYTES_COUNT))


class Realm(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

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
    scopes: list[str] = Field(default_factory=list, description="Области видимости")
    already_seen_secret: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)

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
        for scope in scopes:
            if not scope.replace(":", "").isalnum():
                raise ValueError(f"Invalid scope format: {scope}")
        return scopes


class ClientCredentials(BaseModel):
    """Авторизационные данные клиента"""
    client_id: str
    client_secret: SecretStr
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
