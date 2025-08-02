from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database.base import create_sessionmaker
from .database.repository import ClientRepository, RealmRepository
from .settings import Settings, settings


class AppProvider(Provider):
    app_settings = from_context(provides=Settings, scope=Scope.APP)

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


container = make_async_container(AppProvider(), context={Settings: settings})
