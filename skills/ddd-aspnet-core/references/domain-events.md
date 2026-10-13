# Domain events

Something happened that other code must react to: the aggregate records it, the unit of work dispatches it after the commit, a handler reacts.

## The event is a record in the past tense

```csharp
/// <summary>
///     An order was placed: it is on its way to the restaurant.
/// </summary>
/// <param name="OrderId">The order.</param>
/// <param name="CustomerId">The customer who placed it.</param>
public record OrderPlacedEvent(int OrderId, int CustomerId) : IEvent;
```

- **Named in the past tense, in the ubiquitous language**: `OrderPlacedEvent`, `OrderCancelledEvent`, `PaymentRejectedEvent`. Not `PlaceOrderEvent`, not `OrderStatusChangedEvent` — the second makes every handler inspect the status to learn what happened.
- **It carries identities and the facts a handler needs, in primitives**, not the aggregate: a handler in another context must not hold an `Order` it could change.
- **`IEvent` is a plain marker interface** of the kernel. The domain depends on no messaging library.

## The aggregate records it

```csharp
public void Place()
{
    if (Status != OrderStatus.Draft)
        throw new BusinessRuleViolationException($"Cannot place an order that is {Status}.");
    if (_lines.Count == 0)
        throw new BusinessRuleViolationException("Cannot place an order without lines.");
    Status = OrderStatus.Placed;
    AddDomainEvent(new OrderPlacedEvent(Id, CustomerId.Value));
}
```

`AddDomainEvent` (from `AuditableAggregateRoot`) only appends to a list. The event is recorded **after** the state changed and **only** if the method succeeded; a method that threw recorded nothing. The application service does not raise events; the aggregate knows what happened to it.

## The unit of work dispatches it, after the commit

```csharp
public async Task CompleteAsync(CancellationToken cancellationToken = default)
{
    // Taken before saving: a deleted aggregate is no longer tracked afterwards.
    var aggregates = context.ChangeTracker.Entries<AuditableAggregateRoot>()
        .Select(entry => entry.Entity)
        .Where(aggregate => aggregate.DomainEvents.Count > 0)
        .ToList();
    var domainEvents = aggregates.SelectMany(aggregate => aggregate.DomainEvents).ToList();
    aggregates.ForEach(aggregate => aggregate.ClearDomainEvents());

    await context.SaveChangesAsync(cancellationToken);

    // Only after the commit: a handler must never react to a change that was rolled back.
    await eventDispatcher.DispatchAsync(domainEvents, cancellationToken);
}
```

- **After the commit, never before.** If the save fails, the events are dropped with it, and no handler notifies a kitchen about an order that was never placed.
- **The consequence is the other half of the trade:** a handler runs after the change is durable, and what it saves goes in a transaction of its own. If it fails, the change it reacted to stays. That is the right default for reactions — notifying the kitchen, updating a read model, sending an email — and the wrong tool for an invariant. A rule that must hold *atomically* with the change belongs inside the aggregate.
- **Every service commits through `IUnitOfWork`.** A `context.SaveChangesAsync()` called directly saves the change and never dispatches its events.

## A handler reacts, in the application layer

```csharp
public class OrderPlacedEventHandler(ILogger<OrderPlacedEventHandler> logger) : IEventHandler<OrderPlacedEvent>
{
    /// <inheritdoc />
    public Task Handle(OrderPlacedEvent domainEvent, CancellationToken cancellationToken)
    {
        logger.LogInformation("Order {OrderId} placed by customer {CustomerId}: notifying the kitchen",
            domainEvent.OrderId, domainEvent.CustomerId);
        return Task.CompletedTask;
    }
}
```

It lives in `Application/Internal/EventHandlers` of the context that reacts — which is not always the context that raised the event — and it is registered in that context's `Add<Context>Context`:

```csharp
services.AddScoped<IEventHandler<OrderPlacedEvent>, OrderPlacedEventHandler>();
```

A handler that changes something does what a command service does: it loads an aggregate through a repository, calls a method, and completes the unit of work — or, simpler, it builds a command and calls the command service. The events that save raises are dispatched in turn.

## What the dispatcher does with failures

`DomainEventDispatcher` resolves every `IEventHandler<T>` registered for the event's type and runs them **one after another**: they share the request's `DbContext`, which does not allow two operations at once.

**A handler that throws is logged with its stack trace and skipped.** The next handler still runs, and the request that raised the event still succeeds — measured with a handler that always throws, registered before the real one: the response was 200, the order stayed placed in the database, the error was in the log, and the second handler logged its line.

## When this is not enough

The dispatcher runs handlers inside the request that committed the change, after the commit but before the response — a slow handler makes the response slow — and it loses events on a crash between the two. When either matters — a handler calls a slow external service, or a lost event is a lost payment — keep the events and the handlers, and change what dispatches: write the events to an outbox table in the same transaction as the change, and let a background worker deliver them. That is a change to the unit of work and the dispatcher, not to the aggregates or the handlers.

No mediator library is involved. Dispatching events after a commit is a few dozen lines in the kernel; a library would add request pipelines nothing here uses, and the most common one, MediatR, is dual-licensed — reciprocal or commercial — since version 13.
