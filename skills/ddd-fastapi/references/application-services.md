# Application services

One class per aggregate, one method per use case: load, act, save, commit, publish.

## The shape

```python
class OrderApplicationService:
    """Use cases that open, fill, place, cancel and read orders."""

    def __init__(
        self,
        order_repository: OrderRepository,
        customer_service: ExternalCustomerService,
        unit_of_work: UnitOfWork,
        event_bus: EventBus,
    ) -> None:
        self._orders = order_repository
        self._customers = customer_service
        self._unit_of_work = unit_of_work
        self._event_bus = event_bus

    async def open_order(self, customer_id: int, delivery_address: str) -> Order:
        """Open an empty draft order for a customer.

        Raises:
            CustomerNotFoundError: If the customer does not exist.
            DomainError: If the address is blank.
        """
        customer = CustomerId(customer_id)
        if not await self._customers.exists(customer):
            raise CustomerNotFoundError(customer_id)
        order = await self._orders.save(Order(customer, delivery_address))
        await self._unit_of_work.commit()
        return order

    async def place_order(self, order_id: int) -> Order:
        """Send a draft order to the restaurant.

        Raises:
            OrderNotFoundError: If no order has the id.
            ConflictError: If the order is not a draft or has no lines.
        """
        order = await self.get_order_by_id(order_id)
        order.place()
        return await self._save_and_publish(order)

    async def get_order_by_id(self, order_id: int) -> Order:
        """Return one order with its lines.

        Raises:
            OrderNotFoundError: If no order has the id.
        """
        order = await self._orders.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    async def _save_and_publish(self, order: Order) -> Order:
        events = order.pull_events()
        saved = await self._orders.save(order)
        await self._unit_of_work.commit()
        await self._event_bus.publish(events)
        return saved
```

It lives in `application/services.py`. The collaborators come in through `__init__`, typed with their ports; `interfaces/dependencies.py` builds it once per request. See `rest.md`.

## What a method does, in order

1. **Turn primitives into domain types.** The route passes `int`s and `str`s; the service builds `CustomerId(customer_id)`, `Money(unit_price)`. A malformed value fails here, as a `DomainError`, before anything is loaded.
2. **Answer what needs persistence to answer.** Does the customer exist? Is the email taken? These are not rules of one aggregate — the aggregate cannot see other rows — so the service asks, and raises the named exception.
3. **Load the aggregate**, or raise its `…NotFoundError`.
4. **Ask it to act**: `order.place()`. The aggregate decides whether it may.
5. **Save it, commit**, and use what `save` returned — it carries the ids the database assigned.
6. **Publish the events** the aggregate recorded, after the commit.

What it never does: decide a business rule. If a line of the service reads `if order.status == OrderStatus.DRAFT`, that condition belongs in a method of `Order`, and the service should call the method.

## One service, commands and queries together

Reads (`get_order_by_id`, `get_all_orders`) and writes (`open_order`, `place_order`) are methods of the same class. A write method often begins with the read (`place_order` calls `get_order_by_id`), and one class keeps that reuse free. When the reads of a context grow into something different — reports, joins across aggregates, a denormalized view — give them their own port, as `persistence.md` describes under "Queries that are not aggregates", and leave the aggregate out of them.

## The unit of work is the transaction

The application service owns the transaction, and it says so in code: every method that changes state ends with `await self._unit_of_work.commit()`, once. That line is the promise the method makes — everything before it happens, or nothing does.

- **Nothing commits by itself.** The repository flushes (so ids are assigned) but never commits; the session never commits in its teardown. A method that raises before its `commit` leaves nothing behind: the session is closed and the change rolled back.
- **One aggregate per commit.** A method that saves two aggregates in one transaction is a sign the boundary is wrong, or that the second change should react to an event from the first.
- **`UnitOfWork` is a `Protocol`, and the request's `AsyncSession` satisfies it.** The service cannot run a query through it; it can only commit or roll back.

Committing in a `yield` dependency's teardown instead is the common alternative, and it is the wrong one here: by default the teardown runs after the response is sent — measured on FastAPI 0.122 and 0.141: when the teardown raised, the client had already received a 200. A failed commit would report success.

## What each method returns

| Kind of use case | Returns | Why |
| --- | --- | --- |
| creates an aggregate | the saved aggregate | the route needs its id and state for the 201 body |
| changes an aggregate | the saved aggregate | the route answers with the new state; no second query |
| removes an aggregate | `None` | the route answers 204 |
| reads one | the aggregate, or raises `…NotFoundError` | a missing id is a 404, not an empty body |
| reads many | `list[Aggregate]`, possibly empty | an empty collection is a 200 with `[]` |

Raising for a missing aggregate in the service — rather than returning `None` and letting the route decide — is what keeps every route one line long and every 404 identical.

## Arguments are primitives, not schemas

`open_order(customer_id: int, delivery_address: str)`, never `open_order(request: OpenOrderRequest)`. The service belongs to the application layer and must not import from `interfaces`; a schema is an HTTP concern. When a use case takes many arguments, keyword arguments from the route keep the call readable:

```python
order = await service.add_line(
    order_id, dish_name=request.dish_name, quantity=request.quantity, unit_price=request.unit_price
)
```

## What it may import

Its own `domain` (entities, value objects, exceptions, repository ports), `shared.domain`, `shared.application`, and — only in `application/acl.py` — another context's facade. Never its own `infrastructure`, never `fastapi`, never `sqlalchemy`. A service that needs something the domain cannot express — hashing a password, sending an email, reading a clock that tests must control — declares a port for it in `application/outbound_services.py` and receives the adapter through `__init__`. The IAM context does exactly that; see `iam.md`.

## Using one without FastAPI

Because nothing in it knows about HTTP, a service runs anywhere a session exists — a script, a CLI command, a test:

```python
async with session_factory() as session:
    service = CustomerApplicationService(SqlAlchemyCustomerRepository(session), session)
    await service.register_customer("Ana Torres", "ana@quickbite.dev")
```

In a unit test, pass an in-memory implementation of `CustomerRepository` and any object with `async def commit(self) -> None` and `async def rollback(self) -> None`; nothing else is needed.
