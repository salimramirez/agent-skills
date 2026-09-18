"""HTTP translation of the IAM bounded context's own exceptions."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from iam.domain.exceptions import InvalidCredentialsError


async def handle_invalid_credentials(request: Request, exc: Exception) -> JSONResponse:
    """Answer a failed sign-in with 401 and the reason."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


def register_iam_exception_handlers(app: FastAPI) -> None:
    """Register the IAM handlers; more specific than the shared one, so they win."""
    app.add_exception_handler(InvalidCredentialsError, handle_invalid_credentials)
