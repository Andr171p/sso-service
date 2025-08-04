import time
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis

from .core.base import BaseStore
from .core.schemas import Session


class RedisSessionStore(BaseStore[Session]):
    def __init__(self, redis: AsyncRedis) -> None:
        self._redis = redis

    async def add(self, session: Session) -> None:
        key = f"session:{session.session_id}"
        await self._redis.hset(key, mapping=session.model_dump())
        await self._redis.expire(key, time=int(session.expires_at - time.time()))

    async def get(self, session_id: UUID) -> Session | None:
        key = f"session:{session_id}"
        data = await self._redis.hgetall(key)
        return Session.model_load(data) if data else None

    async def delete(self, session_id: UUID) -> bool:
        key = f"session:{session_id}"
        deleted_keys = await self._redis.delete(key)
        return deleted_keys > 0
