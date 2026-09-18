# Value objects

Concepts with a rule and no identity: frozen dataclasses that validate themselves.

## A frozen dataclass that refuses to exist in a bad state

```python
@dataclass(frozen=True, slots=True)
class EmailAddress:
    """An email address, stored lower-cased.

    Attributes:
        value (str): The address, e.g. ``ana@quickbite.dev``.
    """

    value: str

    def __post_init__(self) -> None:
        """Normalize the address and reject one that cannot be an email.

        Raises:
            DomainError: If the value is not an email address.
        """
        normalized = self.value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise DomainError(f"'{self.value}' is not a valid email address")
        object.__setattr__(self, "value", normalized)
```

- **`frozen=True`** — assigning to a field raises `FrozenInstanceError`. A value object is replaced, never changed.
- **`slots=True`** — no `__dict__`, so no attribute can be added by accident, and the instance is smaller.
- **Equality and hashing come for free**: two `EmailAddress("ana@quickbite.dev")` are equal and can be set members and dict keys. That is what "defined by its attributes" means in code.
- **`__post_init__` is the constructor's guard.** It validates, and normalizes through `object.__setattr__` — the one sanctioned way to write a frozen field, and only here.
- **It raises `DomainError`** (400), not `ValueError`. A `ValueError` that escapes is a 500 — a bug — which is exactly what a bad email is not.

A value object is **created from primitives at the boundary of the application service**, not in the route: the route passes `request.email` (a `str`), the service builds `EmailAddress(email)`. The domain type never appears in a schema.

## Operations return new instances

```python
@dataclass(frozen=True, slots=True)
class Money:
    """An amount in one currency."""

    amount: Decimal
    currency: str = "PEN"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise DomainError("An amount of money cannot be negative")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise DomainError(f"'{self.currency}' is not a currency code")
        object.__setattr__(self, "amount", self.amount.quantize(Decimal("0.01")))
        object.__setattr__(self, "currency", self.currency.upper())

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise DomainError(f"Cannot add {other.currency} to {self.currency}")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: int) -> "Money":
        return Money(self.amount * factor, self.currency)

    @classmethod
    def zero(cls, currency: str = "PEN") -> "Money":
        return cls(Decimal("0"), currency)
```

Money is `Decimal`, never `float`: `0.1 + 0.2` is not `0.3` in binary floating point, and a total that is off by a cent is a defect. The request schema declares `unit_price: Decimal` too, so the value is never a float on its way in, and the response serializes it as a string (`"32.50"`), which is how JSON keeps it exact.

## References to other aggregates

An aggregate never holds another aggregate — it holds its identity, as a value object named after it:

```python
@dataclass(frozen=True, slots=True)
class CustomerId:
    """Reference to a customer, who lives in the Customers context."""

    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise DomainError("Customer id must be positive")
```

`order.customer_id` is a `CustomerId`, not an `int`: a signature like `find_all(customer_id: CustomerId | None, status: OrderStatus | None)` cannot receive the arguments in the wrong order, and the type says which context the number belongs to. Inside its own context an aggregate's id stays a plain `int | None` — see `aggregates.md`.

## Enums

A closed set of values is a `StrEnum`:

```python
class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
```

- **Name and value are the same string.** A `StrEnum` member *is* a `str`, so it serializes to JSON as `"PLACED"` and compares equal to it; keeping name and value identical means the database, the API and the code all spell it one way.
- **Stored as a `String` column**, and converted in the repository (`status=order.status.value` on the way in, `OrderStatus(model.status)` on the way out). Not SQLAlchemy's `Enum` type: by default it stores the member *names* and creates a PostgreSQL enum type, whose values a later migration can add to but not easily remove — a cost that buys nothing when the application already guards the values.
- **A route may take the enum directly** as a query parameter (`status: OrderStatus | None = None`): FastAPI validates it and documents the allowed values, and an unknown one is a 422 before any code runs.

## Where a rule about several values goes

A rule about **one value** goes in its `__post_init__`. A rule that relates **fields of one value object** (a date range whose end is after its start) goes there too. A rule that relates **several attributes of an aggregate** (the delivery address must be in a zone the restaurant serves) goes in the aggregate. A rule that needs **data from outside the aggregate** goes in a domain service or is checked by the application service before it asks the aggregate to act — see `aggregates.md`.

## When not to make one

A value object earns its place with a rule, a unit, or a meaning a primitive would lose. `delivery_address: str` with "must not be blank" checked by the aggregate is fine until addresses gain structure (a district, a reference, coordinates); then it becomes `DeliveryAddress`. Wrapping every string on day one only adds `.value` everywhere.
