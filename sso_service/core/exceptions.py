from __future__ import annotations

from dataclasses import dataclass

from .constants import MIN_STATUS_CODE


class _RepositoryError(Exception):
    """Базовая ошибка репозитория"""


class MismatchError(_RepositoryError):
    """Ошибка при несоответствии данных"""


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


class NotEnabledError(UnauthorizedError):
    """Запрашиваемый ресурс пока не доступен"""


class PermissionDeniedError(UnauthorizedError):
    """Ошибка прав доступа"""


class InvalidTokenError(_AuthenticationError):
    """Инвалидный токен"""


class NotRegisteredResourceError(_AuthenticationError):
    """Ресурс не зарегистрирован или не был создан"""


class BaseHTTPError(Exception):
    def __init__(self, message: str, code: int) -> None:
        self.code = code if code > MIN_STATUS_CODE else 500
        self.message = message

    def __str__(self):
        return f"{self.message} ({self.code})"


class BadRequestHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Bad Request") -> None:
        super().__init__(message, 400)


class UnauthorizedHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Authorization Required") -> None:
        super().__init__(message, 401)


class ForbiddenHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, 403)


class NotFoundHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Not Found") -> None:
        super().__init__(message, 404)


class NotAllowHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Method Not Allowed") -> None:
        super().__init__(message, 405)


class InternalHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Internal Server Error") -> None:
        super().__init__(message, 500)


class ExistsHTTPError(BaseHTTPError):
    def __init__(self, message: str = "Entry already exists") -> None:
        super().__init__(message, 409)


class NoPlacesHTTPError(BaseHTTPError):
    def __init__(self, message: str = "No places") -> None:
        super().__init__(message, 403)


@dataclass
class JSONError:
    message: str
    description: str
    error: Exception

    @classmethod
    def create(cls, exception: Exception, description: str | None = None) -> JSONError:
        return cls(
            message=getattr(exception, "message", str(exception)),
            description=description if isinstance(description, str) else "",
            error=exception,
        )

    def to_dict(self):
        return {
            "message": self.message,
            "description": self.description,
            "error": f"{type(self.error)} - {self.error}",
        }
