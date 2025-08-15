from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    Base,
    DatetimeNullable,
    PostgresUUID,
    StringArray,
    StrNullable,
    StrUnique,
    TextNullable,
)


class UserModel(Base):
    __tablename__ = "users"

    email: Mapped[StrNullable]
    username: Mapped[StrNullable]
    password: Mapped[StrNullable]
    status: Mapped[str]

    identities: Mapped[list["UserIdentityModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    user_groups: Mapped[list["UserGroupModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class GroupModel(Base):
    __tablename__ = "groups"

    realm_id: Mapped[UUID] = mapped_column(ForeignKey("realms.id"), unique=False)
    name: Mapped[str]
    description: Mapped[TextNullable]
    roles: Mapped[StringArray]

    realm: Mapped["RealmModel"] = relationship(back_populates="groups")
    user_groups: Mapped[list["UserGroupModel"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        single_parent=True
    )


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=False)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id"), unique=False)

    group: Mapped["GroupModel"] = relationship(back_populates="user_groups")
    user: Mapped["UserModel"] = relationship(back_populates="user_groups")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="user_group_uc"),
    )


class RealmModel(Base):
    __tablename__ = "realms"

    name: Mapped[StrUnique]
    slug: Mapped[StrUnique]
    description: Mapped[TextNullable]
    enabled: Mapped[bool]

    clients: Mapped[list["ClientModel"]] = relationship(back_populates="realm")
    groups: Mapped[list["GroupModel"]] = relationship(back_populates="realm")


class ClientModel(Base):
    __tablename__ = "clients"

    realm_id: Mapped[UUID] = mapped_column(
        ForeignKey("realms.id"), unique=False, nullable=False
    )
    client_id: Mapped[StrUnique]
    client_secret: Mapped[StrUnique]
    name: Mapped[StrUnique]
    description: Mapped[TextNullable]
    expires_at: Mapped[DatetimeNullable]
    enabled: Mapped[bool]
    client_type: Mapped[str]
    grant_types: Mapped[StringArray]
    redirect_uris: Mapped[StringArray]
    scopes: Mapped[StringArray]

    realm: Mapped["RealmModel"] = relationship(back_populates="clients")

    __table_args__ = (UniqueConstraint("realm_id", "client_id", name="client_uq"),)


class IdentityProviderModel(Base):
    __tablename__ = "identity_providers"

    name: Mapped[StrUnique]
    protocol: Mapped[str]
    scopes: Mapped[StringArray]


class UserIdentityModel(Base):
    __tablename__ = "user_identities"

    user_id: Mapped[PostgresUUID]
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_providers.id"), unique=False
    )
    provider_user_id: Mapped[StrUnique]
    email: Mapped[StrNullable]

    __table_args__ = (
        UniqueConstraint("user_id", "provider_user_id", name="identity_uq"),
    )
