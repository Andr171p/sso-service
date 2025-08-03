from datetime import timedelta

# Крайние значения для client
MIN_CLIENT_ID_LENGTH = 3
MAX_CLIENT_ID_LENGTH = 63
MAX_NAME_LENGTH = 127
# Количество байтов в client_secret
BYTES_COUNT = 32
# Минимальное количество grant types
MIN_GRANT_TYPES_COUNT = 1
# Дефолтное время протухания токена в минутах
EXPIRES_DELTA_MINUTES = 15
# Создатель токенов
ISSUER = "https://davalka.ru"
# Время истечение токенов
CLIENT_ACCESS_TOKEN_EXPIRE = timedelta(hours=2)
