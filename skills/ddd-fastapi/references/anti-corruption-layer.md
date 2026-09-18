# Anti-corruption layer

How one bounded context asks another something, without either one knowing the other's model.

## Two halves, one on each side

| Side | Module | Class | Speaks |
| --- | --- | --- | --- |
| **Provider** — the context being asked | `customers/interfaces/acl.py` | `CustomersContextFacade` | primitives in, primitives out |
| **Consumer** — the context asking | `ordering/application/acl.py` | `ExternalCustomerService` | the consumer's own value objects |

Nothing else crosses the line. Ordering never imports from `customers.domain` or `customers.infrastructure`; Customers never knows Ordering exists.

## The provider's facade

```python
class CustomersContextFacade:
    """What other bounded contexts may ask the Customers context."""

    def __init__(self, session: AsyncSession) -> None:
        self._customers = SqlAlchemyCustomerRepository(session)

    async def customer_exists(self, customer_id: int) -> bool:
        """Tell whether a customer with the id exists."""
        return await self._customers.find_by_id(customer_id) is not None
```

- It lives in `interfaces/` because it is an entry point into the context, like a route.
- **Its signatures are primitives** (`int`, `str`, `bool`, or a small dataclass of primitives defined in the facade module). Returning a `Customer` would hand the caller the provider's model, and every change to it would ripple out.
- **Each method answers one question someone actually asks.** Not a generic `get_customer(id) -> dict`; `customer_exists`, `customer_email(customer_id) -> str | None`. The facade is the provider's published language, and it should be small enough to read in one screen.
- **It takes the caller's session**, so the question is answered inside the caller's transaction and sees what the caller sees.
- It may use the provider's repository or application service internally; that is its own business.

## The consumer's service

```python
class ExternalCustomerService:
    """What Ordering needs to know about customers."""

    def __init__(self, customers_facade: CustomersContextFacade) -> None:
        self._customers = customers_facade

    async def exists(self, customer_id: CustomerId) -> bool:
        """Tell whether the customer an order refers to exists."""
        return await self._customers.customer_exists(customer_id.value)
```

- It lives in the consumer's `application/acl.py`, and it is the **only** module of the consumer that imports the provider.
- **It translates**: Ordering's `CustomerId` goes in, the facade's `int` goes out, and the answer comes back in Ordering's terms. If Customers renamed `customer_exists` tomorrow, one line in this file would change.
- The application service depends on it, and on nothing of the provider:

```python
    async def open_order(self, customer_id: int, delivery_address: str) -> Order:
        customer = CustomerId(customer_id)
        if not await self._customers.exists(customer):
            raise CustomerNotFoundError(customer_id)
        ...
```

`CustomerNotFoundError` here is **Ordering's** exception, declared in `ordering/domain/exceptions.py`. The consumer names its own failures.

## Wiring

The consumer's `interfaces/dependencies.py` builds the chain on the request's session:

```python
async def get_order_service(session: SessionDep) -> OrderApplicationService:
    return OrderApplicationService(
        SqlAlchemyOrderRepository(session),
        ExternalCustomerService(CustomersContextFacade(session)),
        session,
        event_bus,
    )
```

## What this replaces

The shortcut is to import the other context's repository straight into the application service — `from customers.infrastructure.repositories import …` — and query it. It works on the first day. From then on the consumer depends on the provider's persistence: a renamed column, a changed finder or a moved table breaks a context that never asked for it, and nothing in the code says the dependency exists except the import. Wrapping the same query in a facade and an external service costs two small classes, and turns that import into a published, named contract.

## When the other context is another system

The same shape holds when the provider is a remote service rather than a package in this codebase. `ExternalCustomerService` stays exactly as it is; what changes is what it calls — an HTTP client (`httpx.AsyncClient`) in `infrastructure/`, behind a port the service depends on, translating the remote payload into this context's value objects. The application service does not change at all, which is the point of having the layer.
