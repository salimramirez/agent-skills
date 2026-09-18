"""Repository port of the __Context_title__ bounded context.

The domain says what it needs from persistence; ``infrastructure`` says how.
The methods are ``async`` because every implementation does I/O, but the
domain objects themselves never await anything.
"""
from abc import ABC, abstractmethod

from __context__.domain.entities import __Entity__


class __Entity__Repository(ABC):
    """Collection-like access to :class:`__Entity__` aggregates."""

    @abstractmethod
    async def save(self, __entity__: __Entity__) -> __Entity__:
        """Insert or update a __entity_words__.

        Returns:
            __Entity__: The aggregate as stored, with its ``id`` assigned.
        """

    @abstractmethod
    async def find_by_id(self, __entity___id: int) -> __Entity__ | None:
        """Return the __entity_words__ with the given id, or ``None``."""

    @abstractmethod
    async def find_all(self) -> list[__Entity__]:
        """Return every __entity_words__, ordered by id."""

    @abstractmethod
    async def delete(self, __entity__: __Entity__) -> None:
        """Remove a __entity_words__."""
