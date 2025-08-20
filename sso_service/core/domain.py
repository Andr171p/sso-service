from __future__ import annotations

from typing import Any, Literal

from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import urlencode
from uuid import UUID, uuid4

from authlib.common.security import generate_token
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    SecretStr,
    field_serializer,
    field_validator,
    model_validator,
)

from ..settings import settings
from .constants import ISSUER, MAX_NAME_LENGTH, MIN_GRANT_TYPES_COUNT
from .enums import ClientType, GrantType, Role, TokenType, UserStatus, ProtocolType
from .utils import (
    current_datetime,
    current_timestamp,
    generate_public_id,
    generate_secret,
    validate_scopes,
)


class User(BaseModel):
    """Зарегистрированный пользователь системы.

    Attributes:
        id: Уникальный идентификатор пользователя во всей системе.
        email: Адрес почты пользователя для подтверждения аккаунта (опционален).
        status: Статус пользователя в системе.
        (при флаге False - пользователь больше не может входить в систему).
        created_at: Дата и время добавления пользователя.
    """
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    password: SecretStr | None = None
    status: UserStatus = Field(default=UserStatus.REGISTERED)
    created_at: datetime = Field(default_factory=current_datetime)

    model_config = ConfigDict(from_attributes=True)

    def hash_password(self) -> User:
        from ..security import hash_secret

        if self.password is None:
            raise ValueError("Password must be provided!")
        self.password = SecretStr(hash_secret(self.password.get_secret_value()))
        return self

    @field_serializer("password")
    def serialize_secret(self, password: SecretStr | None) -> str | None:
        if password is None:
            return password
        return password.get_secret_value()

    def to_payload(self, **kwargs) -> dict[str, Any]:
        realm: str = kwargs.pop("realm")
        roles: list[str] = kwargs.pop("roles")
        return {
            "iss": ISSUER,
            "sub": str(self.id),
            "email": self.email,
            "status": self.status.value,
            "realm": realm,
            "roles": " ".join(roles),
            **kwargs,
        }


class Group(BaseModel):
    """Ролевые группы для пользователей"""
    id: UUID = Field(default_factory=uuid4)
    realm_id: UUID
    name: str
    description: str | None = None
    roles: list[Role]
    created_at: datetime = Field(default_factory=current_datetime)

    model_config = ConfigDict(from_attributes=True)


class UserGroup(BaseModel):
    """Привязка пользователя к группе"""
    user_id: UUID
    group_id: UUID


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
    created_at: datetime = Field(default_factory=current_datetime)

    model_config = ConfigDict(from_attributes=True)

    def to_payload(self, **kwargs) -> dict[str, Any]:
        """Полезная нагрузка для JWT"""
        return {"iss": ISSUER, "sub": self.client_id, "scope": " ".join(self.scopes), **kwargs}

    def hash_client_secret(self) -> Client:
        from ..security import hash_secret

        self.client_secret = SecretStr(hash_secret(self.client_secret.get_secret_value()))
        return self

    @model_validator(mode="after")
    def validate_client(self) -> Client:
        if (
            self.client_type == ClientType.PUBLIC
            and GrantType.CLIENT_CREDENTIALS in self.grant_types
        ):
            raise ValueError("Public clients cannot use client_credentials")
        return self

    @field_validator("scopes")
    def validate_scopes(cls, scopes: list[str]) -> list[str]:
        return validate_scopes(scopes)

    @field_serializer("client_secret")
    def serialize_secret(self, client_secret: SecretStr) -> str:
        return client_secret.get_secret_value()


class IdentityProvider(BaseModel):
    """Провайдер аутентификации и регистрации.
    Например: Google, VK, Yandex ...
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    protocol: ProtocolType
    client_id: str
    client_secret: SecretStr
    scopes: list[str] = Field(default_factory=list)
    enabled: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserIdentity(BaseModel):
    """Привязка аккаунта пользователя к провайдеру.

    Attributes:
        id: Уникальный идентификатор.
        user_id: Пользователь к которому привязан аккаунт.
        provider_id: Провайдер, которому принадлежит аккаунт пользователя.
        provider_user_id: Уникальный идентификатор пользователя у провайдера.
        email: Почта, которая привязана к провайдеру.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID | None = None
    provider_id: UUID | None = None
    provider_user_id: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class Session(BaseModel):
    """Пользовательская сессия в SSO"""
    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    expires_at: int | float
    user_agent: str | None = None
    ip_address: str | None = None
    last_activity: float = Field(default_factory=current_timestamp)

    @field_serializer("session_id", "user_id")
    def serialize_guid(self, guid: UUID) -> str:
        return str(guid)


class Token(BaseModel):
    access_token: str
    expires_at: int | float


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    session_id: UUID
    expires_at: int


class Claims(BaseModel):
    """Базовая модель для интроспекции JWT"""
    active: bool = False
    cause: str | None = None
    token_type: TokenType | None = None
    iss: HttpUrl | None = None
    sub: str | None = None
    aud: str | None = None
    exp: int | float | None = None
    iat: int | float | None = None
    jti: UUID | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("iss")
    def serialize_iss(self, iss: HttpUrl) -> str:
        return str(iss)


class ClientClaims(Claims):
    realm: str | None = None
    scope: str | None = None


class UserClaims(Claims):
    status: UserStatus | None = None
    realm: str | None = None
    roles: list[Role] | None = None

    @field_validator("roles", mode="before")
    def validate_roles(cls, roles: str | list[Role]) -> list[Role]:
        if isinstance(roles, list):
            return roles
        return [Role(role) for role in roles.split(" ")]


class Codes(BaseModel):
    state: str
    code_verifier: str
    code_challenge: str

    @classmethod
    def generate(cls) -> Codes:
        verifier = generate_token(64)
        return cls(
            state=str(uuid4()),
            code_verifier=verifier,
            code_challenge=create_s256_code_challenge(verifier),
        )


class VKRedirect(BaseModel):
    client_id: str = settings.vk_settings.vk_app_id
    redirect_uri: str = settings.vk_settings.vk_redirect_uri

    def to_url(self, state: str, code_challenge: str) -> str:
        query = urlencode({
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "email",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })
        return f"{settings.vk_settings.vk_auth_url}?{query}"


class YandexRedirect(BaseModel):
    client_id: str = settings.yandex_settings.yandex_app_id

    def to_url(self, state: str, code_challenge: str) -> str:
        query = urlencode({
            "client_id": self.client_id,
            "response_type": "code",
            "state": state,
            "scope": "login:info login:email",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })
        return f"{settings.yandex_settings.yandex_auth_url}?{query}"


class BaseCallback(BaseModel, ABC):
    code: str
    state: str

    @abstractmethod
    def to_dict(self, code_verifier: str) -> dict: ...


class YandexCallback(BaseCallback):
    def to_dict(self, code_verifier: str) -> dict:
        return {
            "grant_type": "authorization_code",
            "code": self.code,
            "client_id": settings.yandex_settings.yandex_app_id,
            "client_secret": settings.yandex_settings.yandex_app_secret,
            "code_verifier": code_verifier,
        }


class VKCallback(BaseCallback):
    device_id: str

    def to_dict(self, code_verifier: str) -> dict:
        return {
            "grant_type": "authorization_code",
            "code": self.code,
            "code_verifier": code_verifier,
            "client_id": settings.vk_settings.vk_app_id,
            "device_id": self.device_id,
            "redirect_uri": settings.vk_settings.vk_redirect_uri,
            "state": self.state,
        }


class VKGetData(BaseModel):
    access_token: str
    user_id: str = Field(exclude=True)
    client_id: str = settings.vk_settings.vk_app_id


class YandexGetData(BaseModel):
    oauth_token: str
    format: Literal["json"] = "json"
