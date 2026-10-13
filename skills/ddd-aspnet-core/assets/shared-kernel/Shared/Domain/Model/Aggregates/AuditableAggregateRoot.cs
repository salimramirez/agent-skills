using __RootNamespace__.Shared.Domain.Model.Events;

namespace __RootNamespace__.Shared.Domain.Model.Aggregates;

/// <summary>
///     Base class of every aggregate root: the identity the database assigns, the audit timestamps,
///     and the domain events raised since the aggregate was loaded.
/// </summary>
/// <remarks>
///     Nothing in the domain writes <see cref="Id" />, <see cref="CreatedAt" /> or <see cref="UpdatedAt" />:
///     the database assigns the first on insert, and the persistence layer sets the other two on every save.
///     The unit of work dispatches <see cref="DomainEvents" /> after the commit and clears them.
/// </remarks>
public abstract class AuditableAggregateRoot
{
    private readonly List<IEvent> _domainEvents = [];

    /// <summary>
    ///     Gets the identity the database assigned on the first save; <c>0</c> before it.
    /// </summary>
    public int Id { get; private set; }

    /// <summary>
    ///     Gets when the aggregate was first saved.
    /// </summary>
    public DateTimeOffset CreatedAt { get; private set; }

    /// <summary>
    ///     Gets when the aggregate was last saved.
    /// </summary>
    public DateTimeOffset UpdatedAt { get; private set; }

    /// <summary>
    ///     Gets the domain events raised since the aggregate was loaded and not yet dispatched.
    /// </summary>
    public IReadOnlyCollection<IEvent> DomainEvents => _domainEvents.AsReadOnly();

    /// <summary>
    ///     Records a domain event, to be dispatched once the change that raised it is committed.
    /// </summary>
    /// <param name="domainEvent">What happened.</param>
    protected void AddDomainEvent(IEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }

    /// <summary>
    ///     Forgets the recorded domain events. Called by the unit of work once it has taken them.
    /// </summary>
    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}
