from datetime import timedelta
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis

from .core.base import BaseStore, T
from .core.constants import DEFAULT_TTL
from .core.domain import Codes, Session


class RedisStore(BaseStore[T]):
    schema: type[T]

    def __init__(self, redis: AsyncRedis, prefix: str) -> None:
        self._redis = redis
        self._prefix = prefix

    def _build_key(self, string: str | UUID) -> str:
        return f"{self._prefix}:{string}"

    async def add(
            self, key: str | UUID, schema: T, ttl: timedelta | int | None = DEFAULT_TTL
    ) -> None:
        key = self._build_key(key)
        await self._redis.set(key, schema.model_dump_json(exclude_none=True))
        if ttl:
            await self._redis.expire(key, time=ttl)

    async def get(self, key: str | UUID) -> T | None:
        key = self._build_key(key)
        data = await self._redis.get(key)
        if data is None:
            return None
        json_string = data.decode("utf-8")
        return self.schema.model_validate_json(json_string)

    async def exists(self, key: str | UUID) -> bool:
        key = self._build_key(key)
        return await self._redis.exists(key)

    async def refresh_ttl(self, key: str | UUID, ttl: timedelta) -> T | None:
        key = self._build_key(key)
        if not await self.exists(key):
            return None
        if ttl:
            await self._redis.expire(key, ttl)
        return await self.get(key)

    async def delete(self, key: str | UUID) -> bool:
        key = self._build_key(key)
        deleted_keys = await self._redis.delete(key)
        return deleted_keys > 0


class RedisSessionStore(RedisStore[Session]):
    schema = Session


class RedisCodesStore(RedisStore[Codes]):
    schema = Codes
