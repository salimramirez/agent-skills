"""Entry point of the __project_title__ API.

Assembles the application: registers every bounded context's router, the
exception handlers and the event handlers, and disposes of the database
engine on shutdown. The schema is Alembic's job (``alembic upgrade head``),
never this module's.

Run it with::

    fastapi dev main.py
"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from shared.infrastructure.database import engine
from shared.infrastructure.settings import settings
from shared.interfaces.exception_handlers import register_exception_handlers

# Uvicorn configures its own loggers only; without this, the application's
# INFO messages (an event handler's, for one) are silently dropped.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start-up and shutdown work that must happen exactly once per process."""
    yield
    await engine.dispose()


def route_name_as_operation_id(route: APIRoute) -> str:
    """Use the route function's name as its OpenAPI ``operationId``."""
    return route.name


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    generate_unique_id_function=route_name_as_operation_id,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

register_exception_handlers(app)
