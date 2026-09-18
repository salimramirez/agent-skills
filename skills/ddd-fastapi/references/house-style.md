# House style

The conventions that make this code recognizable, beyond where the files sit.

## A docstring on every module, class and public function

Google style, the format the standard tooling (Sphinx `napoleon`, IDEs, `help()`) reads. A module opens with what it holds and why it exists; a class says what it *is* in the ubiquitous language; a function says what it does, then `Args:`, `Returns:`, `Raises:` as needed.

```python
"""Aggregates and entities of the Ordering bounded context."""
```

```python
class Order(AggregateRoot):
    """What a customer asks for, from draft until placed or cancelled.

    Every rule about an order is a method here: lines can only be added while
    it is a draft, an empty order cannot be placed, and only a placed order
    can be cancelled.

    Attributes:
        id (int | None): Identity assigned when the order is first saved.
        customer_id (CustomerId): Who the order is for.
        status (OrderStatus): Where the order is in its life.
    """
```

```python
    def place(self) -> None:
        """Send the order to the restaurant.

        Raises:
            ConflictError: If the order is not a draft, or has no lines.
        """
```

What goes in, and what stays out:

- **`Raises:` is part of the contract.** A reader of the application service learns which HTTP statuses a route can answer from it; list the domain exceptions a method raises, by name.
- **Say the rule, not the type.** The type hint already says `int`; the docstring says "at least one".
- **An implementation of a port method carries no docstring.** The contract is written once, on the `ABC` in `domain/repositories.py` or `application/outbound_services.py`, and `help()`, `inspect.getdoc()` and IDEs show the port's docstring on the override. A second copy on the override would drift.
- **A route's docstring is its OpenAPI description** — FastAPI copies it. Keep it one line, written for the API client: "Send a draft order to the restaurant."
- **Private helpers (`_require_name`) need none** unless they are not obvious.

## Type hints everywhere, checked

Every function signature is fully annotated, including `-> None`. The project runs `mypy --strict` with the Pydantic plugin (`[tool.mypy]` in `pyproject.toml`), and the shipped code passes it. Use the modern spellings: `int | None`, `list[Order]`, `collections.abc.Iterable`, `type` aliases on 3.12.

An identity is `int | None` on the entity — `None` until the first save — so a response schema narrows it with `assert order.id is not None` before building the response. That assertion documents an invariant (a stored aggregate always has an id), and mypy relies on it.

## Names

- **The ubiquitous language, in snake_case.** `open_order`, `place_order`, `delivery_address`. Never `Data`, `Info`, `Manager`, `Helper`, `Util`, `Handler` as a class name.
- **Application service methods are use cases**: a verb of the domain plus the aggregate — `place_order`, `register_customer`, `cancel_order` — or `get_<aggregate>_by_id` / `get_all_<aggregates>` for reads.
- **Repository methods read like a collection**: `save`, `find_by_id`, `find_all`, `exists_by_email`, `delete`.
- **Private state is a single underscore** (`self._status`), exposed read-only with `@property`, changed only by methods that enforce the rule.
- **Constants are UPPER_CASE at module level**; enum members too (`OrderStatus.PLACED`).

## Imports

Absolute, from the project root, one statement per module: `from ordering.domain.entities import Order, OrderLine`. Never relative (`from ..domain import`): the context name at the front of every import is how a reader sees which contexts a module touches. `ruff check --fix` keeps them sorted — run it after pasting the lines a script prints into `main.py` or `alembic/env.py`.

## Collaborators come in through `__init__`

An application service, a repository adapter or a facade receives what it needs as constructor arguments, typed with the port — never builds its own, never reaches for a module-level global. The one place that builds them is `interfaces/dependencies.py`. That is what makes a service testable with an in-memory repository and nothing else.

The exception is the process-wide singletons of the kernel — `settings`, `engine`, `event_bus` — which are created once, at import, on purpose.

## Formatting and linting

`ruff` with the rule set in `pyproject.toml` (`E`, `F`, `I`, `UP`, `B`, `SIM`, `ASYNC`), line length 120. `ASYNC` flags the blocking calls it can recognize inside `async def` — `time.sleep`, `requests`, `open()` — see `async.md` for the ones it cannot. Generated migrations are excluded; read them instead.

## Smells, by layer

**Domain**
- An import from `fastapi`, `pydantic` or `sqlalchemy`.
- A public attribute that callers assign (`order.status = "PLACED"`). State changes through methods.
- An entity with no methods but its constructor — the rules went somewhere else. Find them.
- A `ValueError` or bare `Exception` raised for a business rule. Use the kernel's hierarchy (`exceptions.md`).
- `async def` anywhere. The domain does not wait for anything.

**Application**
- An `if` on an aggregate's state (`if order.status == …`) — that decision belongs in a method of the aggregate.
- An import from its own `infrastructure`. The service knows ports, not adapters.
- A method that changes an aggregate and never commits, or commits twice.
- Reaching into another context's repository or models instead of its facade.

**Infrastructure**
- A model returned out of the repository. Map it to the entity first.
- Business logic in the mapping (`status = "PLACED" if … else …`).
- Relationships to another context's table.

**Interfaces**
- A route that does anything but call one service method and build one response.
- An entity returned directly from a route, or used as a request body.
- A `try/except` in a route translating a domain exception into an `HTTPException` — that is what the exception handlers are for.
- A schema validator (`@field_validator`) that repeats a domain rule.
