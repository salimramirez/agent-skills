"""HTTP translation of the shared domain exceptions.

The domain raises exceptions that say what kind of failure happened; this
module is the one place that decides which status code each kind becomes. A
bounded context with an exception of its own registers its own handler in its
``interfaces`` package; the most specific handler for an exception's class
wins.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shared.domain.exceptions import ConflictError, DomainError, NotFoundError

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DomainError: status.HTTP_400_BAD_REQUEST,
}


async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    """Turn a domain exception into ``{"detail": message}`` with its status.

    Args:
        request (Request): The request that failed.
        exc (Exception): The domain exception raised while handling it.

    Returns:
        JSONResponse: The error response.
    """
    status_code = next(code for kind, code in STATUS_BY_ERROR.items() if isinstance(exc, kind))
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """Register the shared domain exception handler on the application.

    Args:
        app (FastAPI): The application being assembled in ``main.py``.
    """
    app.add_exception_handler(DomainError, handle_domain_error)
