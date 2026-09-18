"""REST routes of the __Context_title__ bounded context.

Each route translates the request into one call on the application service
and the result into a response schema. No business decision is made here.
"""
from fastapi import APIRouter, status

from __context__.interfaces.dependencies import __Entity__ServiceDep
from __context__.interfaces.schemas import Create__Entity__Request, Update__Entity__Request, __Entity__Response
from shared.interfaces.schemas import error_responses

router = APIRouter(prefix="/api/v1/__entities-kebab__", tags=["__Entities_title__"])


@router.post("", status_code=status.HTTP_201_CREATED, responses=error_responses(400))
async def create___entity__(request: Create__Entity__Request, service: __Entity__ServiceDep) -> __Entity__Response:
    """Create a __entity_words__."""
    return __Entity__Response.from_entity(await service.create___entity__(request.name))


@router.get("")
async def get_all___entities__(service: __Entity__ServiceDep) -> list[__Entity__Response]:
    """List every __entity_words__."""
    return [__Entity__Response.from_entity(__entity__) for __entity__ in await service.get_all___entities__()]


@router.get("/{__entity___id}", responses=error_responses(404))
async def get___entity___by_id(__entity___id: int, service: __Entity__ServiceDep) -> __Entity__Response:
    """Get one __entity_words__."""
    return __Entity__Response.from_entity(await service.get___entity___by_id(__entity___id))


@router.put("/{__entity___id}", responses=error_responses(400, 404))
async def update___entity__(
    __entity___id: int, request: Update__Entity__Request, service: __Entity__ServiceDep
) -> __Entity__Response:
    """Replace a __entity_words__'s name."""
    return __Entity__Response.from_entity(await service.update___entity__(__entity___id, request.name))


@router.delete("/{__entity___id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404))
async def delete___entity__(__entity___id: int, service: __Entity__ServiceDep) -> None:
    """Remove a __entity_words__."""
    await service.delete___entity__(__entity___id)
