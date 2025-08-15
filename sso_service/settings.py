from typing import Literal

from pathlib import Path
import pytz

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корневая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Секретные переменные
ENV_PATH = BASE_DIR / ".env"
# Временная зона
TIMEZONE = "Europe/Moscow"
moscow_tz = pytz.timezone(TIMEZONE)

load_dotenv(ENV_PATH)


class JWTSettings(BaseSettings):
    secret_key: str = ""
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_prefix="JWT_")


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"


class SQLiteSettings(BaseModel):
    driver: str = "aiosqlite"
    filename: str = "db.sqlite3"

    @property
    def sqlalchemy_url(self) -> str:
        return f"sqlite+{self.driver}:///{BASE_DIR}/{self.filename}"


class PostgresSettings(BaseSettings):
    user: str = ""
    password: str = ""
    host: str = "localhost"
    port: int = 5432
    db: str = ""
    driver: Literal["asyncpg"] = "asyncpg"

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @property
    def sqlalchemy_url(self) -> str:
        return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    sqlite: SQLiteSettings = SQLiteSettings()
    postgres: PostgresSettings = PostgresSettings()
    jwt: JWTSettings = JWTSettings()
    redis: RedisSettings = RedisSettings()


settings = Settings()
