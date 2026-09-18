# Domain events

Something happened that other code must react to: the aggregate records it, the application service publishes it after the commit, a handler reacts.

## The event is a frozen dataclass in the past tense

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderPlaced(DomainEvent):
    """A customer placed an order; the kitchen can start on it.

    Attributes:
        order_id (int): The order that was placed.
        customer_id (int): Who placed it.
    """

    order_id: int
    customer_id: int
```

- It lives in `domain/events.py` and extends the kernel's `DomainEvent`, which adds `occurred_at` (UTC).
- **It is built with keywords** (`OrderPlaced(order_id=…, customer_id=…)`), which `kw_only=True` enforces: an event is read far from where it was raised, and a positional `OrderPlaced(7, 3)` does not say which number is which. The base class declares `occurred_at` keyword-only too, and that is what lets a subclass add fields without defaults after a field that has one.
- **It carries primitives**: ids and the facts a handler needs, not the aggregate. A handler in another context must be able to read it without importing this context's domain types.
- **Past tense, in the ubiquitous language**: `OrderPlaced`, `OrderCancelled`, `PaymentRejected`. Not `PlaceOrderEvent`, not `OrderStatusChanged` — the second one makes every handler inspect the status to learn what happened.

## The aggregate records it

```python
    def place(self) -> None:
        if self._status is not OrderStatus.DRAFT:
            raise ConflictError(f"Cannot place an order that is {self._status}")
        if not self._lines:
            raise ConflictError("Cannot place an order without lines")
        self._status = OrderStatus.PLACED
        assert self.id is not None
        self.record_event(OrderPlaced(order_id=self.id, customer_id=self._customer_id.value))
```

`record_event` (from `AggregateRoot`) only appends to a list. The event is recorded **after** the state changed and **only** if the method succeeded; a method that raised recorded nothing.

## The application service publishes it, after the commit

```python
    async def _save_and_publish(self, order: Order) -> Order:
        events = order.pull_events()
        saved = await self._orders.save(order)
        await self._unit_of_work.commit()
        await self._event_bus.publish(events)
        return saved
```

- **Pull the events before `save`.** The repository returns a *new* aggregate built from the stored row, with an empty event list; the events live only on the instance that raised them.
- **Publish after `commit`.** A handler must never react to something that was rolled back. If the commit fails, the events are dropped with it.
- The consequence is the other half of the trade: a handler runs **after** the change is durable, in its own transaction. If it fails, the change it reacted to stays. That is the right default for reactions — notifying the kitchen, updating a read model, sending an email — and the wrong tool for an invariant. A rule that must hold *atomically* with the change belongs inside the aggregate, not in a handler.

## The bus and the handlers

`shared/application/events.py` holds a small in-process `EventBus` and the one instance the application uses, `event_bus`. Handlers are `async` functions in the reacting context's `application/event_handlers.py`, subscribed by event type through a `register_event_handlers` function:

```python
logger = logging.getLogger(__name__)


async def notify_kitchen(event: DomainEvent) -> None:
    """Tell the kitchen a new order is waiting."""
    assert isinstance(event, OrderPlaced)
    logger.info("Order %s placed by customer %s: notifying the kitchen", event.order_id, event.customer_id)


def register_event_handlers(event_bus: EventBus) -> None:
    """Subscribe this context's handlers; called once, at start-up."""
    event_bus.subscribe(OrderPlaced, notify_kitchen)
```

`main.py` calls each context's `register_event_handlers(event_bus)` in `lifespan`, once per process:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    register_ordering_event_handlers(event_bus)
    yield
    await engine.dispose()
```

What the bus guarantees, measured:

- Every handler subscribed to the event's exact type is called, in subscription order.
- **A handler that raises is logged with its traceback and skipped**; the next handler still runs, and the request that published the event still succeeds.
- Nothing is stored. An event published while the process dies is lost.

A handler that changes data opens its own session and uses an application service, like any other entry point — it is an inbound adapter, just not an HTTP one:

```python
async def open_loyalty_account(event: DomainEvent) -> None:
    assert isinstance(event, CustomerRegistered)
    async with session_factory() as session:
        service = LoyaltyAccountApplicationService(SqlAlchemyLoyaltyAccountRepository(session), session)
        await service.open_account(event.customer_id)
```

Handlers log through `logging.getLogger(__name__)`. Under uvicorn that output appears only because `main.py` calls `logging.basicConfig(level=logging.INFO)`: uvicorn configures its own loggers and leaves the root logger at `WARNING` with no handler, and an `INFO` from the application is silently dropped without that line.

## When in-process is not enough

The bus runs handlers inside the request that published the event, after the commit but before the route returns — a slow handler makes the response slow. And it loses events on a crash. When either matters — a handler calls a slow external service, or a lost event is a lost payment — keep the events and the bus interface, and change what publishes: write the events to an outbox table in the same transaction as the change, and let a worker deliver them. That is a change to `EventBus` and the application service's `_save_and_publish`, not to the aggregates or the handlers.
