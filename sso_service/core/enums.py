from enum import StrEnum


class ClientType(StrEnum):
    PUBLIC = "public"                    # SPA, мобильные приложения (нет секрета)
    CONFIDENTIAL = "confidential"        # Серверные приложения (есть секрет)
    SERVICE_ACCOUNT = "service-account"  # Для меж сервисной аутентификации


class GrantType(StrEnum):
    """Определяет, как клиент может получать токены."""
    AUTHORIZATION_CODE = "authorization_code"  # Web-приложения
    CLIENT_CREDENTIALS = "client_credentials"  # Сервис-сервис


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class Role(StrEnum):
    """Глобальные роли пользователя в рамках области"""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(StrEnum):
    """Статусы пользователя

    Attributes:
        REGISTERED: Зарегистрированный пользователь (ещё не подтверждён email).
        EMAIL_VERIFIED: Пользователь с подтверждённым email.
        ACTIVE: Активны пользователь (после подтверждения email).
        INACTIVE: Неактивный пользователь (не совершал действия долгое время).
        BANNED: Забаненный пользователь.
        DELETED: Удалённый пользователь (при удалении пользователь остаётся в системе).
    """
    REGISTERED = "registered"
    EMAIL_VERIFIED = "email_verified"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    DELETED = "deleted"


class ProtocolType(StrEnum):
    """Тип протокола аутентификации через провайдера"""
    OAUTH = "oauth"
    OIDC = "oidc"
