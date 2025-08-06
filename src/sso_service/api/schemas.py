from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..core.enums import ClientType, GrantType


class RealmCreate(BaseModel):
    """Схема для создания области"""
    name: str
    description: str | None


class RealmUpdate(BaseModel):
    """Схема для обновления области"""
    name: str | None = None
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
    client_type: ClientType
    grant_types: list[GrantType]
    scopes: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    """Схема для обновления клиента"""
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    enabled: bool = True
