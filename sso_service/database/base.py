from typing import Annotated

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

StrNullable = Annotated[str | None, mapped_column(nullable=True)]
StringArray = Annotated[list[str], mapped_column(ARRAY(String))]
StrUnique = Annotated[str, mapped_column(unique=True)]
TextNullable = Annotated[str | None, mapped_column(Text, nullable=True)]
PostgresUUID = Annotated[UUID, mapped_column(PG_UUID(as_uuid=True), unique=False)]
DatetimeNullable = Annotated[datetime | None, mapped_column(DateTime, nullable=True)]


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def create_sessionmaker(sqlalchemy_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url=sqlalchemy_url, echo=True)
    return async_sessionmaker(
        engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
    )
