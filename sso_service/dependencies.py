from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, make_async_container, provide
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .core.base import BaseStore
from .core.domain import Codes, Session
from .database.base import create_sessionmaker
from .database.repository import (
    ClientRepository,
    GroupRepository,
    IdentityProviderRepository,
    RealmRepository,
    UserRepository,
)
from .providers import (
    ClientCredentialsProvider,
    UserCredentialsProvider,
    VKProvider,
    YandexProvider,
)
from .services import ClientTokenService, UserTokenService
from .settings import Settings, settings
from .storage import RedisCodesStore, RedisSessionStore


class AppProvider(Provider):
    app_settings = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_redis(self, app_settings: Settings) -> AsyncRedis:  # noqa: PLR6301
        return AsyncRedis.from_url(app_settings.redis.url)

    @provide(scope=Scope.APP)
    def get_sessionmaker(self) -> async_sessionmaker[AsyncSession]:  # noqa: PLR6301
        return create_sessionmaker()

    @provide(scope=Scope.REQUEST)
    async def get_session(  # noqa: PLR6301
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
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
    def get_provider_repository(self, session: AsyncSession) -> IdentityProviderRepository:  # noqa: PLR6301
        return IdentityProviderRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_group_repository(self, session: AsyncSession) -> GroupRepository:  # noqa: PLR6301
        return GroupRepository(session)

    @provide(scope=Scope.APP)
    def get_session_store(self, redis: AsyncRedis) -> BaseStore[Session]:  # noqa: PLR6301
        return RedisSessionStore(redis, prefix="session")

    @provide(scope=Scope.APP)
    def get_codes_store(self, redis: AsyncRedis) -> BaseStore[Codes]:  # noqa: PLR6301
        return RedisCodesStore(redis, prefix="codes")

    @provide(scope=Scope.REQUEST)
    def get_client_token_service(self) -> ClientTokenService:  # noqa: PLR6301
        return ClientTokenService()

    @provide(scope=Scope.REQUEST)
    def get_user_token_service(  # noqa: PLR6301
        self,
        user_repository: UserRepository,
        realm_repository: RealmRepository,
        session_store: BaseStore[Session],
    ) -> UserTokenService:
        return UserTokenService(user_repository, realm_repository, session_store)

    @provide(scope=Scope.REQUEST)
    def get_client_credentials_provider(  # noqa: PLR6301
        self, repository: ClientRepository
    ) -> ClientCredentialsProvider:
        return ClientCredentialsProvider(repository)

    @provide(scope=Scope.REQUEST)
    def get_user_credentials_provider(  # noqa: PLR6301
        self, repository: UserRepository, session_store: BaseStore[Session]
    ) -> UserCredentialsProvider:
        return UserCredentialsProvider(repository, session_store)

    @provide(scope=Scope.REQUEST)
    def get_vk_provider(  # noqa: PLR6301
        self,
        provider_repository: IdentityProviderRepository,
        user_repository: UserRepository,
        codes_store: BaseStore[Codes],
        session_store: BaseStore[Session],
    ) -> VKProvider:
        return VKProvider(
            provider_repository=provider_repository,
            user_repository=user_repository,
            session_store=session_store,
            codes_store=codes_store,
        )

    @provide(scope=Scope.REQUEST)
    def get_yandex_provider(  # noqa: PLR6301
        self,
        provider_repository: IdentityProviderRepository,
        user_repository: UserRepository,
        codes_store: BaseStore[Codes],
        session_store: BaseStore[Session],
    ) -> YandexProvider:
        return YandexProvider(
            provider_repository=provider_repository,
            user_repository=user_repository,
            session_store=session_store,
            codes_store=codes_store,
        )


container = make_async_container(AppProvider(), context={Settings: settings})
