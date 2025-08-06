from typing import Any

from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from .core.enums import TokenType
from .core.exceptions import InvalidTokenError
from .settings import moscow_tz, settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_secret(secret: str) -> str:
    """Хэширует секрет (password, client_secret, etc...)"""
    return pwd_context.hash(secret)


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Сверяет ожидаемый пароль с хэшем пароля"""
    return pwd_context.verify(plain_secret, hashed_secret)


def issue_token(
        token_type: TokenType,
        payload: dict[str, Any],
        expires_delta: timedelta,
) -> str:
    now = datetime.now(tz=moscow_tz)
    expire = now + expires_delta
    payload = payload.copy()
    payload.update({
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
        "type": token_type.value,
        "jti": str(uuid4())
    })
    return jwt.encode(
        payload=payload,
        key=settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            key=settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
            options={"verify_aud": False}
        )
    except jwt.PyJWTError:
        raise InvalidTokenError("Invalid token")
