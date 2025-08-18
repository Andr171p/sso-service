from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, make_async_container, provide
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sso_service.rest import VKApi, YandexApi

from .database.base import create_sessionmaker
from .database.repository import (
    ClientRepository,
    GroupRepository,
    IdentityProviderRepository,
    RealmRepository,
    UserIdentityRepository,
    UserRepository,
)
from .providers.vk import VKControl
from .providers.yandex import YandexControl
from .services import ClientAuthService, UserAuthService
from .settings import Settings, settings
from .storage import RedisSessionStore, RedisStorage


class AppProvider(Provider):
    app_settings = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_redis(self, app_settings: Settings) -> AsyncRedis:  # noqa: PLR6301
        return AsyncRedis.from_url(app_settings.redis.url)

    @provide(scope=Scope.APP)
    def get_sessionmaker(  # noqa: PLR6301
        self, app_settings: Settings
    ) -> async_sessionmaker[AsyncSession]:
        return create_sessionmaker(app_settings.postgres.sqlalchemy_url)

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
    def get_identity_repository(self, session: AsyncSession) -> IdentityProviderRepository:  # noqa: PLR6301
        return IdentityProviderRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_user_identity_repository(self, session: AsyncSession) -> UserIdentityRepository:  # noqa: PLR6301
        return UserIdentityRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_group_repository(self, session: AsyncSession) -> GroupRepository:  # noqa: PLR6301
        return GroupRepository(session)

    @provide(scope=Scope.APP)
    def get_session_store(self, redis: AsyncRedis) -> RedisSessionStore:  # noqa: PLR6301
        return RedisSessionStore(redis)

    @provide(scope=Scope.APP)
    def get_codes_store(self, redis: AsyncRedis) -> RedisStorage:  # noqa: PLR6301
        return RedisStorage(redis)

    @provide(scope=Scope.REQUEST)
    def get_client_auth_service(  # noqa: PLR6301
        self, repository: ClientRepository
    ) -> ClientAuthService:
        return ClientAuthService(repository)

    @provide(scope=Scope.REQUEST)
    def get_vk_api(  # noqa: PLR6301
        self,
    ) -> VKApi:
        return VKApi()

    @provide(scope=Scope.REQUEST)
    def get_yandex_api(  # noqa: PLR6301
        self,
    ) -> YandexApi:
        return YandexApi()

    @provide(scope=Scope.REQUEST)
    def get_user_auth_service(  # noqa: PLR6301
        self,
        user_repository: UserRepository,
        group_repository: GroupRepository,
        realm_repository: RealmRepository,
        session_store: RedisSessionStore,
    ) -> UserAuthService:
        return UserAuthService(
            user_repository=user_repository,
            group_repository=group_repository,
            realm_repository=realm_repository,
            session_store=session_store,
        )

    @provide(scope=Scope.REQUEST)
    def get_vk_control(  # noqa: PLR6301
        self,
        user_auth_service: UserAuthService,
        user_repository: UserRepository,
        user_identity_repository: UserIdentityRepository,
        identity_repository: IdentityProviderRepository,
        redis: RedisStorage,
        api: VKApi,
    ) -> VKControl:
        return VKControl(
            user_auth_service=user_auth_service,
            user_repository=user_repository,
            user_identity_repository=user_identity_repository,
            identity_repository=identity_repository,
            redis=redis,
            api=api,
        )

    @provide(scope=Scope.REQUEST)
    def get_yandex_control(  # noqa: PLR6301
        self,
        user_auth_service: UserAuthService,
        user_repository: UserRepository,
        user_identity_repository: UserIdentityRepository,
        identity_repository: IdentityProviderRepository,
        redis: RedisStorage,
        api: YandexApi,
    ) -> YandexControl:
        return YandexControl(
            user_auth_service=user_auth_service,
            user_repository=user_repository,
            user_identity_repository=user_identity_repository,
            identity_repository=identity_repository,
            redis=redis,
            api=api,
        )


container = make_async_container(AppProvider(), context={Settings: settings})
