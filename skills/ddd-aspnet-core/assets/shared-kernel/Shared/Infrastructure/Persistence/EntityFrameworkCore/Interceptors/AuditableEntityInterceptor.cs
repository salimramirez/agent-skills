using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;
using __RootNamespace__.Shared.Domain.Model.Aggregates;

namespace __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Interceptors;

/// <summary>
///     Sets the audit timestamps of every aggregate being saved: <c>CreatedAt</c> once, on insert;
///     <c>UpdatedAt</c> whenever the root or any entity inside it is inserted, updated or deleted.
/// </summary>
/// <remarks>
///     It writes through the change tracker, so the timestamps keep private setters and no code in the
///     domain can touch them.
/// </remarks>
public sealed class AuditableEntityInterceptor : SaveChangesInterceptor
{
    /// <inheritdoc />
    public override InterceptionResult<int> SavingChanges(DbContextEventData eventData, InterceptionResult<int> result)
    {
        ApplyAuditTimestamps(eventData.Context);
        return base.SavingChanges(eventData, result);
    }

    /// <inheritdoc />
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken cancellationToken = default)
    {
        ApplyAuditTimestamps(eventData.Context);
        return base.SavingChangesAsync(eventData, result, cancellationToken);
    }

    private static void ApplyAuditTimestamps(DbContext? context)
    {
        if (context is null) return;

        var now = DateTimeOffset.UtcNow;
        foreach (var aggregate in ChangedAggregates(context).Distinct())
        {
            var entry = context.Entry(aggregate);
            if (entry.State == EntityState.Deleted) continue;
            if (entry.State == EntityState.Added) entry.Property(root => root.CreatedAt).CurrentValue = now;
            entry.Property(root => root.UpdatedAt).CurrentValue = now;
        }
    }

    // A change to an entity inside an aggregate is a change to the aggregate: adding a line updates the order.
    private static IEnumerable<AuditableAggregateRoot> ChangedAggregates(DbContext context)
    {
        var changed = context.ChangeTracker.Entries()
            .Where(entry => entry.State is EntityState.Added or EntityState.Modified or EntityState.Deleted)
            .ToList();
        foreach (var entry in changed)
        {
            if (entry.Entity is AuditableAggregateRoot aggregate)
            {
                yield return aggregate;
                continue;
            }

            var keysToRoots = entry.Metadata.GetForeignKeys()
                .Where(key => typeof(AuditableAggregateRoot).IsAssignableFrom(key.PrincipalEntityType.ClrType));
            foreach (var foreignKey in keysToRoots)
            {
                var keyValues = foreignKey.Properties.Select(property => entry.Property(property.Name).CurrentValue)
                    .ToArray();
                if (context.Find(foreignKey.PrincipalEntityType.ClrType, keyValues) is AuditableAggregateRoot root)
                    yield return root;
            }
        }
    }
}
