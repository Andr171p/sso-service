from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class UserModel(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(nullable=True)
    email_verified: Mapped[bool]
    username: Mapped[str | None] = mapped_column(nullable=True)
    password: Mapped[str]
    active: Mapped[bool]

    user_groups: Mapped[list["UserGroupModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class GroupModel(Base):
    __tablename__ = "groups"

    realm_id: Mapped[UUID] = mapped_column(ForeignKey("realms.id"), unique=False)
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(nullable=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String))

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

    name: Mapped[str] = mapped_column(unique=True)
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool]

    clients: Mapped[list["ClientModel"]] = relationship(back_populates="realm")
    groups: Mapped[list["GroupModel"]] = relationship(back_populates="realm")


class ClientModel(Base):
    __tablename__ = "clients"

    realm_id: Mapped[UUID] = mapped_column(
        ForeignKey("realms.id"), unique=False, nullable=False
    )
    client_id: Mapped[str] = mapped_column(unique=True)
    client_secret: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool]
    client_type: Mapped[str]
    grant_types: Mapped[list[str]] = mapped_column(ARRAY(String))
    redirect_uris: Mapped[list[str]] = mapped_column(ARRAY(String))
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String))

    realm: Mapped["RealmModel"] = relationship(back_populates="clients")

    __table_args__ = (UniqueConstraint("realm_id", "client_id", name="client_uq"),)


class IdentityProviderModel(Base):
    __tablename__ = "identity_providers"

    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[str]
    client_id: Mapped[str] = mapped_column(unique=True)
    client_secret: Mapped[str] = mapped_column(unique=True)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String))


class UserIdentityModel(Base):
    __tablename__ = "user_identities"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), unique=False)
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_providers.id"), unique=False
    )
    provider_user_id: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "provider_user_id", name="identity_uq"),
    )
