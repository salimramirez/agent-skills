using __RootNamespace__.Shared.Domain.Model.Events;

namespace __RootNamespace__.Shared.Application.Internal.EventHandlers;

/// <summary>
///     Reacts to one kind of domain event, after the change that raised it was committed.
/// </summary>
/// <typeparam name="TEvent">The event it reacts to.</typeparam>
public interface IEventHandler<in TEvent> where TEvent : IEvent
{
    /// <summary>
    ///     Reacts to the event.
    /// </summary>
    /// <param name="domainEvent">What happened.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    Task Handle(TEvent domainEvent, CancellationToken cancellationToken);
}
