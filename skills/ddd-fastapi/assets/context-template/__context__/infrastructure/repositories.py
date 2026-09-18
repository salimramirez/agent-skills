"""SQLAlchemy implementation of the __Context_title__ repository port.

The repository is the only place that knows both the aggregate and its table:
it maps one to the other in both directions, so neither has to know about the
other.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from __context__.domain.entities import __Entity__
from __context__.domain.repositories import __Entity__Repository
from __context__.infrastructure.models import __Entity__Model


class SqlAlchemy__Entity__Repository(__Entity__Repository):
    """Stores :class:`__Entity__` aggregates in the ``__entities__`` table."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository on the request's session.

        Args:
            session (AsyncSession): The session of the current unit of work.
        """
        self._session = session

    async def save(self, __entity__: __Entity__) -> __Entity__:
        model = await self._session.merge(self._to_model(__entity__))
        await self._session.flush()
        return self._to_entity(model)

    async def find_by_id(self, __entity___id: int) -> __Entity__ | None:
        model = await self._session.get(__Entity__Model, __entity___id)
        return self._to_entity(model) if model else None

    async def find_all(self) -> list[__Entity__]:
        models = await self._session.scalars(select(__Entity__Model).order_by(__Entity__Model.id))
        return [self._to_entity(model) for model in models]

    async def delete(self, __entity__: __Entity__) -> None:
        model = await self._session.get(__Entity__Model, __entity__.id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    @staticmethod
    def _to_model(__entity__: __Entity__) -> __Entity__Model:
        return __Entity__Model(id=__entity__.id, name=__entity__.name)

    @staticmethod
    def _to_entity(model: __Entity__Model) -> __Entity__:
        return __Entity__(model.name, id=model.id)
