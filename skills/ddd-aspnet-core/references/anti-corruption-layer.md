# Anti-corruption layer

How one bounded context asks another for something without taking on its model: the facade the provider exposes, and the external service that consumes it.

## The provider exposes a facade, in primitives

The context that owns the knowledge — `Customers` — declares what it is willing to answer, in its `Interfaces/Acl` folder:

```csharp
namespace QuickBite.Platform.Customers.Interfaces.Acl;

/// <summary>
///     What the Customers bounded context offers to the other bounded contexts, in primitives only.
/// </summary>
public interface ICustomersContextFacade
{
    Task<bool> ExistsCustomerById(int customerId, CancellationToken cancellationToken);
    Task<int?> FetchCustomerIdByEmail(string email, CancellationToken cancellationToken);
}
```

- **Primitives in, primitives out.** No `Customer`, no `EmailAddress` crosses the boundary: the consumer would start depending on Customers' model, and every change to it would ripple out.
- **The answer for "none" is `null`, not `0`.** A consumer that gets `0` for a customer that does not exist stores it as if it were an identity.
- **It is an inbound adaptor** of the provider — another context driving it — so the interface lives in `Interfaces/Acl`.

The implementation lives in `Application/Acl` and answers through the provider's own query service, translating between primitives and its model:

```csharp
public class CustomersContextFacade(ICustomerQueryService customerQueryService) : ICustomersContextFacade
{
    /// <inheritdoc />
    public async Task<bool> ExistsCustomerById(int customerId, CancellationToken cancellationToken)
    {
        return await customerQueryService.Handle(new GetCustomerByIdQuery(customerId), cancellationToken) is not null;
    }

    /// <inheritdoc />
    public async Task<int?> FetchCustomerIdByEmail(string email, CancellationToken cancellationToken)
    {
        EmailAddress address;
        try
        {
            address = new EmailAddress(email);
        }
        catch (InvalidValueException)
        {
            return null;
        }

        var customer = await customerQueryService.Handle(new GetCustomerByEmailQuery(address), cancellationToken);
        return customer?.Id;
    }
}
```

A string that is not an email address is not a customer's address: the facade answers `null`, not a 400 for a request the caller never made. It is registered with the rest of the provider, in `AddCustomersContext`:

```csharp
services.AddScoped<ICustomersContextFacade, CustomersContextFacade>();
```

Forget that line and, in development, the application does not start: the container finds that the consumer needs a facade nobody registered and names it (measured). It is the line most easily forgotten, because nothing in the provider itself uses the facade.

## The consumer wraps it in an external service

The context that needs the answer — `Ordering` — never calls the facade from its command service. It has its own outbound service that asks in Ordering's terms and translates:

```csharp
namespace QuickBite.Platform.Ordering.Application.Internal.OutboundServices.Acl;

public class ExternalCustomerService(ICustomersContextFacade customersContextFacade)
{
    public async Task<bool> ExistsCustomerAsync(CustomerId customerId, CancellationToken cancellationToken)
    {
        return await customersContextFacade.ExistsCustomerById(customerId.Value, cancellationToken);
    }
}
```

- **It speaks the consumer's language**: it takes a `CustomerId` — Ordering's value object — and the command service never sees a primitive identity of another context.
- **It is the one place that knows the other context.** If Customers splits its facade, changes a method, or moves to another process behind HTTP, this class changes and Ordering's model does not.
- **It is registered by the consumer**, in `AddOrderingContext`: `services.AddScoped<ExternalCustomerService>();`.

The command service uses it before acting:

```csharp
var order = new Order(command);
if (!await externalCustomerService.ExistsCustomerAsync(order.CustomerId, cancellationToken))
    return Result<Order>.Invalid($"Customer {command.CustomerId} does not exist.");
```

A reference in the request body to something that does not exist is `Invalid` — a 400 — not `NotFound`: the URL the client called exists; what it sent cannot be used.

## What crosses, and what does not

| Crosses the boundary | Never crosses |
| --- | --- |
| identities as primitives (`int`), simple facts (`bool`, `string`) | aggregates, entities, value objects of the other context |
| a call to the facade, inside a use case | a repository of the other context, its `DbContext` set, its tables in a query |
| an event, handled by the context that reacts | a navigation property from one context's entity to another's |

The facade is for asking. When one context must react to what happened in another — a customer deleted, an order placed — the provider raises a domain event and the consumer handles it (see `domain-events.md`); the provider does not call the consumer's facade, and the dependency between the two stays one-way.
