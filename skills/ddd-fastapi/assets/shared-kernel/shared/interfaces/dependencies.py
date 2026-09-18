"""Request-scoped dependencies every bounded context shares.

Each context's ``interfaces/dependencies.py`` builds its application service
on :data:`SessionDep`, so every collaborator of one request shares one
session, and with it one transaction.
"""
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.infrastructure.database import session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a session for the duration of one request.

    Yields:
        AsyncSession: A session bound to the shared engine.
    """
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
