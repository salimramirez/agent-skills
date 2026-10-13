# House style

The conventions every file follows, and the smells to look for in each layer.

## XML comments on everything public

Every public type and member carries a `///` comment. The project builds with `<GenerateDocumentationFile>true</GenerateDocumentationFile>`, so a public member without one is a compiler warning (CS1591), and the comments are what the API description shows: the `<summary>` of an action is its summary in Swagger UI, each `<response>` the description of a status code.

```csharp
/// <summary>
///     Sends a draft order to the restaurant.
/// </summary>
/// <exception cref="BusinessRuleViolationException">The order is not a draft, or has no lines.</exception>
public void Place()
```

- **The summary says what the thing is or does, in the ubiquitous language**: "What a customer asks for, from draft until placed or cancelled", not "Order entity class".
- **`<param>` for every parameter**, including the parameters of a positional record and of a primary constructor; `<returns>` for what a method gives back; `<exception cref>` for what a domain method throws on purpose.
- **An implementation says `/// <inheritdoc />`** and nothing else: the interface documents the contract, and a second copy would drift from it.
- **A controller action documents its responses** with `<response code="…">`, next to the matching `[ProducesResponseType]` — see `rest.md`.
- **`///`, never `/** … */`.** Both compile; `///` is what the C# tooling and the rest of the code base expect.

A comment *inside* a method says why, never what: `// Only after the commit: a handler must never react to a change that was rolled back.`

## Types

- **A record for everything without identity**: commands, queries, events, resources, value objects. A class for what has identity or behavior over time: aggregates, entities, services, controllers.
- **Primary constructors for injection, and the parameter used as it is.** `public class OrderCommandService(IOrderRepository orderRepository, IUnitOfWork unitOfWork)` and then `orderRepository.AddAsync(...)` — not a `_orderRepository` field assigned from the parameter, which says the same thing twice.
- **One type per file**, file-scoped `namespace` matching the folder.
- **No prefixes on enums** — `OrderStatus`, not `EOrderStatus`; the type system already says it is an enum. Interfaces keep their `I`.
- **`sealed` on the kernel's leaf types and on value objects**, which nothing should extend. Aggregates, services and controllers are left open.
- **Collection expressions** (`[]`) for empty collections and fields: `private readonly List<OrderLine> _lines = [];`.

## Async and cancellation

- **Every method that does I/O is `async` and takes a `CancellationToken cancellationToken` as its last parameter**, and passes it to everything it awaits. A controller action gets it from ASP.NET Core, which cancels it when the client disconnects.
- **Repository methods end in `Async`** (`FindByIdAsync`); service methods are all named `Handle`, overloaded on the command or query, as the convention of the layer.
- **A middleware takes the token from `context.RequestAborted`**, never as a parameter of `InvokeAsync`: the extra parameters of `InvokeAsync` are resolved from the container, and a `CancellationToken` parameter fails every request with a 500 ("Unable to resolve service for type 'System.Threading.CancellationToken'") — measured.
- **Nothing catches `OperationCanceledException` to answer it.** When the client hangs up there is no one to answer; ASP.NET Core ends the request without logging an error (measured).

## Nullability

`<Nullable>enable</Nullable>` is on. A query service returns `Order?` and the controller answers `null` with a 404. The `null!` that silences the compiler appears in one place only: the private parameterless constructor EF Core uses to materialize an entity, before it sets the properties itself.

A request property declared non-nullable is required: a body without it is a 400 before the controller runs — see `rest.md`.

## Logging

Inject `ILogger<T>` and write message templates with named placeholders:

```csharp
logger.LogInformation("Order {OrderId} placed by customer {CustomerId}: notifying the kitchen",
    domainEvent.OrderId, domainEvent.CustomerId);
```

Never `Console.WriteLine`, never string interpolation inside a log call (the placeholders are what make the entry searchable), and never a token or a password. A record prints every property in `ToString()`, so a command or a resource that carries a password prints it into any log line that formats it — measured. The IAM context's `SignUpCommand`, `SignInCommand` and their resources override `PrintMembers` to leave it out:

```csharp
protected virtual bool PrintMembers(StringBuilder builder)
{
    builder.Append($"Username = {Username}");
    return true;
}
```

## Limits are constants, defined once

A length or an amount the domain refuses is a public constant on the type that refuses it, and the mapping reuses it:

```csharp
public const int DishNameMaxLength = 100;                                        // OrderLine, Domain
builder.Property(line => line.DishName).HasMaxLength(OrderLine.DishNameMaxLength);   // Infrastructure
```

A column narrower than what the domain accepts turns a client's mistake into a 500 — see `value-objects.md`.

## Smells by layer

**Domain**
- A public setter, or a property a service assigns: the rule that guards it has nowhere to live.
- A `using Microsoft.…`, an EF Core attribute, `[JsonIgnore]`: persistence and serialization belong outside.
- `throw new ArgumentException` or `InvalidOperationException`: the framework throws those for bugs. The domain throws `InvalidValueException` or `BusinessRuleViolationException` — see `exceptions.md`.
- A method that does nothing when its condition fails (`if (_lines.Count > 0) Status = OrderStatus.Placed;`): the caller believes it worked. Throw instead.
- A navigation property to another aggregate.

**Application**
- `if (order.Status == OrderStatus.Draft)` before calling `order.Place()`: the aggregate checks that.
- `try { … } catch (Exception) { return Result.Failure(...); }`: it hides bugs as expected failures and logs nothing. Let unexpected exceptions out — see `exceptions.md`.
- A repository from another bounded context.
- `SaveChangesAsync` on the `DbContext` instead of `unitOfWork.CompleteAsync`: the domain events are never dispatched.

**Infrastructure**
- A `HasMaxLength` with a literal, or with no rule in the domain behind it.
- A repository that returns `IQueryable` or an EF Core type: the domain sees persistence through the port only.
- A business decision in a configuration or in a repository query.

**Interfaces**
- A domain type in an action's signature or inside a resource.
- A controller that calls a repository, or that decides a status code from anything but the result.
- `[Produces("application/json")]` on a controller: it turns the problem details the controller writes into plain `application/json` — see `rest.md`.
