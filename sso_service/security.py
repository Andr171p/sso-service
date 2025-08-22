from typing import Any

import logging
from datetime import timedelta
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from .core.constants import MEMORY_COST, PARALLELISM, ROUNDS, SALT_SIZE, TIME_COST
from .core.enums import TokenType
from .core.exceptions import InvalidTokenError
from .core.utils import current_datetime
from .settings import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    argon2__memory_cost=MEMORY_COST,
    argon2__time_cost=TIME_COST,
    argon2__parallelism=PARALLELISM,
    argon2__salt_size=SALT_SIZE,
    bcrypt__rounds=ROUNDS,
    deprecated="auto",
)


def hash_secret(secret: str) -> str:
    """Хэширует секрет (password, client_secret, etc...)"""
    return pwd_context.hash(secret)


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Сверяет ожидаемый пароль с хэшем пароля"""
    return pwd_context.verify(plain_secret, hashed_secret)


def issue_token(
    token_type: TokenType,
    payload: dict[str, Any],
    expires_in: timedelta,
) -> str:
    """Подписывает токен.

    :param token_type: Тип токен, например: ACCESS, REFRESH.
    :param payload: Дополнительные данные, которые нужно закодировать в токен.
    :param expires_in: Временной промежуток через который истекает токен.
    :return Подписанный токен.
    """
    now = current_datetime()
    expires_at = now + expires_in
    payload.update({
        "exp": expires_at.timestamp(),
        "iat": now.timestamp(),
        "token_type": token_type.value,
        "jti": str(uuid4()),
    })
    return jwt.encode(
        payload=payload, key=settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует токен.

    :param token: Токен, который нужно декодировать.
    :return: Словарь с информацией из токена.
    :exception InvalidTokenError: Токен не был подписан этим сервисом.
    """
    try:
        return jwt.decode(
            token,
            key=settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError:
        raise InvalidTokenError("Invalid token") from None
