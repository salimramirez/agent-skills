# Project setup

What `pyproject.toml`, the environment, the settings, `main.py` and Alembic look like before the first context goes in.

The fastest way to get all of it is the installer, run in an empty directory:

```bash
SKILL=.claude/skills/ddd-fastapi
python3 "$SKILL/scripts/install.py" project --name "QuickBite Platform"
```

It writes everything below plus the shared kernel. The rest of this file explains what it wrote.

## `pyproject.toml`

```toml
[project]
name = "quickbite-platform"
version = "0.1.0"
description = "QuickBite Platform API"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.122",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.16",
    "pydantic-settings>=2.6",
]

[dependency-groups]
dev = [
    "ruff>=0.8",
    "mypy>=1.13",
]

# An application, not a library: install its dependencies, never the project itself.
# The directories next to main.py are bounded contexts, not packages to distribute.
[tool.uv]
package = false

[tool.setuptools]
packages = []
```

Why each floor is where it is:

- **`fastapi[standard]>=0.122`** — `[standard]` brings `uvicorn`, the `fastapi` command and `httpx`. From 0.122 a missing bearer token is answered **401** with `WWW-Authenticate: Bearer`; before it, `HTTPBearer` answered 403.
- **`sqlalchemy[asyncio]`** — the extra pulls `greenlet`, which the async session needs.
- **`alembic>=1.16`** — the version the shipped setup was run on at its lowest, and the one that introduced `path_separator` in `alembic.ini`. Without that key, current Alembic falls back to legacy path splitting and emits a `DeprecationWarning` (hidden by default); older versions simply ignore it.
- The IAM context adds `pyjwt` and `pwdlib[argon2]`; `iam.md` says so.

`[tool.uv] package = false` and `[tool.setuptools] packages = []` say the same thing to the two installers: there is nothing here to build. Without the second line, `pip install .` fails on a project laid out like this one, with "Multiple top-level packages discovered in a flat-layout".

## The virtual environment

Both routes create a `.venv/` in the project root and install into it; nothing goes into the system Python.

With **uv**, which creates and syncs the environment itself:

```bash
uv sync
```

```bash
uv run fastapi dev main.py
```

`uv run` executes inside `.venv/` without activating it; `uv add pyjwt` adds a dependency to `pyproject.toml` and installs it; `uv.lock` pins every version and is committed.

With **pip**:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install . --group dev
```

`--group` needs pip 25.1 or later; with an older pip, install `ruff` and `mypy` by hand. There is no lock file on this route.

## Settings

`shared/infrastructure/settings.py` reads the environment, and a `.env` file in the working directory, into one `Settings` object at import time:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "QuickBite Platform"
    database_url: str
    database_echo: bool = False
    docs_enabled: bool = True


settings = Settings()
```

`database_url` has no default on purpose. Without it the application does not start: the `ValidationError` names the field (`database_url`, `Field required`), instead of the first request failing somewhere deeper. A context with settings of its own gives them their own class and prefix — the IAM context reads `JWT_SECRET` and `JWT_EXPIRATION_DAYS` through `JwtSettings(env_prefix="JWT_")` — so that every variable says which context owns it.

`.env.example` is committed and lists every variable; `.env` holds the real values and is in `.gitignore`:

```bash
DATABASE_URL=postgresql+asyncpg://quickbite:quickbite@localhost:5432/quickbite
DATABASE_ECHO=false
DOCS_ENABLED=true
```

The URL must name the async driver: `postgresql+asyncpg://`. With a plain `postgresql://` SQLAlchemy looks for `psycopg2`, the synchronous default, and the engine fails to start with `No module named 'psycopg2'` — an error that points at a missing package when the mistake is in the URL.

## PostgreSQL

The shipped code was run against PostgreSQL 17. For development, one container is enough:

```bash
docker run -d --name quickbite-db -e POSTGRES_USER=quickbite -e POSTGRES_PASSWORD=quickbite -e POSTGRES_DB=quickbite -p 5432:5432 postgres:17
```

## `main.py`

The application is assembled in one module, in this order: logging, lifespan, the `FastAPI` object, the exception handlers, the routers.

```python
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start-up and shutdown work that must happen exactly once per process."""
    register_ordering_event_handlers(event_bus)
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
register_iam_exception_handlers(app)

authenticated = [Depends(get_current_user)]
unauthenticated = error_responses(401)

app.include_router(authentication_router)
app.include_router(customers_router, dependencies=authenticated, responses=unauthenticated)
app.include_router(ordering_router, dependencies=authenticated, responses=unauthenticated)
```

- **`logging.basicConfig`** — uvicorn configures its own loggers and leaves the root logger at `WARNING` with no handler, so without this line every `logger.info(...)` in the application is dropped.
- **`lifespan`** runs once per process, before the first request is accepted and after the last one. It is the place for start-up work — subscribing event handlers, warming a cache — never a check on the first request. It does **not** create tables: the schema is Alembic's.
- **`generate_unique_id_function`** — by default FastAPI builds operation ids like `place_order_api_v1_orders__order_id__placements_post`; with this, the id is the function name, `place_order`, which is what a generated client will call the method. Function names must then be unique across the application, which `get_<aggregate>_by_id` naming already ensures.
- **One `include_router` per router**, with the authentication dependency on every router but the public one. See `rest.md` and `iam.md`.

Run it with:

```bash
fastapi dev main.py
```

`fastapi dev` reloads on change and serves on `127.0.0.1:8000`; `fastapi run main.py` is the production form (no reload, `0.0.0.0`). The API description is at `/docs` (Swagger UI) and `/redoc`.

## Alembic

`alembic.ini` holds no URL; `alembic/env.py` reads `settings.database_url`, so the database is configured in one place. `env.py` also imports every context's models, because autogenerate compares the database with `Base.metadata`, and a model that was never imported is not in it:

```python
import customers.infrastructure.models  # noqa: F401
import iam.infrastructure.models  # noqa: F401
import ordering.infrastructure.models  # noqa: F401
from shared.infrastructure.models import Base
from shared.infrastructure.settings import settings

target_metadata = Base.metadata
```

That is the order `ruff check --fix` leaves them in; paste each new context's line anywhere in the block and let it sort.

The workflow, every time a model changes:

```bash
alembic revision --autogenerate -m "add delivery address to orders"
```

```bash
alembic upgrade head
```

**Read the generated file before upgrading.** Autogenerate is a diff, not a mind reader: it sees a renamed column as a drop and an add, which loses the data, and it does not compare a changed `server_default` unless `env.py` sets `compare_server_default=True`. The file is ordinary Python; fix it and commit it with the model change. `alembic downgrade -1` undoes the last one; `alembic upgrade head --sql` prints the SQL instead of running it.

The application never calls `Base.metadata.create_all()`. Creating tables at start-up is fine for a demo and a trap for anything with data: it creates what is missing and never changes what exists, so the first renamed column silently diverges from the code.
