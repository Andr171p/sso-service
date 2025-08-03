from datetime import datetime


def validate_scopes(scopes: list[str]) -> list[str]:
    for scope in scopes:
        if not scope.replace(":", "").isalnum():
            raise ValueError(f"Invalid scope format: {scope}")
    return scopes


def format_scope(scope: str) -> list[str]:
    return validate_scopes(scope.split(" "))


def current_time() -> datetime:
    from ..settings import moscow_tz
    return datetime.now(tz=moscow_tz)


def current_timestamp() -> float:
    from ..settings import moscow_tz
    return datetime.now(tz=moscow_tz).timestamp()
