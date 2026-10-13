using Microsoft.EntityFrameworkCore;
using __RootNamespace__.Shared.Domain.Repositories;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration;

namespace __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

/// <summary>
///     The operations every repository has, over the shared <see cref="AppDbContext" />.
/// </summary>
/// <remarks>
///     A repository whose aggregate needs more than the default query to load whole overrides
///     <see cref="FindByIdAsync" /> and <see cref="ListAsync" />.
/// </remarks>
/// <param name="context">The database context.</param>
/// <typeparam name="TEntity">The aggregate root the repository holds.</typeparam>
public abstract class BaseRepository<TEntity>(AppDbContext context) : IBaseRepository<TEntity>
    where TEntity : class
{
    /// <summary>
    ///     Gets the database context, for the queries of the concrete repository.
    /// </summary>
    protected AppDbContext Context { get; } = context;

    /// <inheritdoc />
    public async Task AddAsync(TEntity entity, CancellationToken cancellationToken = default)
    {
        await Context.Set<TEntity>().AddAsync(entity, cancellationToken);
    }

    /// <inheritdoc />
    public virtual async Task<TEntity?> FindByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        return await Context.Set<TEntity>().FindAsync([id], cancellationToken);
    }

    /// <inheritdoc />
    public void Remove(TEntity entity)
    {
        Context.Set<TEntity>().Remove(entity);
    }

    /// <inheritdoc />
    public virtual async Task<IEnumerable<TEntity>> ListAsync(CancellationToken cancellationToken = default)
    {
        return await Context.Set<TEntity>().ToListAsync(cancellationToken);
    }
}
