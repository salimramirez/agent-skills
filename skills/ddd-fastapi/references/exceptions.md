# Domain exceptions and error handling

Failures named in the ubiquitous language, and one place that turns them into HTTP responses.

## Three kinds of failure, and the fourth

| The situation | What is raised | Where | Becomes |
| --- | --- | --- | --- |
| A value that cannot be right: a blank name, a negative amount, an unknown role | `DomainError` | value objects, the aggregate, the service building a value object | 400 |
| Something the current state forbids: placing a placed order, an email already registered | `ConflictError` (or a subclass) | the aggregate, for its own state; the service, for uniqueness | 409 |
| A named thing that does not exist | a subclass of `NotFoundError`, `OrderNotFoundError` | the application service | 404 |
| Something this context cannot express with those: wrong credentials | a subclass of `DomainError`, `InvalidCredentialsError` | wherever the rule lives | whatever the context's own handler says |
| The request body or a parameter has the wrong shape | — FastAPI's `RequestValidationError` | before the route runs | 422 |

The hierarchy is in `shared/domain/exceptions.py`:

```python
class DomainError(Exception):
    """A domain rule rejected the input."""


class ConflictError(DomainError):
    """The current state of the domain forbids the operation."""


class NotFoundError(DomainError):
    """A named aggregate does not exist."""
```

Anything else that escapes — a `ValueError`, a `KeyError`, an `IntegrityError` — is a **500**, and should be: it is a bug, not a business outcome. That is why a rule never raises `ValueError`. When every failure is a `ValueError`, the route has to catch it, every catch returns the same 400, and a genuine bug (a `ValueError` from a library, a typo in a conversion) is reported to the client as their mistake.

The one `IntegrityError` that is not quite a bug is a race on a uniqueness rule: two requests can both pass `exists_by_email` and then both insert. The unique constraint in the table is what guarantees the rule; the check in the service is what gives the common case a 409 with a message. If the race matters, close it in the repository adapter — the only layer that knows SQLAlchemy — by catching `IntegrityError` around the `flush` in `save` and raising the same domain exception (`EmailAlreadyRegisteredError`). The application service stays free of SQLAlchemy.

## Named exceptions build their own message

A context's exceptions live in its `domain/exceptions.py`, extend the kernel's, and take what they need to say what went wrong:

```python
class OrderNotFoundError(NotFoundError):
    """No order has the given id."""

    def __init__(self, order_id: int) -> None:
        super().__init__(f"Order with id {order_id} not found")
```

The message is written for the API client — it is what `detail` will say — and never contains a stack trace, a SQL fragment or another user's data.

A context names its own failures even when another context has a similar one: Ordering raises its own `CustomerNotFoundError` when the ACL says a customer does not exist, rather than importing the Customers context's exception.

The application service raises for a missing aggregate; it does not return `None` for the route to check. Raising is what keeps every 404 identical and every route one line.

## One handler for the kernel's kinds

`shared/interfaces/exception_handlers.py` maps the three kinds to status codes, in one place:

```python
STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DomainError: status.HTTP_400_BAD_REQUEST,
}


async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    status_code = next(code for kind, code in STATUS_BY_ERROR.items() if isinstance(exc, kind))
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
```

It is registered once, on `DomainError`, and catches every subclass: Starlette looks a handler up along the exception's class hierarchy, so `OrderNotFoundError` reaches the `DomainError` handler, which then picks 404 because it is a `NotFoundError`. The table is ordered most specific first — `DomainError` last, or everything would be 400.

The body is `{"detail": "..."}`, the same shape FastAPI uses for its own errors (`HTTPException`, 401 from the bearer scheme, 422 from validation). A client reads `detail` everywhere. The one difference it must handle: for a 422, `detail` is a list of field errors instead of a string.

## A context's own handler, for its own exceptions

When a context has a failure the three kinds do not express, it registers a handler for that exception alone, in its `interfaces/exception_handlers.py`:

```python
async def handle_invalid_credentials(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


def register_iam_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidCredentialsError, handle_invalid_credentials)
```

`InvalidCredentialsError` extends `DomainError`, so both handlers match it; the lookup walks the class hierarchy from the exception's own class upward and takes the first handler it finds, so the more specific one wins regardless of registration order. Measured: the sign-in with a wrong password answers 401, not 400.

Register it in `main.py` next to the shared one. Only the owning context registers a handler for its exception, and never for another context's.

## What routes and services never do

- **A route never catches a domain exception** to turn it into an `HTTPException`. That duplicates the handler, and the next route forgets.
- **The domain never raises `HTTPException`** or knows a status code. `HTTPException` belongs to `interfaces` — `get_current_user` raises one for a bad token, because that failure is about HTTP headers, not the domain.
- **A service never catches and re-raises something vaguer.** `except Exception: raise DomainError("Something went wrong")` hides the bug and blames the client.
