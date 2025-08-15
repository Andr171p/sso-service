import time
from datetime import timedelta
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis

from .core.base import BaseStore
from .core.domain import Session

PREFIX = "session"


class RedisSessionStore(BaseStore[Session]):
    def __init__(self, redis: AsyncRedis, prefix: str = PREFIX) -> None:
        self._redis = redis
        self._prefix = prefix

    def _build_key(self, session_id: UUID | str) -> str:
        return f"{self._prefix}:{str(session_id)}"

    async def add(self, session: Session) -> None:
        key = self._build_key(session.session_id)
        await self._redis.set(key, session.model_dump_json(exclude_none=True))
        await self._redis.expire(key, time=int(session.expires_at - time.time()))

    async def get(self, session_id: UUID) -> Session | None:
        key = self._build_key(session_id)
        data = await self._redis.get(key)
        if data is None:
            return None
        json_string = data.decode("utf-8")
        return Session.model_validate_json(json_string)

    async def exists(self, session_id: UUID) -> bool:
        key = self._build_key(session_id)
        return await self._redis.exists(key)

    async def update(
            self, session_id: UUID, ttl: timedelta | None = None, **kwargs
    ) -> Session | None:
        key = self._build_key(session_id)
        if not await self._redis.exists(key):
            return None
        if ttl:
            await self._redis.expire(key, ttl)
        return await self.get(session_id)

    async def delete(self, session_id: UUID) -> bool:
        key = self._build_key(session_id)
        deleted_keys = await self._redis.delete(key)
        return deleted_keys > 0
