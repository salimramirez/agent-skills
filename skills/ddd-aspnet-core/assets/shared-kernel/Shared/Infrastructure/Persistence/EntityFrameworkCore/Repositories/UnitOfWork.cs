using __RootNamespace__.Shared.Domain.Model.Aggregates;
using __RootNamespace__.Shared.Domain.Repositories;
using __RootNamespace__.Shared.Infrastructure.Events;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration;

namespace __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

/// <summary>
///     Commits the changes tracked by the <see cref="AppDbContext" />, then dispatches the domain events.
/// </summary>
/// <param name="context">The database context.</param>
/// <param name="eventDispatcher">Delivers the domain events to their handlers.</param>
public class UnitOfWork(AppDbContext context, DomainEventDispatcher eventDispatcher) : IUnitOfWork
{
    /// <inheritdoc />
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
}
