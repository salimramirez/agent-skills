"""Request and response schemas of the __Context_title__ REST API.

Requests check the *shape* of the input: presence, types, lengths. Whether a
value is acceptable to the business is the domain's call, so these schemas
never repeat a domain rule.
"""
from pydantic import BaseModel, Field

from __context__.domain.entities import __Entity__


class Create__Entity__Request(BaseModel):
    """Body of ``POST /api/v1/__entities-kebab__``."""

    name: str = Field(min_length=1, max_length=120)


class Update__Entity__Request(BaseModel):
    """Body of ``PUT /api/v1/__entities-kebab__/{__entity___id}``."""

    name: str = Field(min_length=1, max_length=120)


class __Entity__Response(BaseModel):
    """A __entity_words__ as the API returns it."""

    id: int
    name: str

    @classmethod
    def from_entity(cls, __entity__: __Entity__) -> "__Entity__Response":
        """Build the response from the aggregate.

        Args:
            __entity__ (__Entity__): A stored __entity_words__.

        Returns:
            __Entity__Response: Its public representation.
        """
        assert __entity__.id is not None
        return cls(id=__entity__.id, name=__entity__.name)
