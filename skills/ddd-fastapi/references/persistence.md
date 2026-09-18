# Repositories and persistence

The port in the domain, the ORM models apart from the entities, the mapping between them, and the migrations.

## The port

`domain/repositories.py` declares what the domain needs, as an abstract class over the aggregate:

```python
class OrderRepository(ABC):
    """Collection-like access to :class:`Order` aggregates, lines included."""

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Insert or update an order and its lines.

        Returns:
            Order: The aggregate as stored, with its ``id`` and its lines' ids.
        """

    @abstractmethod
    async def find_by_id(self, order_id: int) -> Order | None:
        """Return the order with its lines, or ``None``."""

    @abstractmethod
    async def find_all(self, customer_id: CustomerId | None = None, status: OrderStatus | None = None) -> list[Order]:
        """Return the orders matching every filter given, ordered by id."""
```

- **One repository per aggregate root**, never per entity: there is no `OrderLineRepository`, because a line is saved with its order.
- **It speaks the domain**: it takes and returns aggregates and value objects (`CustomerId`, `OrderStatus`), never models, never rows, never dicts.
- **`save` returns the aggregate as stored.** The caller replaces its reference with the result, which has the ids the database assigned.
- **Finders are the queries the use cases need**, named like a collection: `find_by_id`, `find_all`, `exists_by_email`. Filters are optional keyword arguments rather than a method per combination.
- **An `ABC`, not a `Protocol`**: the adapter says `class SqlAlchemyOrderRepository(OrderRepository)`, so a missing method is a `TypeError` the moment it is instantiated, and the class states which port it implements.

## The ORM models are not the entities

`infrastructure/models.py` describes tables, and nothing else:

```python
class OrderModel(AuditableModel, Base):
    """The ``orders`` table.

    ``customer_id`` is a plain column, not a foreign key: customers belong to
    another bounded context, and its tables are not this context's to join.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(index=True)
    delivery_address: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20))
    lines: Mapped[list["OrderLineModel"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="OrderLineModel.id"
    )


class OrderLineModel(Base):
    """The ``order_lines`` table: rows owned by an order."""

    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    dish_name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int]
    unit_price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_price_currency: Mapped[str] = mapped_column(String(3))
```

Why two classes for one concept: the entity's shape is dictated by the rules (private state, a tuple of lines, `Money`), the model's by the table (columns, a foreign key, two columns for one `Money`). Mapping the entity itself with SQLAlchemy would work, but the ORM instruments the class — it replaces attributes with descriptors and adds state to every instance — and the domain would then depend on the ORM, however quietly. Two classes and a mapping function keep the dependency pointing one way; the cost is the mapping, which is short and boring, and that is the right place for boring.

The conventions of a model:

- **`__tablename__` is written out**, plural snake_case: `orders`, `order_lines`, `menu_items`.
- **Every aggregate root's model mixes in `AuditableModel`** for `created_at` / `updated_at`. Models of inner entities do not need it.
- **Column types carry lengths** (`String(120)`, `Numeric(10, 2)`) that match the request schema's `max_length`, so a value that passes validation also fits the column.
- **A value object with several fields becomes several columns** with its name as a prefix: `unit_price_amount`, `unit_price_currency`.
- **An enum is a `String` column** holding the enum's value — see `value-objects.md`.
- **A reference to another aggregate in the same context is a plain column with a foreign key**; to an aggregate in another context, a plain column with an index and no foreign key. Contexts do not share constraints.
- **The parts of an aggregate hang from the root with `cascade="all, delete-orphan", lazy="selectin"`.** `selectin` loads them with the root, in the same `await`, so the aggregate always arrives whole; `delete-orphan` removes a row when its entity leaves the collection.

## The adapter maps both ways

```python
class SqlAlchemyOrderRepository(OrderRepository):
    """Stores :class:`Order` aggregates in ``orders`` and ``order_lines``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> Order:
        model = await self._session.merge(self._to_model(order))
        await self._session.flush()
        return self._to_entity(model)

    async def find_by_id(self, order_id: int) -> Order | None:
        model = await self._session.get(OrderModel, order_id)
        return self._to_entity(model) if model else None

    async def find_all(self, customer_id: CustomerId | None = None, status: OrderStatus | None = None) -> list[Order]:
        statement = select(OrderModel).order_by(OrderModel.id)
        if customer_id is not None:
            statement = statement.where(OrderModel.customer_id == customer_id.value)
        if status is not None:
            statement = statement.where(OrderModel.status == status.value)
        return [self._to_entity(model) for model in await self._session.scalars(statement)]

    @staticmethod
    def _to_model(order: Order) -> OrderModel:
        return OrderModel(
            id=order.id,
            customer_id=order.customer_id.value,
            delivery_address=order.delivery_address,
            status=order.status.value,
            lines=[
                OrderLineModel(
                    id=line.id,
                    dish_name=line.dish_name,
                    quantity=line.quantity,
                    unit_price_amount=line.unit_price.amount,
                    unit_price_currency=line.unit_price.currency,
                )
                for line in order.lines
            ],
        )

    @staticmethod
    def _to_entity(model: OrderModel) -> Order:
        return Order(
            CustomerId(model.customer_id),
            model.delivery_address,
            id=model.id,
            status=OrderStatus(model.status),
            lines=[
                OrderLine(line.dish_name, line.quantity, Money(line.unit_price_amount, line.unit_price_currency), id=line.id)
                for line in model.lines
            ],
        )
```

### `save` is `merge` + `flush`, for new and existing aggregates alike

`session.merge()` takes the freshly mapped model and reconciles it with what the session and the database hold, by primary key:

- a model with `id=None` is **inserted**;
- a model with an id **updates** the row, loading it first if the session has not;
- in the collection, a line with an id is **updated in place**, a line with `id=None` is **inserted**, and a row whose line is no longer in the list is **deleted** — that is `delete-orphan`.

All three were measured: adding a second line to a draft kept the first line's id and gave the new one the next; replacing the lines deleted the old rows. `flush()` then sends the SQL without committing, which is what assigns the ids; `_to_entity(model)` builds the aggregate the caller gets back. The commit is the application service's.

So the adapter never asks "is this new?" and never diffs collections by hand; it maps the whole aggregate every time. For an aggregate with hundreds of parts that is a cost worth measuring; for the aggregates DDD recommends — small — it is not.

### The mapping holds no logic

`_to_model` and `_to_entity` copy fields and convert types: `.value` out of a value object, the value object back in. The moment a condition appears there (`status = "PLACED" if … else …`), a rule has leaked out of the domain.

## Queries that are not aggregates

A read that joins several aggregates, aggregates across rows (`count`, `sum`) or feeds a report does not need to rebuild entities. Give it a port of its own — `OrderQueries`, an `ABC` in `application/queries.py` whose methods return plain frozen dataclasses (`OrderSummary`), not aggregates — and an implementation, `SqlAlchemyOrderQueries`, in `infrastructure/queries.py` that selects exactly the columns it needs. The route turns the result into its response schema like any other. The repository stays about loading and saving aggregates.

## Migrations

Every change to a model is an Alembic migration, generated and **read** before it is applied:

```bash
alembic revision --autogenerate -m "add placed_at to orders"
```

```bash
alembic upgrade head
```

The first migration of a context comes right after its models are written — it is the quickest way to find a mapping mistake, before any route exists. Check that `alembic/env.py` imports the context's `infrastructure.models`; autogenerate does not see models that were never imported, and a migration that "detects no changes" for a brand-new context usually means exactly that.

Things autogenerate gets wrong, and the migration must be fixed by hand:

- **A renamed column or table** is detected as a drop plus an add, which loses the data. Replace both with `op.alter_column(..., new_column_name=...)` or `op.rename_table`.
- **A new `NOT NULL` column on a table with rows** fails: add it nullable, fill it with `op.execute("UPDATE …")`, then make it `NOT NULL`, or give it a `server_default`.
- **A changed `server_default`** is not compared unless `compare_server_default=True` is set in `env.py`.

Migrations are committed with the model change that needs them, and never edited once another environment has applied them — write a new one instead.
