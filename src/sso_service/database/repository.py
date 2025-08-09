from typing import TypeVar

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.domain import Client, Realm, User, Group
from ..core.exceptions import (
    AlreadyExistsError,
    CreationError,
    DeletionError,
    ReadingError,
    UpdateError,
)
from .base import Base
from .models import ClientModel, RealmModel, UserModel, GroupModel, UserGroupModel

Model = TypeVar("Model", bound=Base)
Schema = TypeVar("Schema", bound=BaseModel)


class CRUDRepository[Model: Base, Schema: BaseModel]:
    model: type[Model]
    schema: type[Schema]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, schema: Schema) -> Schema:
        try:
            stmt = insert(self.model).values(**schema.model_dump()).returning(self.model)
            result = await self.session.execute(stmt)
            await self.session.commit()
            created_model = result.scalar_one()
            return self.schema.model_validate(created_model)
        except IntegrityError as e:
            await self.session.rollback()
            raise AlreadyExistsError(f"Already created error: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise CreationError(f"Error while creation: {e}") from e

    async def read(self, id: UUID) -> Schema | None:  # noqa: A002
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return self.schema.model_validate(model) if model else None
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading: {e}") from e

    async def update(self, id: UUID, **kwargs) -> Schema | None:  # noqa: A002
        try:
            stmt = (
                update(self.model)
                .values(**kwargs)
                .where(self.model.id == id)
                .returning(self.model)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            updated_model = result.scalar_one_or_none()
            return self.schema.model_validate(updated_model) if updated_model else None
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise UpdateError(f"Error while update: {e}") from e

    async def delete(self, id: UUID) -> bool:  # noqa: A002
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DeletionError(f"Error while deletion: {e}") from e
        else:
            return result.rowcount > 0


class RealmRepository(CRUDRepository[RealmModel, Realm]):
    model = RealmModel
    schema = Realm

    async def read_all(self, limit: int, page: int) -> list[Realm]:
        try:
            offset = (page - 1) * limit
            stmt = select(self.model).offset(offset).limit(limit)
            results = await self.session.execute(stmt)
            models = results.scalars().all()
            return [Realm.model_validate(model) for model in models]
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading all realms: {e}") from e

    async def get_by_slug(self, slug: str) -> Realm | None:
        try:
            stmt = select(RealmModel).where(self.model.slug == slug)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return self.schema.model_validate(model) if model else None
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading realm: {e}") from e


class ClientRepository(CRUDRepository[ClientModel, Client]):
    model = ClientModel
    schema = Client

    async def get_by_realm(self, realm_id: UUID) -> list[Client]:
        try:
            stmt = select(self.model).where(self.model.realm_id == realm_id)
            results = await self.session.execute(stmt)
            models = results.scalars().all()
            return [self.schema.model_validate(model) for model in models]
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading: {e}") from e

    async def get_by_client_id(self, realm_slug: str, client_id: str) -> Client | None:
        try:
            stmt = (
                select(self.model)
                .join(self.model.realm)
                .where(
                    (RealmModel.slug == realm_slug) &
                    (self.model.client_id == client_id)
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return self.schema.model_validate(model) if model else None
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading: {e}") from e


class UserRepository(CRUDRepository[UserModel, User]):
    model = UserModel
    schema = User

    async def get_by_email(self, email: str) -> User | None:
        try:
            stmt = select(UserModel).where(self.model.email == email)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return self.schema.model_validate(model) if model else None
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading: {e}") from e


class GroupRepository(CRUDRepository[GroupModel, Group]):
    model = GroupModel
    schema = Group

    async def get_by_user(self, realm_slug: str, user_id: UUID) -> list[Group]:
        try:
            stmt = (
                select(self.model)
                .join(RealmModel, GroupModel.realm_id == RealmModel.id)
                .join(UserGroupModel, GroupModel.id == UserGroupModel.group_id)
                .where(
                    (UserGroupModel.user_id == user_id) &
                    (RealmModel.slug == realm_slug)
                )
                .options(joinedload(GroupModel.realm))
            )
            results = await self.session.execute(stmt)
            models = results.scalars().all()
            return [
                self.schema.model_validate(model) for model in models
            ]
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ReadingError(f"Error while reading: {e}") from e
