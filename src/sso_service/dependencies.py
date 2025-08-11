from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from redis.asyncio import Redis as AsyncRedis

from .database.base import create_sessionmaker
from .database.repository import (
    ClientRepository,
    RealmRepository,
    UserRepository,
    GroupRepository
)
from .services import ClientAuthService, UserAuthService
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

    @provide(scope=Scope.REQUEST)
    def get_user_repository(self, session: AsyncSession) -> UserRepository:  # noqa: PLR6301
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_group_repository(self, session: AsyncSession) -> GroupRepository:  # noqa: PLR6301
        return GroupRepository(session)

    @provide(scope=Scope.APP)
    def get_session_store(self, redis: AsyncRedis) -> RedisSessionStore:  # noqa: PLR6301
        return RedisSessionStore(redis)

    @provide(scope=Scope.REQUEST)
    def get_client_auth_service(  # noqa: PLR6301
            self, repository: ClientRepository
    ) -> ClientAuthService:
        return ClientAuthService(repository)

    @provide(scope=Scope.REQUEST)
    def get_user_auth_service(  # noqa: PLR6301
            self,
            user_repository: UserRepository,
            group_repository: GroupRepository,
            realm_repository: RealmRepository,
            session_store: RedisSessionStore
    ) -> UserAuthService:
        return UserAuthService(
            user_repository=user_repository,
            group_repository=group_repository,
            realm_repository=realm_repository,
            session_store=session_store
        )


container = make_async_container(AppProvider(), context={Settings: settings})
