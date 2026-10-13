# Repositories and persistence

The database context, the mapping of each aggregate, loading an aggregate whole, the repository, and what the MySQL provider does that EF Core's documentation will not tell you.

## One context, one configuration per type

There is one `AppDbContext` for the whole platform (see `shared-kernel.md`). Each bounded context maps its types in `Infrastructure/Persistence/EntityFrameworkCore/Configuration`, one `IEntityTypeConfiguration<T>` per aggregate root and per entity inside one, and the context picks them all up with `ApplyConfigurationsFromAssembly` — adding a bounded context never edits `AppDbContext`.

```csharp
public class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    /// <inheritdoc />
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(order => order.Id);
        builder.Property(order => order.Id).ValueGeneratedOnAdd();

        builder.Property(order => order.CustomerId)
            .HasConversion(customerId => customerId.Value, value => new CustomerId(value))
            .IsRequired();
        builder.HasIndex(order => order.CustomerId);

        builder.Property(order => order.DeliveryAddress).HasMaxLength(Order.DeliveryAddressMaxLength).IsRequired();
        builder.Property(order => order.Status).HasMaxLength(20).IsRequired();

        // The lines are part of the order: loaded with it every time, deleted with it, removed when it drops them.
        builder.HasMany(order => order.Lines).WithOne().HasForeignKey("OrderId").IsRequired()
            .OnDelete(DeleteBehavior.Cascade);
        builder.Navigation(order => order.Lines).AutoInclude();
    }
}

public class OrderLineConfiguration : IEntityTypeConfiguration<OrderLine>
{
    /// <inheritdoc />
    public void Configure(EntityTypeBuilder<OrderLine> builder)
    {
        builder.HasKey(line => line.Id);
        builder.Property(line => line.Id).ValueGeneratedOnAdd();
        builder.Property(line => line.DishName).HasMaxLength(OrderLine.DishNameMaxLength).IsRequired();
        builder.ComplexProperty(line => line.UnitPrice, price =>
        {
            price.Property(p => p.Amount).HasPrecision(10, 2); // holds Money.MaxAmount
            price.Property(p => p.Currency).HasMaxLength(Money.CurrencyLength);
        });
    }
}
```

No table names, no column names: the shared convention writes `orders`, `order_lines`, `customer_id`, `unit_price_amount`. The mapping says only what the convention cannot know — keys, lengths, conversions, relationships. An enum such as `Status` is stored by name in a `varchar(50)` without a word in the mapping; `HasMaxLength(20)` narrows it where the longest name is known to be short.

## Two contexts, one word

The table is named after the class, without its namespace. A `Product` in `Catalog` and another in `Inventory` both want `products`, and the model refuses to build — `dotnet ef migrations add` stops with *The table 'products' cannot be used for entity type 'Product' since it is being used for entity type 'Product' and potentially other entity types, but there is no linking relationship* (measured). Their controllers collide too — see `rest.md`.

Two contexts rarely mean the same thing by one word, and the collision is usually the hint: `Inventory` keeps a `StockItem`, not a `Product`. When the word really is right in both, the second one names its table and its route:

```csharp
builder.ToTable("InventoryProducts");        // the convention writes inventory_products
```
```csharp
[Route("api/v1/inventory/[controller]")]     // /api/v1/inventory/products
```

Measured: both tables created, both `POST`s answered 201, each list showed only its own rows. `new-context.py` refuses a name another context already uses for an aggregate, an entity or a controller, and says this.

## Loading an aggregate whole

An aggregate loaded without its parts is a broken aggregate: `Place()` sees no lines and refuses a full order; a rule that checks "every line is ready" passes on an empty list. The mapping makes it impossible to load an `Order` without its lines:

- **`HasMany(...).WithOne().HasForeignKey("OrderId")`** — the lines point at their order through a shadow foreign key; `OrderLine` has no navigation back and no `OrderId` property, because the domain does not need one.
- **`IsRequired()` with `DeleteBehavior.Cascade`** — a line cannot exist without its order, and deleting an order deletes its lines (`ON DELETE CASCADE` in the migration).
- **`AutoInclude()`** — every query for an order, `Find` included, brings its lines. Measured through the application: a line added in one request was there when the next request placed the order, and the total was right.
- **Removing a line from `_lines` deletes its row.** The relationship is required, so EF Core treats the dropped line as an orphan and deletes it on save — measured: `order_lines` held only the remaining line, no row with a null foreign key.

Why not `OwnsMany`, the textbook mapping for an entity inside an aggregate? Owned types load with their owner too, but an owned type cannot hold a complex property — `OwnedNavigationBuilder` has no `ComplexProperty` (measured) — and `OrderLine` holds a `Money`. A regular entity with `AutoInclude` gives the same guarantee and keeps the value object a value object.

When one query is not enough to load an aggregate — a second level of entities, a filtered collection — the concrete repository overrides `FindByIdAsync` and `ListAsync`, which `BaseRepository` declares `virtual`.

## The repository

The interface is a port, in the domain:

```csharp
public interface IOrderRepository : IBaseRepository<Order>
{
    Task<IEnumerable<Order>> FindByCustomerIdAsync(CustomerId customerId, CancellationToken cancellationToken);
}
```

The implementation extends `BaseRepository<T>` and adds the finders:

```csharp
public class OrderRepository(AppDbContext context) : BaseRepository<Order>(context), IOrderRepository
{
    /// <inheritdoc />
    public async Task<IEnumerable<Order>> FindByCustomerIdAsync(
        CustomerId customerId, CancellationToken cancellationToken)
    {
        return await Context.Set<Order>().Where(order => order.CustomerId == customerId).ToListAsync(cancellationToken);
    }
}
```

- **It speaks the domain**: it takes and returns aggregates and value objects (`CustomerId`), never an `IQueryable`, an entry or a row. A query that leaks `IQueryable` lets the application layer write SQL by accident.
- **Finders take value objects.** `order.CustomerId == customerId` compares a converted value object; EF Core translates it to a comparison of the column.
- **There is no `Update`.** An aggregate loaded through the repository is tracked; the change tracker sees what its methods changed, and `CompleteAsync` saves it.
- **A uniqueness rule is also a unique index** (`builder.HasIndex(customer => customer.Email).IsUnique()`); the repository's `ExistsBy…` gives the readable answer, the index makes the rule true under concurrency — see `application-services.md`.

## What the MySQL provider does

Measured with `MySql.EntityFrameworkCore` 10.0.9 against MySQL 8.0. Each one either has a fix in the kernel or a rule in this skill.

- **Text comparisons ignore case and accents.** The default collation is `utf8mb4_0900_ai_ci`: a unique index rejects `lomo SALTADO` once `Lomo saltado` exists, and `José` matches `jose`. PostgreSQL does neither. Normalize in the value object whatever must compare the same everywhere.
- **Strict mode turns an oversized value into an error, not a truncation**: "Data too long for column", "Out of range value" — a 500, unless the domain refuses the value first. Every `HasMaxLength` and `HasPrecision` has its constant in the domain (see `value-objects.md`).
- **A collection of primitives is stored as garbage.** Left to EF Core's primitive-collection convention, a `List<Role>` was saved as the text `System.Collections.Generic.List`1[…Role]`, with no error, and reading it back threw — the first sign-in of that user was a 500. The IAM context maps its roles with an explicit converter and a value comparer:
  ```csharp
  builder.Ignore(user => user.Roles);
  builder.Property<List<Role>>("_roles")
      .HasColumnName("Roles")
      .HasConversion(
          roles => string.Join(',', roles),
          value => value.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(Enum.Parse<Role>).ToList(),
          new ValueComparer<List<Role>>(
              (left, right) => left!.SequenceEqual(right!),
              roles => roles.Aggregate(0, (hash, role) => HashCode.Combine(hash, role)),
              roles => roles.ToList()))
      .HasMaxLength(100)
      .IsRequired();
  ```
  The comparer gives the change tracker a way to compare two lists by content; without one, EF Core compares the list by reference and a role added to the same list goes unnoticed.
- **`DateTimeOffset` is written to the microsecond and read back to the second.** The shared convention gives the columns `datetime(6)`, and the rows hold `01:44:55.588536`; reading them through the provider returned `01:44:55`, offset `+00:00`. Audit timestamps survive that; anything that needs the fraction back from MySQL stores a `DateTime` in UTC instead (which round-trips the fraction, with `Kind` unspecified). On PostgreSQL the column is `timestamp with time zone`.

## Timestamps and version follow the aggregate

`CreatedAt`, `UpdatedAt` and `Version` are set by the kernel's interceptor, never by the domain. A save that only adds, changes or removes an `OrderLine` leaves the `Order` unchanged as far as EF Core knows; the interceptor follows the line's foreign key to its root and updates the root's `UpdatedAt` and `Version` (measured: without that, adding a line two seconds later left the order's timestamp where it was). A change to any part of the aggregate is a change to the aggregate.

`Version` is a concurrency token on every root (`ConfigureAggregateRoots`, in the kernel), so EF Core writes the update as `UPDATE orders SET … version = @new WHERE id = @id AND version = @read`. A save that finds the row already moved on changes nothing and throws `DbUpdateConcurrencyException`, which the kernel answers with 409, as it answers a MySQL deadlock between two saves that add parts to one aggregate — see `aggregates.md`. Nothing in a bounded context's mapping mentions it; the migration that adds a context adds the `version` column with the rest.

## Migrations

The schema is the migrations: `dotnet ef migrations add <Name>` after every change to the model, read, then applied at start-up by `Migrate()`. The workflow, the start-up log line that signals a forgotten migration, and moving to PostgreSQL are in `project-setup.md`.
