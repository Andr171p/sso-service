from datetime import timedelta

from ..settings import settings
from .enums import Role

PATH_ENDPOINT = "/api/v1"
MIN_STATUS_CODE = 100
GOOD_STATUS_CODE = 200
BYTES_SECRET_KEY_HASH = bytes(settings.secret_settings.secret_key_hash, "utf-8")

PATH_VK = "https://id.vk.com/"
PATH_YANDEX = "https://oauth.yandex.ru/"
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
SESSION_EXPIRE_IN = timedelta(days=7)
SESSION_REFRESH_THRESHOLD = timedelta(days=5)
SESSION_REFRESH_IN = timedelta(days=2)
# Создатель токенов
ISSUER = "https://davalka.ru"
# Роли пользователя по умолчанию
DEFAULT_ROLES: list[Role] = [Role.USER]
# Время истечения ресурса в хранилище
DEFAULT_TTL = timedelta(seconds=3600)
# Хеширование паролей
MEMORY_COST = 100  # Размер выделяемой памяти в mb
TIME_COST = 2
PARALLELISM = 2
SALT_SIZE = 16
ROUNDS = 14  # Количество раундов для хеширования
