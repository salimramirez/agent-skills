"""Database engine and session factory.

One async engine per process. Sessions come from :data:`session_factory`:
one per request through the ``get_session`` dependency in
``shared.interfaces.dependencies``, or one per unit of work in a script or an
event handler. A session never commits by itself: the application service
that changes an aggregate commits through the ``UnitOfWork`` port, and a
session closed without a commit rolls back.
"""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared.infrastructure.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True)

# expire_on_commit=False: with the default, reading any attribute after a
# commit triggers a lazy refresh, which an async session cannot do implicitly.
session_factory = async_sessionmaker(engine, expire_on_commit=False)
