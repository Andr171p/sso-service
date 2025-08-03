import time

from redis.asyncio import Redis as AsyncRedis

from .core.schemas import Token


class RedisTokenStore:
    def __init__(self, redis: AsyncRedis) -> None:
        self._redis = redis

    async def add(self, token: Token) -> None:
        name = f"token:{token.jti}"
        await self._redis.hset(name, mapping=token.model_dump())
        await self._redis.expire(name, time=int(token.expires_at - time.time()))

    async def get(self, jti: str) -> Token | None:
        name = f"token:{jti}"
        data = await self._redis.hgetall(name)
        return Token.model_validate(data) if data else None

    async def delete(self, jti: str) -> bool:
        name = f"token:{jti}"
        deleted_keys = await self._redis.delete(name)
        return deleted_keys > 0
