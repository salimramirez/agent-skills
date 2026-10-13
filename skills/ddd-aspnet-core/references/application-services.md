# Commands, queries, and their services

The records that name a use case, the services that run them, what each returns, and the shape every command handler has.

## Commands and queries are records in the domain

```csharp
/// <summary>
///     Open a draft order.
/// </summary>
/// <param name="CustomerId">The customer who orders.</param>
/// <param name="DeliveryAddress">Where to deliver it.</param>
public record OpenOrderCommand(int CustomerId, string DeliveryAddress);

public record GetOrdersByCustomerIdQuery(CustomerId CustomerId);
```

- **A command is a sentence in the ubiquitous language**: `<Verb><Aggregate>Command` — `OpenOrderCommand`, `PlaceOrderCommand`, `AddOrderLineCommand`. It carries what the use case needs and nothing else; the identity of the aggregate it acts on is one of its members (`PlaceOrderCommand(int OrderId)`).
- **A command carries primitives**; the aggregate turns them into value objects, and that is where they are validated — the aggregate takes the command as a constructor argument (`new Order(command)`).
- **A query may carry value objects**, built by the controller from the route or the query string: `new GetOrdersByCustomerIdQuery(new CustomerId(customerId))`.
- **A command checks only what no domain object ever will.** A password never becomes part of the model — only its hash reaches the `User` — so `SignUpCommand` checks it itself, with a property that re-declares the positional parameter:

```csharp
public record SignUpCommand(string Username, string Password, IReadOnlyCollection<Role> Roles)
{
    public string Password { get; } = Password.Length < PasswordMinLength
        ? throw new InvalidValueException($"A password has at least {PasswordMinLength} characters.")
        : Encoding.UTF8.GetByteCount(Password) > PasswordMaxBytes
            ? throw new InvalidValueException($"A password has at most {PasswordMaxBytes} bytes.")
            : Password;
}
```

## The services

The interfaces live in `Application/CommandServices` and `Application/QueryServices`; every method is `Handle`, overloaded on the command or query:

```csharp
public interface IOrderCommandService
{
    Task<Result<Order>> Handle(OpenOrderCommand command, CancellationToken cancellationToken);
    Task<Result<Order>> Handle(AddOrderLineCommand command, CancellationToken cancellationToken);
    Task<Result<Order>> Handle(PlaceOrderCommand command, CancellationToken cancellationToken);
    Task<Result<Order>> Handle(CancelOrderCommand command, CancellationToken cancellationToken);
}

public interface IOrderQueryService
{
    Task<Order?> Handle(GetOrderByIdQuery query, CancellationToken cancellationToken);
    Task<IEnumerable<Order>> Handle(GetAllOrdersQuery query, CancellationToken cancellationToken);
    Task<IEnumerable<Order>> Handle(GetOrdersByCustomerIdQuery query, CancellationToken cancellationToken);
}
```

The split is the light form of CQRS: one model, one database, and the code that changes state kept apart from the code that reads it.

What each one returns:

| Use case | Returns | The controller answers |
| --- | --- | --- |
| create | `Result<Order>` | 201 with the resource, or the failure |
| change, transition | `Result<Order>` — the aggregate after the change | 200 with the resource, or the failure |
| delete | `Result` | 204, or the failure |
| get one | `Order?` | 200, or 404 for `null` |
| list | `IEnumerable<Order>` | 200, possibly an empty array |

A command service returns the aggregate it changed, so the controller answers with the state after the change without a second query. A query service returns domain objects too; turning them into resources is the controller's job.

## The shape of a command handler

Every handler is the same five steps — load, not found, act, commit, success:

```csharp
public async Task<Result<Order>> Handle(PlaceOrderCommand command, CancellationToken cancellationToken)
{
    var order = await orderRepository.FindByIdAsync(command.OrderId, cancellationToken);
    if (order is null) return Result<Order>.NotFound($"Order {command.OrderId} was not found.");

    order.Place();
    await unitOfWork.CompleteAsync(cancellationToken);
    return Result<Order>.Success(order);
}
```

- **It decides nothing.** `order.Place()` checks whether the order may be placed and throws if not; the handler does not look at the status first. If a line of a handler reads `if (order.Status == …)`, that condition belongs in a method of `Order`.
- **It commits through `IUnitOfWork`**, never through the `DbContext`: `CompleteAsync` is what dispatches the domain events after the commit.
- **It returns a result for what the use case can expect** — not found, a conflict, a reference to something that does not exist, a failed sign-in — and lets the domain's exceptions through. See `exceptions.md`.

Creating is the same shape, with the ACL check in place of the load:

```csharp
public async Task<Result<Order>> Handle(OpenOrderCommand command, CancellationToken cancellationToken)
{
    var order = new Order(command);
    if (!await externalCustomerService.ExistsCustomerAsync(order.CustomerId, cancellationToken))
        return Result<Order>.Invalid($"Customer {command.CustomerId} does not exist.");

    await orderRepository.AddAsync(order, cancellationToken);
    await unitOfWork.CompleteAsync(cancellationToken);
    return Result<Order>.Success(order);
}
```

## The order of the checks

What does not exist is a 404, whatever else is wrong with the request; what is malformed is a 400 before anything is compared with what exists; a conflict comes last. An update therefore finds first, builds the value objects second, and checks uniqueness third:

```csharp
var customer = await customerRepository.FindByIdAsync(command.CustomerId, cancellationToken);
if (customer is null) return Result<Customer>.NotFound($"Customer {command.CustomerId} was not found.");

var email = new EmailAddress(command.Email);                       // 400 if malformed
var name = new PersonName(command.FirstName, command.LastName);
if (await customerRepository.ExistsByEmailAsync(email, customer.Id, cancellationToken))
    return Result<Customer>.Conflict($"A customer is already registered with {email.Address}.");

customer.UpdateContactDetails(name, email);
```

A `PUT` to a customer that does not exist, with an invalid email in the body, answers 404 — measured.

## Uniqueness: the check and the index

"No two customers share an email" is checked twice: by the service, which returns a `Conflict` with a message that says what clashed, and by a unique index in the database, which catches the requests that pass the check at the same moment. Measured with ten simultaneous registrations of one address: one 201, eight 409s from the service, and one 409 from the index — `DbUpdateException`, answered by the kernel's exception handler — none a 500. The index is what makes the rule true; the check is what makes the answer readable.

## What a service never does

- **It never catches an exception to turn it into a result.** `try { … } catch (Exception) { return Result.Failure(...); }` makes a bug look like an expected failure, answers the client with the wrong status, and logs nothing. An unexpected exception goes out; the default handler answers 500 and logs it with its stack trace.
- **It never calls another context's repository or service.** It asks the other context's facade, through its own `External<Context>Service`.
- **It never builds a response.** No resource, no status code, no `IActionResult`.

## Why the domain throws and the services return

The two mechanisms answer two different questions. A result says "this use case can end this way, and the caller must decide what that means" — the signature of `Handle` shows it, and the controller cannot read a value that is not there. An exception says "this must not happen" — an order with no lines must not be placed, whoever asks. A constructor cannot return a result, and a returned result can be ignored: a `Result` that nobody reads compiles without a warning, even with warnings as errors (measured). A rule of the domain cannot be optional, so the domain throws.
