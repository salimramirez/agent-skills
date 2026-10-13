namespace __RootNamespace__.Shared.Domain.Model.Events;

/// <summary>
///     A statement that something meaningful happened in the domain, named in the past tense
///     (<c>OrderPlacedEvent</c>).
/// </summary>
/// <remarks>
///     A plain marker: the domain depends on no messaging library. Aggregates record events through
///     <c>AuditableAggregateRoot.AddDomainEvent</c>; handlers implement <c>IEventHandler&lt;TEvent&gt;</c>.
/// </remarks>
public interface IEvent;
