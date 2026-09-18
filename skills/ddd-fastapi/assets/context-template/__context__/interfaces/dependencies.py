"""Dependency wiring of the __Context_title__ bounded context.

The one place that chooses the concrete repository for each port. Routes ask
for the application service by its annotated alias and never build it.
"""
from typing import Annotated

from fastapi import Depends

from __context__.application.services import __Entity__ApplicationService
from __context__.infrastructure.repositories import SqlAlchemy__Entity__Repository
from shared.infrastructure.database import SessionDep


def get___entity___service(session: SessionDep) -> __Entity__ApplicationService:
    """Build the application service on the request's session.

    Args:
        session (AsyncSession): The session of the current request.

    Returns:
        __Entity__ApplicationService: The service for this request.
    """
    return __Entity__ApplicationService(SqlAlchemy__Entity__Repository(session), session)


__Entity__ServiceDep = Annotated[__Entity__ApplicationService, Depends(get___entity___service)]
