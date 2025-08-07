from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from redis.asyncio import Redis as AsyncRedis

from .database.base import create_sessionmaker
from .database.repository import ClientRepository, RealmRepository
from .services import ClientAuthService
from .storage import RedisSessionStore
from .settings import Settings, settings


class AppProvider(Provider):
    app_settings = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_redis(self, app_settings: Settings) -> AsyncRedis:
        return AsyncRedis.from_url(app_settings.redis.url)

    @provide(scope=Scope.APP)
    def get_sessionmaker(  # noqa: PLR6301
        self, app_settings: Settings
    ) -> async_sessionmaker[AsyncSession]:
        return create_sessionmaker(app_settings.postgres.sqlalchemy_url)

    @provide(scope=Scope.REQUEST)
    async def get_session(  # noqa: PLR6301
        self, sessionmaker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_realm_repository(self, session: AsyncSession) -> RealmRepository:  # noqa: PLR6301
        return RealmRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_client_repository(self, session: AsyncSession) -> ClientRepository:  # noqa: PLR6301
        return ClientRepository(session)

    @provide(scope=Scope.APP)
    def get_session_store(self, redis: AsyncRedis) -> RedisSessionStore:
        return RedisSessionStore(redis)

    @provide(scope=Scope.REQUEST)
    def get_client_auth_service(self, repository: ClientRepository) -> ClientAuthService:
        return ClientAuthService(repository)


container = make_async_container(AppProvider(), context={Settings: settings})
