from __future__ import annotations

from typing import Any

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    EmailStr,
    HttpUrl,
    SecretStr,
    field_validator,
    model_validator
)

from .constants import MAX_NAME_LENGTH, MIN_GRANT_TYPES_COUNT, ISSUER
from .enums import ClientType, GrantType
from .utils import (
    current_datetime,
    validate_scopes,
    generate_public_id,
    generate_secret
)


class User(BaseModel):
    """Зарегистрированный пользователь системы.

    Attributes:
        id: Уникальный идентификатор пользователя во всей системе.
        email: Адрес почты пользователя для подтверждения аккаунта (опционален).
        username: Уникальное имя пользователя, логин (опционален)
        active: Активен ли пользователь в системе
        (при флаге False - пользователь больше не может входить в систему).
        created_at: Дата и время добавления пользователя.
    """
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr | None = None
    username: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=current_datetime)


class Realm(BaseModel):
    """Область приложения (группа изолированных микро-сервисов).

    Attributes:
        id: Уникальный идентификатор области.
        name: Название области (для улучшения читабельности).
        slug: Уникальный псевдоним сервиса используемый в URL,
        например, https://api.com/{slug}/users
        description: Краткое описание (для улучшения читабельности).
        enabled: Активна ли область
        (при значении False отключаются все сервисы внутри неё).
        created_at: Дата и время создания области.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=MAX_NAME_LENGTH)
    slug: str
    description: str | None = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=current_datetime)

    model_config = ConfigDict(from_attributes=True)


class Client(BaseModel):
    """Клиент системы (приложение, микро-сервис, web-интерфейс)

    Attributes:
        id: Уникальный идентификатор клиента, только внутри системы или токена.
        realm_id: Идентификатор области в которой находится клиент.
        client_id: Публичный идентификатор клиента.
        client_secret: Секретный пароль клиента (не допускается в публичный доступ).
        name: Имя клиента (только для читабельности).
        description: Описание клиента (опционально).
        expires_at: Дата истечения client credentials (пары client_id:client_secret),
        опционально.
        client_type: Тип клиента (важен для определения grant_type).
        grant_types: Определяет метод получения токенов клиенту.
        scopes: Права выдаваемые клиенту для ограничения доступа к другим клиентам.
        already_seen_secret: Просмотрен ли client_secret в админ панели.
        created_at: Дата создания клиента.
    """
    id: UUID = Field(default_factory=uuid4)
    realm_id: UUID
    client_id: str = Field(default_factory=generate_public_id)
    client_secret: SecretStr = Field(default_factory=generate_secret)
    name: str = Field(..., max_length=MAX_NAME_LENGTH)
    description: str | None = None
    expires_at: datetime | None = None
    enabled: bool = True
    client_type: ClientType
    grant_types: list[GrantType] = Field(
        default=[GrantType.CLIENT_CREDENTIALS], min_length=MIN_GRANT_TYPES_COUNT
    )
    redirect_uris: list[HttpUrl] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    already_seen_secret: bool = False
    created_at: datetime = Field(default_factory=current_datetime)

    model_config = ConfigDict(from_attributes=True)

    @property
    def payload(self) -> dict[str, Any]:
        """Полезная нагрузка для JWT"""
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


class IdentityProvider(BaseModel):
    """Провайдер аутентификации и регистрации"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ...
    client_id: str
    client_secret: SecretStr
    scopes: list[str] = Field(default_factory=list)


class UserIdentity(BaseModel):
    """Привязка аккаунта пользователя"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    provider_id: UUID
    provider_user_id: UUID


class ClientCredentials(BaseModel):
    """Авторизационные данные клиента"""
    client_id: str
    client_secret: SecretStr
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Tokens(BaseModel):
    """JWT токены для авторизации"""
    access_token: str
    refresh_token: str | None = None
    session_id: UUID | None = None


class Session(BaseModel):
    """Пользовательская сессия в SSO"""
    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    expires_at: int | float
    ip_address: str | None = None
