from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, SecretStr

from ..core.enums import ClientType, GrantType, Role


class RealmCreate(BaseModel):
    """Схема для создания области"""
    name: str
    slug: str
    description: str | None


class RealmUpdate(BaseModel):
    """Схема для обновления области"""
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    enabled: bool = True


class ClientCreate(BaseModel):
    """Схема для создания клиента"""
    realm_id: UUID
    name: str
    description: str | None = None
    client_type: ClientType
    scopes: list[str]

    model_config = ConfigDict(from_attributes=True)


class CreatedClient(BaseModel):
    """Схема для просмотра уже созданного клиента"""
    id: UUID
    name: str
    description: str | None = None
    enabled: bool = True
    client_id: str
    client_secret: str
    client_type: ClientType
    grant_types: list[GrantType]
    scopes: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("client_secret", mode="before")
    def validate_secret(cls, client_secret: SecretStr) -> str:
        return client_secret.get_secret_value()


class ClientUpdate(BaseModel):
    """Схема для обновления клиента"""
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    enabled: bool = True


class GroupCreate(BaseModel):
    """Схема запроса для создания группы"""
    name: str
    description: str | None = None
    roles: list[Role]


class GroupUpdate(BaseModel):
    """Схема запроса для обновления группы"""
    name: str | None = None
    description: str | None = None
    roles: list[Role] | None = None
