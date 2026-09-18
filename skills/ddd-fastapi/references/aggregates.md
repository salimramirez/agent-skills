# Aggregates and entities

The root with behavior, the entities inside it, and when a rule belongs to a domain service instead.

## The aggregate root is a class that guards itself

```python
class Order(AggregateRoot):
    """What a customer asks for, from draft until placed or cancelled."""

    def __init__(
        self,
        customer_id: CustomerId,
        delivery_address: str,
        id: int | None = None,
        status: OrderStatus = OrderStatus.DRAFT,
        lines: Iterable[OrderLine] = (),
    ) -> None:
        super().__init__()
        if not delivery_address.strip():
            raise DomainError("Delivery address must not be blank")
        self._id = id
        self._customer_id = customer_id
        self._delivery_address = delivery_address.strip()
        self._status = status
        self._lines = list(lines)

    @property
    def id(self) -> int | None:
        """Identity assigned by the first save; ``None`` before it."""
        return self._id

    @property
    def status(self) -> OrderStatus:
        """Where the order is in its life."""
        return self._status

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        """What was ordered; read-only, change it through the order."""
        return tuple(self._lines)

    @property
    def total(self) -> Money:
        """Sum of every line's subtotal."""
        total = Money.zero()
        for line in self._lines:
            total = total.add(line.subtotal)
        return total

    def add_line(self, dish_name: str, quantity: int, unit_price: Money) -> OrderLine:
        if self._status is not OrderStatus.DRAFT:
            raise ConflictError(f"Cannot add lines to an order that is {self._status}")
        line = OrderLine(dish_name, quantity, unit_price)
        self._lines.append(line)
        return line

    def place(self) -> None:
        if self._status is not OrderStatus.DRAFT:
            raise ConflictError(f"Cannot place an order that is {self._status}")
        if not self._lines:
            raise ConflictError("Cannot place an order without lines")
        self._status = OrderStatus.PLACED
        assert self.id is not None
        self.record_event(OrderPlaced(order_id=self.id, customer_id=self._customer_id.value))
```

What makes it an aggregate rather than a record:

- **Every rule about an order is a method of `Order`.** "Only a draft takes lines", "an empty order cannot be placed", "only a placed order can be cancelled" — each is one `if` inside the method that would break it. No service checks `order.status` before calling `place()`; `place()` checks.
- **State is private and read through properties** — the id included. `order.status` reads; `order.status = …` is an `AttributeError`. The only way to change the status is a method that knows when it may.
- **Collections go out as tuples.** `order.lines.append(...)` is impossible, so no line gets in without passing `add_line`. The tuple protects the collection, not what is in it — which is why the entities inside are read-only too (below).
- **Derived values are properties, computed**, not stored: `total` cannot disagree with the lines.
- **The constructor is also the rehydration path.** The repository builds a stored order with `Order(customer_id, address, id=…, status=…, lines=…)`, which re-runs the constructor's checks. A row that no longer satisfies them fails loudly on load instead of spreading.
- **A transition records an event** after it changes the state. See `domain-events.md`.

The identity is a plain `int | None`: `None` for an aggregate that was never saved, the database's value after. The repository returns a new instance with it set (`order = await repository.save(order)`), so a caller never holds a half-saved object. `place()` asserts the id exists because an event about an order must say which order; an unsaved order cannot be placed, and the assertion says so.

**The anemic version, and why not.** A common layout keeps the entity as a bag of public attributes and puts its validation in a "domain service" that constructs it (an `OrderService.create_order(...)` that validates the input, then calls the constructor). It looks layered and it is the anemic model: the entity can be constructed invalid by anyone who skips the service, and every later rule about it has nowhere obvious to go. Put the check in the constructor or in a value object, and the domain service has nothing left to do.

## Entities inside the aggregate

`OrderLine` has an identity of its own (two lines with the same dish are still two lines), but it is reached, created and changed only through its `Order`:

```python
class OrderLine:
    """One dish in an order, and how many of it."""

    def __init__(self, dish_name: str, quantity: int, unit_price: Money, id: int | None = None) -> None:
        if not dish_name.strip():
            raise DomainError("Dish name must not be blank")
        if quantity < 1:
            raise DomainError("Quantity must be at least 1")
        self._id = id
        self._dish_name = dish_name.strip()
        self._quantity = quantity
        self._unit_price = unit_price

    @property
    def quantity(self) -> int:
        return self._quantity

    # id, dish_name and unit_price: read-only properties, the same way

    @property
    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)
```

- It does **not** extend `AggregateRoot`: only a root records events or has a repository.
- It lives in the same `entities.py` as its root, because it has no meaning without it.
- It is created by the root (`order.add_line(...)` builds it), never by the application service.
- **Its state is read-only, like the root's.** `order.lines` hands out the line objects themselves, so a writable `quantity` would let any code change a placed order — measured: `order.lines[0].quantity = 99` on a placed order went through and the total jumped from 60.00 to 2970.00. With properties it is an `AttributeError`. A change to a line is a method of the root (`order.change_quantity(line_id, quantity)`), which checks the status first.

## Another aggregate is a reference, never an object

An `Order` holds a `CustomerId`, not a `Customer`. One transaction changes one aggregate; if placing an order needed to change a customer in the same breath, the two would have to be loaded, locked and saved together, and the boundary would be wrong. When one must react to the other, it reacts to an event — see `domain-events.md`.

Whether the customer *exists* is a question for the application service, through the ACL, before the order is created — see `anti-corruption-layer.md`.

## When a domain service is right

A domain service is a stateless function or class in `domain/services.py` that holds a rule which **belongs to no single aggregate**: it reads several of them, or a value that lives outside the model.

```python
class DeliveryFeePolicy:
    """What delivering an order costs, from its total and the distance."""

    def fee_for(self, order: Order, distance_km: Decimal) -> Money:
        if order.total.amount >= Decimal("80"):
            return Money.zero()
        return Money(Decimal("5") + Decimal("1.5") * distance_km)
```

It is still pure: it takes what it needs as arguments and does no I/O. The application service fetches the distance (through a port), calls the policy, and hands the result to the aggregate (`order.charge_delivery(fee)`).

Reach for one only when the rule has no single owner. "Validate the input, then build the entity" is not a domain service — that is the aggregate's constructor.

## What does not go in the aggregate

- **I/O of any kind.** No repository call, no `await`, no clock read hidden in a method when the time matters to a rule — take `now: datetime` as an argument, and the application service passes `datetime.now(UTC)`.
- **Presentation.** No `to_dict`, no JSON; the response schema reads the properties.
- **Persistence details.** No ORM base class, no `Column`, no session. The mapping lives in the repository — see `persistence.md`.
