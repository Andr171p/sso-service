from typing import Any

import secrets
import string
from datetime import datetime, timedelta

from pydantic import SecretStr

from .constants import BYTES_COUNT, GOOD_STATUS_CODE
from .exceptions import NotFoundHTTPError


def generate_secret() -> SecretStr:
    """Генерирует произвольный секретный код"""
    return SecretStr(secrets.token_urlsafe(BYTES_COUNT))


def generate_public_id() -> str:
    """Генерирует произвольный публичный id"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(BYTES_COUNT))


def validate_scopes(scopes: list[str]) -> list[str]:
    """Производит валидацию (проверку) прав на нужный формат"""
    for scope in scopes:
        if not scope.replace(":", "").isalnum():
            raise ValueError(f"Invalid scope format: {scope}")
    return scopes


def format_scope(scope: str) -> list[str]:
    """Форматирует строку из прав в массив"""
    return validate_scopes(scope.split(" "))


def current_datetime() -> datetime:
    from ..settings import moscow_tz  # noqa: PLC0415

    return datetime.now(tz=moscow_tz)


def current_timestamp() -> float:
    from ..settings import moscow_tz  # noqa: PLC0415

    return datetime.now(tz=moscow_tz).timestamp()


def expires_at(expires_in: timedelta) -> int:
    """Рассчитывает время истечения"""
    return int((current_datetime() + expires_in).timestamp())


async def valid_answer(response: Any) -> dict:
    if response.status != GOOD_STATUS_CODE:
        raise NotFoundHTTPError
    return await response.json()
