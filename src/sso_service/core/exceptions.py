class _RepositoryError(Exception):
    """Базовая ошибка репозитория"""


class CreationError(_RepositoryError):
    """Ошибка при создании ресурса"""


class AlreadyExistsError(_RepositoryError):
    """Ресурс уже создан"""


class ReadingError(_RepositoryError):
    """Ошибка при чтении данных"""


class UpdateError(_RepositoryError):
    """Ошибка обновления данных"""


class DeletionError(_RepositoryError):
    """Ошибка удаления данных"""


class _AuthenticationError(Exception):
    """Базовая ошибка аутентификации"""


class UnsupportedGrantTypeError(_AuthenticationError):
    """Не валидный grant type"""


class InvalidCredentialsError(_AuthenticationError):
    """Не валидные авторизационные данные"""


class UnauthorizedError(_AuthenticationError):
    """Ошибка несанкционированного доступа"""


class NotEnabledError(_AuthenticationError):
    """Запрашиваемый ресурс пока не доступен"""


class PermissionDeniedError(_AuthenticationError):
    """Ошибка прав доступа"""


class InvalidTokenError(_AuthenticationError):
    """Инвалидный токен"""

