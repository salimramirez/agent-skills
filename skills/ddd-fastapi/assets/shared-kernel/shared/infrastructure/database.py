"""Database engine and session.

One async engine per process, and one :class:`AsyncSession` per request,
obtained through the :func:`get_session` dependency. The session never
commits by itself: the application service that changes an aggregate commits
through the ``UnitOfWork`` port, and a session closed without a commit rolls
back.
"""
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.infrastructure.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True)

# expire_on_commit=False: with the default, reading any attribute after a
# commit triggers a lazy refresh, which an async session cannot do implicitly.
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a session for the duration of one request.

    Yields:
        AsyncSession: A session bound to the shared engine.
    """
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
