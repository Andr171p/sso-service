import time
import json
from datetime import timedelta
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis

from .core.base import BaseStore
from .core.domain import Session


class RedisSessionStore(BaseStore[Session]):
    def __init__(self, redis: AsyncRedis) -> None:
        self._redis = redis

    async def add(self, session: Session) -> None:
        key = f"session:{session.session_id}"
        await self._redis.set(key, session.model_dump_json(exclude_none=True))
        # await self._redis.hmset(key, mapping=session.model_dump(exclude_none=True))
        await self._redis.expire(key, time=int(session.expires_at - time.time()))

    async def get(self, session_id: UUID) -> Session | None:
        key = f"session:{session_id}"
        data = await self._redis.get(key)
        if data is None:
            return None
        json_string = data.decode("utf-8")
        # data = await self._redis.hgetall(key)
        return Session.model_validate_json(json_string)

    async def update(
            self, session_id: UUID, ttl: timedelta | None = None, **kwargs
    ) -> Session | None:
        key = f"session:{session_id}"
        if not await self._redis.exists(key):
            return None
        if ttl:
            await self._redis.expire(key, ttl)
        return await self.get(session_id)

    async def delete(self, session_id: UUID) -> bool:
        key = f"session:{session_id}"
        deleted_keys = await self._redis.delete(key)
        return deleted_keys > 0
