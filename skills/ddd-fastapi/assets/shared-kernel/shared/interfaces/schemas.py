"""Response schemas every bounded context shares."""
from typing import Any

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """A short confirmation for an action that returns no resource.

    Attributes:
        message (str): What happened, written for the API client.
    """

    message: str


class ErrorResponse(BaseModel):
    """The body of every error response, in the shape FastAPI itself uses.

    Attributes:
        detail (str): What went wrong, written for the API client.
    """

    detail: str


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Document error statuses of a route in OpenAPI, all with :class:`ErrorResponse`.

    Use it as ``responses=error_responses(404, 409)`` on a route decorator.

    Args:
        *status_codes (int): The error statuses the route can answer with.

    Returns:
        dict[int | str, dict[str, Any]]: The ``responses`` argument FastAPI expects.
    """
    return {code: {"model": ErrorResponse} for code in status_codes}
