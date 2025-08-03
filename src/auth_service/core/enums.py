from enum import StrEnum


class ClientType(StrEnum):
    PUBLIC = "public"                    # SPA, мобильные приложения (нет секрета)
    CONFIDENTIAL = "confidential"        # Серверные приложения (есть секрет)
    SERVICE_ACCOUNT = "service-account"  # Для меж сервисной аутентификации


class GrantType(StrEnum):
    """Определяет, как клиент может получать токены."""
    AUTHORIZATION_CODE = "authorization_code"  # Web-приложения
    CLIENT_CREDENTIALS = "client_credentials"  # Сервис-сервис
    REFRESH_TOKEN = "refresh_token"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
