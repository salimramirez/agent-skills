# Aggregates and entities

The root with behavior, the entities inside it, references to other aggregates, and the typed-key alternative.

## The aggregate root guards itself

```csharp
public class Order : AuditableAggregateRoot
{
    public const int DeliveryAddressMaxLength = 200;

    private readonly List<OrderLine> _lines = [];

    public Order(CustomerId customerId, string deliveryAddress)
    {
        if (string.IsNullOrWhiteSpace(deliveryAddress))
            throw new InvalidValueException("A delivery address is required.");
        if (deliveryAddress.Trim().Length > DeliveryAddressMaxLength)
            throw new InvalidValueException($"A delivery address has at most {DeliveryAddressMaxLength} characters.");
        CustomerId = customerId;
        DeliveryAddress = deliveryAddress.Trim();
        Status = OrderStatus.Draft;
    }

    public Order(OpenOrderCommand command) : this(new CustomerId(command.CustomerId), command.DeliveryAddress)
    {
    }

    // For Entity Framework Core, which sets the properties itself.
    private Order()
    {
        CustomerId = null!;
        DeliveryAddress = null!;
    }

    public CustomerId CustomerId { get; private set; }
    public string DeliveryAddress { get; private set; }
    public OrderStatus Status { get; private set; }
    public IReadOnlyList<OrderLine> Lines => _lines.AsReadOnly();

    public Money Total => _lines.Aggregate(Money.Zero(_lines.FirstOrDefault()?.UnitPrice.Currency ?? "PEN"),
        (total, line) => total.Add(line.Subtotal));

    public OrderLine AddLine(string dishName, int quantity, Money unitPrice)
    {
        if (Status != OrderStatus.Draft)
            throw new BusinessRuleViolationException($"Cannot add lines to an order that is {Status}.");
        if (_lines.Count > 0 && _lines[0].UnitPrice.Currency != unitPrice.Currency)
            throw new InvalidValueException(
                $"This order is in {_lines[0].UnitPrice.Currency}, not {unitPrice.Currency}.");
        var line = new OrderLine(dishName, quantity, unitPrice);
        _lines.Add(line);
        return line;
    }

    public void Place()
    {
        if (Status != OrderStatus.Draft)
            throw new BusinessRuleViolationException($"Cannot place an order that is {Status}.");
        if (_lines.Count == 0)
            throw new BusinessRuleViolationException("Cannot place an order without lines.");
        Status = OrderStatus.Placed;
        AddDomainEvent(new OrderPlacedEvent(Id, CustomerId.Value));
    }

    // Cancel, RemoveLine and HasLine follow the same shape.
}
```

What makes it an aggregate rather than a record:

- **Every rule about an order is a method of `Order`.** "Only a draft takes lines", "an empty order cannot be placed", "only a placed order can be cancelled" — each is one `if` inside the method that would break it. No service checks `order.Status` before calling `Place()`; `Place()` checks.
- **Every setter is private.** The only way to change the status is a method that knows when it may. `order.Status = OrderStatus.Placed` does not compile.
- **The collection goes out read-only.** `Lines` is an `IReadOnlyList` over the private `_lines`, so no line gets in without passing `AddLine`.
- **A derived value is computed, not stored.** `Total` cannot disagree with the lines; EF Core does not map a property with no setter and no backing field, so it never becomes a column.
- **Two exceptions, two meanings.** A value the order cannot accept, whatever its state — a blank address, a currency different from the other lines — is an `InvalidValueException` (400). An operation the order refuses *because of its state* — placing an order that is already placed — is a `BusinessRuleViolationException` (409). See `exceptions.md`.
- **A method never does nothing silently.** A `Place()` that returns without placing when its condition fails leaves the caller believing it worked; it throws instead.
- **A transition records an event** after the state changed and only if it did. An order is saved when it is opened, so by the time it can be placed it has its `Id` — see `domain-events.md`.

**The private parameterless constructor is the one concession to persistence.** EF Core needs a way to create the object before it sets the properties from a row. `private` keeps it out of the code base's reach, and the `null!` assignments tell the compiler that EF Core fills those properties — the only place in the domain where `null!` appears.

**The anemic version, and why not.** The common layout keeps the entity as public properties with public setters and puts its checks in the service that changes it. It looks layered, and it is the anemic model: any code can set `Status = Placed` on an empty order, and every new rule about orders has to be found and repeated in every service that touches one. Put the check in the method or in a value object, and the service has nothing left to decide.

## Entities inside the aggregate

`OrderLine` has an identity of its own — two lines with the same dish are still two lines, and a line is removed by its `Id` — but it is reached, created and changed only through its `Order`:

```csharp
public class OrderLine
{
    public const int DishNameMaxLength = 100;

    internal OrderLine(string dishName, int quantity, Money unitPrice)
    {
        if (string.IsNullOrWhiteSpace(dishName)) throw new InvalidValueException("A dish name is required.");
        if (dishName.Trim().Length > DishNameMaxLength)
            throw new InvalidValueException($"A dish name has at most {DishNameMaxLength} characters.");
        if (quantity < 1) throw new InvalidValueException("The quantity must be at least 1.");
        DishName = dishName.Trim();
        Quantity = quantity;
        UnitPrice = unitPrice;
    }

    // For Entity Framework Core, which sets the properties itself.
    private OrderLine() { DishName = null!; UnitPrice = null!; }

    public int Id { get; private set; }
    public string DishName { get; private set; }
    public int Quantity { get; private set; }
    public Money UnitPrice { get; private set; }
    public Money Subtotal => UnitPrice.Multiply(Quantity);
}
```

- **It does not extend `AuditableAggregateRoot`** and has no repository: only a root has those. Its row's changes still update the root's `UpdatedAt` — see `shared-kernel.md`.
- **It lives in `Domain/Model/Entities`** of the same context, because it has no meaning without its root.
- **Its state is read-only from outside**, like the root's. `Lines` hands out the line objects themselves; with a public setter on `Quantity`, any code could change a placed order's line. With `private set`, `order.Lines[0].Quantity = 99` does not compile (CS0272, measured). A change to a line is a method of the root, which checks the status first.
- **Its constructor is `internal`, and that is a statement of intent, not a lock.** It keeps the constructor out of other assemblies; in a single project, another bounded context can still call it — measured, it compiles. That `new OrderLine(...)` appears only inside `Order` is something a reviewer checks.
- **It is loaded with its root, always.** The mapping makes the lines part of every query for an order — see `persistence.md`. An aggregate loaded without its parts is worse than no aggregate: `Place()` would see no lines and refuse a full order, or a rule that checks "all lines are ready" would pass on an empty list.

## Another aggregate is a reference, never an object

An `Order` holds a `CustomerId`, not a `Customer`, and EF Core is never given a navigation property between them. One transaction changes one aggregate; if placing an order needed to change a customer in the same breath, the two would have to be loaded, locked and saved together, and the boundary would be wrong. When one must react to the other, it reacts to an event — see `domain-events.md`.

A navigation to another aggregate also leaks into the API: the response ends up nesting the other aggregate (`"customer": {"id": 3, "firstName": "…"}`) where a client expects the reference (`"customerId": 3`), and every query for the one loads the other. A resource carries the identity; a client that needs the other aggregate asks for it.

Whether the customer *exists* is a question for the application service, through the ACL, before the order is opened — see `anti-corruption-layer.md`.

## A typed key for the root

The house style keeps the root's identity a database-generated `int` from the base class, and gives types only to references between aggregates (`CustomerId`). EF Core can also generate a *typed* key — measured with MySQL: the column is `AUTO_INCREMENT`, the key is assigned on save, and both `Find` and `==` in a query work:

```csharp
public readonly record struct OrderId(int Value);

builder.HasKey(order => order.Id);
builder.Property(order => order.Id)
    .HasConversion(id => id.Value, value => new OrderId(value))
    .ValueGeneratedOnAdd();
```

It was measured with a `record struct`, whose default, `OrderId(0)`, is the value EF Core takes for "not saved yet". The cost is a converter per key, a `new OrderId(orderId)` in every controller and repository call, and a base class that cannot declare the `Id` any more. Choose it for a context where mixing up two identities is a real risk; the default here stays the `int`.

## When the rule is not one aggregate's

A rule that needs two aggregates at once — a transfer between two accounts, a price that depends on the customer's tier — does not belong to either. Put it in a *domain service*: a stateless class in `Domain/Services` that takes the aggregates (or their values) and decides. The application service loads them, asks the domain service, and saves. Reach for it only after trying to give the rule to one aggregate; most rules have an owner.
