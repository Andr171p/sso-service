class _RepositoryError(Exception):
    """Базовая ошибка репозитория"""


class CreationError(_RepositoryError):
    """Ошибка при создании ресурса"""


class AlreadyCreatedError(_RepositoryError):
    """Ресурс уже был создан"""


class ReadingError(_RepositoryError):
    """Ошибка при чтении данных"""


class UpdateError(_RepositoryError):
    """Ошибка обновления данных"""


class DeletionError(_RepositoryError):
    """Ошибка удаления данных"""
