"""Application service of the __Context_title__ bounded context.

Each method is one use case: it loads what it needs through the repository,
asks the aggregate to act, saves it and commits. It holds no business rule.
"""
from __context__.domain.entities import __Entity__
from __context__.domain.exceptions import __Entity__NotFoundError
from __context__.domain.repositories import __Entity__Repository
from shared.application.unit_of_work import UnitOfWork


class __Entity__ApplicationService:
    """Use cases that create, change, read and remove __entities_words__."""

    def __init__(self, __entity___repository: __Entity__Repository, unit_of_work: UnitOfWork) -> None:
        """Initialize the service with its collaborators.

        Args:
            __entity___repository (__Entity__Repository): Access to __entities_words__.
            unit_of_work (UnitOfWork): The transaction to commit.
        """
        self.___entities__ = __entity___repository
        self._unit_of_work = unit_of_work

    async def create___entity__(self, name: str) -> __Entity__:
        """Create a __entity_words__.

        Returns:
            __Entity__: The stored __entity_words__, with its ``id``.

        Raises:
            DomainError: If the name is blank.
        """
        __entity__ = await self.___entities__.save(__Entity__(name))
        await self._unit_of_work.commit()
        return __entity__

    async def update___entity__(self, __entity___id: int, name: str) -> __Entity__:
        """Rename a __entity_words__.

        Returns:
            __Entity__: The __entity_words__ as stored after the change.

        Raises:
            __Entity__NotFoundError: If no __entity_words__ has the id.
            DomainError: If the name is blank.
        """
        __entity__ = await self.get___entity___by_id(__entity___id)
        __entity__.rename(name)
        __entity__ = await self.___entities__.save(__entity__)
        await self._unit_of_work.commit()
        return __entity__

    async def delete___entity__(self, __entity___id: int) -> None:
        """Remove a __entity_words__.

        Raises:
            __Entity__NotFoundError: If no __entity_words__ has the id.
        """
        __entity__ = await self.get___entity___by_id(__entity___id)
        await self.___entities__.delete(__entity__)
        await self._unit_of_work.commit()

    async def get___entity___by_id(self, __entity___id: int) -> __Entity__:
        """Return one __entity_words__.

        Raises:
            __Entity__NotFoundError: If no __entity_words__ has the id.
        """
        __entity__ = await self.___entities__.find_by_id(__entity___id)
        if __entity__ is None:
            raise __Entity__NotFoundError(__entity___id)
        return __entity__

    async def get_all___entities__(self) -> list[__Entity__]:
        """Return every __entity_words__, ordered by id."""
        return await self.___entities__.find_all()
