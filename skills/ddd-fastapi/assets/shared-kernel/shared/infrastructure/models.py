"""Declarative base and auditing mixin for every ORM model.

Every context's ``infrastructure/models.py`` declares its tables on
:class:`Base`, so Alembic sees all of them through one ``MetaData``. The naming
convention gives every index and constraint a predictable name, which is what
lets Alembic drop or alter them in a later migration.
"""
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base shared by the ORM models of every bounded context."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class AuditableModel:
    """Mixin that adds creation and update timestamps, set by the database.

    Attributes:
        created_at (datetime): When the row was inserted.
        updated_at (datetime): When the row was last updated.
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
