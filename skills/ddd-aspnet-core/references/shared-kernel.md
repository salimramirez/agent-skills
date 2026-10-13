# The shared kernel

The classes every bounded context builds on, what each is for, and what never goes into `Shared/`.

Install it with `install.py shared-kernel` (or as part of `install.py project`). It has the same four layers as a context, and it knows no bounded context: nothing in it knows what an `Order` is.

```
Shared/
├── Domain/
│   ├── Model/Aggregates/        AuditableAggregateRoot
│   ├── Model/Events/            IEvent
│   ├── Model/Exceptions/        DomainException, InvalidValueException, BusinessRuleViolationException
│   └── Repositories/            IBaseRepository<T>, IUnitOfWork
├── Application/
│   ├── Model/                   Result<T>, Result, Error, ErrorKind
│   └── Internal/EventHandlers/  IEventHandler<TEvent>
├── Infrastructure/
│   ├── Persistence/EntityFrameworkCore/
│   │   ├── Configuration/                   AppDbContext, Extensions/ModelBuilderExtensions
│   │   ├── Interceptors/                    AuditableEntityInterceptor
│   │   ├── Repositories/                    BaseRepository<T>, UnitOfWork
│   │   └── Extensions/                      DbUpdateExceptionExtensions
│   ├── Events/                              DomainEventDispatcher
│   ├── Pipeline/ExceptionHandlers/          DomainExceptionHandler
│   └── Interfaces/AspNetCore/Configuration/ KebabCaseParameterTransformer
└── Interfaces/Rest/Transform/   ActionResultAssembler, ErrorKindExtensions
```

## Domain

**`AuditableAggregateRoot`** — the base class of every aggregate root. It holds what every root has and no rule of its own:

```csharp
public abstract class AuditableAggregateRoot
{
    private readonly List<IEvent> _domainEvents = [];

    public int Id { get; private set; }
    public DateTimeOffset CreatedAt { get; private set; }
    public DateTimeOffset UpdatedAt { get; private set; }
    public IReadOnlyCollection<IEvent> DomainEvents => _domainEvents.AsReadOnly();

    protected void AddDomainEvent(IEvent domainEvent) { _domainEvents.Add(domainEvent); }
    public void ClearDomainEvents() { _domainEvents.Clear(); }
}
```

Every setter is private: the database assigns `Id`, the interceptor sets the timestamps through the change tracker, and only the aggregate itself records events. An entity *inside* an aggregate does not extend it — see `aggregates.md`.

**`IEvent`** — the marker of a domain event. A plain interface, so the domain depends on no messaging library.

**`DomainException`, `InvalidValueException`, `BusinessRuleViolationException`** — the only exceptions the domain throws. `InvalidValueException` is a value the domain cannot accept (400); `BusinessRuleViolationException` is an operation the aggregate refuses in its current state (409). See `exceptions.md` for why the domain never throws `ArgumentException` or `InvalidOperationException`.

**`IBaseRepository<T>`** — `AddAsync`, `FindByIdAsync`, `Remove`, `ListAsync`. There is no `Update`: an aggregate loaded through a repository is tracked, and the unit of work saves what changed in it.

**`IUnitOfWork`** — `CompleteAsync`: commit the use case, then dispatch its events.

## Application

**`Result<T>`, `Result`, `Error`, `ErrorKind`** — what a command service returns: the value, or an expected failure of one of four kinds.

| `ErrorKind` | Means | Status |
| --- | --- | --- |
| `NotFound` | what the use case acts on does not exist | 404 |
| `Conflict` | the request conflicts with what already exists | 409 |
| `Invalid` | the request refers to something it cannot use | 400 |
| `Unauthorized` | the caller could not be authenticated | 401 |

`result.Value` throws when the result is a failure, so a controller can never read a value that is not there. See `application-services.md`.

**`IEventHandler<TEvent>`** — what a handler implements: `Task Handle(TEvent domainEvent, CancellationToken cancellationToken)`.

## Infrastructure

**`AppDbContext`** — the one database context. It picks up every `IEntityTypeConfiguration<T>` in the assembly, so a new bounded context never edits it, and it applies three conventions to the whole model:

- enums are stored by name, so reordering an enum does not change what the rows mean;
- `DateTimeOffset` columns keep microseconds (`datetime(6)` on MySQL);
- tables are plural snake_case, and columns, keys, foreign keys and indexes snake_case — `order_lines`, `unit_price_amount`, `pk_orders`, `ix_customers_email` — by `UseSnakeCaseNamingConvention()`, applied last so it renames what every configuration produced.

The naming convention reads each column's name *as it is in its table*. A complex property's columns carry the property's name as a prefix there (`UnitPrice_Amount`); read without the table, the name is just `Amount`, and two values of the same type in one entity end up on the same column — measured, and the reason the convention passes a `StoreObjectIdentifier`.

**`AuditableEntityInterceptor`** — sets `CreatedAt` on insert and `UpdatedAt` on every save of an aggregate, **including a save in which only an entity inside it changed**. Adding a line to an order inserts a row in `order_lines` and leaves the `Order` itself unchanged as far as EF Core knows; the interceptor follows the line's foreign key to its root and updates the root's `UpdatedAt` too (measured: without it, the order's timestamp did not move).

**`BaseRepository<T>`** — the four operations of `IBaseRepository<T>`, plus a protected `Context` for the queries of the concrete repository. `FindByIdAsync` and `ListAsync` are `virtual`, so a repository that needs a different query to load its aggregate overrides them.

**`UnitOfWork`** — takes the events of every changed aggregate, clears them, commits, and only then dispatches them. See `domain-events.md`.

**`DbUpdateExceptionExtensions.IsUniqueConstraintViolation()`** — the one line in the kernel that knows the database: MySQL's error 1062. Switching databases changes this line — see `project-setup.md`.

**`DomainEventDispatcher`** — delivers each event to every registered `IEventHandler<T>` for its type, one after another, logging and skipping a handler that throws.

**`DomainExceptionHandler`** — an `IExceptionHandler` that answers `InvalidValueException`, `BusinessRuleViolationException` and a unique-index conflict with problem details, and leaves everything else to the default 500. See `exceptions.md`.

**`KebabCaseParameterTransformer`** — writes the `[controller]` route token in kebab-case.

## Interfaces

**`ActionResultAssembler.ToActionResult(...)`** — turns a `Result<T>` or a `Result` into the controller's response: the success the controller describes, or `Problem(...)` with the status of the `ErrorKind`. **`ErrorKindExtensions.ToStatusCode()`** is the table above, in code; the exception handler uses it too, so a kind of failure has one status code wherever it comes from.

## What stays out

The kernel grows only when every context needs the same thing. A `Money` used by two contexts is not a reason to share it: each context models money in its own terms, and sharing the class couples their changes. A rule that mentions a business concept belongs in the context that owns the concept. Before adding a class to `Shared/`, ask whether a second context would have written exactly the same one.
