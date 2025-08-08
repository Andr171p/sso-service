from datetime import timedelta

from .enums import Role

# Крайние значения для client
MIN_CLIENT_ID_LENGTH = 3
MAX_CLIENT_ID_LENGTH = 63
MAX_NAME_LENGTH = 127
# Количество байтов в client_secret
BYTES_COUNT = 32
# Минимальное количество grant types
MIN_GRANT_TYPES_COUNT = 1
# Время истечения токенов
USER_ACCESS_TOKEN_EXPIRE_IN = timedelta(minutes=15)
USER_REFRESH_TOKEN_EXPIRE_IN = timedelta(days=7)
CLIENT_ACCESS_TOKEN_EXPIRE_IN = timedelta(minutes=30)
# Время истечение пользовательской сессии
USER_SESSION_EXPIRE_IN = timedelta(days=7)
# Создатель токенов
ISSUER = "https://davalka.ru"
# Роли пользователя по умолчанию
DEFAULT_ROLES: list[str] = [Role.USER]
