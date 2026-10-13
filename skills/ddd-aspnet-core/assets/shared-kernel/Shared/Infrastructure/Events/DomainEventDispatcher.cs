using System.Reflection;
using __RootNamespace__.Shared.Application.Internal.EventHandlers;
using __RootNamespace__.Shared.Domain.Model.Events;

namespace __RootNamespace__.Shared.Infrastructure.Events;

/// <summary>
///     Delivers each domain event to every <see cref="IEventHandler{TEvent}" /> registered for its type.
/// </summary>
/// <remarks>
///     Handlers run one after another, in the request that committed the change: they share its database
///     context, which does not allow two operations at once. A handler that throws is logged and skipped;
///     the change it reacted to is already committed, and the next handler still runs.
/// </remarks>
/// <param name="serviceProvider">Resolves the handlers of the current request.</param>
/// <param name="logger">Records the handlers that fail.</param>
public sealed class DomainEventDispatcher(IServiceProvider serviceProvider, ILogger<DomainEventDispatcher> logger)
{
    private static readonly MethodInfo DispatchOneMethod = typeof(DomainEventDispatcher)
        .GetMethod(nameof(DispatchOneAsync), BindingFlags.Instance | BindingFlags.NonPublic)!;

    /// <summary>
    ///     Delivers the events, in the order they were raised.
    /// </summary>
    /// <param name="domainEvents">The events to deliver.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    public async Task DispatchAsync(IEnumerable<IEvent> domainEvents, CancellationToken cancellationToken)
    {
        foreach (var domainEvent in domainEvents)
        {
            var dispatchOne = DispatchOneMethod.MakeGenericMethod(domainEvent.GetType());
            await (Task)dispatchOne.Invoke(this, [domainEvent, cancellationToken])!;
        }
    }

    private async Task DispatchOneAsync<TEvent>(TEvent domainEvent, CancellationToken cancellationToken)
        where TEvent : IEvent
    {
        foreach (var handler in serviceProvider.GetServices<IEventHandler<TEvent>>())
            try
            {
                await handler.Handle(domainEvent, cancellationToken);
            }
            catch (Exception exception) when (exception is not OperationCanceledException)
            {
                logger.LogError(exception, "{Handler} failed to handle {Event}", handler.GetType().Name, domainEvent);
            }
    }
}
