"""Application settings.

Read once, at import time, from the environment and from a ``.env`` file in
the working directory. A missing required value stops the application at
start-up, with the variable's name in the error, instead of failing on the
first request that needs it.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings every bounded context shares.

    Attributes:
        app_name (str): Title of the API in the OpenAPI description.
        database_url (str): SQLAlchemy URL with an async driver, e.g.
            ``postgresql+asyncpg://user:password@localhost:5432/dbname``.
        database_echo (bool): Log every SQL statement. For development only.
        docs_enabled (bool): Serve ``/docs``, ``/redoc`` and ``/openapi.json``.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "__project_title__"
    database_url: str
    database_echo: bool = False
    docs_enabled: bool = True


settings = Settings()
