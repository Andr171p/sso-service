from typing import Literal

from pathlib import Path

import pytz
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корневая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent
# Секретные переменные
ENV_PATH = BASE_DIR / ".env"
# Временная зона
TIMEZONE = "Europe/Moscow"
moscow_tz = pytz.timezone(TIMEZONE)

load_dotenv(ENV_PATH)


class VKSettings(BaseSettings):
    vk_app_id: str = ""
    vk_app_secret: str = ""
    vk_client_secret: str = ""
    vk_redirect_uri: str = ""


class YandexSettings(BaseSettings):
    yandex_app_id: str = ""
    yandex_app_secret: str = ""


class SecretSettings(BaseSettings):
    secret_key: str = ""
    secret_key_hash: str = ""


class JWTSettings(BaseSettings):
    secret_key: str = ""
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_prefix="JWT_")


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis"
    password: str = "<PASSWORD>"

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    @property
    def url(self) -> str:
        return f"redis://{self.user}:{self.password}{self.host}:{self.port}/0"


class PostgresSettings(BaseSettings):
    user: str = ""
    password: str = ""
    host: str = "postgres"
    port: int = 5432
    db: str = ""
    driver: Literal["asyncpg"] = "asyncpg"

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @property
    def sqlalchemy_url(self) -> str:
        return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    vk_settings: VKSettings = VKSettings()
    yandex_settings: YandexSettings = YandexSettings()
    secret_settings: SecretSettings = SecretSettings()
    postgres: PostgresSettings = PostgresSettings()
    jwt: JWTSettings = JWTSettings()
    redis: RedisSettings = RedisSettings()


settings = Settings()
